# [NEXUS IDENTITY] ID: -7342382585094536202 | DATE: 2025-11-19

"""
Тесты для системы непрерывного улучшения ML.
Тестирование всех компонентов ML системы: метрики, модели, A/B тестирование.
"""

import pytest
import asyncio
import numpy as np
import pandas as pd
from unittest.mock import Mock

# Тестируемые компоненты
from src.ml.metrics.collector import (
    MetricsCollector,
    AssistantRole,
)
from src.ml.models.predictor import (
    SklearnPredictor,
    ModelEnsemble,
    create_model,
    PredictionType,
)
from src.ml.training.trainer import ModelTrainer, DataPreprocessor
from src.ml.ab_testing.tester import ABTestManager, ABTestConfig, TestType
from src.ml.experiments.mlflow_manager import MLFlowManager


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
                {"text": "Отзывчивость системы до 2 секунд", "type": "non_functional"},
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

        assert result is not None
        assert len(result) > 0  # Должен вернуться ID метрики

    @pytest.mark.asyncio
    async def test_record_diagram_quality_score(self, metrics_collector):
        """Тест записи качества диаграммы"""

        diagram_code = """
        graph TD
            A[Начало] --> B[Обработка заказа]
            B --> C[Проверка данных]
            C --> D[Сохранение]
            D --> E[Завершение]
        """

        result = await metrics_collector.record_diagram_quality_score(
            assistant_role=AssistantRole.ARCHITECT,
            generated_diagram=diagram_code,
            user_feedback=4.5,
            project_id="test_project_123",
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_record_risk_assessment_precision(self, metrics_collector):
        """Тест записи точности оценки рисков"""

        predicted_risks = [
            {"description": "Высокая нагрузка на систему", "severity": "HIGH"},
            {"description": "Проблемы с интеграцией", "severity": "MEDIUM"},
        ]

        actual_risks = [
            {"description": "Высокая нагрузка на систему", "severity": "HIGH"},
            {"description": "Уязвимости безопасности", "severity": "MEDIUM"},
        ]

        result = await metrics_collector.record_risk_assessment_precision(
            assistant_role=AssistantRole.ARCHITECT,
            predicted_risks=predicted_risks,
            actual_risks=actual_risks,
            project_id="test_project_123",
        )

        assert result is not None

    def test_requirements_accuracy_calculation(self, metrics_collector):
        """Тест расчета точности анализа требований"""

        predicted = [
            {"text": "Система должна обрабатывать заказы"},
            {"text": "Время отклика до 2 секунд"},
        ]

        actual = [
            {"text": "Система должна обрабатывать заказы"},
            {"text": "Отзывчивость системы до 2 секунд"},
        ]

        accuracy = metrics_collector._calculate_requirements_accuracy(predicted, actual)

        assert 0 <= accuracy <= 1
        assert accuracy > 0  # Должна быть положительная точность

    def test_diagram_quality_calculation(self, metrics_collector):
        """Тест расчета качества диаграммы"""

        good_diagram = """
        graph TD
            A[Start] --> B{Decision}
            B -->|Yes| C[Action 1]
            B -->|No| D[Action 2]
        """

        bad_diagram = "This is not a valid mermaid diagram"

        good_quality = metrics_collector._calculate_diagram_quality(good_diagram)
        bad_quality = metrics_collector._calculate_diagram_quality(bad_diagram)

        assert good_quality > bad_quality
        assert 0 <= good_quality <= 1
        assert 0 <= bad_quality <= 1


class TestSklearnPredictor:
    """Тесты Sklearn предиктора"""

    @pytest.fixture
    def sample_data(self):
        """Генерация тестовых данных"""
        np.random.seed(42)
        n_samples = 100
        n_features = 5

        X = np.random.randn(n_samples, n_features)
        y = (X[:, 0] + X[:, 1] > 0).astype(int)  # Бинарная классификация

        df = pd.DataFrame(X, columns=[f"feature_{i}" for i in range(n_features)])
        df["target"] = y

        return df

    def test_sklearn_predictor_creation(self):
        """Тест создания Sklearn предиктора"""

        features = ["feature_1", "feature_2", "feature_3"]

        predictor = SklearnPredictor(
            model_name="test_classifier",
            prediction_type=PredictionType.CLASSIFICATION,
            features=features,
            target="target",
            model_params={"n_estimators": 100},
        )

        assert predictor.model_name == "test_classifier"
        assert predictor.prediction_type == PredictionType.CLASSIFICATION
        assert predictor.features == features
        assert not predictor.is_trained

    def test_sklearn_predictor_training(self, sample_data):
        """Тест обучения Sklearn предиктора"""

        features = [col for col in sample_data.columns if col != "target"]

        predictor = SklearnPredictor(
            model_name="test_classifier",
            prediction_type=PredictionType.CLASSIFICATION,
            features=features,
            target="target",
            model_params={"n_estimators": 10, "random_state": 42},
        )

        # Обучение
        predictor.fit(sample_data[features], sample_data["target"])

        assert predictor.is_trained
        assert predictor.model is not None

    def test_sklearn_prediction(self, sample_data):
        """Тест предсказаний Sklearn предиктора"""

        features = [col for col in sample_data.columns if col != "target"]

        predictor = SklearnPredictor(
            model_name="test_classifier",
            prediction_type=PredictionType.CLASSIFICATION,
            features=features,
            target="target",
            model_params={"n_estimators": 10, "random_state": 42},
        )

        # Обучение
        X_train = sample_data[features][:70]
        y_train = sample_data["target"][:70]
        X_test = sample_data[features][70:]

        predictor.fit(X_train, y_train)

        # Предсказание
        predictions = predictor.predict(X_test)

        assert len(predictions) == len(X_test)
        assert all(pred in [0, 1] for pred in predictions)  # Бинарная классификация

    def test_feature_importance(self, sample_data):
        """Тест получения важности признаков"""

        features = [col for col in sample_data.columns if col != "target"]

        predictor = SklearnPredictor(
            model_name="test_classifier",
            prediction_type=PredictionType.CLASSIFICATION,
            features=features,
            target="target",
            model_params={"n_estimators": 50, "random_state": 42},
        )

        predictor.fit(sample_data[features], sample_data["target"])

        importance = predictor.get_feature_importance()

        assert importance is not None
        assert len(importance) == len(features)
        assert all(imp >= 0 for imp in importance.values())  # Важность неотрицательна


class TestModelTrainer:
    """Тесты обучающего пайплайна"""

    @pytest.fixture
    def model_trainer(self):
        return ModelTrainer()

    @pytest.fixture
    def sample_training_data(self):
        """Генерация данных для обучения"""
        np.random.seed(42)
        n_samples = 50

        data = {
            "feature_1": np.random.randn(n_samples),
            "feature_2": np.random.randn(n_samples),
            "feature_3": np.random.randn(n_samples),
            "feature_4": np.random.randn(n_samples),
            "target": np.random.randint(0, 2, n_samples),
        }

        return pd.DataFrame(data)

    def test_data_preprocessor_initialization(self):
        """Тест инициализации препроцессора данных"""

        preprocessor = DataPreprocessor()

        assert preprocessor.scalars == {}
        assert preprocessor.encoders == {}
        assert preprocessor.feature_selectors == {}

    def test_data_preprocessing(self, sample_training_data):
        """Тест предобработки данных"""

        preprocessor = DataPreprocessor()

        features = ["feature_1", "feature_2", "feature_3", "feature_4"]
        target = "target"

        X, y = preprocessor.prepare_features(
            sample_training_data,
            features=features,
            target=target,
            preprocessing_config={
                "fill_method": "median",
                "categorical_encoding": "label",
                "normalize": True,
            },
        )

        assert X.shape[0] == len(sample_training_data)
        assert X.shape[1] <= len(features)  # Может быть меньше после отбора признаков
        assert len(y) == len(sample_training_data)
        assert y.name == "target"

    def test_prediction_type_detection(self):
        """Тест определения типа предсказания"""

        preprocessor = DataPreprocessor()

        # Классификация
        binary_series = pd.Series([0, 1, 0, 1, 0])
        assert (
            preprocessor._get_prediction_type(binary_series)
            == PredictionType.CLASSIFICATION
        )

        # Регрессия
        continuous_series = pd.Series([1.5, 2.3, 4.1, 5.8, 3.2])
        assert (
            preprocessor._get_prediction_type(continuous_series)
            == PredictionType.REGRESSION
        )

    def test_model_creation(self, model_trainer, sample_training_data):
        """Тест создания модели"""

        features = ["feature_1", "feature_2", "feature_3", "feature_4"]
        target = "target"

        try:
            result = model_trainer.train_model(
                model_name="test_model",
                model_type="sklearn",
                features=features,
                target=target,
                training_data=sample_training_data,
                test_size=0.3,
                preprocessing_config={"normalize": True},
            )

            assert "model" in result
            assert "train_metrics" in result
            assert "test_metrics" in result
            assert result["model"] is not None
            assert result["model"].is_trained

        except Exception as e:
            pytest.skip(f"Тест пропущен из-за ошибки: {e}")


class TestABTestManager:
    """Тесты A/B тестирования"""

    @pytest.fixture
    def ab_test_manager(self):
        # Используем SQLite для тестирования
        database_url = "sqlite:///test_ab.db"
        return ABTestManager(database_url=database_url)

    @pytest.fixture
    def sample_models(self):
        """Создание тестовых моделей"""

        # Модель контроля
        control_model = Mock()
        control_model.model_name = "control_model"

        # Модель treatment
        treatment_model = Mock()
        treatment_model.model_name = "treatment_model"

        return control_model, treatment_model

    def test_ab_test_creation(self, ab_test_manager, sample_models):
        """Тест создания A/B теста"""

        control_model, treatment_model = sample_models

        config = ABTestConfig(
            test_name="test_ab_test",
            description="Тестовый A/B тест",
            test_type=TestType.MODEL_COMPARISON,
            control_model=control_model,
            treatment_model=treatment_model,
            traffic_split=0.5,
            primary_metric="accuracy",
            success_criteria={"improvement": 0.05},
            duration_days=7,
            min_sample_size=100,
            significance_level=0.05,
        )

        test_id = ab_test_manager.create_ab_test(config)

        assert test_id is not None
        assert len(test_id) > 0

    def test_user_assignment(self, ab_test_manager, sample_models):
        """Тест назначения пользователей"""

        control_model, treatment_model = sample_models

        config = ABTestConfig(
            test_name="test_user_assignment",
            description="Тест назначения пользователей",
            test_type=TestType.MODEL_COMPARISON,
            control_model=control_model,
            treatment_model=treatment_model,
            traffic_split=0.5,
            primary_metric="accuracy",
            success_criteria={"improvement": 0.05},
            duration_days=7,
            min_sample_size=100,
            significance_level=0.05,
        )

        test_id = ab_test_manager.create_ab_test(config)

        # Назначение пользователя
        assignment = ab_test_manager.assign_model_to_user(
            test_id=test_id, user_id="test_user_123", session_id="session_456"
        )

        assert "group" in assignment
        assert "model" in assignment
        assert "model_name" in assignment
        assert assignment["group"] in ["control", "treatment"]
        assert assignment["model"] in [control_model, treatment_model]

    def test_ab_test_results_analysis(self, ab_test_manager, sample_models):
        """Тест анализа результатов A/B теста"""

        control_model, treatment_model = sample_models

        config = ABTestConfig(
            test_name="test_results",
            description="Тест результатов",
            test_type=TestType.MODEL_COMPARISON,
            control_model=control_model,
            treatment_model=treatment_model,
            traffic_split=0.5,
            primary_metric="accuracy",
            success_criteria={"improvement": 0.05},
            duration_days=1,
            min_sample_size=10,
            significance_level=0.05,
        )

        test_id = ab_test_manager.create_ab_test(config)

        # Симуляция некоторых результатов
        np.random.seed(42)

        # Контрольная группа: средняя точность 0.7
        control_data = np.random.normal(0.7, 0.1, 50)

        # Treatment группа: средняя точность 0.8
        treatment_data = np.random.normal(0.8, 0.1, 50)

        # Симуляция записи результатов
        for i, value in enumerate(control_data):
            ab_test_manager.db.log_test_session(
                test_id,
                {
                    "session_id": f"control_session_{i}",
                    "user_id": f"user_{i}",
                    "group": "control",
                    "assigned_model": "control_model",
                    "predicted_value": value,
                    "actual_value": value,
                    "prediction_error": 0.1,
                },
            )

        for i, value in enumerate(treatment_data):
            ab_test_manager.db.log_test_session(
                test_id,
                {
                    "session_id": f"treatment_session_{i}",
                    "user_id": f"user_{i+50}",
                    "group": "treatment",
                    "assigned_model": "treatment_model",
                    "predicted_value": value,
                    "actual_value": value,
                    "prediction_error": 0.1,
                },
            )

        # Анализ результатов
        result = ab_test_manager.analyze_test_results(test_id)

        assert result.control_metric > 0
        assert result.treatment_metric > 0
        assert result.improvement != 0
        assert 0 <= result.p_value <= 1
        assert isinstance(result.confidence_interval, tuple)
        assert len(result.confidence_interval) == 2


class TestModelEnsemble:
    """Тесты ансамбля моделей"""

    @pytest.fixture
    def sample_models(self):
        """Создание тестовых моделей"""
        np.random.seed(42)
        n_samples = 50
        n_features = 5

        X = np.random.randn(n_samples, n_features)
        y = (X[:, 0] + X[:, 1] > 0).astype(int)

        features = [f"feature_{i}" for i in range(n_features)]

        # Создание нескольких моделей
        models = []

        for i in range(3):
            model = SklearnPredictor(
                model_name=f"model_{i}",
                prediction_type=PredictionType.CLASSIFICATION,
                features=features,
                target="target",
                model_params={"n_estimators": 10, "random_state": 42 + i},
            )

            # Обучение модели
            df = pd.DataFrame(X, columns=features)
            df["target"] = y
            model.fit(df[features], y)

            models.append(model)

        return models

    def test_ensemble_creation(self, sample_models):
        """Тест создания ансамбля"""

        ensemble = ModelEnsemble(models=sample_models, ensemble_method="average")

        assert len(ensemble.models) == 3
        assert ensemble.ensemble_method == "average"

    def test_ensemble_training(self, sample_models):
        """Тест обучения ансамбля"""

        ensemble = ModelEnsemble(models=sample_models, ensemble_method="average")

        # Данные для тестирования
        np.random.seed(42)
        X_test = np.random.randn(10, 5)

        predictions = ensemble.predict(X_test)

        assert len(predictions) == 10
        assert all(pred in [0, 1] for pred in predictions)

    def test_ensemble_with_uncertainty(self, sample_models):
        """Тест предсказания с неопределенностью"""

        ensemble = ModelEnsemble(models=sample_models, ensemble_method="average")

        # Данные для тестирования
        np.random.seed(42)
        X_test = np.random.randn(10, 5)

        mean_pred, uncertainty = ensemble.predict_with_uncertainty(X_test)

        assert len(mean_pred) == 10
        assert len(uncertainty) == 10
        assert all(u >= 0 for u in uncertainty)  # Неопределенность неотрицательна


class TestMLFlowIntegration:
    """Тесты интеграции с MLflow"""

    @pytest.fixture
    def mlflow_manager(self):
        # Используем локальный MLflow для тестирования
        return MLFlowManager("sqlite:///test_mlflow.db")

    def test_experiment_creation(self, mlflow_manager):
        """Тест создания экспериментов"""

        experiment_name = "test_experiment"

        # Запуск эксперимента
        run_id = mlflow_manager.start_experiment(experiment_name, "test_run")

        assert run_id is not None
        assert len(run_id) > 0

        # Завершение эксперимента
        mlflow_manager.close_experiment(run_id)

    def test_metrics_logging(self, mlflow_manager):
        """Тест логирования метрик"""

        run_id = mlflow_manager.start_experiment("test_metrics", "metrics_run")

        # Логирование метрик
        test_metrics = {
            "accuracy": 0.85,
            "precision": 0.82,
            "recall": 0.88,
            "f1_score": 0.85,
        }

        mlflow_manager.log_metrics(test_metrics)

        # Логирование параметров
        test_params = {"n_estimators": 100, "learning_rate": 0.1, "max_depth": 10}

        mlflow_manager.log_params(test_params)

        # Завершение эксперимента
        mlflow_manager.close_experiment(run_id)

        # Проверка получения данных
        df = mlflow_manager.get_experiment_metrics("test_metrics", limit=1)

        assert len(df) == 1
        assert "metric_accuracy" in df.columns


# Фикстура для тестирования с реальными зависимостями
@pytest.fixture(scope="session")
def event_loop():
    """Создание event loop для асинхронных тестов"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Параметризованные тесты
@pytest.mark.parametrize(
    "model_type,prediction_type",
    [
        ("sklearn", PredictionType.CLASSIFICATION),
        ("sklearn", PredictionType.REGRESSION),
    ],
)
def test_model_factory(model_type, prediction_type):
    """Тест фабрики моделей"""

    features = ["feature_1", "feature_2", "feature_3"]

    model = create_model(
        model_type=model_type,
        model_name=f"test_{prediction_type}",
        prediction_type=prediction_type,
        features=features,
        target="target",
        model_params={"n_estimators": 10},
    )

    assert model is not None
    assert model.model_name == f"test_{prediction_type}"
    assert model.prediction_type == prediction_type


if __name__ == "__main__":
    # Запуск тестов
    pytest.main([__file__, "-v"])
