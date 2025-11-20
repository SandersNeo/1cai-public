# [NEXUS IDENTITY] ID: -8238533014010474398 | DATE: 2025-11-19

"""
Интеграционные тесты для EmbeddingService с продвинутыми компонентами
"""

import pytest
import os
import time
from unittest.mock import Mock, patch
from src.services.embedding_service import EmbeddingService


@pytest.fixture
def embedding_service_basic():
    """Базовый EmbeddingService без продвинутых компонентов"""
    os.environ.pop("EMBEDDING_SLO_TRACKING", None)
    os.environ.pop("EMBEDDING_ADAPTIVE_QUANTIZATION", None)
    os.environ.pop("EMBEDDING_SEMANTIC_CACHE_ANN", None)
    os.environ.pop("EMBEDDING_PREDICTIVE_BATCH", None)
    os.environ.pop("EMBEDDING_MEMORY_AWARE_BATCHING", None)

    with patch("src.services.embedding_service.SentenceTransformer"):
        service = EmbeddingService(hybrid_mode=False)
        service.model = Mock()
        service.model.encode = Mock(return_value=[[0.1] * 384])
        service.model.get_sentence_embedding_dimension = Mock(return_value=384)
        return service


@pytest.fixture
def embedding_service_advanced():
    """EmbeddingService со всеми продвинутыми компонентами"""
    os.environ["EMBEDDING_SLO_TRACKING"] = "true"
    os.environ["EMBEDDING_ADAPTIVE_QUANTIZATION"] = "true"
    os.environ["EMBEDDING_SEMANTIC_CACHE_ANN"] = "true"
    os.environ["EMBEDDING_SEMANTIC_CACHE_ANN_TYPE"] = "linear"
    os.environ["EMBEDDING_PREDICTIVE_BATCH"] = "true"
    os.environ["EMBEDDING_MEMORY_AWARE_BATCHING"] = "true"
    os.environ["EMBEDDING_SEMANTIC_CACHE"] = "true"

    with patch("src.services.embedding_service.SentenceTransformer"):
        service = EmbeddingService(hybrid_mode=False)
        service.model = Mock()
        service.model.encode = Mock(return_value=[[0.1] * 384])
        service.model.get_sentence_embedding_dimension = Mock(return_value=384)
        return service


