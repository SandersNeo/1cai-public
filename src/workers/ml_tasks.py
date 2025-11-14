"""
Celery Worker для background обучения моделей и ML задач.
Обрабатывает асинхронные ML задачи: обучение, переобучение, оптимизация гиперпараметров.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Celery
from celery import Celery
from celery.utils.log import get_task_logger

# ML библиотеки
import pandas as pd
import numpy as np

# Локальные импорты
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ml.training.trainer import ModelTrainer
from ml.experiments.mlflow_manager import MLFlowManager
from ml.metrics.collector import MetricsCollector
from config import settings
from src.utils.structured_logging import StructuredLogger

# Настройка Celery
celery_app = Celery(
    "ml_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        'workers.ml_tasks'
    ]
)

# Конфигурация Celery
celery_app.conf.update(
    # Временные зоны
    timezone='UTC',
    enable_utc=True,
    
    # Сериализация
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Времена выполнения
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 минут
    task_soft_time_limit=25 * 60,  # 25 минут
    
    # Ретрай задач
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    
    # Мониторинг
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Cron-like периодические задачи
    beat_schedule={
        'retrain-models-daily': {
            'task': 'workers.ml_tasks.retrain_all_models',
            'schedule': crontab(hour=2, minute=0),  # Ежедневно в 2:00 UTC
        },
        'update-feature-store': {
            'task': 'workers.ml_tasks.update_feature_store',
            'schedule': crontab(minute=0),  # Каждый час
        },
        'cleanup-old-experiments': {
            'task': 'workers.ml_tasks.cleanup_old_experiments',
            'schedule': crontab(hour=1, minute=0),  # Ежечасно в 1:00
        },
        'check-model-drift': {
            'task': 'workers.ml_tasks.check_model_drift',
            'schedule': crontab(minute=30),  # Каждые 30 минут
        },
        'retrain-underperforming': {
            'task': 'workers.ml_tasks.retrain_underperforming_models',
            'schedule': crontab(hour=3, minute=0),  # Ежедневно в 3:00
        }
    },
    beat_schedule_filename='/tmp/celerybeat-schedule'
)

# Логгер
task_logger = StructuredLogger(__name__).logger

# Инициализация сервисов
mlflow_manager = None
metrics_collector = None
model_trainer = None


def init_services():
    """Инициализация сервисов (вызывается при старте worker)"""
    global mlflow_manager, metrics_collector, model_trainer
    
    if mlflow_manager is None:
        mlflow_manager = MLFlowManager()
        task_logger.info("MLflow Manager инициализирован")
    
    if metrics_collector is None:
        metrics_collector = MetricsCollector()
        task_logger.info("Metrics Collector инициализирован")
    
    if model_trainer is None:
        model_trainer = ModelTrainer(
            mlflow_manager=mlflow_manager,
            metrics_collector=metrics_collector,
            celery_app=celery_app
        )
        task_logger.info("Model Trainer инициализирован")


# Инициализация при загрузке модуля
init_services()


@celery_app.task(bind=True)
def train_model(self, config: Dict[str, Any]):
    """Обучение модели ML"""
    
    task_logger.info(
        "Начато обучение модели",
        extra={"model_name": config.get('model_name')}
    )
    
    try:
        # Преобразование данных
        training_data = pd.DataFrame(config['training_data'])
        
        # Обучение модели
        result = model_trainer.train_model(
            model_name=config['model_name'],
            model_type=config['model_type'],
            features=config['features'],
            target=config['target'],
            training_data=training_data,
            test_size=config.get('test_size', 0.2),
            hyperparameters=config.get('hyperparameters'),
            preprocessing_config=config.get('preprocessing_config'),
            experiment_name=f"{config['model_name']}_celery_training"
        )
        
        # Обновление статуса задачи
        self.update_state(
            state='PROGRESS',
            meta={
                'status': 'training_completed',
                'model_name': config['model_name'],
                'training_duration': result['training_duration_seconds'],
                'test_metrics': result['test_metrics']
            }
        )
        
        task_logger.info(
            f"Обучение модели {config['model_name']} завершено за "
            f"{result['training_duration_seconds']:.2f} секунд"
        )
        
        return {
            'status': 'completed',
            'model_name': config['model_name'],
            'training_duration': result['training_duration_seconds'],
            'test_metrics': result['test_metrics']
        }
        
    except Exception as e:
        task_logger.error(
            "Ошибка обучения модели",
            extra={
                "model_name": config.get('model_name'),
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        
        self.update_state(
            state='FAILURE',
            meta={
                'status': 'training_failed',
                'error': str(e),
                'model_name': config.get('model_name')
            }
        )
        
        raise


@celery_app.task(bind=True)
def hyperparameter_optimization(self, config: Dict[str, Any]):
    """Оптимизация гиперпараметров модели"""
    
    task_logger.info(
        f"Начата оптимизация гиперпараметров для модели: {config.get('model_name')}"
    )
    
    try:
        # Преобразование данных
        training_data = pd.DataFrame(config['training_data'])
        
        # Оптимизация гиперпараметров
        result = model_trainer.hyperparameter_tuning(
            model_name=config['model_name'],
            model_type=config['model_type'],
            features=config['features'],
            target=config['target'],
            training_data=training_data,
            param_space=config['param_space'],
            n_trials=config.get('n_trials', 100),
            experiment_name=f"{config['model_name']}_hyperopt"
        )
        
        self.update_state(
            state='PROGRESS',
            meta={
                'status': 'optimization_completed',
                'model_name': config['model_name'],
                'best_score': result['best_score'],
                'best_params': result['best_params']
            }
        )
        
        task_logger.info(
            f"Оптимизация гиперпараметров для {config['model_name']} завершена. "
            f"Лучший скор: {result['best_score']:.4f}"
        )
        
        return {
            'status': 'completed',
            'model_name': config['model_name'],
            'best_score': result['best_score'],
            'best_params': result['best_params'],
            'optimization_duration': result['tuning_duration_seconds']
        }
        
    except Exception as e:
        task_logger.error(
            "Ошибка оптимизации гиперпараметров",
            extra={
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        
        self.update_state(
            state='FAILURE',
            meta={
                'status': 'optimization_failed',
                'error': str(e),
                'model_name': config.get('model_name')
            }
        )
        
        raise


@celery_app.task
def retrain_all_models():
    """Периодическое переобучение всех моделей"""
    
    task_logger.info("Запуск периодического переобучения всех моделей")
    
    try:
        models_retrained = 0
        retrain_results = []
        
        # Здесь можно добавить логику автоматического переобучения
        # на основе новых данных или деградации качества
        
        # Пример: переобучение моделей с низкой производительностью
        performance_summary = model_trainer.metrics_collector.get_performance_summary(hours_back=24)
        
        for role, metrics in performance_summary.items():
            for metric_type, metric_data in metrics.items():
                if metric_data.get('mean', 0) < 0.6:  # Порог качества
                    task_logger.warning(
                        f"Низкое качество метрики {metric_type} для роли {role}: "
                        f"{metric_data.get('mean', 0):.3f}"
                    )
                    
                    # Здесь можно инициировать переобучение
        
        task_logger.info(
            "Завершено периодическое переобучение",
            extra={"models_retrained": models_retrained}
        )
        
        return {
            'status': 'completed',
            'models_retrained': models_retrained,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        task_logger.error(
            "Ошибка периодического переобучения",
            extra={
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise


@celery_app.task
def update_feature_store():
    """Обновление Feature Store с новыми данными"""
    
    task_logger.info("Запуск обновления Feature Store")
    
    try:
        # Здесь можно добавить логику обновления фичей
        # например, извлечение новых признаков из данных
        
        features_updated = 0
        
        # Пример: обновление статистик по метрикам
        recent_metrics = model_trainer.metrics_collector.get_performance_summary(hours_back=1)
        
        if recent_metrics:
            # Логирование обновленных фичей в MLflow
            with model_trainer.mlflow_manager.start_experiment("feature_store_update"):
                model_trainer.mlflow_manager.log_metrics({
                    'metrics_updated': len(recent_metrics),
                    'roles_tracked': len([k for k, v in recent_metrics.items() if v])
                })
        
        task_logger.info(
            "Обновление Feature Store завершено",
            extra={"features_updated": features_updated}
        )
        
        return {
            'status': 'completed',
            'features_updated': features_updated,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        task_logger.error(
            "Ошибка обновления Feature Store",
            extra={
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise


@celery_app.task
def cleanup_old_experiments():
    """Очистка старых MLflow экспериментов"""
    
    task_logger.info("Запуск очистки старых экспериментов")
    
    try:
        # Получение списка экспериментов
        experiments = model_trainer.mlflow_manager.client.search_experiments()
        
        cleanup_count = 0
        
        for experiment in experiments:
            # Удаляем эксперименты старше 30 дней
            if hasattr(experiment, 'creation_time'):
                age_days = (datetime.utcnow().timestamp() - experiment.creation_time / 1000) / (24 * 3600)
                
                if age_days > 30:
                    try:
                        model_trainer.mlflow_manager.client.delete_experiment(experiment.experiment_id)
                        cleanup_count += 1
                        task_logger.info(
                            "Удален старый эксперимент",
                            extra={"experiment_name": experiment.name}
                        )
                    except Exception as e:
                        task_logger.warning(
                            "Не удалось удалить эксперимент",
                            extra={
                                "experiment_name": experiment.name,
                                "error": str(e),
                                "error_type": type(e).__name__
                            }
                        )
        
        task_logger.info(
            "Очистка завершена",
            extra={"experiments_deleted": cleanup_count}
        )
        
        return {
            'status': 'completed',
            'experiments_deleted': cleanup_count,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        task_logger.error(
            "Ошибка очистки экспериментов",
            extra={
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise


@celery_app.task
def check_model_drift():
    """Проверка дрейфа моделей"""
    
    task_logger.info("Запуск проверки дрейфа моделей")
    
    try:
        drift_detected = False
        drift_details = []
        
        # Получение актуальных метрик
        current_metrics = model_trainer.metrics_collector.get_performance_summary(hours_back=1)
        historical_metrics = model_trainer.metrics_collector.get_performance_summary(hours_back=168)  # Неделя назад
        
        # Сравнение метрик для выявления дрейфа
        for role in current_metrics:
            for metric_type in current_metrics[role]:
                current_mean = current_metrics[role][metric_type].get('mean', 0)
                historical_mean = historical_metrics.get(role, {}).get(metric_type, {}).get('mean', 0)
                
                if historical_mean > 0:
                    drift_percent = abs(current_mean - historical_mean) / historical_mean * 100
                    
                    if drift_percent > 15:  # Порог дрейфа 15%
                        drift_detected = True
                        drift_details.append({
                            'role': role,
                            'metric_type': metric_type,
                            'current_mean': current_mean,
                            'historical_mean': historical_mean,
                            'drift_percent': drift_percent
                        })
        
        if drift_detected:
            task_logger.warning(
                "Обнаружен дрейф моделей",
                extra={"drift_cases": len(drift_details)}
            )
            
            # Можно инициировать автоматическое переобучение
            for drift in drift_details:
                task_logger.info(
                    "Дрейф обнаружен",
                    extra={
                        "role": drift['role'],
                        "metric_type": drift['metric_type'],
                        "drift_percent": round(drift['drift_percent'], 1)
                    }
                )
        else:
            task_logger.info("Дрейф моделей не обнаружен")
        
        return {
            'status': 'completed',
            'drift_detected': drift_detected,
            'drift_details': drift_details,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        task_logger.error(
            "Ошибка проверки дрейфа",
            extra={
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise


@celery_app.task
def retrain_underperforming_models():
    """Переобучение моделей с низкой производительностью"""
    
    task_logger.info("Запуск переобучения слабых моделей")
    
    try:
        models_retrained = 0
        retrain_details = []
        
        # Получение метрик за последние 24 часа
        performance_summary = model_trainer.metrics_collector.get_performance_summary(hours_back=24)
        
        # Определение моделей для переобучения
        for role, metrics in performance_summary.items():
            for metric_type, metric_data in metrics.items():
                mean_score = metric_data.get('mean', 0)
                
                # Пороги для разных типов метрик
                if 'accuracy' in metric_type.lower() or 'precision' in metric_type.lower():
                    threshold = 0.7
                elif 'response_time' in metric_type.lower():
                    threshold = 2.0  # секунд
                elif 'satisfaction' in metric_type.lower():
                    threshold = 0.8
                else:
                    threshold = 0.6
                
                if mean_score < threshold:
                    task_logger.warning(
                        f"Низкая производительность {metric_type} для {role}: {mean_score:.3f}"
                    )
                    
                    # Инициируем переобучение
                    model_name = f"{role}_{metric_type}_predictor"
                    
                    try:
                        # Здесь можно добавить логику сбора новых данных для обучения
                        # и переобучения модели
                        
                        retrain_details.append({
                            'model_name': model_name,
                            'role': role,
                            'metric_type': metric_type,
                            'current_score': mean_score,
                            'threshold': threshold
                        })
                        
                        models_retrained += 1
                        
                        task_logger.info(
                            "Инициировано переобучение модели",
                            extra={"model_name": model_name}
                        )
                        
                    except Exception as e:
                        task_logger.error(
                            "Ошибка переобучения",
                            extra={
                                "model_name": model_name,
                                "error": str(e),
                                "error_type": type(e).__name__
                            },
                            exc_info=True
                        )
        
        task_logger.info(
            "Переобучение слабых моделей завершено",
            extra={"models_retrained": models_retrained}
        )
        
        return {
            'status': 'completed',
            'models_retrained': models_retrained,
            'retrain_details': retrain_details,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        task_logger.error(
            "Ошибка переобучения слабых моделей",
            extra={
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise


@celery_app.task(bind=True)
def process_metrics_batch(self, metrics_data: List[Dict[str, Any]]):
    """Пакетная обработка метрик"""
    
    task_logger.info(
        "Обработка пакета метрик",
        extra={"records_count": len(metrics_data)}
    )
    
    try:
        processed_count = 0
        error_count = 0
        
        for metric_data in metrics_data:
            try:
                # Преобразование enum
                from ml.metrics.collector import MetricType, AssistantRole
                
                metric_type = MetricType(metric_data['metric_type'].lower())
                assistant_role = AssistantRole(metric_data['assistant_role'].lower())
                
                # Запись метрики
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                loop.run_until_complete(
                    model_trainer.metrics_collector.record_requirement_analysis_accuracy(
                        assistant_role=assistant_role,
                        predicted_requirements=metric_data.get('predicted_requirements', []),
                        actual_requirements=metric_data.get('actual_requirements', []),
                        project_id=metric_data['project_id'],
                        context=metric_data.get('context', {})
                    )
                )
                
                processed_count += 1
                
            except Exception as e:
                task_logger.error(
                    "Ошибка обработки метрики",
                    extra={
                        "error": str(e),
                        "error_type": type(e).__name__
                    },
                    exc_info=True
                )
                error_count += 1
        
        self.update_state(
            state='PROGRESS',
            meta={
                'status': 'batch_processing_completed',
                'processed_count': processed_count,
                'error_count': error_count
            }
        )
        
        task_logger.info(
            f"Пакетная обработка метрик завершена. Успешно: {processed_count}, "
            f"ошибок: {error_count}"
        )
        
        return {
            'status': 'completed',
            'processed_count': processed_count,
            'error_count': error_count
        }
        
    except Exception as e:
        task_logger.error(
            "Ошибка пакетной обработки метрик",
            extra={
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise


# Импорт для cron
from celery.schedules import crontab

# Запуск worker'а
if __name__ == "__main__":
    celery_app.start()
