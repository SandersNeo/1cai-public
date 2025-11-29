# [NEXUS IDENTITY] ID: 7440467212354374219 | DATE: 2025-11-19

"""
Custom Business Metrics Health Check
Проверка кастомных бизнес-метрик
"""

import asyncio
import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import aiohttp


class MetricStatus(Enum):
    OPTIMAL = "optimal"
    GOOD = "good"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class BusinessMetric:
    """Одна бизнес-метрика"""
    name: str
    value: Union[float, int, str]
    unit: str
    status: MetricStatus
    threshold_warning: Optional[Union[float, int]] = None
    threshold_critical: Optional[Union[float, int]] = None
    description: Optional[str] = None

@dataclass
class MetricCheck:
    """Результат проверки одной метрики"""
    metric: BusinessMetric
    timestamp: str
    historical_values: List[Dict[str, Any]]
    trend: str  # improving, stable, degrading, volatile
    percentage_from_target: Optional[float] = None
    recommendations: List[str] = None

@dataclass
class CustomMetricsHealthInfo:
    """Полная информация о бизнес-метриках"""
    overall_status: MetricStatus
    check_time: str
    total_metrics: int
    optimal_count: int
    good_count: int
    warning_count: int
    critical_count: int
    unknown_count: int
    metrics: List[MetricCheck]
    key_insights: List[str]
    business_health_score: float

class MetricCollector(ABC):
    """Абстрактный класс для сбора метрик"""
    
    @abstractmethod
    async def collect(self) -> List[BusinessMetric]:
        """Собрать метрики"""

class UserEngagementCollector(MetricCollector):
    """Сборщик метрик пользовательского вовлечения"""
    
    def __init__(self, analytics_service_url: str):
        self.analytics_service_url = analytics_service_url
    
    async def collect(self) -> List[BusinessMetric]:
        """Собрать метрики вовлечения пользователей"""
        metrics = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.analytics_service_url}/engagement") as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # DAU (Daily Active Users)
                        metrics.append(BusinessMetric(
                            name="Daily Active Users",
                            value=data.get('dau', 0),
                            unit="users",
                            status=self._determine_status(
                                data.get('dau', 0), 1000, 500, "higher"
                            ),
                            threshold_warning=1000,
                            threshold_critical=500,
                            description="Количество активных пользователей в день"
                        ))
                        
                        # Session Duration
                        avg_session = data.get('avg_session_duration', 0)
                        metrics.append(BusinessMetric(
                            name="Average Session Duration",
                            value=round(avg_session, 2),
                            unit="seconds",
                            status=self._determine_status(
                                avg_session, 300, 120, "higher"
                            ),
                            threshold_warning=300,
                            threshold_critical=120,
                            description="Средняя длительность сессии"
                        ))
                        
                        # Bounce Rate
                        bounce_rate = data.get('bounce_rate', 0)
                        metrics.append(BusinessMetric(
                            name="Bounce Rate",
                            value=round(bounce_rate, 2),
                            unit="percent",
                            status=self._determine_status(
                                bounce_rate, 40, 60, "lower"
                            ),
                            threshold_warning=40,
                            threshold_critical=60,
                            description="Процент пользователей, покинувших сайт сразу"
                        ))
                        
                        # Feature Usage Rate
                        feature_usage = data.get('feature_usage_rate', 0)
                        metrics.append(BusinessMetric(
                            name="Feature Usage Rate",
                            value=round(feature_usage, 2),
                            unit="percent",
                            status=self._determine_status(
                                feature_usage, 60, 30, "higher"
                            ),
                            threshold_warning=60,
                            threshold_critical=30,
                            description="Процент использования ключевых функций"
                        ))
                    
        except Exception as e:
            # Fallback метрики при ошибке
            metrics = [
                BusinessMetric(
                    name="DAU Collection Status",
                    value="error",
                    unit="status",
                    status=MetricStatus.CRITICAL,
                    description=f"Ошибка сбора метрик: {str(e)}"
                )
            ]
        
        return metrics
    
    def _determine_status(self, value: float, warning_threshold: float, 
                         critical_threshold: float, direction: str) -> MetricStatus:
        """Определить статус метрики"""
        if direction == "higher":
            if value < critical_threshold:
                return MetricStatus.CRITICAL
            elif value < warning_threshold:
                return MetricStatus.WARNING
            else:
                return MetricStatus.OPTIMAL
        else:  # "lower"
            if value > critical_threshold:
                return MetricStatus.CRITICAL
            elif value > warning_threshold:
                return MetricStatus.WARNING
            else:
                return MetricStatus.OPTIMAL

class SystemPerformanceCollector(MetricCollector):
    """Сборщик метрик производительности системы"""
    
    def __init__(self, api_gateway_url: str):
        self.api_gateway_url = api_gateway_url
    
    async def collect(self) -> List[BusinessMetric]:
        """Собрать метрики производительности"""
        metrics = []
        
        try:
            # Сбор метрик через API Gateway
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_gateway_url}/metrics/system") as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # API Response Time
                        avg_response_time = data.get('avg_response_time', 0)
                        metrics.append(BusinessMetric(
                            name="API Average Response Time",
                            value=round(avg_response_time, 2),
                            unit="ms",
                            status=self._determine_status(
                                avg_response_time, 1000, 3000, "lower"
                            ),
                            threshold_warning=1000,
                            threshold_critical=3000,
                            description="Среднее время ответа API"
                        ))
                        
                        # Error Rate
                        error_rate = data.get('error_rate', 0)
                        metrics.append(BusinessMetric(
                            name="API Error Rate",
                            value=round(error_rate, 2),
                            unit="percent",
                            status=self._determine_status(
                                error_rate, 2, 5, "lower"
                            ),
                            threshold_warning=2,
                            threshold_critical=5,
                            description="Процент ошибок API"
                        ))
                        
                        # Throughput
                        throughput = data.get('throughput', 0)
                        metrics.append(BusinessMetric(
                            name="API Throughput",
                            value=throughput,
                            unit="requests/sec",
                            status=self._determine_status(
                                throughput, 100, 50, "higher"
                            ),
                            threshold_warning=100,
                            threshold_critical=50,
                            description="Пропускная способность API"
                        ))
                        
        except Exception as e:
            metrics = [
                BusinessMetric(
                    name="System Metrics Collection",
                    value="error",
                    unit="status",
                    status=MetricStatus.CRITICAL,
                    description=f"Ошибка сбора метрик системы: {str(e)}"
                )
            ]
        
        return metrics
    
    def _determine_status(self, value: float, warning_threshold: float, 
                         critical_threshold: float, direction: str) -> MetricStatus:
        """Определить статус метрики"""
        if direction == "higher":
            if value < critical_threshold:
                return MetricStatus.CRITICAL
            elif value < warning_threshold:
                return MetricStatus.WARNING
            else:
                return MetricStatus.OPTIMAL
        else:  # "lower"
            if value > critical_threshold:
                return MetricStatus.CRITICAL
            elif value > warning_threshold:
                return MetricStatus.WARNING
            else:
                return MetricStatus.OPTIMAL

