# [NEXUS IDENTITY] ID: 5603947591919373997 | DATE: 2025-11-19

"""
Система метрик и мониторинга блокировок Rate Limiting
Основана на стандартах мониторинга 1С:Предприятие (ЦУП/КИП)

Модуль обеспечивает:
- Сбор метрик блокировок и производительности
- Экспорт в Prometheus формат
- Система алертов при превышении порогов
- Данные для Grafana дашбордов
- Мониторинг в реальном времени
- Health checks для всех компонентов
"""

import functools
import json
import logging
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Уровни критичности алертов"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class MetricType(Enum):
    """Типы метрик"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class RateLimitMetric:
    """Структура метрики блокировки"""
    timestamp: datetime
    metric_name: str
    metric_type: MetricType
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    def to_prometheus(self) -> str:
        """Формат метрики для Prometheus"""
        label_str = ""
        if self.labels:
            labels_str = ','.join([f'{k}="{v}"' for k, v in self.labels.items()])
            label_str = f'{{{labels_str}}}'
        
        timestamp_ms = int(self.timestamp.timestamp() * 1000)
        return f"{self.metric_name}{label_str} {self.value} {timestamp_ms}"


@dataclass
class AlertRule:
    """Правило генерации алерта"""
    name: str
    metric_name: str
    condition: str  # ">", "<", ">=", "<=", "==", "!="
    threshold: float
    severity: AlertSeverity
    duration: timedelta = field(default_factory=lambda: timedelta(seconds=0))
    labels: Dict[str, str] = field(default_factory=dict)
    description: str = ""
    enabled: bool = True
    
    def evaluate(self, value: float, duration: timedelta) -> bool:
        """Проверка условия алерта"""
        if not self.enabled:
            return False
        
        if duration < self.duration:
            return False
            
        try:
            if self.condition == ">":
                return value > self.threshold
            elif self.condition == "<":
                return value < self.threshold
            elif self.condition == ">=":
                return value >= self.threshold
            elif self.condition == "<=":
                return value <= self.threshold
            elif self.condition == "==":
                return value == self.threshold
            elif self.condition == "!=":
                return value != self.threshold
            else:
                logger.error(f"Unknown condition: {self.condition}")
                return False
        except Exception as e:
            logger.error(f"Error evaluating alert rule {self.name}: {e}")
            return False


@dataclass
class ActiveAlert:
    """Активный алерт"""
    alert_id: str
    rule: AlertRule
    current_value: float
    start_time: datetime
    last_update: datetime
    count: int = 1
    resolved: bool = False
    
    def update(self, value: float):
        """Обновление значения алерта"""
        self.current_value = value
        self.last_update = datetime.now()
        self.count += 1


class RateLimitMetrics:
    """Сборщик метрик блокировок Rate Limiting"""
    
    def __init__(self, max_history_size: int = 10000):
        self.max_history_size = max_history_size
        self._lock = threading.RLock()
        
        # Метрики
        self._metrics: deque = deque(maxlen=max_history_size)
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        
        # Детализация по IP, пользователю, MCP tool
        self._ip_metrics: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self._user_metrics: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self._tool_metrics: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        
        # RPS метрики (окно 1 минута)
        self._rps_windows: Dict[str, deque] = defaultdict(lambda: deque(maxlen=60))
        
        # Активные ограничения
        self._active_limits: Dict[str, Dict[str, Any]] = {}
        
        # Health check
        self._health_status = "healthy"
        self._last_update = datetime.now()
        
    def record_request(self, 
                      ip: str = None, 
                      user_id: str = None, 
                      tool: str = None,
                      response_time: float = None,
                      blocked: bool = False,
                      limit_exceeded: bool = False):
        """Запись метрик запроса"""
        with self._lock:
            timestamp = datetime.now()
            base_labels = {}
            
            if ip:
                base_labels['ip'] = ip
            if user_id:
                base_labels['user_id'] = user_id
            if tool:
                base_labels['tool'] = tool
            
            # Общие метрики
            self._record_counter('rate_limit_requests_total', base_labels, 1)
            
            if blocked or limit_exceeded:
                self._record_counter('rate_limit_blocked_total', base_labels, 1)
                self._record_gauge('rate_limit_blocked_current', base_labels, 1)
            else:
                self._record_gauge('rate_limit_blocked_current', base_labels, 0)
            
            # Время отклика
            if response_time is not None:
                self._record_histogram('rate_limit_response_time_seconds', response_time, base_labels)
            
            # RPS метрики
            if ip:
                self._record_rps('ip', ip)
            if user_id:
                self._record_rps('user', user_id)
            if tool:
                self._record_rps('tool', tool)
            
            self._last_update = datetime.now()
    
    def _record_counter(self, name: str, labels: Dict[str, str], value: float):
        """Запись счетчика"""
        metric = RateLimitMetric(
            timestamp=datetime.now(),
            metric_name=name,
            metric_type=MetricType.COUNTER,
            value=value,
            labels=labels.copy()
        )
        self._metrics.append(metric)
        
        # Обновление счетчика
        counter_key = f"{name}:{json.dumps(labels, sort_keys=True)}"
        self._counters[counter_key] += value
    
    def _record_gauge(self, name: str, labels: Dict[str, str], value: float):
        """Запись показателя"""
        metric = RateLimitMetric(
            timestamp=datetime.now(),
            metric_name=name,
            metric_type=MetricType.GAUGE,
            value=value,
            labels=labels.copy()
        )
        self._metrics.append(metric)
        
        gauge_key = f"{name}:{json.dumps(labels, sort_keys=True)}"
        self._gauges[gauge_key] = value
    
    def _record_histogram(self, name: str, value: float, labels: Dict[str, str]):
        """Запись гистограммы"""
        metric = RateLimitMetric(
            timestamp=datetime.now(),
            metric_name=name,
            metric_type=MetricType.HISTOGRAM,
            value=value,
            labels=labels.copy()
        )
        self._metrics.append(metric)
        
        hist_key = f"{name}:{json.dumps(labels, sort_keys=True)}"
        self._histograms[hist_key].append(value)
        
        # Ограничение размера гистограммы
        if len(self._histograms[hist_key]) > 1000:
            self._histograms[hist_key] = self._histograms[hist_key][-500:]
    
    def _record_rps(self, entity_type: str, entity_id: str):
        """Запись RPS метрики"""
        timestamp = datetime.now()
        
        # Добавляем метку времени в окно RPS
        rps_key = f"{entity_type}:{entity_id}"
        self._rps_windows[rps_key].append(timestamp)
        
        # Рассчитываем RPS за последнюю минуту
        now = timestamp
        one_minute_ago = now - timedelta(minutes=1)
        
        # Удаляем старые записи
        while (self._rps_windows[rps_key] and 
               self._rps_windows[rps_key][0] < one_minute_ago):
            self._rps_windows[rps_key].popleft()
        
        # Записываем RPS как gauge метрику
        rps_value = len(self._rps_windows[rps_key])
        labels = {entity_type: entity_id}
        self._record_gauge('rate_limit_requests_per_second', labels, rps_value)
    
    def register_active_limit(self, limit_id: str, limit_data: Dict[str, Any]):
        """Регистрация активного ограничения"""
        with self._lock:
            self._active_limits[limit_id] = {
                **limit_data,
                'registered_at': datetime.now(),
                'last_access': datetime.now()
            }
            
            # Обновляем gauge метрику
            self._record_gauge('rate_limit_active_limits', {}, len(self._active_limits))
    
    def unregister_active_limit(self, limit_id: str):
        """Отмена регистрации активного ограничения"""
        with self._lock:
            if limit_id in self._active_limits:
                del self._active_limits[limit_id]
                self._record_gauge('rate_limit_active_limits', {}, len(self._active_limits))
    
    def update_limit_access(self, limit_id: str):
        """Обновление времени доступа к ограничению"""
        with self._lock:
            if limit_id in self._active_limits:
                self._active_limits[limit_id]['last_access'] = datetime.now()
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Получение сводки метрик"""
        with self._lock:
            return {
                'total_requests': sum(v for k, v in self._counters.items() 
                                    if k.startswith('rate_limit_requests_total:')),
                'total_blocked': sum(v for k, v in self._counters.items() 
                                   if k.startswith('rate_limit_blocked_total:')),
                'active_limits': len(self._active_limits),
                'unique_ips': len([k for k in self._rps_windows.keys() if k.startswith('ip:')]),
                'unique_users': len([k for k in self._rps_windows.keys() if k.startswith('user:')]),
                'unique_tools': len([k for k in self._rps_windows.keys() if k.startswith('tool:')]),
                'last_update': self._last_update.isoformat(),
                'health_status': self._health_status
            }
    
    def get_recent_metrics(self, minutes: int = 5) -> List[RateLimitMetric]:
        """Получение недавних метрик"""
        with self._lock:
            cutoff = datetime.now() - timedelta(minutes=minutes)
            return [m for m in self._metrics if m.timestamp >= cutoff]
    
    def set_health_status(self, status: str):
        """Установка статуса здоровья системы"""
        self._health_status = status
        self._last_update = datetime.now()
        self._record_gauge('rate_limit_health_status', {}, 1 if status == "healthy" else 0)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Получение статуса здоровья"""
        with self._lock:
            return {
                'status': self._health_status,
                'last_update': self._last_update.isoformat(),
                'active_limits_count': len(self._active_limits),
                'total_metrics_count': len(self._metrics)
            }


class PrometheusExporter:
    """Экспортер метрик в Prometheus формат"""
    
    def __init__(self, metrics_collector: RateLimitMetrics):
        self.metrics_collector = metrics_collector
        self._export_lock = threading.Lock()
    
    def generate_prometheus_metrics(self) -> str:
        """Генерация метрик в формате Prometheus"""
        with self._export_lock:
            output = []
            
            # Заголовок с комментариями
            output.extend([
                "# HELP Rate limiting metrics generated by 1C Performance Monitoring",
                "# TYPE rate_limit_requests_total counter",
                "# TYPE rate_limit_blocked_total counter",
                "# TYPE rate_limit_requests_per_second gauge",
                "# TYPE rate_limit_active_limits gauge",
                "# TYPE rate_limit_response_time_seconds histogram",
                "# TYPE rate_limit_blocked_current gauge",
                "# TYPE rate_limit_health_status gauge",
                ""
            ])
            
            # Получаем метрики и экспортируем их
            metrics = self.metrics_collector.get_recent_metrics(minutes=10)
            
            for metric in metrics:
                try:
                    output.append(metric.to_prometheus())
                except Exception as e:
                    logger.warning(f"Error exporting metric {metric.metric_name}: {e}")
            
            # Добавляем summary метрики
            output.extend(self._generate_summary_metrics())
            
            return "\n".join(output)
    
    def _generate_summary_metrics(self) -> List[str]:
        """Генерация summary метрик"""
        output = []
        
        # Получаем сводку
        summary = self.metrics_collector.get_metrics_summary()
        
        # Добавляем summary метрики без labels
        summary_metrics = [
            f"rate_limit_summary_total_requests {summary['total_requests']}",
            f"rate_limit_summary_total_blocked {summary['total_blocked']}",
            f"rate_limit_summary_active_limits {summary['active_limits']}",
            f"rate_limit_summary_unique_ips {summary['unique_ips']}",
            f"rate_limit_summary_unique_users {summary['unique_users']}",
            f"rate_limit_summary_unique_tools {summary['unique_tools']}"
        ]
        
        output.extend(summary_metrics)
        output.append("")  # Пустая строка в конце
        
        return output
    
    def export_to_file(self, filepath: str):
        """Экспорт метрик в файл"""
        try:
            metrics_text = self.generate_prometheus_metrics()
            with open(filepath, 'w') as f:
                f.write(metrics_text)
            logger.info(f"Metrics exported to {filepath}")
        except Exception as e:
            logger.error(f"Error exporting metrics to file: {e}")
            raise


class AlertManager:
    """Система алертов при превышении порогов"""
    
    def __init__(self, metrics_collector: RateLimitMetrics):
        self.metrics_collector = metrics_collector
        self._lock = threading.RLock()
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, ActiveAlert] = {}
        self.alert_history: List[Dict[str, Any]] = []
        
        # Threading для мониторинга
        self._monitoring_thread = None
        self._stop_monitoring = False
        self._monitoring_interval = 5  # секунд
        
        # Установка стандартных правил алертов
        self._setup_default_alert_rules()
    
    def _setup_default_alert_rules(self):
        """Настройка стандартных правил алертов"""
        default_rules = [
            AlertRule(
                name="high_block_rate",
                metric_name="rate_limit_summary_blocked_rate",
                condition=">",
                threshold=0.1,  # 10% блокировок
                severity=AlertSeverity.WARNING,
                duration=timedelta(minutes=2),
                description="Высокий процент заблокированных запросов"
            ),
            AlertRule(
                name="excessive_rps",
                metric_name="rate_limit_requests_per_second",
                condition=">",
                threshold=100,  # 100 RPS с одного IP
                severity=AlertSeverity.CRITICAL,
                duration=timedelta(seconds=30),
                labels={"ip": ""},
                description="Превышение лимита RPS"
            ),
            AlertRule(
                name="slow_response",
                metric_name="rate_limit_response_time_seconds",
                condition=">",
                threshold=1.0,  # 1 секунда
                severity=AlertSeverity.WARNING,
                duration=timedelta(minutes=1),
                description="Медленное время отклика rate limiting"
            ),
            AlertRule(
                name="system_unhealthy",
                metric_name="rate_limit_health_status",
                condition="<",
                threshold=1.0,
                severity=AlertSeverity.EMERGENCY,
                duration=timedelta(seconds=10),
                description="Система мониторинга нездорова"
            ),
            AlertRule(
                name="too_many_active_limits",
                metric_name="rate_limit_active_limits",
                condition=">",
                threshold=1000,
                severity=AlertSeverity.WARNING,
                duration=timedelta(minutes=5),
                description="Слишком много активных ограничений"
            )
        ]
        
        for rule in default_rules:
            self.add_alert_rule(rule)
    
    def add_alert_rule(self, rule: AlertRule):
        """Добавление правила алерта"""
        with self._lock:
            self.alert_rules[rule.name] = rule
            logger.info(f"Added alert rule: {rule.name}")
    
    def remove_alert_rule(self, rule_name: str):
        """Удаление правила алерта"""
        with self._lock:
            if rule_name in self.alert_rules:
                del self.alert_rules[rule_name]
                logger.info(f"Removed alert rule: {rule_name}")
    
    def start_monitoring(self):
        """Запуск мониторинга алертов"""
        if self._monitoring_thread is None or not self._monitoring_thread.is_alive():
            self._stop_monitoring = False
            self._monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            self._monitoring_thread.start()
            logger.info("Alert monitoring started")
    
    def stop_monitoring(self):
        """Остановка мониторинга алертов"""
        self._stop_monitoring = True
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
        logger.info("Alert monitoring stopped")
    
    def _monitoring_loop(self):
        """Основной цикл мониторинга"""
        while not self._stop_monitoring:
            try:
                self._check_alerts()
                time.sleep(self._monitoring_interval)
            except Exception as e:
                logger.error(f"Error in alert monitoring loop: {e}")
                time.sleep(self._monitoring_interval)
    
    def _check_alerts(self):
        """Проверка всех алертов"""
        with self._lock:
            # Получаем сводку метрик
            summary = self.metrics_collector.get_metrics_summary()
            
            # Проверяем каждое правило
            for rule_name, rule in self.alert_rules.items():
                try:
                    self._evaluate_rule(rule, summary)
                except Exception as e:
                    logger.error(f"Error evaluating alert rule {rule_name}: {e}")
    
    def _evaluate_rule(self, rule: AlertRule, summary: Dict[str, Any]):
        """Оценка одного правила алерта"""
        alert_key = rule.name
        current_time = datetime.now()
        
        # Определяем текущее значение метрики
        current_value = self._get_metric_value(rule, summary)
        
        if current_value is None:
            return
        
        # Проверяем условие
        if rule.evaluate(current_value, timedelta()):
            if alert_key not in self.active_alerts:
                # Новый алерт
                alert = ActiveAlert(
                    alert_id=f"{rule.name}_{int(current_time.timestamp())}",
                    rule=rule,
                    current_value=current_value,
                    start_time=current_time,
                    last_update=current_time
                )
                self.active_alerts[alert_key] = alert
                self._trigger_alert(alert)
            else:
                # Обновляем существующий алерт
                self.active_alerts[alert_key].update(current_value)
        else:
            # Условие не выполнено, проверяем нужно ли разрешить алерт
            if alert_key in self.active_alerts:
                alert = self.active_alerts[alert_key]
                duration = current_time - alert.start_time
                if rule.duration == timedelta(0) or duration >= rule.duration:
                    self._resolve_alert(alert_key)
    
    def _get_metric_value(self, rule: AlertRule, summary: Dict[str, Any]) -> Optional[float]:
        """Получение значения метрики для проверки правила"""
        metric_name = rule.metric_name
        
        if metric_name == "rate_limit_summary_blocked_rate":
            if summary['total_requests'] > 0:
                return summary['total_blocked'] / summary['total_requests']
            return 0.0
        
        elif metric_name == "rate_limit_requests_per_second":
            # Ищем максимальный RPS среди всех сущностей
            metrics = self.metrics_collector.get_recent_metrics(minutes=1)
            max_rps = 0
            for metric in metrics:
                if (metric.metric_name == "rate_limit_requests_per_second" and 
                    all(rule.labels.get(k) == v for k, v in metric.labels.items() if k in rule.labels)):
                    max_rps = max(max_rps, metric.value)
            return max_rps
        
        elif metric_name == "rate_limit_response_time_seconds":
            # Ищем среднее время отклика
            response_times = []
            metrics = self.metrics_collector.get_recent_metrics(minutes=1)
            for metric in metrics:
                if metric.metric_name == "rate_limit_response_time_seconds":
                    response_times.append(metric.value)
            
            return sum(response_times) / len(response_times) if response_times else 0.0
        
        elif metric_name == "rate_limit_health_status":
            health = self.metrics_collector.get_health_status()
            return 1.0 if health['status'] == 'healthy' else 0.0
        
        elif metric_name == "rate_limit_active_limits":
            return summary['active_limits']
        
        else:
            logger.warning(f"Unknown metric name for alert rule: {metric_name}")
            return None
    
    def _trigger_alert(self, alert: ActiveAlert):
        """Срабатывание алерта"""
        logger.warning(f"ALERT TRIGGERED: {alert.rule.name} - {alert.rule.description}")
        
        # Добавляем в историю
        self.alert_history.append({
            'alert_id': alert.alert_id,
            'rule_name': alert.rule.name,
            'severity': alert.rule.severity.value,
            'description': alert.rule.description,
            'triggered_at': alert.start_time.isoformat(),
            'current_value': alert.current_value,
            'threshold': alert.rule.threshold,
            'status': 'triggered'
        })
        
        # Здесь можно добавить отправку уведомлений (email, Slack, etc.)
        self._send_alert_notification(alert)
    
    def _resolve_alert(self, alert_key: str):
        """Разрешение алерта"""
        if alert_key in self.active_alerts:
            alert = self.active_alerts[alert_key]
            logger.info(f"ALERT RESOLVED: {alert.rule.name}")
            
            # Добавляем в историю
            self.alert_history.append({
                'alert_id': alert.alert_id,
                'rule_name': alert.rule.name,
                'severity': alert.rule.severity.value,
                'description': alert.rule.description,
                'triggered_at': alert.start_time.isoformat(),
                'resolved_at': datetime.now().isoformat(),
                'duration_seconds': (datetime.now() - alert.start_time).total_seconds(),
                'status': 'resolved'
            })
            
            del self.active_alerts[alert_key]
    
    def _send_alert_notification(self, alert: ActiveAlert):
        """Отправка уведомления об алерте"""
        # Базовая реализация - логирование
        # В реальной системе здесь можно добавить отправку в:
        # - Email
        # - Slack/Teams
        # - Prometheus Alertmanager
        # - etc.
        
        message = f"""
        🚨 Rate Limiting Alert
        
        Rule: {alert.rule.name}
        Severity: {alert.rule.severity.value.upper()}
        Description: {alert.rule.description}
        Current Value: {alert.current_value}
        Threshold: {alert.rule.threshold}
        Triggered At: {alert.start_time.isoformat()}
        """
        
        if alert.rule.severity == AlertSeverity.EMERGENCY:
            logger.critical(message)
        elif alert.rule.severity == AlertSeverity.CRITICAL:
            logger.error(message)
        elif alert.rule.severity == AlertSeverity.WARNING:
            logger.warning(message)
        else:
            logger.info(message)
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Получение активных алертов"""
        with self._lock:
            return [
                {
                    'alert_id': alert.alert_id,
                    'rule_name': alert.rule.name,
                    'severity': alert.rule.severity.value,
                    'description': alert.rule.description,
                    'current_value': alert.current_value,
                    'threshold': alert.rule.threshold,
                    'start_time': alert.start_time.isoformat(),
                    'duration_minutes': (datetime.now() - alert.start_time).total_seconds() / 60,
                    'count': alert.count
                }
                for alert in self.active_alerts.values()
            ]
    
    def get_alert_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Получение истории алертов"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [
            alert for alert in self.alert_history
            if datetime.fromisoformat(alert.get('triggered_at', '')) >= cutoff
        ]


