# [NEXUS IDENTITY] ID: -7342382585094536202 | DATE: 2025-11-19

"""
Тесты для системы непрерывного улучшения ML.
Тестирование всех компонентов ML системы: метрики, модели, A/B тестирование.
"""

import asyncio
from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest

from src.ml.ab_testing.tester import ABTestConfig, ABTestManager, TestType
from src.ml.experiments.mlflow_manager import MLFlowManager
# Тестируемые компоненты
from src.ml.metrics.collector import AssistantRole, MetricsCollector
from src.ml.models.predictor import (ModelEnsemble, PredictionType,
                                     SklearnPredictor, create_model)
from src.ml.training.trainer import DataPreprocessor, ModelTrainer


class TestMetricsCollector:
    """Тесты сборщика метрик"""

    @pytest.fixture
    def metrics_collector(self):
        return MetricsCollector()

    @pytest.fixture
    def sample_requirements_data(self):
        return {
            "predicted_requirements": [
                {"text": "Система должна обрабатывать заказы", "type": "functional"},
                {
                    "text": "Время отклика должно быть менее 2 секунд",
                    "type": "non_functional",
                },
            ],
            "actual_requirements": [
                {"text": "Система должна обрабатывать заказы", "type": "functional"},
                {"text": "Отзывчивость системы до 2 секунд",
                    "type": "non_functional"},
            ],
        }

    @pytest.mark.asyncio
    async def test_record_requirement_analysis_accuracy(
        self, metrics_collector, sample_requirements_data
    ):
        """Тест записи точности анализа требований"""

        result = await metrics_collector.record_requirement_analysis_accuracy(
            assistant_role=AssistantRole.ARCHITECT,
            predicted_requirements=sample_requirements_data["predicted_requirements"],
            actual_requirements=sample_requirements_data["actual_requirements"],
            project_id="test_project_123",
        )

        if not (result is not None):
            raise AssertionError("Assertion failed: result is not None")
        if not (len(result) > 0  # Должен вернуться ID метрики):
            raise AssertionError(
                "Assertion failed: len(result) > 0  # Должен вернуться ID метрики")

    @ pytest.mark.asyncio
    async def test_record_diagram_quality_score(self, metrics_collector):
        """Тест записи качества диаграммы"""

        diagram_code="""
        graph TD
            A[Начало] --> B[Обработка заказа]
            B --> C[Проверка данных]
            C --> D[Сохранение]
            D --> E[Завершение]
        """

        result=await metrics_collector.record_diagram_quality_score(
            assistant_role=AssistantRole.ARCHITECT,
            generated_diagram=diagram_code,
            user_feedback=4.5,
            project_id="test_project_123",
        )

        if not (result is not None):
            raise AssertionError("Assertion failed: result is not None")

    @ pytest.mark.asyncio
    async def test_record_risk_assessment_precision(self, metrics_collector):
        """Тест записи точности оценки рисков"""

        predicted_risks=[
            {"description": "Высокая нагрузка на систему", "severity": "HIGH"},
            {"description": "Проблемы с интеграцией", "severity": "MEDIUM"},
        ]

        actual_risks=[
            {"description": "Высокая нагрузка на систему", "severity": "HIGH"},
            {"description": "Уязвимости безопасности", "severity": "MEDIUM"},
        ]

        result=await metrics_collector.record_risk_assessment_precision(
            assistant_role=AssistantRole.ARCHITECT,
            predicted_risks=predicted_risks,
            actual_risks=actual_risks,
            project_id="test_project_123",
        )

        if not (result is not None):
            raise AssertionError("Assertion failed: result is not None")

    def test_requirements_accuracy_calculation(self, metrics_collector):
        """Тест расчета точности анализа требований"""

        predicted=[
            {"text": "Система должна обрабатывать заказы"},
            {"text": "Время отклика до 2 секунд"},
        ]

        actual=[
            {"text": "Система должна обрабатывать заказы"},
            {"text": "Отзывчивость системы до 2 секунд"},
        ]

        accuracy=metrics_collector._calculate_requirements_accuracy(
            predicted, actual)

        if not (0 <= accuracy <= 1):
            raise AssertionError("Assertion failed: 0 <= accuracy <= 1")
        if not (accuracy > 0  # Должна быть положительная точность):
            raise AssertionError(
                "Assertion failed: accuracy > 0  # Должна быть положительная точность")

    def test_diagram_quality_calculation(self, metrics_collector):
        """Тест расчета качества диаграммы"""

        good_diagram="""
        graph TD
            A[Start] --> B{Decision}
            B -->|Yes| C[Action 1]
            B -->|No| D[Action 2]
        """

        bad_diagram="This is not a valid mermaid diagram"

        good_quality=metrics_collector._calculate_diagram_quality(good_diagram)
        bad_quality=metrics_collector._calculate_diagram_quality(bad_diagram)

        if not (good_quality > bad_quality):
            raise AssertionError(
                "Assertion failed: good_quality > bad_quality")
        if not (0 <= good_quality <= 1):
            raise AssertionError("Assertion failed: 0 <= good_quality <= 1")
        if not (0 <= bad_quality <= 1):
            raise AssertionError("Assertion failed: 0 <= bad_quality <= 1")


class TestSklearnPredictor:
    """Тесты Sklearn предиктора"""

    @ pytest.fixture
    def sample_data(self):
        """Генерация тестовых данных"""
        np.random.seed(42)
        n_samples=100
        n_features=5

        X=np.random.randn(n_samples, n_features)
        y=(X[:, 0] + X[:, 1] > 0).astype(int)  # Бинарная классификация

        df=pd.DataFrame(X, columns=[f"feature_{i}" for i in range(n_features)])
        df["target"]=y

        return df

    def test_sklearn_predictor_creation(self):
        """Тест создания Sklearn предиктора"""

        features=["feature_1", "feature_2", "feature_3"]

        predictor=SklearnPredictor(
            model_name="test_classifier",
            prediction_type=PredictionType.CLASSIFICATION,
            features=features,
            target="target",
            model_params={"n_estimators": 100},
        )

        if not (predictor.model_name == "test_classifier"):
            raise AssertionError("Assertion failed: predictor.model_name == "test_classifier"")
        if not (predictor.prediction_type == PredictionType.CLASSIFICATION):
            raise AssertionError(
                "Assertion failed: predictor.prediction_type == PredictionType.CLASSIFICATION")
        if not (predictor.features == features):
            raise AssertionError(
                "Assertion failed: predictor.features == features")
        if not (not predictor.is_trained):
            raise AssertionError("Assertion failed: not predictor.is_trained")

    def test_sklearn_predictor_training(self, sample_data):
        """Тест обучения Sklearn предиктора"""

        features=[col for col in sample_data.columns if col != "target"]

        predictor=SklearnPredictor(
            model_name="test_classifier",
            prediction_type=PredictionType.CLASSIFICATION,
            features=features,
            target="target",
            model_params={"n_estimators": 10, "random_state": 42},
        )

        # Обучение
        predictor.fit(sample_data[features], sample_data["target"])

        if not (predictor.is_trained):
            raise AssertionError("Assertion failed: predictor.is_trained")
        if not (predictor.model is not None):
            raise AssertionError(
                "Assertion failed: predictor.model is not None")

    def test_sklearn_prediction(self, sample_data):
        """Тест предсказаний Sklearn предиктора"""

        features=[col for col in sample_data.columns if col != "target"]

        predictor=SklearnPredictor(
            model_name="test_classifier",
            prediction_type=PredictionType.CLASSIFICATION,
            features=features,
            target="target",
            model_params={"n_estimators": 10, "random_state": 42},
        )

        # Обучение
        X_train=sample_data[features][:70]
        y_train=sample_data["target"][:70]
        X_test=sample_data[features][70:]

        predictor.fit(X_train, y_train)

        # Предсказание
        predictions=predictor.predict(X_test)

        if not (len(predictions) == len(X_test)):
            raise AssertionError(
                "Assertion failed: len(predictions) == len(X_test)")
        if not (all(pred in [0, 1] for pred in predictions)  # Бинарная классификация):
            raise AssertionError(
                "Assertion failed: all(pred in [0, 1] for pred in predictions)  # Бинарная классификация")

    def test_feature_importance(self, sample_data):
        """Тест получения важности признаков"""

        features=[col for col in sample_data.columns if col != "target"]

        predictor=SklearnPredictor(
            model_name="test_classifier",
            prediction_type=PredictionType.CLASSIFICATION,
            features=features,
            target="target",
            model_params={"n_estimators": 50, "random_state": 42},
        )

        predictor.fit(sample_data[features], sample_data["target"])

        importance=predictor.get_feature_importance()

        if not (importance is not None):
            raise AssertionError("Assertion failed: importance is not None")
        if not (len(importance) == len(features)):
            raise AssertionError(
                "Assertion failed: len(importance) == len(features)")
        if not (all(imp >= 0 for imp in importance.values())  # Важность неотрицательна):
            raise AssertionError(
                "Assertion failed: all(imp >= 0 for imp in importance.values())  # Важность неотрицательна")


class TestModelTrainer:
    """Тесты обучающего пайплайна"""

    @ pytest.fixture
    def model_trainer(self):
        return ModelTrainer()

    @ pytest.fixture
    def sample_training_data(self):
        """Генерация данных для обучения"""
        np.random.seed(42)
        n_samples=50

        data={
            "feature_1": np.random.randn(n_samples),
            "feature_2": np.random.randn(n_samples),
            "feature_3": np.random.randn(n_samples),
            "feature_4": np.random.randn(n_samples),
            "target": np.secrets.randbelow(0, 2, n_samples),
        }

        return pd.DataFrame(data)

    def test_data_preprocessor_initialization(self):
        """Тест инициализации препроцессора данных"""

        preprocessor=DataPreprocessor()

        if not (preprocessor.scalars == {}):
            raise AssertionError(
                "Assertion failed: preprocessor.scalars == {}")
        if not (preprocessor.encoders == {}):
            raise AssertionError(
                "Assertion failed: preprocessor.encoders == {}")
        if not (preprocessor.feature_selectors == {}):
            raise AssertionError(
                "Assertion failed: preprocessor.feature_selectors == {}")

    def test_data_preprocessing(self, sample_training_data):
        """Тест предобработки данных"""

        preprocessor=DataPreprocessor()

        features=["feature_1", "feature_2", "feature_3", "feature_4"]
        target="target"

        X, y=preprocessor.prepare_features(
            sample_training_data,
            features=features,
            target=target,
            preprocessing_config={
                "fill_method": "median",
                "categorical_encoding": "label",
                "normalize": True,
            },
        )

        if not (X.shape[0] == len(sample_training_data)):
            raise AssertionError(
                "Assertion failed: X.shape[0] == len(sample_training_data)")
        if not (X.shape[1] <= len(features)  # Может быть меньше после отбора признаков):
            raise AssertionError(
                "Assertion failed: X.shape[1] <= len(features)  # Может быть меньше после отбора признаков")
        if not (len(y) == len(sample_training_data)):
            raise AssertionError(
                "Assertion failed: len(y) == len(sample_training_data)")
        if not (y.name == "target"):
            raise AssertionError("Assertion failed: y.name == "target"")

    def test_prediction_type_detection(self):
        """Тест определения типа предсказания"""

        preprocessor=DataPreprocessor()

        # Классификация
        binary_series=pd.Series([0, 1, 0, 1, 0])
        if not (():
            raise AssertionError("Assertion failed: (")
            preprocessor._get_prediction_type(binary_series)
            == PredictionType.CLASSIFICATION
        )

        # Регрессия
        continuous_series=pd.Series([1.5, 2.3, 4.1, 5.8, 3.2])
        if not (():
            raise AssertionError("Assertion failed: (")
            preprocessor._get_prediction_type(continuous_series)
            == PredictionType.REGRESSION
        )

    def test_model_creation(self, model_trainer, sample_training_data):
        """Тест создания модели"""

        features=["feature_1", "feature_2", "feature_3", "feature_4"]
        target="target"

        try:
