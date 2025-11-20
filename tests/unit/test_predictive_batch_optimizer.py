# [NEXUS IDENTITY] ID: 2803891306712773357 | DATE: 2025-11-19

"""
Unit тесты для PredictiveBatchOptimizer
"""

from src.services.advanced_optimizations import PredictiveBatchOptimizer


class TestPredictiveBatchOptimizer:
    """Тесты для PredictiveBatchOptimizer"""

    def test_init(self):
        """Тест инициализации"""
        optimizer = PredictiveBatchOptimizer()
        assert optimizer.max_history == 1000
        assert len(optimizer.history) == 0
        assert optimizer.model is None
        assert optimizer.model_trained is False

    def test_init_custom_max_history(self):
        """Тест инициализации с кастомным max_history"""
        optimizer = PredictiveBatchOptimizer(max_history=500)
        assert optimizer.max_history == 500

    def test_predict_optimal_batch_size_empirical(self):
        """Тест предсказания batch size (эмпирическая формула)"""
        optimizer = PredictiveBatchOptimizer()

        batch_size = optimizer.predict_optimal_batch_size(
            text_length=1000, available_memory=1024.0
        )

        assert isinstance(batch_size, int)
        assert 8 <= batch_size <= 256

    def test_predict_optimal_batch_size_with_history(self):
        """Тест предсказания с историей"""
        optimizer = PredictiveBatchOptimizer()

        # Добавляем историю
        for i in range(10):
            optimizer.update_model(
                text_length=1000, batch_size=32, actual_time=0.5, memory_used=512.0
            )

        batch_size = optimizer.predict_optimal_batch_size(
            text_length=1000, available_memory=1024.0
        )

        assert isinstance(batch_size, int)
        assert 8 <= batch_size <= 256

    def test_update_model(self):
        """Тест обновления модели"""
        optimizer = PredictiveBatchOptimizer()

        optimizer.update_model(
            text_length=1000, batch_size=32, actual_time=0.5, memory_used=512.0
        )

        assert len(optimizer.history) == 1
        assert optimizer.history[0]["text_length"] == 1000
        assert optimizer.history[0]["batch_size"] == 32
        assert optimizer.history[0]["actual_time"] == 0.5
        assert optimizer.history[0]["memory_used"] == 512.0

    def test_update_model_multiple(self):
        """Тест множественных обновлений"""
        optimizer = PredictiveBatchOptimizer()

        for i in range(50):
            optimizer.update_model(
                text_length=1000 + i,
                batch_size=32 + i,
                actual_time=0.5,
                memory_used=512.0,
            )

        assert len(optimizer.history) == 50

    def test_update_model_max_history(self):
        """Тест ограничения max_history"""
        optimizer = PredictiveBatchOptimizer(max_history=10)

        for i in range(20):
            optimizer.update_model(
                text_length=1000, batch_size=32, actual_time=0.5, memory_used=512.0
            )

        # Должно быть максимум 10 записей
        assert len(optimizer.history) == 10

    def test_get_stats_empty(self):
        """Тест получения статистики для пустого optimizer"""
        optimizer = PredictiveBatchOptimizer()
        stats = optimizer.get_stats()

        assert stats["history_size"] == 0
        assert stats["model_trained"] is False

    def test_get_stats_with_history(self):
        """Тест получения статистики с историей"""
        optimizer = PredictiveBatchOptimizer()

        for i in range(10):
            optimizer.update_model(
                text_length=1000, batch_size=32, actual_time=0.5, memory_used=512.0
            )

        stats = optimizer.get_stats()

        assert stats["history_size"] == 10
        assert "avg_efficiency" in stats

    def test_retrain_model(self):
        """Тест переобучения модели (если scikit-learn доступен)"""
        optimizer = PredictiveBatchOptimizer()

        # Добавляем достаточно данных
        for i in range(100):
            optimizer.update_model(
                text_length=1000 + i * 10,
                batch_size=32 + i,
                actual_time=0.5,
                memory_used=512.0,
            )

        # Модель должна быть обучена (если scikit-learn доступен)
        # Проверяем, что метод не падает
        stats = optimizer.get_stats()
        assert "history_size" in stats

    def test_extract_features(self):
        """Тест извлечения признаков"""
        optimizer = PredictiveBatchOptimizer()

        features = optimizer._extract_features(
            text_length=1000, available_memory=1024.0
        )

        assert isinstance(features, list)
        assert len(features) >= 3
        assert features[0] == 1000
        assert features[1] == 1024.0

    def test_empirical_formula(self):
        """Тест эмпирической формулы"""
        optimizer = PredictiveBatchOptimizer()

        batch_size = optimizer._empirical_formula(
            text_length=1000, available_memory=1024.0
        )

        assert isinstance(batch_size, int)
        assert 8 <= batch_size <= 256

    def test_empirical_formula_small_memory(self):
        """Тест эмпирической формулы с маленькой памятью"""
        optimizer = PredictiveBatchOptimizer()

        batch_size = optimizer._empirical_formula(
            text_length=1000, available_memory=10.0  # Очень мало памяти
        )

        assert batch_size >= 8  # Минимум

    def test_empirical_formula_large_memory(self):
        """Тест эмпирической формулы с большой памятью"""
        optimizer = PredictiveBatchOptimizer()

        batch_size = optimizer._empirical_formula(
            text_length=1000, available_memory=100000.0  # Очень много памяти
        )

        assert batch_size <= 256  # Максимум