class RateLimitDashboard:
    """Генерация данных для Grafana дашборда"""
    
    def __init__(self, metrics_collector: RateLimitMetrics):
        self.metrics_collector = metrics_collector
    
    def generate_grafana_dashboard_config(self) -> Dict[str, Any]:
        """Генерация конфигурации Grafana дашборда"""
        dashboard = {
            "dashboard": {
                "id": None,
                "title": "Rate Limiting Monitoring",
                "tags": ["rate-limiting", "1c-performance"],
                "timezone": "browser",
                "refresh": "5s",
                "time": {
                    "from": "now-1h",
                    "to": "now"
                },
                "panels": [
                    self._create_requests_panel(),
                    self._create_blocked_panel(),
                    self._create_rps_panel(),
                    self._create_response_time_panel(),
                    self._create_active_limits_panel(),
                    self._create_alerts_panel(),
                    self._create_health_panel()
                ],
                "annotations": {
                    "list": [
                        {
                            "datasource": "Prometheus",
                            "enable": True,
                            "expr": "rate_limit_requests_total",
                            "iconColor": "blue",
                            "name": "Request Rate",
                            "titleFormat": "Request Spike",
                            "textFormat": "High request rate detected"
                        }
                    ]
                }
            }
        }
        return dashboard
    
    def _create_requests_panel(self) -> Dict[str, Any]:
        """Панель запросов"""
        return {
            "id": 1,
            "title": "Total Requests Rate",
            "type": "graph",
            "targets": [
                {
                    "expr": "rate(rate_limit_requests_total[1m])",
                    "legendFormat": "Requests/sec"
                }
            ],
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
            "yAxes": [
                {
                    "label": "Requests/sec",
                    "min": 0
                }
            ]
        }
    
    def _create_blocked_panel(self) -> Dict[str, Any]:
        """Панель заблокированных запросов"""
        return {
            "id": 2,
            "title": "Blocked Requests",
            "type": "graph",
            "targets": [
                {
                    "expr": "rate(rate_limit_blocked_total[1m])",
                    "legendFormat": "Blocked/sec"
                },
                {
                    "expr": "rate(rate_limit_requests_total[1m])",
                    "legendFormat": "Total/sec"
                }
            ],
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
            "yAxes": [
                {
                    "label": "Requests/sec",
                    "min": 0
                }
            ]
        }
    
    def _create_rps_panel(self) -> Dict[str, Any]:
        """Панель RPS по IP"""
        return {
            "id": 3,
            "title": "Requests Per Second by IP",
            "type": "table",
            "targets": [
                {
                    "expr": "topk(10, rate_limit_requests_per_second)",
                    "legendFormat": "{{ip}}"
                }
            ],
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
            "transformations": [
                {
                    "id": "organize",
                    "options": {
                        "excludeByName": {},
                        "indexByName": {},
                        "renameByName": {
                            "ip": "IP Address",
                            "Value": "RPS"
                        }
                    }
                }
            ]
        }
    
    def _create_response_time_panel(self) -> Dict[str, Any]:
        """Панель времени отклика"""
        return {
            "id": 4,
            "title": "Response Time Distribution",
            "type": "heatmap",
            "targets": [
                {
                    "expr": "rate_limit_response_time_seconds_bucket",
                    "legendFormat": "{{le}}"
                }
            ],
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
        }
    
    def _create_active_limits_panel(self) -> Dict[str, Any]:
        """Панель активных ограничений"""
        return {
            "id": 5,
            "title": "Active Limits",
            "type": "stat",
            "targets": [
                {
                    "expr": "rate_limit_active_limits",
                    "legendFormat": "Active Limits"
                }
            ],
            "gridPos": {"h": 4, "w": 6, "x": 0, "y": 16},
            "fieldConfig": {
                "defaults": {
                    "thresholds": {
                        "steps": [
                            {"color": "green", "value": 0},
                            {"color": "yellow", "value": 500},
                            {"color": "red", "value": 1000}
                        ]
                    }
                }
            }
        }
    
    def _create_alerts_panel(self) -> Dict[str, Any]:
        """Панель алертов"""
        return {
            "id": 6,
            "title": "Active Alerts",
            "type": "table",
            "targets": [
                {
                    "expr": "ALERTS{alertstate=\"firing\"}",
                    "legendFormat": "{{alertname}}"
                }
            ],
            "gridPos": {"h": 4, "w": 6, "x": 6, "y": 16}
        }
    
    def _create_health_panel(self) -> Dict[str, Any]:
        """Панель здоровья системы"""
        return {
            "id": 7,
            "title": "System Health",
            "type": "stat",
            "targets": [
                {
                    "expr": "rate_limit_health_status",
                    "legendFormat": "Health Status"
                }
            ],
            "gridPos": {"h": 4, "w": 6, "x": 12, "y": 16},
            "fieldConfig": {
                "defaults": {
                    "mappings": [
                        {
                            "options": {
                                "0": {"text": "Unhealthy", "color": "red"},
                                "1": {"text": "Healthy", "color": "green"}
                            },
                            "type": "value"
                        }
                    ]
                }
            }
        }
    
    def get_prometheus_queries(self) -> Dict[str, str]:
        """Получение PromQL запросов для дашборда"""
        return {
            "total_requests_rate": "rate(rate_limit_requests_total[1m])",
            "blocked_requests_rate": "rate(rate_limit_blocked_total[1m])",
            "requests_by_ip": "topk(10, rate_limit_requests_per_second)",
            "response_time_percentiles": "histogram_quantile(0.95, rate_limit_response_time_seconds_bucket[5m])",
            "active_limits": "rate_limit_active_limits",
            "blocked_rate_percentage": "(rate(rate_limit_blocked_total[5m]) / rate(rate_limit_requests_total[5m])) * 100",
            "system_health": "rate_limit_health_status"
        }
    
    def export_dashboard_config(self, filepath: str):
        """Экспорт конфигурации дашборда в файл"""
        try:
            dashboard_config = self.generate_grafana_dashboard_config()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(dashboard_config, f, indent=2, ensure_ascii=False)
            logger.info(f"Dashboard config exported to {filepath}")
        except Exception as e:
            logger.error(f"Error exporting dashboard config: {e}")
            raise


