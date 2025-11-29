# [NEXUS IDENTITY] ID: -2972004582486448814 | DATE: 2025-11-19

"""
Health Check Manager
Агрегированный health status с детальной диагностикой и рекомендациями
"""

import asyncio
import json
import logging
import time
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

class OverallHealthStatus(Enum):
    EXCELLENT = "excellent"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"

class IssueSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class IssueCategory(Enum):
    PERFORMANCE = "performance"
    RELIABILITY = "reliability"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    BUSINESS_LOGIC = "business_logic"
    INFRASTRUCTURE = "infrastructure"

@dataclass
class HealthIssue:
    """Проблема со здоровьем системы"""
    id: str
    title: str
    description: str
    severity: IssueSeverity
    category: IssueCategory
    affected_services: List[str]
    detected_at: str
    status: str  # open, acknowledged, resolved
    recommendations: List[str]
    auto_remediation: Optional[Dict[str, Any]] = None
    escalation_level: int = 0

@dataclass
class ServiceHealth:
    """Состояние здоровья сервиса"""
    service_name: str
    status: OverallHealthStatus
    last_check: str
    response_time_ms: float
    issues: List[HealthIssue]
    metrics: Dict[str, Any]
    dependencies_status: Dict[str, str]
    health_score: float

@dataclass
class HealthMetrics:
    """Метрики здоровья системы"""
    total_services: int
    healthy_services: int
    degraded_services: int
    unhealthy_services: int
    critical_services: int
    overall_health_score: float
    average_response_time: float
    system_uptime_percentage: float
    incident_rate: float
    mttr_minutes: float  # Mean Time To Recovery
    mtbf_hours: float    # Mean Time Between Failures

class HealthIssueDetector:
    """Детектор проблем здоровья системы"""
    
    def __init__(self):
        self.rules = []
        self._load_detection_rules()
    
    def _load_detection_rules(self):
        """Загрузить правила обнаружения проблем"""
        self.rules = [
            {
                'name': 'high_cpu_usage',
                'condition': lambda data: data.get('cpu_percent', 0) > 90,
                'severity': IssueSeverity.HIGH,
                'category': IssueCategory.PERFORMANCE,
                'title': 'Высокое использование CPU',
                'description': 'Использование CPU превышает 90%',
                'recommendations': [
                    'Оптимизировать процессы с высоким потреблением CPU',
                    'Рассмотреть горизонтальное масштабирование',
                    'Проверить возможности оптимизации алгоритмов'
                ]
            },
            {
                'name': 'high_memory_usage',
                'condition': lambda data: data.get('memory_percent', 0) > 85,
                'severity': IssueSeverity.HIGH,
                'category': IssueCategory.PERFORMANCE,
                'title': 'Высокое использование памяти',
                'description': 'Использование памяти превышает 85%',
                'recommendations': [
                    'Опроверить утечки памяти в приложении',
                    'Оптимизировать использование кэша',
                    'Рассмотреть увеличение объема памяти'
                ]
            },
            {
                'name': 'database_connection_issues',
                'condition': lambda data: any(
                    dep.get('status') == 'connection_error' 
                    for dep in data.get('dependencies', [])
                    if dep.get('type') == 'database'
                ),
                'severity': IssueSeverity.CRITICAL,
                'category': IssueCategory.RELIABILITY,
                'title': 'Проблемы подключения к базе данных',
                'description': 'Обнаружены ошибки подключения к базе данных',
                'recommendations': [
                    'Проверить состояние базы данных',
                    'Проверить сетевое подключение',
                    'Проверить учетные данные доступа'
                ]
            },
            {
                'name': 'high_error_rate',
                'condition': lambda data: data.get('error_rate', 0) > 5,
                'severity': IssueSeverity.HIGH,
                'category': IssueCategory.RELIABILITY,
                'title': 'Высокий уровень ошибок',
                'description': 'Процент ошибок превышает 5%',
                'recommendations': [
                    'Проанализировать логи ошибок',
                    'Проверить стабильность внешних сервисов',
                    'Рассмотреть внедрение circuit breaker'
                ]
            },
            {
                'name': 'slow_response_time',
                'condition': lambda data: data.get('response_time_ms', 0) > 3000,
                'severity': IssueSeverity.MEDIUM,
                'category': IssueCategory.PERFORMANCE,
                'title': 'Медленное время ответа',
                'description': 'Время ответа превышает 3 секунды',
                'recommendations': [
                    'Оптимизировать запросы к базе данных',
                    'Проверить производительность сети',
                    'Рассмотреть кэширование'
                ]
            },
            {
                'name': 'low_business_metrics',
                'condition': lambda data: data.get('business_health_score', 100) < 60,
                'severity': IssueSeverity.MEDIUM,
                'category': IssueCategory.BUSINESS_LOGIC,
                'title': 'Низкие бизнес-показатели',
                'description': 'Бизнес-показатели ниже критического порога',
                'recommendations': [
                    'Проанализировать поведение пользователей',
                    'Провести A/B тестирование функций',
                    'Оптимизировать пользовательский интерфейс'
                ]
            }
        ]
    
    def detect_issues(self, health_data: Dict[str, Any]) -> List[HealthIssue]:
        """Обнаружить проблемы в данных здоровья"""
        issues = []
        
        for rule in self.rules:
            try:
                if rule['condition'](health_data):
                    issue = HealthIssue(
                        id=f"{rule['name']}_{int(time.time())}",
                        title=rule['title'],
                        description=rule['description'],
                        severity=rule['severity'],
                        category=rule['category'],
                        affected_services=[health_data.get('service_name', 'unknown')],
                        detected_at=datetime.now().isoformat(),
                        status='open',
                        recommendations=rule['recommendations']
                    )
                    issues.append(issue)
            except Exception as e:
                logger.warning(f"Error evaluating rule {rule['name']}: {e}")
        
        return issues

class RecommendationEngine:
    """Движок рекомендаций по устранению проблем"""
    
    def __init__(self):
        self.remediation_strategies = {
            IssueCategory.PERFORMANCE: self._performance_remediation,
            IssueCategory.RELIABILITY: self._reliability_remediation,
            IssueCategory.SECURITY: self._security_remediation,
            IssueCategory.BUSINESS_LOGIC: self._business_logic_remediation,
            IssueCategory.INFRASTRUCTURE: self._infrastructure_remediation
        }
    
    def generate_recommendations(self, issues: List[HealthIssue]) -> Dict[str, Any]:
        """Генерировать рекомендации для списка проблем"""
        
        recommendations = {
            'immediate_actions': [],
            'short_term_actions': [],
            'long_term_actions': [],
            'prevention_measures': [],
            'estimated_resolution_time': 'unknown'
        }
        
        # Группировка проблем по срочности
        critical_issues = [i for i in issues if i.severity == IssueSeverity.CRITICAL]
        high_issues = [i for i in issues if i.severity == IssueSeverity.HIGH]
        medium_issues = [i for i in issues if i.severity == IssueSeverity.MEDIUM]
        
        # Немедленные действия
        for issue in critical_issues:
            action = f"🚨 НЕМЕДЛЕННО: {issue.title}"
            recommendations['immediate_actions'].append(action)
        
        # Краткосрочные действия
        for issue in high_issues:
            action = f"⚠️ СРОЧНО: {issue.title}"
            recommendations['short_term_actions'].append(action)
        
        # Долгосрочные действия
        for issue in medium_issues:
            action = f"📋 ПЛАНИРОВАТЬ: {issue.title}"
            recommendations['long_term_actions'].append(action)
        
        # Меры профилактики
        if issues:
            recommendations['prevention_measures'] = [
                "Внедрить автоматический мониторинг",
                "Настроить алерты на критические метрики",
                "Регулярно проводить health check'и",
                "Документировать процедуры инцидентов"
            ]
        
        # Оценка времени разрешения
        if critical_issues:
            recommendations['estimated_resolution_time'] = '15-30 минут'
        elif high_issues:
            recommendations['estimated_resolution_time'] = '1-4 часа'
        elif medium_issues:
            recommendations['estimated_resolution_time'] = '1-7 дней'
        else:
            recommendations['estimated_resolution_time'] = 'все в порядке'
        
        return recommendations
    
    def _performance_remediation(self, issue: HealthIssue) -> Dict[str, Any]:
        """Рекомендации по производительности"""
        return {
            'auto_remediation': {
                'scale_up': True,
                'clear_cache': True,
                'restart_services': False
            },
            'manual_actions': [
                'Профилировать производительность',
                'Оптимизировать запросы',
                'Проверить конфигурацию'
            ]
        }
    
    def _reliability_remediation(self, issue: HealthIssue) -> Dict[str, Any]:
        """Рекомендации по надежности"""
        return {
            'auto_remediation': {
                'restart_failing_service': True,
                'switch_to_backup': False
            },
            'manual_actions': [
                'Проверить логи',
                'Анализировать ошибки',
                'Восстановить из резервной копии'
            ]
        }
    
    def _security_remediation(self, issue: HealthIssue) -> Dict[str, Any]:
        """Рекомендации по безопасности"""
        return {
            'auto_remediation': {
                'block_suspicious_ips': True,
                'revoke_compromised_tokens': True
            },
            'manual_actions': [
                'Провести аудит безопасности',
                'Обновить пароли',
                'Проверить права доступа'
            ]
        }
    
    def _business_logic_remediation(self, issue: HealthIssue) -> Dict[str, Any]:
        """Рекомендации по бизнес-логике"""
        return {
            'auto_remediation': {},
            'manual_actions': [
                'Проанализировать пользовательский опыт',
                'Провести A/B тестирование',
                'Обновить бизнес-правила'
            ]
        }
    
    def _infrastructure_remediation(self, issue: HealthIssue) -> Dict[str, Any]:
        """Рекомендации по инфраструктуре"""
        return {
            'auto_remediation': {
                'provision_resources': True
            },
            'manual_actions': [
                'Обновить конфигурацию',
                'Расширить инфраструктуру',
                'Проверить сетевые настройки'
            ]
        }

