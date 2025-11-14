"""
Базовый класс для ML моделей предсказания.
Интеграция с TensorFlow/PyTorch и scikit-learn для различных типов моделей.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union, Tuple
import numpy as np
import pandas as pd
import pickle
import joblib
from datetime import datetime
import json

# ML модели
from sklearn.base import BaseEstimator, ClassifierMixin, RegressorMixin
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.svm import SVC, SVR
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, mean_squared_error, r2_score

# TensorFlow интеграция
try:
    import tensorflow as tf
    from tensorflow import keras
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False

# PyTorch интеграция
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from src.config import settings
from src.ml.experiments.mlflow_manager import MLFlowManager
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class PredictionType:
    """Типы предсказаний"""
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    RECOMMENDATION = "recommendation"


class MLPredictor(ABC):
    """Абстрактный базовый класс для всех ML моделей"""
    
    def __init__(
        self,
        model_name: str,
        prediction_type: str,
        features: List[str],
        target: Optional[str] = None,
        mlflow_manager: Optional[MLFlowManager] = None
    ):
        self.model_name = model_name
        self.prediction_type = prediction_type
        self.features = features
        self.target = target
        self.mlflow_manager = mlflow_manager
        self.model = None
        self.is_trained = False
        
        # Конфигурация модели
        self.config = {
            'model_name': model_name,
            'prediction_type': prediction_type,
            'features': features,
            'target': target,
            'created_at': datetime.utcnow().isoformat()
        }
        
        logger.info(
            "Инициализирован MLPredictor",
            extra={"model_name": model_name}
        )

    @abstractmethod
    def fit(self, X: Union[pd.DataFrame, np.ndarray], y: Optional[Union[pd.Series, np.ndarray]] = None) -> 'MLPredictor':
        """Обучение модели"""
        pass

    @abstractmethod
    def predict(self, X: Union[pd.DataFrame, np.ndarray]) -> Union[np.ndarray, pd.DataFrame]:
        """Предсказание"""
        pass

    @abstractmethod
    def predict_proba(self, X: Union[pd.DataFrame, np.ndarray]) -> Optional[np.ndarray]:
        """Предсказание вероятностей (для классификации)"""
        pass

    def save_model(self, filepath: str):
        """Сохранение модели"""
        try:
            model_data = {
                'config': self.config,
                'is_trained': self.is_trained,
                'model': self.model,
                'features': self.features,
                'target': self.target
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
                
            logger.info(
                "Модель сохранена",
                extra={
                    "model_name": self.model_name,
                    "filepath": filepath
                }
            )
            
        except Exception as e:
            logger.error(
                "Ошибка сохранения модели",
                extra={
                    "model_name": self.model_name,
                    "filepath": filepath,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise

    def load_model(self, filepath: str):
        """Загрузка модели"""
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.config = model_data['config']
            self.model = model_data['model']
            self.is_trained = model_data['is_trained']
            self.features = model_data['features']
            self.target = model_data['target']
            
            logger.info(
                "Модель загружена",
                extra={
                    "model_name": self.model_name,
                    "filepath": filepath
                }
            )
            
        except Exception as e:
            logger.error(
                "Ошибка загрузки модели",
                extra={
                    "model_name": self.model_name,
                    "filepath": filepath,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise

    def evaluate(self, X: Union[pd.DataFrame, np.ndarray], y: Union[pd.Series, np.ndarray]) -> Dict[str, float]:
        """Оценка модели"""
        
        if not self.is_trained:
            raise ValueError("Модель не обучена")
        
        predictions = self.predict(X)
        
        metrics = {}
        
        if self.prediction_type == PredictionType.CLASSIFICATION:
            metrics.update({
                'accuracy': accuracy_score(y, predictions),
                'precision': precision_score(y, predictions, average='weighted'),
                'recall': recall_score(y, predictions, average='weighted'),
                'f1_score': f1_score(y, predictions, average='weighted')
            })
            
        elif self.prediction_type == PredictionType.REGRESSION:
            metrics.update({
                'mse': mean_squared_error(y, predictions),
                'rmse': np.sqrt(mean_squared_error(y, predictions)),
                'r2_score': r2_score(y, predictions)
            })
        
        logger.info(
            "Оценка модели",
            extra={
                "model_name": self.model_name,
                "metrics": metrics
            }
        )
        
        return metrics

    def log_model_metrics_to_mlflow(self, metrics: Dict[str, float], run_id: Optional[str] = None):
        """Логирование метрик в MLflow"""
        
        if self.mlflow_manager:
            self.mlflow_manager.log_metrics(metrics)
        
    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """Получение важности признаков (если поддерживается)"""
        
        if hasattr(self.model, 'feature_importances_'):
            return dict(zip(self.features, self.model.feature_importances_))
        elif hasattr(self.model, 'coef_'):
            importance = np.abs(self.model.coef_[0]) if len(self.model.coef_.shape) == 1 else np.abs(self.model.coef_[0])
            return dict(zip(self.features, importance))
        
        return None

    def explain_prediction(self, X: Union[pd.DataFrame, np.ndarray], index: int = 0) -> Dict[str, Any]:
        """Объяснение предсказания"""
        
        if not self.is_trained:
            raise ValueError("Модель не обучена")
        
        if isinstance(X, pd.DataFrame):
            sample = X.iloc[index].to_dict()
        else:
            sample = dict(zip(self.features, X[index]))
        
        # Базовая интерпретация на основе важности признаков
        importance = self.get_feature_importance()
        
        explanation = {
            'sample': sample,
            'prediction': None,
            'feature_importance': importance,
            'contributing_features': []
        }
        
        if importance:
            sorted_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)
            explanation['contributing_features'] = sorted_features[:5]  # Топ-5 фич
        
        return explanation


class SklearnPredictor(MLPredictor):
    """Реализация предиктора на основе scikit-learn"""
    
    def __init__(
        self,
        model_name: str,
        prediction_type: str,
        features: List[str],
        target: Optional[str] = None,
        model_class: Optional[type] = None,
        model_params: Optional[Dict] = None,
        mlflow_manager: Optional[MLFlowManager] = None
    ):
        super().__init__(model_name, prediction_type, features, target, mlflow_manager)
        
        self.model_class = model_class or self._get_default_model_class(prediction_type)
        self.model_params = model_params or {}
        
        logger.info(
            "Инициализирован SklearnPredictor",
            extra={
                "model_name": model_name,
                "model_class": self.model_class.__name__
            }
        )

    def _get_default_model_class(self, prediction_type: str) -> type:
        """Получение класса модели по умолчанию"""
        
        if prediction_type == PredictionType.CLASSIFICATION:
            return RandomForestClassifier
        elif prediction_type == PredictionType.REGRESSION:
            return RandomForestRegressor
        else:
            return RandomForestClassifier

    def fit(self, X: Union[pd.DataFrame, np.ndarray], y: Optional[Union[pd.Series, np.ndarray]] = None) -> 'SklearnPredictor':
        """Обучение модели"""
        
        try:
            # Преобразование данных
            if isinstance(X, pd.DataFrame):
                X_processed = X[self.features].fillna(0)
            else:
                X_processed = pd.DataFrame(X, columns=self.features).fillna(0)
            
            # Создание и обучение модели
            self.model = self.model_class(**self.model_params)
            self.model.fit(X_processed, y)
            
            self.is_trained = True
            
            logger.info(
                "Модель обучена",
                extra={
                    "model_name": self.model_name,
                    "samples_count": len(X_processed)
                }
            )
            
            return self
            
        except Exception as e:
            logger.error(
                "Ошибка обучения модели",
                extra={
                    "model_name": self.model_name,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise

    def predict(self, X: Union[pd.DataFrame, np.ndarray]) -> Union[np.ndarray, pd.DataFrame]:
        """Предсказание"""
        
        if not self.is_trained:
            raise ValueError("Модель не обучена")
        
        try:
            # Преобразование данных
            if isinstance(X, pd.DataFrame):
                X_processed = X[self.features].fillna(0)
            else:
                X_processed = pd.DataFrame(X, columns=self.features).fillna(0)
            
            predictions = self.model.predict(X_processed)
            
            logger.debug(
                "Выполнено предсказание",
                extra={"samples_count": len(X_processed)}
            )
            
            return predictions
            
        except Exception as e:
            logger.error(
                "Ошибка предсказания",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise

    def predict_proba(self, X: Union[pd.DataFrame, np.ndarray]) -> Optional[np.ndarray]:
        """Предсказание вероятностей"""
        
        if not self.is_trained or not hasattr(self.model, 'predict_proba'):
            return None
        
        try:
            # Преобразование данных
            if isinstance(X, pd.DataFrame):
                X_processed = X[self.features].fillna(0)
            else:
                X_processed = pd.DataFrame(X, columns=self.features).fillna(0)
            
            probabilities = self.model.predict_proba(X_processed)
            
            logger.debug(
                "Вычислены вероятности",
                extra={"samples_count": len(X_processed)}
            )
            
            return probabilities
            
        except Exception as e:
            logger.error(
                "Ошибка вычисления вероятностей",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            return None


class TensorFlowPredictor(MLPredictor):
    """Реализация предиктора на основе TensorFlow"""
    
    def __init__(
        self,
        model_name: str,
        prediction_type: str,
        features: List[str],
        target: Optional[str] = None,
        model_params: Optional[Dict] = None,
        mlflow_manager: Optional[MLFlowManager] = None
    ):
        super().__init__(model_name, prediction_type, features, target, mlflow_manager)
        
        self.model_params = model_params or {}
        self.history = None
        
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow не установлен")
        
        logger.info(
            "Инициализирован TensorFlowPredictor",
            extra={"model_name": model_name}
        )

    def _build_model(self, input_shape: int) -> 'tf.keras.Model':
        """Построение модели TensorFlow"""
        
        # Базовая архитектура нейронной сети
        model = keras.Sequential([
            keras.layers.Dense(128, activation='relu', input_shape=(input_shape,)),
            keras.layers.Dropout(0.3),
            keras.layers.Dense(64, activation='relu'),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(32, activation='relu'),
        ])
        
        # Выходной слой в зависимости от типа задачи
        if self.prediction_type == PredictionType.CLASSIFICATION:
            # Для классификации - softmax
            num_classes = self.model_params.get('num_classes', 2)
            model.add(keras.layers.Dense(num_classes, activation='softmax'))
            loss = 'sparse_categorical_crossentropy'
            metrics = ['accuracy']
        else:
            # Для регрессии - линейный выход
            model.add(keras.layers.Dense(1))
            loss = 'mse'
            metrics = ['mae']
        
        # Компиляция модели
        optimizer = self.model_params.get('optimizer', 'adam')
        learning_rate = self.model_params.get('learning_rate', 0.001)
        
        model.compile(
            optimizer=optimizer,
            loss=loss,
            metrics=metrics
        )
        
        return model

    def fit(self, X: Union[pd.DataFrame, np.ndarray], y: Optional[Union[pd.Series, np.ndarray]] = None) -> 'TensorFlowPredictor':
        """Обучение модели"""
        
        try:
            # Преобразование данных
            if isinstance(X, pd.DataFrame):
                X_processed = X[self.features].fillna(0).values.astype(np.float32)
            else:
                X_processed = pd.DataFrame(X, columns=self.features).fillna(0).values.astype(np.float32)
            
            y_processed = None
            if y is not None:
                if isinstance(y, pd.Series):
                    y_processed = y.values.astype(np.float32)
                else:
                    y_processed = np.array(y, dtype=np.float32)
            
            # Построение модели
            input_shape = X_processed.shape[1]
            self.model = self._build_model(input_shape)
            
            # Параметры обучения
            epochs = self.model_params.get('epochs', 100)
            batch_size = self.model_params.get('batch_size', 32)
            validation_split = self.model_params.get('validation_split', 0.2)
            
            # Обучение
            self.history = self.model.fit(
                X_processed, y_processed,
                epochs=epochs,
                batch_size=batch_size,
                validation_split=validation_split,
                verbose=1
            )
            
            self.is_trained = True
            
            logger.info(
                "Модель обучена",
                extra={
                    "model_name": self.model_name,
                    "samples_count": len(X_processed)
                }
            )
            
            return self
            
        except Exception as e:
            logger.error(
                "Ошибка обучения модели",
                extra={
                    "model_name": self.model_name,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise

    def predict(self, X: Union[pd.DataFrame, np.ndarray]) -> Union[np.ndarray, pd.DataFrame]:
        """Предсказание"""
        
        if not self.is_trained:
            raise ValueError("Модель не обучена")
        
        try:
            # Преобразование данных
            if isinstance(X, pd.DataFrame):
                X_processed = X[self.features].fillna(0).values.astype(np.float32)
            else:
                X_processed = pd.DataFrame(X, columns=self.features).fillna(0).values.astype(np.float32)
            
            predictions = self.model.predict(X_processed)
            
            # Преобразование результатов
            if self.prediction_type == PredictionType.CLASSIFICATION:
                predictions = np.argmax(predictions, axis=1)
            
            logger.debug(
                "Выполнено предсказание",
                extra={"samples_count": len(X_processed)}
            )
            
            return predictions
            
        except Exception as e:
            logger.error(
                "Ошибка предсказания",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise

    def predict_proba(self, X: Union[pd.DataFrame, np.ndarray]) -> Optional[np.ndarray]:
        """Предсказание вероятностей"""
        
        if not self.is_trained or self.prediction_type != PredictionType.CLASSIFICATION:
            return None
        
        try:
            # Преобразование данных
            if isinstance(X, pd.DataFrame):
                X_processed = X[self.features].fillna(0).values.astype(np.float32)
            else:
                X_processed = pd.DataFrame(X, columns=self.features).fillna(0).values.astype(np.float32)
            
            probabilities = self.model.predict(X_processed)
            
            logger.debug(
                "Вычислены вероятности",
                extra={"samples_count": len(X_processed)}
            )
            
            return probabilities
            
        except Exception as e:
            logger.error(
                "Ошибка вычисления вероятностей",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            return None

    def save_model(self, filepath: str):
        """Сохранение модели TensorFlow"""
        
        try:
            self.model.save(f"{filepath}.h5")
            super().save_model(filepath)  # Сохраняем также конфигурацию
            logger.info(
                "Модель TensorFlow сохранена",
                extra={
                    "model_name": self.model_name,
                    "filepath": filepath
                }
            )
        except Exception as e:
            logger.error(
                "Ошибка сохранения модели TensorFlow",
                extra={
                    "model_name": self.model_name,
                    "filepath": filepath,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise

    def load_model(self, filepath: str):
        """Загрузка модели TensorFlow"""
        
        try:
            self.model = keras.models.load_model(f"{filepath}.h5")
            super().load_model(filepath)  # Загружаем также конфигурацию
            logger.info(
                "Модель TensorFlow загружена",
                extra={
                    "model_name": self.model_name,
                    "filepath": filepath
                }
            )
        except Exception as e:
            logger.error(
                "Ошибка загрузки модели TensorFlow",
                extra={
                    "model_name": self.model_name,
                    "filepath": filepath,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise


class ModelEnsemble:
    """Ансамбль моделей для улучшения точности предсказаний"""
    
    def __init__(self, models: List[MLPredictor], ensemble_method: str = 'average'):
        self.models = models
        self.ensemble_method = ensemble_method
        
        logger.info(
            "Создан ансамбль моделей",
            extra={
                "models_count": len(models),
                "ensemble_method": ensemble_method
            }
        )

    def fit(self, X: Union[pd.DataFrame, np.ndarray], y: Optional[Union[pd.Series, np.ndarray]] = None) -> 'ModelEnsemble':
        """Обучение всех моделей в ансамбле"""
        
        for model in self.models:
            model.fit(X, y)
        
        logger.info("Все модели в ансамбле обучены")
        return self

    def predict(self, X: Union[pd.DataFrame, np.ndarray]) -> Union[np.ndarray, pd.DataFrame]:
        """Предсказание ансамбля"""
        
        predictions = []
        
        for model in self.models:
            pred = model.predict(X)
            predictions.append(pred)
        
        # Объединение предсказаний
        if self.ensemble_method == 'average':
            ensemble_pred = np.mean(predictions, axis=0)
        elif self.ensemble_method == 'majority_vote':
            # Для классификации - голосование большинством
            if self.models[0].prediction_type == PredictionType.CLASSIFICATION:
                ensemble_pred = np.round(np.mean(predictions, axis=0))
            else:
                ensemble_pred = np.mean(predictions, axis=0)
        else:
            ensemble_pred = predictions[0]  # Fallback
        
        return ensemble_pred

    def predict_with_uncertainty(self, X: Union[pd.DataFrame, np.ndarray]) -> Tuple[np.ndarray, np.ndarray]:
        """Предсказание с оценкой неопределенности"""
        
        predictions = []
        
        for model in self.models:
            pred = model.predict(X)
            predictions.append(pred)
        
        predictions = np.array(predictions)
        
        # Среднее предсказание
        mean_pred = np.mean(predictions, axis=0)
        
        # Стандартное отклонение (как мера неопределенности)
        uncertainty = np.std(predictions, axis=0)
        
        return mean_pred, uncertainty

    def evaluate_ensemble(self, X: Union[pd.DataFrame, np.ndarray], y: Union[pd.Series, np.ndarray]) -> Dict[str, float]:
        """Оценка ансамбля"""
        
        ensemble_metrics = {}
        individual_metrics = {}
        
        # Оценка отдельных моделей
        for i, model in enumerate(self.models):
            try:
                metrics = model.evaluate(X, y)
                individual_metrics[f"model_{i}"] = metrics
            except Exception as e:
                logger.warning(
                    "Ошибка оценки модели",
                    extra={
                        "model_index": i,
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                )
        
        # Оценка ансамбля
        try:
            ensemble_pred = self.predict(X)
            
            if self.models[0].prediction_type == PredictionType.CLASSIFICATION:
                ensemble_metrics['ensemble_accuracy'] = accuracy_score(y, ensemble_pred)
            else:
                ensemble_metrics['ensemble_r2'] = r2_score(y, ensemble_pred)
                ensemble_metrics['ensemble_rmse'] = np.sqrt(mean_squared_error(y, ensemble_pred))
                
        except Exception as e:
            logger.error(
                "Ошибка оценки ансамбля",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
        
        # Сравнение с лучшей индивидуальной моделью
        if individual_metrics:
            best_model_name = max(individual_metrics.keys(), 
                                key=lambda k: list(individual_metrics[k].values())[0])
            ensemble_metrics['best_individual_model'] = best_model_name
        
        return ensemble_metrics


# Фабрика для создания моделей
def create_model(
    model_type: str,
    model_name: str,
    prediction_type: str,
    features: List[str],
    target: Optional[str] = None,
    model_params: Optional[Dict] = None,
    mlflow_manager: Optional[MLFlowManager] = None
) -> MLPredictor:
    """Фабрика для создания ML моделей"""
    
    if model_type.lower() in ['sklearn', 'scikit-learn', 'random_forest', 'rf']:
        model_class_map = {
            PredictionType.CLASSIFICATION: RandomForestClassifier,
            PredictionType.REGRESSION: RandomForestRegressor
        }
        
        return SklearnPredictor(
            model_name=model_name,
            prediction_type=prediction_type,
            features=features,
            target=target,
            model_class=model_class_map.get(prediction_type, RandomForestClassifier),
            model_params=model_params,
            mlflow_manager=mlflow_manager
        )
    
    elif model_type.lower() in ['tensorflow', 'keras', 'tf', 'neural_network', 'nn']:
        return TensorFlowPredictor(
            model_name=model_name,
            prediction_type=prediction_type,
            features=features,
            target=target,
            model_params=model_params,
            mlflow_manager=mlflow_manager
        )
    
    else:
        raise ValueError(f"Неподдерживаемый тип модели: {model_type}")