class RealTimeMonitor:
    """Мониторинг в реальном времени"""
    
    def __init__(self, metrics_collector: RateLimitMetrics):
        self.metrics_collector = metrics_collector
        self.alert_manager = AlertManager(metrics_collector)
        
        # Threading
        self._monitor_thread = None
        self._stop_monitor = False
        self._monitor_interval = 1  # секунда
        
        # Callbacks для уведомлений
        self._alert_callbacks: List[callable] = []
        self._metrics_callbacks: List[callable] = []
        
        # Statistics
        self._stats = {
            'total_checks': 0,
            'alerts_triggered': 0,
            'avg_response_time': 0.0,
            'peak_rps': 0.0,
            'last_check_time': None
        }
    
    def add_alert_callback(self, callback: callable):
        """Добавление callback для алертов"""
        self._alert_callbacks.append(callback)
    
    def add_metrics_callback(self, callback: callable):
        """Добавление callback для метрик"""
        self._metrics_callbacks.append(callback)
    
    def start_monitoring(self):
        """Запуск реального мониторинга"""
        if self._monitor_thread is None or not self._monitor_thread.is_alive():
            self._stop_monitor = False
            self._monitor_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            self._monitor_thread.start()
            self.alert_manager.start_monitoring()
            logger.info("Real-time monitoring started")
    
    def stop_monitoring(self):
        """Остановка мониторинга"""
        self._stop_monitor = True
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        self.alert_manager.stop_monitoring()
        logger.info("Real-time monitoring stopped")
    
    def _monitoring_loop(self):
        """Основной цикл мониторинга"""
        while not self._stop_monitor:
            try:
                start_time = time.time()
                
                # Сбор метрик
                self._collect_realtime_metrics()
                
                # Проверка алертов
                self._check_realtime_alerts()
                
                # Обновление статистики
                self._update_stats()
                
                # Вызов callbacks
                self._trigger_callbacks()
                
                # Ожидание до следующего цикла
                elapsed = time.time() - start_time
                sleep_time = max(0, self._monitor_interval - elapsed)
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in real-time monitoring: {e}")
                time.sleep(self._monitor_interval)
    
    def _collect_realtime_metrics(self):
        """Сбор метрик в реальном времени"""
        # Получаем недавние метрики
        recent_metrics = self.metrics_collector.get_recent_metrics(minutes=1)
        
        # Анализируем метрики
        current_stats = {
            'timestamp': datetime.now().isoformat(),
            'requests_last_minute': 0,
            'blocked_last_minute': 0,
            'avg_response_time': 0.0,
            'peak_rps': 0.0,
            'active_alerts': len(self.alert_manager.active_alerts),
            'system_health': self.metrics_collector.get_health_status()['status']
        }
        
        response_times = []
        rps_values = []
        
        for metric in recent_metrics:
            if metric.metric_name == 'rate_limit_requests_total':
                current_stats['requests_last_minute'] += metric.value
            elif metric.metric_name == 'rate_limit_blocked_total':
                current_stats['blocked_last_minute'] += metric.value
            elif metric.metric_name == 'rate_limit_response_time_seconds':
                response_times.append(metric.value)
            elif metric.metric_name == 'rate_limit_requests_per_second':
                rps_values.append(metric.value)
        
        if response_times:
            current_stats['avg_response_time'] = sum(response_times) / len(response_times)
        
        if rps_values:
            current_stats['peak_rps'] = max(rps_values)
        
        # Сохраняем в статистике
        with threading.Lock():
            self._stats.update(current_stats)
    
    def _check_realtime_alerts(self):
        """Проверка алертов в реальном времени"""
        # Запускаем проверку алертов
        self.alert_manager._check_alerts()
        
        # Обновляем статистику сработавших алертов
        with threading.Lock():
            self._stats['alerts_triggered'] = len(self.alert_manager.active_alerts)
    
    def _update_stats(self):
        """Обновление статистики мониторинга"""
        with threading.Lock():
            self._stats['total_checks'] += 1
            self._stats['last_check_time'] = datetime.now().isoformat()
    
    def _trigger_callbacks(self):
        """Запуск callbacks"""
        # Alert callbacks
        if self.alert_manager.active_alerts:
            for callback in self._alert_callbacks:
                try:
                    callback(self.alert_manager.get_active_alerts())
                except Exception as e:
                    logger.error(f"Error in alert callback: {e}")
        
        # Metrics callbacks
        with threading.Lock():
            stats_copy = self._stats.copy()
        
        for callback in self._metrics_callbacks:
            try:
                callback(stats_copy)
            except Exception as e:
                logger.error(f"Error in metrics callback: {e}")
    
    def get_current_stats(self) -> Dict[str, Any]:
        """Получение текущей статистики мониторинга"""
        with threading.Lock():
            return self._stats.copy()
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Получение метрик в реальном времени"""
        summary = self.metrics_collector.get_metrics_summary()
        current_stats = self.get_current_stats()
        active_alerts = self.alert_manager.get_active_alerts()
        
        return {
            'summary': summary,
            'realtime_stats': current_stats,
            'active_alerts': active_alerts,
            'system_status': self._get_system_status()
        }
    
    def _get_system_status(self) -> Dict[str, Any]:
        """Получение статуса системы мониторинга"""
        health = self.metrics_collector.get_health_status()
        
        # Определяем общий статус
        if health['status'] != 'healthy':
            status = 'unhealthy'
        elif self.alert_manager.active_alerts:
            status = 'alerting'
        else:
            status = 'healthy'
        
        return {
            'overall_status': status,
            'health': health,
            'monitoring_active': self._monitor_thread and self._monitor_thread.is_alive(),
            'alerts_active': len(self.alert_manager.active_alerts),
            'checks_per_minute': 60 / self._monitor_interval if self._monitor_interval > 0 else 0
        }
    
    def force_health_check(self) -> Dict[str, Any]:
        """Принудительная проверка здоровья"""
        health_status = self.metrics_collector.get_health_status()
        
        # Проверяем различные аспекты системы
        checks = {
            'metrics_collection': health_status['status'] == 'healthy',
            'active_limits_check': health_status['active_limits_count'] >= 0,
            'memory_usage': self._check_memory_usage(),
            'thread_health': self._check_thread_health(),
            'alert_system': self._check_alert_system()
        }
        
        overall_health = all(checks.values())
        
        return {
            'overall_health': overall_health,
            'timestamp': datetime.now().isoformat(),
            'checks': checks,
            'details': health_status
        }
    
    def _check_memory_usage(self) -> bool:
        """Проверка использования памяти"""
        # Простая проверка - можно расширить использованием psutil
        import sys
        return sys.getsizeof(self.metrics_collector._metrics) < 100 * 1024 * 1024  # 100MB
    
    def _check_thread_health(self) -> bool:
        """Проверка состояния потоков"""
        return (self._monitor_thread is not None and self._monitor_thread.is_alive() and
                self.alert_manager._monitoring_thread is not None and 
                self.alert_manager._monitoring_thread.is_alive())
    
    def _check_alert_system(self) -> bool:
        """Проверка системы алертов"""
        return len(self.alert_manager.alert_rules) > 0


class RateLimitMonitoringSystem:
    """Полная система мониторинга Rate Limiting"""
    
    def __init__(self, 
                 metrics_history_size: int = 10000,
                 monitoring_interval: int = 1,
                 enable_prometheus_export: bool = True,
                 enable_realtime_monitoring: bool = True):
        
        # Основные компоненты
        self.metrics_collector = RateLimitMetrics(metrics_history_size)
        self.prometheus_exporter = PrometheusExporter(self.metrics_collector)
        self.alert_manager = AlertManager(self.metrics_collector)
        self.dashboard_generator = RateLimitDashboard(self.metrics_collector)
        self.realtime_monitor = RealTimeMonitor(self.metrics_collector)
        
        # Настройки
        self.monitoring_interval = monitoring_interval
        self.enable_prometheus_export = enable_prometheus_export
        self.enable_realtime_monitoring = enable_realtime_monitoring
        
        # Статус системы
        self._system_started = False
        self._start_time = None
        
        # Threading
        self._main_thread = None
        self._stop_system = False
        
        # Автоматический экспорт метрик
        self._export_interval = 30  # секунд
        self._export_thread = None
    
    def start(self):
        """Запуск системы мониторинга"""
        if self._system_started:
            logger.warning("Monitoring system is already started")
            return
        
        try:
            logger.info("Starting Rate Limit Monitoring System...")
            
            # Устанавливаем статус здоровья
            self.metrics_collector.set_health_status("starting")
            
            # Запускаем компоненты
            if self.enable_realtime_monitoring:
                self.realtime_monitor.start_monitoring()
            
            # Запускаем мониторинг алертов
            self.alert_manager.start_monitoring()
            
            # Запускаем автоматический экспорт если включен
            if self.enable_prometheus_export:
                self._start_prometheus_export()
            
            # Запускаем основной поток системы
            self._start_main_thread()
            
            # Устанавливаем статус здоровья
            self.metrics_collector.set_health_status("healthy")
            
            self._system_started = True
            self._start_time = datetime.now()
            
            logger.info("Rate Limit Monitoring System started successfully")
            
        except Exception as e:
            logger.error(f"Error starting monitoring system: {e}")
            self.metrics_collector.set_health_status("error")
            raise
    
    def stop(self):
        """Остановка системы мониторинга"""
        if not self._system_started:
            return
        
        try:
            logger.info("Stopping Rate Limit Monitoring System...")
            
            self._stop_system = True
            
            # Останавливаем компоненты
            if self.enable_realtime_monitoring:
                self.realtime_monitor.stop_monitoring()
            
            self.alert_manager.stop_monitoring()
            
            # Останавливаем экспорт метрик
            self._stop_prometheus_export()
            
            # Останавливаем основной поток
            if self._main_thread and self._main_thread.is_alive():
                self._main_thread.join(timeout=5)
            
            # Устанавливаем статус здоровья
            self.metrics_collector.set_health_status("stopped")
            
            self._system_started = False
            
            logger.info("Rate Limit Monitoring System stopped")
            
        except Exception as e:
            logger.error(f"Error stopping monitoring system: {e}")
    
    def _start_main_thread(self):
        """Запуск основного потока системы"""
        self._main_thread = threading.Thread(
            target=self._main_system_loop,
            daemon=True
        )
        self._main_thread.start()
    
    def _main_system_loop(self):
        """Основной цикл системы"""
        while not self._stop_system:
            try:
                # Проверяем здоровье системы
                self._perform_health_check()
                
                # Собираем системные метрики
                self._collect_system_metrics()
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in main system loop: {e}")
                time.sleep(self.monitoring_interval)
    
    def _start_prometheus_export(self):
        """Запуск автоматического экспорта метрик"""
        self._export_thread = threading.Thread(
            target=self._prometheus_export_loop,
            daemon=True
        )
        self._export_thread.start()
        logger.info("Prometheus export started")
    
    def _stop_prometheus_export(self):
        """Остановка автоматического экспорта метрик"""
        # Просто останавливаем поток, он завершится автоматически
        if self._export_thread and self._export_thread.is_alive():
            # Можно добавить флаг для остановки, но для простоты оставляем как есть
            pass
    
    def _prometheus_export_loop(self):
        """Цикл экспорта метрик в Prometheus"""
        while not self._stop_system:
            try:
                # Экспортируем метрики
                self.metrics_collector.set_health_status("exporting")
                self.prometheus_exporter.export_to_file('/tmp/rate_limit_metrics.prom')
                self.metrics_collector.set_health_status("healthy")
                
                time.sleep(self._export_interval)
                
            except Exception as e:
                logger.error(f"Error in Prometheus export loop: {e}")
                self.metrics_collector.set_health_status("export_error")
                time.sleep(self._export_interval)
    
    def _perform_health_check(self):
        """Выполнение проверки здоровья системы"""
        # Проверяем основные компоненты
        health_checks = [
            self._check_metrics_collector_health(),
            self._check_alert_manager_health(),
            self._check_realtime_monitor_health()
        ]
        
        if all(health_checks):
            self.metrics_collector.set_health_status("healthy")
        else:
            self.metrics_collector.set_health_status("degraded")
    
    def _check_metrics_collector_health(self) -> bool:
        """Проверка здоровья сборщика метрик"""
        try:
            summary = self.metrics_collector.get_metrics_summary()
            return summary is not None
        except:
            return False
    
    def _check_alert_manager_health(self) -> bool:
        """Проверка здоровья менеджера алертов"""
        try:
            # Проверяем что правила алертов загружены
            return len(self.alert_manager.alert_rules) > 0
        except:
            return False
    
    def _check_realtime_monitor_health(self) -> bool:
        """Проверка здоровья мониторинга в реальном времени"""
        try:
            stats = self.realtime_monitor.get_current_stats()
            return stats is not None
        except:
            return False
    
    def _collect_system_metrics(self):
        """Сбор системных метрик"""
        try:
            # Получаем метрики от всех компонентов
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'system_uptime_seconds': (datetime.now() - self._start_time).total_seconds() if self._start_time else 0,
                'monitoring_active': self._system_started
            }
            
            # Добавляем метрики реального времени
            if self.enable_realtime_monitoring:
                realtime_stats = self.realtime_monitor.get_current_stats()
                metrics.update({f'realtime_{k}': v for k, v in realtime_stats.items()})
            
            # Добавляем метрики алертов
            active_alerts = self.alert_manager.get_active_alerts()
            metrics['active_alerts_count'] = len(active_alerts)
            metrics['alert_rules_count'] = len(self.alert_manager.alert_rules)
            
            # Записываем как системную метрику
            self.metrics_collector._record_gauge('monitoring_system_metrics', {}, 
                                               json.dumps(metrics))
                                               
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def record_request(self, ip: str = None, user_id: str = None, tool: str = None,
                      response_time: float = None, blocked: bool = False, 
                      limit_exceeded: bool = False):
        """Запись запроса для мониторинга"""
        self.metrics_collector.record_request(
            ip=ip, user_id=user_id, tool=tool, 
            response_time=response_time, blocked=blocked, limit_exceeded=limit_exceeded
        )
    
    def register_limit(self, limit_id: str, limit_data: Dict[str, Any]):
        """Регистрация ограничения"""
        self.metrics_collector.register_active_limit(limit_id, limit_data)
    
    def unregister_limit(self, limit_id: str):
        """Отмена регистрации ограничения"""
        self.metrics_collector.unregister_active_limit(limit_id)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Получение статуса системы мониторинга"""
        return {
            'system_started': self._system_started,
            'start_time': self._start_time.isoformat() if self._start_time else None,
            'uptime_seconds': (datetime.now() - self._start_time).total_seconds() if self._start_time else 0,
            'components': {
                'metrics_collector': self.metrics_collector.get_health_status(),
                'alert_manager': {
                    'active_alerts': len(self.alert_manager.active_alerts),
                    'rules_count': len(self.alert_manager.alert_rules)
                },
                'realtime_monitor': self.realtime_monitor.get_system_status() if self.enable_realtime_monitoring else None,
                'prometheus_exporter': self.enable_prometheus_export
            },
            'realtime_metrics': self.realtime_monitor.get_real_time_metrics() if self.enable_realtime_monitoring else None
        }
    
    def export_prometheus_metrics(self, filepath: str = None) -> str:
        """Экспорт метрик в Prometheus формат"""
        if filepath:
            self.prometheus_exporter.export_to_file(filepath)
        
        return self.prometheus_exporter.generate_prometheus_metrics()
    
    def export_grafana_dashboard(self, filepath: str):
        """Экспорт конфигурации Grafana дашборда"""
        self.dashboard_generator.export_dashboard_config(filepath)
    
    def get_prometheus_queries(self) -> Dict[str, str]:
        """Получение PromQL запросов"""
        return self.dashboard_generator.get_prometheus_queries()
    
    def add_custom_alert_rule(self, rule: AlertRule):
        """Добавление пользовательского правила алерта"""
        self.alert_manager.add_alert_rule(rule)
    
    def remove_alert_rule(self, rule_name: str):
        """Удаление правила алерта"""
        self.alert_manager.remove_alert_rule(rule_name)
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Получение активных алертов"""
        return self.alert_manager.get_active_alerts()
    
    def get_alert_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Получение истории алертов"""
        return self.alert_manager.get_alert_history(hours)


