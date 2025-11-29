# [NEXUS IDENTITY] ID: -8778687099600127868 | DATE: 2025-11-19

"""
Automated Recovery System
Self-healing mechanisms, circuit breakers, and emergency procedures
"""

import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional


from ..manager.health_manager import (HealthCheckManager, HealthIssue,
                                      IssueCategory, IssueSeverity)

logger = logging.getLogger(__name__)

class RecoveryStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"

class RecoveryType(Enum):
    RESTART_SERVICE = "restart_service"
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    CLEAR_CACHE = "clear_cache"
    RESTART_POD = "restart_pod"
    SWITCH_TRAFFIC = "switch_traffic"
    CIRCUIT_BREAKER = "circuit_breaker"
    FAILOVER = "failover"
    GRACEFUL_DEGRADATION = "graceful_degradation"

@dataclass
class RecoveryAction:
    """Действие по восстановлению"""
    id: str
    type: RecoveryType
    target: str  # service_name, pod_name, etc.
    parameters: Dict[str, Any]
    max_retries: int
    timeout_seconds: int
    rollback_action: Optional[str] = None
    preconditions: List[str] = None

@dataclass
class RecoveryExecution:
    """Выполнение действия восстановления"""
    action: RecoveryAction
    status: RecoveryStatus
    start_time: str
    end_time: Optional[str] = None
    attempts: int = 0
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    logs: List[str] = None