class FinancialMetricsCollector(MetricCollector):
    """Сборщик финансовых метрик"""
    
    def __init__(self, billing_service_url: str):
        self.billing_service_url = billing_service_url
    
    async def collect(self) -> List[BusinessMetric]:
        """Собрать финансовые метрики"""
        metrics = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.billing_service_url}/metrics") as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Monthly Revenue
                        revenue = data.get('monthly_revenue', 0)
                        metrics.append(BusinessMetric(
                            name="Monthly Revenue",
                            value=revenue,
                            unit="currency",
                            status=self._determine_status(
                                revenue, 10000, 5000, "higher"
                            ),
                            threshold_warning=10000,
                            threshold_critical=5000,
                            description="Месячная выручка"
                        ))
                        
                        # Conversion Rate
                        conversion_rate = data.get('conversion_rate', 0)
                        metrics.append(BusinessMetric(
                            name="Conversion Rate",
                            value=round(conversion_rate, 2),
                            unit="percent",
                            status=self._determine_status(
                                conversion_rate, 3, 1, "higher"
                            ),
                            threshold_warning=3,
                            threshold_critical=1,
                            description="Коэффициент конверсии"
                        ))
                        
                        # Customer Acquisition Cost
                        cac = data.get('customer_acquisition_cost', 0)
                        metrics.append(BusinessMetric(
                            name="Customer Acquisition Cost",
                            value=cac,
                            unit="currency",
                            status=self._determine_status(
                                cac, 50, 100, "lower"
                            ),
                            threshold_warning=50,
                            threshold_critical=100,
                            description="Стоимость привлечения клиента"
                        ))
                        
                        # Customer Lifetime Value
                        clv = data.get('customer_lifetime_value', 0)
                        metrics.append(BusinessMetric(
                            name="Customer Lifetime Value",
                            value=clv,
                            unit="currency",
                            status=self._determine_status(
                                clv, 200, 100, "higher"
                            ),
                            threshold_warning=200,
                            threshold_critical=100,
                            description="Жизненная ценность клиента"
                        ))
                        
        except Exception as e:
            metrics = [
                BusinessMetric(
                    name="Financial Metrics Collection",
                    value="error",
                    unit="status",
                    status=MetricStatus.CRITICAL,
                    description=f"Ошибка сбора финансовых метрик: {str(e)}"
                )
            ]
        
        return metrics
    
    def _determine_status(self, value: float, warning_threshold: float, 
                         critical_threshold: float, direction: str) -> MetricStatus:
        """Определить статус метрики"""
        if direction == "higher":
            if value < critical_threshold:
                return MetricStatus.CRITICAL
            elif value < warning_threshold:
                return MetricStatus.WARNING
            else:
                return MetricStatus.OPTIMAL
        else:  # "lower"
            if value > critical_threshold:
                return MetricStatus.CRITICAL
            elif value > warning_threshold:
                return MetricStatus.WARNING
            else:
                return MetricStatus.OPTIMAL