# Декоратор для автоматического мониторинга функций
def rate_limit_monitoring(monitoring_system: RateLimitMonitoringSystem):
    """Декоратор для автоматического мониторинга функций"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            ip = kwargs.get('ip') or (args[0] if args else None)
            user_id = kwargs.get('user_id') or (args[1] if len(args) > 1 else None)
            tool = kwargs.get('tool') or func.__name__
            
            try:
                result = func(*args, **kwargs)
                response_time = time.time() - start_time
                
                # Записываем успешный запрос
                monitoring_system.record_request(
                    ip=ip, user_id=user_id, tool=tool,
                    response_time=response_time, blocked=False
                )
                
                return result
                
            except Exception as e:
                response_time = time.time() - start_time
                
                # Записываем заблокированный/ошибочный запрос
                monitoring_system.record_request(
                    ip=ip, user_id=user_id, tool=tool,
                    response_time=response_time, blocked=True
                )
                
                raise e
        
        return wrapper
    return decorator


# Пример использования
if __name__ == "__main__":
    # Создание системы мониторинга
    monitoring_system = RateLimitMonitoringSystem(
        metrics_history_size=10000,
        monitoring_interval=1,
        enable_prometheus_export=True,
        enable_realtime_monitoring=True
    )
    
    try:
        # Запуск системы
        monitoring_system.start()
        
        # Добавление callback для алертов
        def alert_callback(alerts):
            print(f"🚨 Active alerts: {len(alerts)}")
            for alert in alerts:
                print(f"  - {alert['rule_name']}: {alert['description']}")
        
        monitoring_system.realtime_monitor.add_alert_callback(alert_callback)
        
        # Добавление callback для метрик
        def metrics_callback(stats):
            print(f"📊 RPS: {stats.get('peak_rps', 0):.1f}, "
                  f"Response time: {stats.get('avg_response_time', 0):.3f}s")
        
        monitoring_system.realtime_monitor.add_metrics_callback(metrics_callback)
        
        # Симуляция запросов
        print("Simulating rate limiting scenarios...")
        
        import random
        
        for i in range(100):
            # Случайные запросы
            ip = f"192.168.1.{random.randint(1, 100)}"
            user_id = f"user_{random.randint(1, 20)}"
            tool = random.choice(["search", "update", "delete", "create"])
            response_time = random.uniform(0.001, 0.5)
            
            # 10% запросов заблокированы
            blocked = random.random() < 0.1
            
            monitoring_system.record_request(
                ip=ip, user_id=user_id, tool=tool,
                response_time=response_time, blocked=blocked
            )
            
            # Регистрация активных ограничений
            if random.random() < 0.05:
                limit_id = f"limit_{random.randint(1, 10)}"
                monitoring_system.register_limit(limit_id, {
                    "type": "rate_limit",
                    "limit": 100,
                    "window": 60
                })
            
            time.sleep(0.1)
        
        # Получение метрик
        print("\n=== System Status ===")
        status = monitoring_system.get_system_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
        
        print("\n=== Prometheus Metrics ===")
        prometheus_metrics = monitoring_system.export_prometheus_metrics()
        print(prometheus_metrics[:500] + "..." if len(prometheus_metrics) > 500 else prometheus_metrics)
        
        print("\n=== Active Alerts ===")
        alerts = monitoring_system.get_active_alerts()
        for alert in alerts:
            print(f"Alert: {alert['rule_name']} - {alert['description']}")
        
        # Экспорт Grafana дашборда
        print("\n=== Exporting Grafana Dashboard ===")
        monitoring_system.export_grafana_dashboard('/tmp/rate_limit_dashboard.json')
        print("Dashboard exported to /tmp/rate_limit_dashboard.json")
        
        # Health check
        print("\n=== Health Check ===")
        health = monitoring_system.realtime_monitor.force_health_check()
        print(f"System health: {health['overall_health']}")
        print(f"Checks: {health['checks']}")
        
        # Ожидание для демонстрации real-time мониторинга
        print("\n=== Running real-time monitoring for 10 seconds ===")
        time.sleep(10)
        
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        # Остановка системы
        monitoring_system.stop()
        print("Monitoring system stopped")