class CircuitBreaker:
    """Реализация паттерна Circuit Breaker"""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half_open
        self.success_count = 0
    
    def can_execute(self) -> bool:
        """Проверить можно ли выполнить операцию"""
        if self.state == 'closed':
            return True
        elif self.state == 'open':
            if self._should_attempt_reset():
                self.state = 'half_open'
                self.success_count = 0
                return True
            return False
        else:  # half_open
            return True
    
    def record_success(self):
        """Записать успешное выполнение"""
        if self.state == 'half_open':
            self.success_count += 1
            if self.success_count >= 3:
                self.state = 'closed'
                self.failure_count = 0
        
        if self.state == 'closed':
            self.failure_count = 0
    
    def record_failure(self):
        """Записать неудачное выполнение"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'open'
    
    def _should_attempt_reset(self) -> bool:
        """Проверить нужно ли попытаться сбросить circuit breaker"""
        return (
            self.last_failure_time and 
            time.time() - self.last_failure_time >= self.timeout
        )
    
    def get_state(self) -> Dict[str, Any]:
        """Получить состояние circuit breaker"""
        return {
            'state': self.state,
            'failure_count': self.failure_count,
            'failure_threshold': self.failure_threshold,
            'timeout': self.timeout,
            'last_failure_time': self.last_failure_time
        }

class KubernetesOperator:
    """Оператор для работы с Kubernetes"""
    
    def __init__(self, kube_config: Dict[str, Any] = None):
        self.config = kube_config or {}
        self.namespace = self.config.get('namespace', 'default')
        # В реальной реализации здесь должен быть клиент Kubernetes
    
    async def restart_pod(self, pod_name: str) -> Dict[str, Any]:
        """Перезапустить pod"""
        # Симуляция перезапуска pod
        logger.info(f"Restarting pod {pod_name} in namespace {self.namespace}")
        
        await asyncio.sleep(2)  # Симуляция времени выполнения
        
        return {
            'success': True,
            'pod_name': pod_name,
            'action': 'restarted',
            'timestamp': datetime.now().isoformat()
        }
    
    async def scale_deployment(self, deployment_name: int, replicas: int) -> Dict[str, Any]:
        """Масштабировать deployment"""
        logger.info(f"Scaling deployment {deployment_name} to {replicas} replicas")
        
        await asyncio.sleep(3)  # Симуляция времени выполнения
        
        return {
            'success': True,
            'deployment': deployment_name,
            'replicas': replicas,
            'timestamp': datetime.now().isoformat()
        }
    
    async def get_pod_status(self, pod_name: str) -> Dict[str, Any]:
        """Получить статус pod"""
        # Симуляция получения статуса
        return {
            'pod_name': pod_name,
            'status': 'Running',
            'restarts': 0,
            'ready': True
        }

class ServiceRestartHandler:
    """Обработчик перезапуска сервисов"""
    
    def __init__(self, kubernetes_operator: KubernetesOperator = None):
        self.k8s = kubernetes_operator or KubernetesOperator()
        self.restart_history = {}
    
    async def restart_service(self, service_name: str, restart_type: str = 'pod') -> Dict[str, Any]:
        """Перезапустить сервис"""
        
        if service_name not in self.restart_history:
            self.restart_history[service_name] = []
        
        restart_record = {
            'service_name': service_name,
            'restart_type': restart_type,
            'timestamp': datetime.now().isoformat(),
            'status': 'started'
        }
        
        try:
            if restart_type == 'pod':
                result = await self._restart_pod(service_name)
            elif restart_type == 'container':
                result = await self._restart_container(service_name)
            else:
                result = await self._restart_systemd(service_name)
            
            restart_record.update({
                'status': 'success',
                'result': result
            })
            
            logger.info(f"Successfully restarted service {service_name}")
            
        except Exception as e:
            restart_record.update({
                'status': 'failed',
                'error': str(e)
            })
            
            logger.error(f"Failed to restart service {service_name}: {e}")
        
        self.restart_history[service_name].append(restart_record)
        
        # Ограничение размера истории
        if len(self.restart_history[service_name]) > 50:
            self.restart_history[service_name] = self.restart_history[service_name][-50:]
        
        return restart_record
    
    async def _restart_pod(self, service_name: str) -> Dict[str, Any]:
        """Перезапустить pod через Kubernetes"""
        pod_name = f"{service_name}-*"
        return await self.k8s.restart_pod(pod_name)
    
    async def _restart_container(self, service_name: str) -> Dict[str, Any]:
        """Перезапустить контейнер Docker"""
        logger.info(f"Restarting container for service {service_name}")
        
        # Симуляция перезапуска Docker контейнера
        await asyncio.sleep(2)
        
        return {
            'service_name': service_name,
            'action': 'container_restarted',
            'timestamp': datetime.now().isoformat()
        }
    
    async def _restart_systemd(self, service_name: str) -> Dict[str, Any]:
        """Перезапустить сервис через systemd"""
        logger.info(f"Restarting systemd service {service_name}")
        
        # Симуляция перезапуска systemd сервиса
        await asyncio.sleep(3)
        
        return {
            'service_name': service_name,
            'action': 'systemd_restarted',
            'timestamp': datetime.now().isoformat()
        }
    
    def get_restart_history(self, service_name: str = None) -> Dict[str, Any]:
        """Получить историю перезапусков"""
        if service_name:
            return {
                service_name: self.restart_history.get(service_name, [])
            }
        return self.restart_history

class CacheClearer:
    """Очистка кэша различных типов"""
    
    def __init__(self):
        self.redis_client = None  # Будет инициализирован в реальной системе
        self.clear_history = []
    
    async def clear_service_cache(self, service_name: str, cache_types: List[str] = None) -> Dict[str, Any]:
        """Очистить кэш сервиса"""
        
        cache_types = cache_types or ['redis', 'memory', 'application']
        
        result = {
            'service_name': service_name,
            'cache_types': cache_types,
            'timestamp': datetime.now().isoformat(),
            'results': {}
        }
        
        for cache_type in cache_types:
            try:
                if cache_type == 'redis':
                    cleared = await self._clear_redis_cache(service_name)
                elif cache_type == 'memory':
                    cleared = await self._clear_memory_cache(service_name)
                elif cache_type == 'application':
                    cleared = await self._clear_application_cache(service_name)
                else:
                    cleared = False
                
                result['results'][cache_type] = {
                    'success': cleared,
                    'cleared_entries': 100 if cleared else 0
                }
                
            except Exception as e:
                result['results'][cache_type] = {
                    'success': False,
                    'error': str(e)
                }
        
        self.clear_history.append(result)
        return result
    
    async def _clear_redis_cache(self, service_name: str) -> bool:
        """Очистить Redis кэш"""
        logger.info(f"Clearing Redis cache for service {service_name}")
        
        # Симуляция очистки Redis
        await asyncio.sleep(1)
        
        return True
    
    async def _clear_memory_cache(self, service_name: str) -> bool:
        """Очистить memory cache"""
        logger.info(f"Clearing memory cache for service {service_name}")
        
        # Принудительная сборка мусора
        import gc
        collected = gc.collect()
        logger.info(f"Garbage collection collected {collected} objects")
        
        return True
    
    async def _clear_application_cache(self, service_name: str) -> bool:
        """Очистить application cache"""
        logger.info(f"Clearing application cache for service {service_name}")
        
        # Симуляция очистки кэша приложения
        await asyncio.sleep(0.5)
        
        return True
    
    def get_clear_history(self) -> List[Dict[str, Any]]:
        """Получить историю очистки кэша"""
        return self.clear_history

class TrafficSwitcher:
    """Переключение трафика между сервисами"""
    
    def __init__(self):
        self.switch_history = []
        self.current_routing = {}
    
    async def switch_traffic(self, service_name: str, target_version: str, 
                           traffic_percentage: float = 100.0) -> Dict[str, Any]:
        """Переключить трафик на другую версию сервиса"""
        
        switch_record = {
            'service_name': service_name,
            'target_version': target_version,
            'traffic_percentage': traffic_percentage,
            'timestamp': datetime.now().isoformat(),
            'status': 'started'
        }
        
        try:
            # Симуляция переключения трафика через load balancer
            logger.info(f"Switching traffic for {service_name} to version {target_version}")
            
            await asyncio.sleep(2)
            
            # Обновление текущей маршрутизации
            self.current_routing[service_name] = {
                'version': target_version,
                'traffic_percentage': traffic_percentage,
                'updated_at': datetime.now().isoformat()
            }
            
            switch_record.update({
                'status': 'success',
                'routing_rule': self.current_routing[service_name]
            })
            
        except Exception as e:
            switch_record.update({
                'status': 'failed',
                'error': str(e)
            })
        
        self.switch_history.append(switch_record)
        return switch_record
    
    async def rollback_traffic(self, service_name: str) -> Dict[str, Any]:
        """Откатить трафик к предыдущей версии"""
        if service_name not in self.current_routing:
            raise Exception(f"No routing configuration found for {service_name}")
        
        current_routing = self.current_routing[service_name]
        # Откат к предыдущей версии (в реальной системе нужно хранить историю)
        
        rollback_record = {
            'service_name': service_name,
            'action': 'rollback',
            'timestamp': datetime.now().isoformat(),
            'previous_routing': current_routing
        }
        
        try:
            # Симуляция отката
            await asyncio.sleep(1)
            
            rollback_record.update({
                'status': 'success',
                'rolled_back_to': 'previous_version'
            })
            
        except Exception as e:
            rollback_record.update({
                'status': 'failed',
                'error': str(e)
            })
        
        self.switch_history.append(rollback_record)
        return rollback_record
    
    def get_switch_history(self) -> List[Dict[str, Any]]:
        """Получить историю переключений трафика"""
        return self.switch_history
    
    def get_current_routing(self) -> Dict[str, Any]:
        """Получить текущую маршрутизацию"""
        return self.current_routing

class AutomatedRecoverySystem:
    """Основная система автоматического восстановления"""
    
    def __init__(self, health_manager: HealthCheckManager = None):
        self.health_manager = health_manager
        self.recovery_handlers = {
            RecoveryType.RESTART_SERVICE: ServiceRestartHandler(),
            RecoveryType.CLEAR_CACHE: CacheClearer(),
            RecoveryType.SWITCH_TRAFFIC: TrafficSwitcher(),
            RecoveryType.CIRCUIT_BREAKER: CircuitBreaker()
        }
        
        self.circuit_breakers = {}  # service_name -> CircuitBreaker
        self.recovery_execution_history = []
        self.emergency_procedures = []
        self.is_running = False
        
        # Регистрация стандартных процедур восстановления
        self._register_default_procedures()
    
    def _register_default_procedures(self):
        """Регистрация стандартных процедур восстановления"""
        
        # Процедура для высокого использования CPU
        self.emergency_procedures.append({
            'name': 'high_cpu_recovery',
            'condition': lambda issue: issue.category == IssueCategory.PERFORMANCE and 'cpu' in issue.description.lower(),
            'actions': [
                RecoveryAction(
                    id='clear_cache',
                    type=RecoveryType.CLEAR_CACHE,
                    target='service',
                    parameters={'cache_types': ['memory', 'redis']},
                    max_retries=2,
                    timeout_seconds=30
                ),
                RecoveryAction(
                    id='restart_service',
                    type=RecoveryType.RESTART_SERVICE,
                    target='service',
                    parameters={'restart_type': 'pod'},
                    max_retries=3,
                    timeout_seconds=120,
                    rollback_action='scale_up'
                )
            ]
        })
        
        # Процедура для проблем с БД
        self.emergency_procedures.append({
            'name': 'database_connection_recovery',
            'condition': lambda issue: issue.category == IssueCategory.RELIABILITY and 'database' in issue.description.lower(),
            'actions': [
                RecoveryAction(
                    id='restart_service',
                    type=RecoveryType.RESTART_SERVICE,
                    target='service',
                    parameters={'restart_type': 'pod'},
                    max_retries=2,
                    timeout_seconds=60
                ),
                RecoveryAction(
                    id='clear_cache',
                    type=RecoveryType.CLEAR_CACHE,
                    target='service',
                    parameters={'cache_types': ['redis']},
                    max_retries=1,
                    timeout_seconds=15
                )
            ]
        })
        
        # Процедура для высокого уровня ошибок
        self.emergency_procedures.append({
            'name': 'high_error_rate_recovery',
            'condition': lambda issue: issue.category == IssueCategory.RELIABILITY and 'error' in issue.description.lower(),
            'actions': [
                RecoveryAction(
                    id='circuit_breaker',
                    type=RecoveryType.CIRCUIT_BREAKER,
                    target='service',
                    parameters={'failure_threshold': 3, 'timeout': 60},
                    max_retries=1,
                    timeout_seconds=10
                ),
                RecoveryAction(
                    id='restart_service',
                    type=RecoveryType.RESTART_SERVICE,
                    target='service',
                    parameters={'restart_type': 'pod'},
                    max_retries=2,
                    timeout_seconds=90
                )
            ]
        })
        
        # Процедура для graceful degradation
        self.emergency_procedures.append({
            'name': 'graceful_degradation',
            'condition': lambda issue: issue.severity == IssueSeverity.HIGH and issue.category == IssueCategory.BUSINESS_LOGIC,
            'actions': [
                RecoveryAction(
                    id='switch_traffic',
                    type=RecoveryType.SWITCH_TRAFFIC,
                    target='service',
                    parameters={'target_version': 'stable', 'traffic_percentage': 80},
                    max_retries=1,
                    timeout_seconds=30
                )
            ]
        })
    
    def add_circuit_breaker(self, service_name: str, failure_threshold: int = 5, timeout: int = 60):
        """Добавить circuit breaker для сервиса"""
        self.circuit_breakers[service_name] = CircuitBreaker(failure_threshold, timeout)
    
    async def execute_recovery_procedure(self, procedure_name: str, target_service: str, 
                                       issues: List[HealthIssue]) -> List[RecoveryExecution]:
        """Выполнить процедуру восстановления"""
        
        procedure = next(
            (proc for proc in self.emergency_procedures if proc['name'] == procedure_name),
            None
        )
        
        if not procedure:
            raise Exception(f"Recovery procedure {procedure_name} not found")
        
        execution_results = []
        
        for action in procedure['actions']:
            # Проверка предварительных условий
            if not await self._check_preconditions(action, target_service, issues):
                result = RecoveryExecution(
                    action=action,
                    status=RecoveryStatus.SKIPPED,
                    start_time=datetime.now().isoformat(),
                    end_time=datetime.now().isoformat(),
                    logs=["Preconditions not met"]
                )
                execution_results.append(result)
                continue
            
            # Выполнение действия
            result = await self._execute_recovery_action(action, target_service)
            execution_results.append(result)
            
            # Логирование
            logger.info(f"Recovery action {action.id} for service {target_service}: {result.status.value}")
            
            # Остановка при критической ошибке
            if result.status in [RecoveryStatus.FAILED, RecoveryStatus.TIMEOUT]:
                if action.type == RecoveryType.RESTART_SERVICE:
                    break  # Не продолжать при неудачном перезапуске
        
        # Сохранение истории выполнения
        self.recovery_execution_history.extend(execution_results)
        
        return execution_results
    
    async def _check_preconditions(self, action: RecoveryAction, target_service: str, 
                                 issues: List[HealthIssue]) -> bool:
        """Проверить предварительные условия для действия"""
        
        # Проверка circuit breaker
        if action.type == RecoveryType.CIRCUIT_BREAKER:
            cb = self.circuit_breakers.get(target_service)
            if cb and not cb.can_execute():
                return False
        
        # Проверка доступности сервиса
        if action.type == RecoveryType.RESTART_SERVICE:
            service_health = await self._get_service_health(target_service)
            if service_health and service_health.get('status') == 'critical':
                # Не перезапускать критически важные сервисы без подтверждения
                return False
        
        # Проверка недавних перезапусков
        if action.type == RecoveryType.RESTART_SERVICE:
            restart_handler = self.recovery_handlers[RecoveryType.RESTART_SERVICE]
            history = restart_handler.get_restart_history(target_service)
            
            # Проверка что не было перезапусков в последние 5 минут
            recent_restarts = [
                record for record in history.get(target_service, [])
                if datetime.fromisoformat(record['timestamp']) > datetime.now() - timedelta(minutes=5)
            ]
            
            if recent_restarts:
                return False
        
        return True
    
    async def _execute_recovery_action(self, action: RecoveryAction, target_service: str) -> RecoveryExecution:
        """Выполнить действие восстановления"""
        
        execution = RecoveryExecution(
            action=action,
            status=RecoveryStatus.IN_PROGRESS,
            start_time=datetime.now().isoformat(),
            attempts=0,
            logs=[f"Starting recovery action {action.id} for {target_service}"]
        )
        
        try:
            handler = self.recovery_handlers.get(action.type)
            if not handler:
                raise Exception(f"No handler found for action type {action.type}")
            
            # Выполнение действия с повторами
            for attempt in range(action.max_retries):
                execution.attempts = attempt + 1
                
                try:
                    if action.type == RecoveryType.RESTART_SERVICE:
                        result = await handler.restart_service(
                            target_service, 
                            action.parameters.get('restart_type', 'pod')
                        )
                    elif action.type == RecoveryType.CLEAR_CACHE:
                        result = await handler.clear_service_cache(
                            target_service,
                            action.parameters.get('cache_types', ['redis'])
                        )
                    elif action.type == RecoveryType.SWITCH_TRAFFIC:
                        result = await handler.switch_traffic(
                            target_service,
                            action.parameters.get('target_version', 'stable'),
                            action.parameters.get('traffic_percentage', 100.0)
                        )
                    elif action.type == RecoveryType.CIRCUIT_BREAKER:
                        # Активация circuit breaker
                        cb = self.circuit_breakers.get(target_service)
                        if cb:
                            cb.record_failure()
                        result = {'circuit_breaker_activated': True}
                    else:
                        raise Exception(f"Action type {action.type} not implemented")
                    
                    execution.result = result
                    execution.status = RecoveryStatus.SUCCESS
                    execution.end_time = datetime.now().isoformat()
                    execution.logs.append(f"Action completed successfully on attempt {attempt + 1}")
                    
                    # Запись успешного выполнения в circuit breaker
                    if action.type == RecoveryType.CIRCUIT_BREAKER:
                        cb = self.circuit_breakers.get(target_service)
                        if cb:
                            cb.record_success()
                    
                    return execution
                    
                except Exception as e:
                    execution.logs.append(f"Attempt {attempt + 1} failed: {str(e)}")
                    
                    if attempt == action.max_retries - 1:
                        raise e
                    
                    # Ожидание перед следующей попыткой
                    await asyncio.sleep(2 ** attempt)
            
        except asyncio.TimeoutError:
            execution.status = RecoveryStatus.TIMEOUT
            execution.error_message = f"Action timeout after {action.timeout_seconds} seconds"
        except Exception as e:
            execution.status = RecoveryStatus.FAILED
            execution.error_message = str(e)
        finally:
            if execution.end_time is None:
                execution.end_time = datetime.now().isoformat()
        
        return execution
    
    async def _get_service_health(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Получить информацию о здоровье сервиса"""
        if self.health_manager:
            try:
                overall_health = await self.health_manager.get_overall_health()
                return overall_health.get('services', {}).get(service_name)
            except Exception as e:
                logger.error(f"Error getting service health for {service_name}: {e}")
        
        return None
    
    async def auto_recovery_monitor(self):
        """Мониторинг и автоматическое восстановление"""
        while self.is_running:
            try:
                if self.health_manager:
                    overall_health = await self.health_manager.get_overall_health()
                    
                    # Анализ проблем и запуск автоматического восстановления
                    issues = overall_health.get('issues', [])
                    
                    for issue in issues:
                        if issue.get('severity') in ['high', 'critical']:
                            affected_services = issue.get('affected_services', [])
                            
                            for service in affected_services:
                                # Поиск подходящей процедуры восстановления
                                for procedure in self.emergency_procedures:
                                    if procedure['condition'](issue):
                                        logger.info(f"Starting recovery procedure {procedure['name']} for service {service}")
                                        
                                        # Выполнение процедуры восстановления
                                        try:
                                            await self.execute_recovery_procedure(
                                                procedure['name'], 
                                                service, 
                                                [issue]
                                            )
                                        except Exception as e:
                                            logger.error(f"Recovery procedure failed for {service}: {e}")
                                        
                                        break  # Выполнить только одну процедуру для каждой проблемы
                
                # Ожидание до следующего цикла мониторинга
                await asyncio.sleep(60)  # Проверка каждую минуту
                
            except Exception as e:
                logger.error(f"Error in auto recovery monitor: {e}")
                await asyncio.sleep(300)  # При ошибке ждать 5 минут
    
    async def start_auto_recovery(self):
        """Запустить автоматическое восстановление"""
        if self.is_running:
            logger.warning("Auto recovery already running")
            return
        
        self.is_running = True
        logger.info("Starting automated recovery system")
        
        # Запуск мониторинга
        monitor_task = asyncio.create_task(self.auto_recovery_monitor())
        
        try:
            await monitor_task
        except asyncio.CancelledError:
            logger.info("Auto recovery monitor cancelled")
        finally:
            self.is_running = False
    
    def stop_auto_recovery(self):
        """Остановить автоматическое восстановление"""
        self.is_running = False
        logger.info("Stopping automated recovery system")
    
    def get_recovery_statistics(self) -> Dict[str, Any]:
        """Получить статистику восстановления"""
        total_executions = len(self.recovery_execution_history)
        successful_executions = len([
            exec for exec in self.recovery_execution_history
            if exec.status == RecoveryStatus.SUCCESS
        ])
        failed_executions = len([
            exec for exec in self.recovery_execution_history
            if exec.status in [RecoveryStatus.FAILED, RecoveryStatus.TIMEOUT]
        ])
        
        action_stats = {}
        for execution in self.recovery_execution_history:
            action_type = execution.action.type.value
            if action_type not in action_stats:
                action_stats[action_type] = {'total': 0, 'success': 0, 'failed': 0}
            
            action_stats[action_type]['total'] += 1
            if execution.status == RecoveryStatus.SUCCESS:
                action_stats[action_type]['success'] += 1
            else:
                action_stats[action_type]['failed'] += 1
        
        return {
            'total_executions': total_executions,
            'successful_executions': successful_executions,
            'failed_executions': failed_executions,
            'success_rate': successful_executions / max(1, total_executions),
            'action_statistics': action_stats,
            'circuit_breaker_states': {
                name: cb.get_state() 
                for name, cb in self.circuit_breakers.items()
            }
        }
    
    def export_recovery_report(self, filename: str = None) -> str:
        """Экспортировать отчет о восстановлении"""
        if not filename:
            filename = f"recovery_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'statistics': self.get_recovery_statistics(),
            'execution_history': [
                {
                    **asdict(execution),
                    'action': {
                        **asdict(execution.action),
                        'type': execution.action.type.value
                    },
                    'status': execution.status.value
                }
                for execution in self.recovery_execution_history[-100:]  # Последние 100 записей
            ],
            'circuit_breaker_states': {
                name: cb.get_state() 
                for name, cb in self.circuit_breakers.items()
            },
            'available_procedures': [
                procedure['name'] for procedure in self.emergency_procedures
            ]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        return filename

if __name__ == "__main__":
    # Пример использования системы автоматического восстановления
    async def main():
        # Создание системы восстановления
        recovery_system = AutomatedRecoverySystem()
        
        # Добавление circuit breaker для сервиса
        recovery_system.add_circuit_breaker('api-gateway', failure_threshold=3, timeout=60)
        
        # Пример выполнения процедуры восстановления
        issues = [
            HealthIssue(
                id='test_issue',
                title='High CPU Usage',
                description='CPU usage is above 90%',
                severity=IssueSeverity.HIGH,
                category=IssueCategory.PERFORMANCE,
                affected_services=['api-gateway'],
                detected_at=datetime.now().isoformat(),
                status='open',
                recommendations=['Restart service', 'Clear cache']
            )
        ]
        
        execution_results = await recovery_system.execute_recovery_procedure(
            'high_cpu_recovery',
            'api-gateway',
            issues
        )
        
        for result in execution_results:
            print(f"Action {result.action.id}: {result.status.value}")
        
        # Получение статистики
        stats = recovery_system.get_recovery_statistics()
        print(f"Recovery statistics: {stats}")
    
    asyncio.run(main())