class CustomMetricsHealthChecker:
    """Проверяльщик кастомных бизнес-метрик"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.collectors = []
        self.history = {}  # История значений метрик
        
        # Инициализация сборщиков
        if 'analytics_service_url' in config:
            self.collectors.append(
                UserEngagementCollector(config['analytics_service_url'])
            )
        
        if 'api_gateway_url' in config:
            self.collectors.append(
                SystemPerformanceCollector(config['api_gateway_url'])
            )
        
        if 'billing_service_url' in config:
            self.collectors.append(
                FinancialMetricsCollector(config['billing_service_url'])
            )
        
        # Добавление кастомных сборщиков
        for collector_config in config.get('custom_collectors', []):
            if collector_config['type'] == 'function':
                self.collectors.append(
                    CustomFunctionCollector(collector_config)
                )
    
    async def collect_all_metrics(self) -> List[BusinessMetric]:
        """Собрать все метрики"""
        all_metrics = []
        
        # Параллельный сбор метрик от всех сборщиков
        tasks = [collector.collect() for collector in self.collectors]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                # Обработка ошибок сборщика
                all_metrics.append(BusinessMetric(
                    name="Collection Error",
                    value="error",
                    unit="status",
                    status=MetricStatus.CRITICAL,
                    description=f"Ошибка сбора метрик: {str(result)}"
                ))
            else:
                all_metrics.extend(result)
        
        return all_metrics
    
    def analyze_metric_trend(self, metric_name: str, current_value: Union[float, int], 
                           historical_values: List[Dict[str, Any]]) -> str:
        """Анализ тренда метрики"""
        if len(historical_values) < 3:
            return "insufficient_data"
        
        # Берем последние 5 значений
        recent_values = [h['value'] for h in historical_values[-5:]]
        recent_values.append(current_value)
        
        # Простая линейная регрессия для определения тренда
        n = len(recent_values)
        x = list(range(n))
        y = recent_values
        
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(xi * xi for xi in x)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        if slope > 0.1:
            return "improving"
        elif slope < -0.1:
            return "degrading"
        else:
            return "stable"
    
    def calculate_business_health_score(self, metrics: List[BusinessMetric]) -> float:
        """Вычислить общий балл здоровья бизнеса"""
        if not metrics:
            return 0.0
        
        score_weights = {
            MetricStatus.OPTIMAL: 100,
            MetricStatus.GOOD: 80,
            MetricStatus.WARNING: 60,
            MetricStatus.CRITICAL: 20,
            MetricStatus.UNKNOWN: 50
        }
        
        total_score = sum(score_weights.get(metric.status, 50) for metric in metrics)
        return total_score / len(metrics)
    
    def generate_insights(self, metrics: List[BusinessMetric]) -> List[str]:
        """Генерировать ключевые инсайты"""
        insights = []
        
        # Анализ метрик пользователей
        user_metrics = [m for m in metrics if "user" in m.name.lower()]
        if user_metrics:
            avg_user_status = sum(m.status.value == "critical" for m in user_metrics) > 0
            if avg_user_status:
                insights.append("⚠️ Критические проблемы с пользовательским опытом")
            else:
                insights.append("✅ Пользовательский опыт в норме")
        
        # Анализ производительности
        perf_metrics = [m for m in metrics if "response" in m.name.lower() or "error" in m.name.lower()]
        if perf_metrics:
            high_error_rate = any(m.value > 5 and isinstance(m.value, (int, float)) for m in perf_metrics if "error" in m.name.lower())
            if high_error_rate:
                insights.append("🔴 Высокий уровень ошибок требует внимания")
        
        # Анализ финансов
        financial_metrics = [m for m in metrics if any(word in m.name.lower() for word in ["revenue", "cost", "value"])]
        if financial_metrics:
            declining_metrics = sum(1 for m in financial_metrics if m.status in [MetricStatus.WARNING, MetricStatus.CRITICAL])
            if declining_metrics > 0:
                insights.append("📉 Тревожные тенденции в финансовых показателях")
        
        return insights
    
    def generate_recommendations(self, metric: BusinessMetric, trend: str) -> List[str]:
        """Генерировать рекомендации для метрики"""
        recommendations = []
        
        if metric.status == MetricStatus.CRITICAL:
            recommendations.append(f"🚨 Немедленное действие требуется для {metric.name}")
        elif metric.status == MetricStatus.WARNING:
            recommendations.append(f"⚠️ Требуется внимание к {metric.name}")
        
        # Специфические рекомендации
        if "DAU" in metric.name and trend == "degrading":
            recommendations.append("Провести анализ причин снижения активности пользователей")
        elif "Conversion" in metric.name and trend == "degrading":
            recommendations.append("Оптимизировать воронку конверсии")
        elif "Response Time" in metric.name and metric.value > 1000:
            recommendations.append("Оптимизировать производительность API")
        elif "Error Rate" in metric.name and metric.value > 2:
            recommendations.append("Провести анализ логов ошибок")
        
        return recommendations
    
    async def check_custom_metrics(self) -> CustomMetricsHealthInfo:
        """Проверить кастомные бизнес-метрики"""
        check_time = datetime.now()
        
        # Сбор метрик
        current_metrics = await self.collect_all_metrics()
        
        # Подсчет статусов
        status_counts = {
            MetricStatus.OPTIMAL: 0,
            MetricStatus.GOOD: 0,
            MetricStatus.WARNING: 0,
            MetricStatus.CRITICAL: 0,
            MetricStatus.UNKNOWN: 0
        }
        
        for metric in current_metrics:
            status_counts[metric.status] += 1
        
        # Анализ каждой метрики
        metric_checks = []
        for metric in current_metrics:
            # Получение истории
            historical_values = self.history.get(metric.name, [])
            trend = self.analyze_metric_trend(metric.name, metric.value, historical_values)
            
            # Генерация рекомендаций
            recommendations = self.generate_recommendations(metric, trend)
            
            # Вычисление отклонения от цели
            percentage_from_target = None
            if metric.threshold_warning:
                if isinstance(metric.value, (int, float)):
                    percentage_from_target = abs((metric.value - metric.threshold_warning) / metric.threshold_warning) * 100
            
            metric_check = MetricCheck(
                metric=metric,
                timestamp=check_time.isoformat(),
                historical_values=historical_values,
                trend=trend,
                percentage_from_target=percentage_from_target,
                recommendations=recommendations
            )
            
            metric_checks.append(metric_check)
            
            # Обновление истории
            self.history[metric.name] = historical_values + [{
                'timestamp': check_time.isoformat(),
                'value': metric.value,
                'status': metric.status.value
            }]
            
            # Ограничение размера истории
            if len(self.history[metric.name]) > 100:
                self.history[metric.name] = self.history[metric.name][-100:]
        
        # Определение общего статуса
        if status_counts[MetricStatus.CRITICAL] > 0:
            overall_status = MetricStatus.CRITICAL
        elif status_counts[MetricStatus.WARNING] > 0:
            overall_status = MetricStatus.WARNING
        elif status_counts[MetricStatus.GOOD] > 0:
            overall_status = MetricStatus.GOOD
        else:
            overall_status = MetricStatus.OPTIMAL
        
        # Вычисление общего балла
        business_health_score = self.calculate_business_health_score(current_metrics)
        
        # Генерация инсайтов
        key_insights = self.generate_insights(current_metrics)
        
        return CustomMetricsHealthInfo(
            overall_status=overall_status,
            check_time=check_time.isoformat(),
            total_metrics=len(current_metrics),
            optimal_count=status_counts[MetricStatus.OPTIMAL],
            good_count=status_counts[MetricStatus.GOOD],
            warning_count=status_counts[MetricStatus.WARNING],
            critical_count=status_counts[MetricStatus.CRITICAL],
            unknown_count=status_counts[MetricStatus.UNKNOWN],
            metrics=metric_checks,
            key_insights=key_insights,
            business_health_score=round(business_health_score, 2)
        )
    
    async def async_check(self) -> Dict[str, Any]:
        """Асинхронная проверка с преобразованием в словарь"""
        health_info = await self.check_custom_metrics()
        
        # Преобразование в словарь
        result = asdict(health_info)
        result['overall_status'] = health_info.overall_status.value
        
        # Преобразование метрик
        result['metrics'] = []
        for check in health_info.metrics:
            metric_dict = asdict(check.metric)
            metric_dict['status'] = check.metric.status.value
            result['metrics'].append({
                'metric': metric_dict,
                'timestamp': check.timestamp,
                'historical_values': check.historical_values,
                'trend': check.trend,
                'percentage_from_target': check.percentage_from_target,
                'recommendations': check.recommendations
            })
        
        return result

class CustomFunctionCollector(MetricCollector):
    """Кастомный сборщик метрик через функцию"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config['name']
        self.function = config['function']
    
    async def collect(self) -> List[BusinessMetric]:
        """Собрать метрики через кастомную функцию"""
        try:
            if callable(self.function):
                if asyncio.iscoroutinefunction(self.function):
                    result = await self.function()
                else:
                    result = self.function()
                
                if isinstance(result, list):
                    return result
                elif isinstance(result, dict):
                    return [BusinessMetric(**result)]
                else:
                    return [BusinessMetric(
                        name=self.name,
                        value=str(result),
                        unit="custom",
                        status=MetricStatus.UNKNOWN,
                        description="Кастомная метрика"
                    )]
            else:
                raise Exception("Function is not callable")
                
        except Exception as e:
            return [BusinessMetric(
                name=f"{self.name} Collection Error",
                value="error",
                unit="status",
                status=MetricStatus.CRITICAL,
                description=f"Ошибка сбора кастомной метрики: {str(e)}"
            )]

# Конфигурация по умолчанию
DEFAULT_CUSTOM_METRICS_CONFIG = {
    'analytics_service_url': os.getenv('ANALYTICS_SERVICE_URL', 'http://localhost:8005'),
    'api_gateway_url': os.getenv('API_GATEWAY_URL', 'http://localhost:8000'),
    'billing_service_url': os.getenv('BILLING_SERVICE_URL', 'http://localhost:8006'),
    'custom_collectors': []
}

if __name__ == "__main__":
    pass

    # Пример использования
    async def main():
        config = DEFAULT_CUSTOM_METRICS_CONFIG
        checker = CustomMetricsHealthChecker(config)
        result = await checker.async_check()
        print(json.dumps(result, indent=2, default=str))
    
    asyncio.run(main())