class TestEmbeddingServiceAdvancedIntegration:
    """Интеграционные тесты для продвинутых компонентов"""

    def test_slo_tracking_integration(self, embedding_service_advanced):
        """Тест интеграции SLO Tracking"""
        service = embedding_service_advanced

        # Выполняем несколько запросов
        for i in range(10):
            service.encode(f"текст {i}")

        # Проверяем статистику SLO
        stats = service.get_advanced_stats()
        assert "slo_tracking" in stats
        assert "sli_status" in stats["slo_tracking"]
        assert "error_budgets" in stats["slo_tracking"]

    def test_adaptive_quantization_integration(self, embedding_service_advanced):
        """Тест интеграции Adaptive Quantization"""
        service = embedding_service_advanced

        # Включаем квантизацию
        service._quantization_enabled = True
        service._adaptive_quantization_enabled = True

        # Выполняем запросы
        embeddings = service.encode("текст для квантизации")

        # Проверяем статистику
        stats = service.get_advanced_stats()
        assert "adaptive_quantization" in stats
        if stats["adaptive_quantization"]:
            assert "calibrated" in stats["adaptive_quantization"]

    def test_semantic_cache_ann_integration(self, embedding_service_advanced):
        """Тест интеграции Semantic Cache ANN"""
        service = embedding_service_advanced

        # Первый запрос - должен обработаться
        embeddings1 = service.encode("функция получения данных")

        # Похожий запрос - должен найтись в кэше
        embeddings2 = service.encode("метод получения данных")

        # Проверяем статистику
        stats = service.get_advanced_stats()
        assert "semantic_cache_ann" in stats

    def test_predictive_batch_optimizer_integration(self, embedding_service_advanced):
        """Тест интеграции Predictive Batch Optimizer"""
        service = embedding_service_advanced

        # Выполняем несколько батчей для обучения модели
        for i in range(100):
            texts = [f"текст {j}" for j in range(10)]
            service.encode(texts, batch_size=32)

        # Проверяем статистику
        stats = service.get_advanced_stats()
        assert "predictive_batch" in stats
        if stats["predictive_batch"]:
            assert "history_size" in stats["predictive_batch"]

    def test_memory_aware_batching_integration(self, embedding_service_advanced):
        """Тест интеграции Memory-Aware Batching"""
        service = embedding_service_advanced

        # Большой список текстов
        texts = [f"очень длинный текст {i} " * 100 for i in range(50)]

        # Должен использовать memory-aware batching
        embeddings = service.encode(texts)

        # Проверяем статистику
        stats = service.get_advanced_stats()
        assert "memory_aware_batching" in stats

    def test_all_components_together(self, embedding_service_advanced):
        """Тест работы всех компонентов вместе"""
        service = embedding_service_advanced

        # Включаем все компоненты
        service._quantization_enabled = True
        service._semantic_cache_enabled = True

        # Выполняем запросы
        texts = [f"текст {i}" for i in range(20)]
        embeddings = service.encode(texts)

        # Проверяем, что все компоненты работают
        stats = service.get_advanced_stats()

        assert "slo_tracking" in stats
        assert "adaptive_quantization" in stats
        assert "semantic_cache_ann" in stats
        assert "predictive_batch" in stats
        assert "memory_aware_batching" in stats

    def test_error_handling_integration(self, embedding_service_advanced):
        """Тест обработки ошибок в интеграции"""
        service = embedding_service_advanced

        # Пытаемся обработать некорректные данные
        result1 = service.encode("")  # Пустой текст
        result2 = service.encode(None)  # None
        result3 = service.encode(123)  # Неправильный тип

        # Не должно падать
        assert result1 is not None or result1 == []
        assert result2 is not None or result2 == []
        assert result3 is not None or result3 == []

    def test_performance_metrics(self, embedding_service_advanced):
        """Тест метрик производительности"""
        service = embedding_service_advanced

        # Выполняем запросы
        start = time.time()
        for i in range(10):
            service.encode(f"текст {i}")
        duration = time.time() - start

        # Проверяем метрики
        device_stats = service.get_device_stats()
        assert "cache_hits" in device_stats or "cache_misses" in device_stats

        # Проверяем SLO метрики
        stats = service.get_advanced_stats()
        if stats.get("slo_tracking", {}).get("sli_status"):
            assert "latency_p95" in stats["slo_tracking"]["sli_status"]


class TestComponentInteraction:
    """Тесты взаимодействия компонентов"""

    def test_slo_with_quantization(self, embedding_service_advanced):
        """Тест SLO Tracking с квантизацией"""
        service = embedding_service_advanced
        service._quantization_enabled = True

        embeddings = service.encode("текст")

        stats = service.get_advanced_stats()
        assert "slo_tracking" in stats
        assert "adaptive_quantization" in stats

    def test_predictive_with_memory_aware(self, embedding_service_advanced):
        """Тест Predictive Batch с Memory-Aware Batching"""
        service = embedding_service_advanced

        texts = [f"текст {i}" for i in range(100)]
        embeddings = service.encode(texts)

        stats = service.get_advanced_stats()
        assert "predictive_batch" in stats
        assert "memory_aware_batching" in stats

    def test_semantic_cache_with_ann(self, embedding_service_advanced):
        """Тест Semantic Cache с ANN"""
        service = embedding_service_advanced

        # Первый запрос
        embeddings1 = service.encode("поиск данных")

        # Похожий запрос
        embeddings2 = service.encode("поиск информации")

        stats = service.get_advanced_stats()
        assert "semantic_cache_ann" in stats