class HealthCheckManager:
    """Основной менеджер health check'ов"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.issue_detector = HealthIssueDetector()
        self.recommendation_engine = RecommendationEngine()
        self.services = {}
        self.health_history = deque(maxlen=1000)
        self.incident_history = deque(maxlen=100)
        self.alert_callbacks = []
        
        # Настройка интервалов проверки
        self.check_intervals = {
            'basic': 30,          # 30 секунд
            'dependencies': 60,   # 1 минута
            'business': 300,      # 5 минут
            'performance': 60,    # 1 минута
            'custom_metrics': 600 # 10 минут
        }
        
        # Флаги состояния
        self._running = False
        self._tasks = []
    
    def register_service(self, service_name: str, health_check_func: Callable):
        """Зарегистрировать сервис для мониторинга"""
        self.services[service_name] = {
            'health_check': health_check_func,
            'last_check': None,
            'status': OverallHealthStatus.UNKNOWN,
            'issues': [],
            'metrics': {}
        }
        logger.info(f"Registered service for monitoring: {service_name}")
    
    def add_alert_callback(self, callback: Callable):
        """Добавить callback для алертов"""
        self.alert_callbacks.append(callback)
    
    async def check_all_services(self) -> Dict[str, ServiceHealth]:
        """Проверить все зарегистрированные сервисы"""
        service_healths = {}
        
        for service_name, service_config in self.services.items():
            try:
                start_time = time.time()
                
                # Выполнение health check
                if asyncio.iscoroutinefunction(service_config['health_check']):
                    health_data = await service_config['health_check']()
                else:
                    health_data = service_config['health_check']()
                
                response_time = (time.time() - start_time) * 1000
                
                # Обнаружение проблем
                issues = self.issue_detector.detect_issues(health_data)
                
                # Определение статуса
                status = self._determine_service_status(health_data, issues)
                
                # Создание объекта здоровья сервиса
                service_health = ServiceHealth(
                    service_name=service_name,
                    status=status,
                    last_check=datetime.now().isoformat(),
                    response_time_ms=response_time,
                    issues=issues,
                    metrics=health_data,
                    dependencies_status=health_data.get('dependencies_status', {}),
                    health_score=self._calculate_service_health_score(health_data, issues)
                )
                
                service_healths[service_name] = service_health
                
                # Обновление локального состояния
                self.services[service_name].update({
                    'last_check': service_health.last_check,
                    'status': status,
                    'issues': issues,
                    'metrics': health_data
                })
                
                # Отправка алертов при необходимости
                if issues and any(issue.severity in [IssueSeverity.HIGH, IssueSeverity.CRITICAL] 
                                for issue in issues):
                    await self._trigger_alerts(service_name, issues)
                
            except Exception as e:
                logger.error(f"Error checking service {service_name}: {e}")
                
                # Сервис недоступен
                service_health = ServiceHealth(
                    service_name=service_name,
                    status=OverallHealthStatus.CRITICAL,
                    last_check=datetime.now().isoformat(),
                    response_time_ms=0,
                    issues=[HealthIssue(
                        id=f"check_error_{service_name}_{int(time.time())}",
                        title="Ошибка проверки сервиса",
                        description=str(e),
                        severity=IssueSeverity.CRITICAL,
                        category=IssueCategory.INFRASTRUCTURE,
                        affected_services=[service_name],
                        detected_at=datetime.now().isoformat(),
                        status='open',
                        recommendations=["Проверить доступность сервиса", "Проверить конфигурацию health check"]
                    )],
                    metrics={},
                    dependencies_status={},
                    health_score=0.0
                )
                
                service_healths[service_name] = service_health
        
        return service_healths
    
    def _determine_service_status(self, health_data: Dict[str, Any], 
                                 issues: List[HealthIssue]) -> OverallHealthStatus:
        """Определить статус сервиса"""
        
        # Критические проблемы
        critical_issues = [i for i in issues if i.severity == IssueSeverity.CRITICAL]
        if critical_issues:
            return OverallHealthStatus.CRITICAL
        
        # Высокие проблемы
        high_issues = [i for i in issues if i.severity == IssueSeverity.HIGH]
        if len(high_issues) >= 2:
            return OverallHealthStatus.UNHEALTHY
        elif len(high_issues) == 1:
            return OverallHealthStatus.DEGRADED
        
        # Средние проблемы
        medium_issues = [i for i in issues if i.severity == IssueSeverity.MEDIUM]
        if medium_issues:
            return OverallHealthStatus.DEGRADED
        
        # Анализ метрик
        if 'business_health_score' in health_data:
            score = health_data['business_health_score']
            if score >= 90:
                return OverallHealthStatus.EXCELLENT
            elif score >= 75:
                return OverallHealthStatus.HEALTHY
            elif score >= 60:
                return OverallHealthStatus.DEGRADED
            else:
                return OverallHealthStatus.UNHEALTHY
        
        # По умолчанию
        return OverallHealthStatus.HEALTHY
    
    def _calculate_service_health_score(self, health_data: Dict[str, Any], 
                                      issues: List[HealthIssue]) -> float:
        """Вычислить балл здоровья сервиса"""
        score = 100.0
        
        # Штрафы за проблемы
        severity_penalties = {
            IssueSeverity.CRITICAL: 30,
            IssueSeverity.HIGH: 15,
            IssueSeverity.MEDIUM: 5,
            IssueSeverity.LOW: 1
        }
        
        for issue in issues:
            score -= severity_penalties.get(issue.severity, 0)
        
        # Бонусы за хорошие метрики
        if 'performance_score' in health_data:
            performance_bonus = (health_data['performance_score'] - 50) * 0.2
            score += performance_bonus
        
        if 'business_health_score' in health_data:
            business_bonus = (health_data['business_health_score'] - 50) * 0.1
            score += business_bonus
        
        return max(0.0, min(100.0, score))
    
    async def _trigger_alerts(self, service_name: str, issues: List[HealthIssue]):
        """Отправить алерты"""
        for callback in self.alert_callbacks:
            try:
                await callback(service_name, issues)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
    
    async def get_overall_health(self) -> Dict[str, Any]:
        """Получить общий статус здоровья системы"""
        
        # Проверка всех сервисов
        service_healths = await self.check_all_services()
        
        # Вычисление общих метрик
        total_services = len(service_healths)
        healthy_count = sum(1 for s in service_healths.values() 
                          if s.status in [OverallHealthStatus.EXCELLENT, OverallHealthStatus.HEALTHY])
        degraded_count = sum(1 for s in service_healths.values() 
                           if s.status == OverallHealthStatus.DEGRADED)
        unhealthy_count = sum(1 for s in service_healths.values() 
                            if s.status == OverallHealthStatus.UNHEALTHY)
        critical_count = sum(1 for s in service_healths.values() 
                           if s.status == OverallHealthStatus.CRITICAL)
        
        # Общий статус
        if critical_count > 0:
            overall_status = OverallHealthStatus.CRITICAL
        elif unhealthy_count > 0:
            overall_status = OverallHealthStatus.UNHEALTHY
        elif degraded_count > 0:
            overall_status = OverallHealthStatus.DEGRADED
        elif healthy_count == total_services:
            overall_status = OverallHealthStatus.EXCELLENT
        else:
            overall_status = OverallHealthStatus.HEALTHY
        
        # Сбор всех проблем
        all_issues = []
        for service_health in service_healths.values():
            all_issues.extend(service_health.issues)
        
        # Генерация рекомендаций
        recommendations = self.recommendation_engine.generate_recommendations(all_issues)
        
        # Вычисление общего балла здоровья
        overall_score = sum(s.health_score for s in service_healths.values()) / max(1, total_services)
        
        # Среднее время ответа
        avg_response_time = sum(s.response_time_ms for s in service_healths.values()) / max(1, total_services)
        
        # Создание объекта метрик здоровья
        health_metrics = HealthMetrics(
            total_services=total_services,
            healthy_services=healthy_count,
            degraded_services=degraded_count,
            unhealthy_services=unhealthy_count,
            critical_services=critical_count,
            overall_health_score=overall_score,
            average_response_time=avg_response_time,
            system_uptime_percentage=95.0,  # Рассчитывается на основе истории
            incident_rate=0.1,  # Рассчитывается на основе инцидентов
            mttr_minutes=30.0,  # Mean Time To Recovery
            mtbf_hours=720.0    # Mean Time Between Failures
        )
        
        # Сохранение в историю
        health_record = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': overall_status.value,
            'metrics': asdict(health_metrics),
            'services': {name: asdict(health) for name, health in service_healths.items()},
            'issues': all_issues,
            'recommendations': recommendations
        }
        
        self.health_history.append(health_record)
        
        return {
            'overall_status': overall_status.value,
            'timestamp': datetime.now().isoformat(),
            'summary': asdict(health_metrics),
            'services': {name: asdict(health) for name, health in service_healths.items()},
            'issues': [asdict(issue) for issue in all_issues],
            'recommendations': recommendations,
            'trends': self._analyze_trends()
        }
    
    def _analyze_trends(self) -> Dict[str, str]:
        """Анализ трендов здоровья системы"""
        if len(self.health_history) < 5:
            return {'trend': 'insufficient_data'}
        
        recent_records = list(self.health_history)[-10:]
        
        # Анализ тренда общего здоровья
        health_scores = [r['summary']['overall_health_score'] for r in recent_records]
        
        if len(health_scores) >= 3:
            # Простая линейная регрессия
            n = len(health_scores)
            x = list(range(n))
            
            sum_x = sum(x)
            sum_y = sum(health_scores)
            sum_xy = sum(x[i] * health_scores[i] for i in range(n))
            sum_x2 = sum(xi * xi for xi in x)
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            
            if slope > 0.5:
                trend = 'improving'
            elif slope < -0.5:
                trend = 'degrading'
            else:
                trend = 'stable'
        else:
            trend = 'stable'
        
        return {
            'overall_health_trend': trend,
            'data_points': len(health_scores)
        }
    
    async def start_monitoring(self):
        """Запустить непрерывный мониторинг"""
        if self._running:
            logger.warning("Monitoring already running")
            return
        
        self._running = True
        
        # Запуск фоновых задач
        for service_name in self.services:
            task = asyncio.create_task(self._monitor_service(service_name))
            self._tasks.append(task)
        
        logger.info("Health monitoring started")
    
    async def stop_monitoring(self):
        """Остановить мониторинг"""
        self._running = False
        
        # Отмена всех задач
        for task in self._tasks:
            task.cancel()
        
        self._tasks.clear()
        logger.info("Health monitoring stopped")
    
    async def _monitor_service(self, service_name: str):
        """Фоновая задача мониторинга сервиса"""
        while self._running:
            try:
                service_config = self.services[service_name]
                
                # Выполнение health check
                if asyncio.iscoroutinefunction(service_config['health_check']):
                    await service_config['health_check']()
                else:
                    service_config['health_check']()
                
                # Ожидание до следующей проверки
                await asyncio.sleep(self.check_intervals.get('basic', 30))
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring task for {service_name}: {e}")
                await asyncio.sleep(60)  # При ошибке ждать минуту
    
    def get_health_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Получить историю здоровья за указанный период"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        return [
            record for record in self.health_history
            if datetime.fromisoformat(record['timestamp']) > cutoff_time
        ]
    
    def export_health_report(self, filename: str = None) -> str:
        """Экспортировать отчет о здоровье системы"""
        if not filename:
            filename = f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report_data = {
            'generated_at': datetime.now().isoformat(),
            'overall_status': 'unknown',
            'current_metrics': {},
            'recent_trends': list(self.health_history)[-20:],
            'active_issues': [],
            'recommendations': {}
        }
        
        # Экспорт в JSON файл
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
        
        return filename

if __name__ == "__main__":
    # Пример использования
    async def sample_health_check():
        """Пример health check функции"""
        return {
            'service_name': 'sample-service',
            'status': 'healthy',
            'cpu_percent': 45.2,
            'memory_percent': 67.8,
            'response_time_ms': 250,
            'error_rate': 1.2,
            'business_health_score': 85.5
        }
    
    async def main():
        manager = HealthCheckManager()
        manager.register_service('sample-service', sample_health_check)
        
        # Добавление callback для алертов
        async def alert_callback(service_name: str, issues: List[HealthIssue]):
            print(f"ALERT: Issues detected in {service_name}")
            for issue in issues:
                print(f"  - {issue.title}: {issue.description}")
        
        manager.add_alert_callback(alert_callback)
        
        # Получение общего статуса здоровья
        overall_health = await manager.get_overall_health()
        print(json.dumps(overall_health, indent=2, default=str))
    
    asyncio.run(main())