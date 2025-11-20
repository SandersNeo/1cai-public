# [NEXUS IDENTITY] ID: 3606667303308695207 | DATE: 2025-11-19

"""
Unit тесты для SemanticCacheANN
"""

import pytest

from src.services.advanced_optimizations import SemanticCacheANN


class TestSemanticCacheANN:
    """Тесты для SemanticCacheANN"""

    def test_init_linear(self):
        """Тест инициализации с linear поиском"""
        ann = SemanticCacheANN(index_type="linear", dimension=5)
        assert ann.index_type == "linear"
        assert ann.dimension == 5
        assert ann.index is None

    def test_init_faiss(self):
        """Тест инициализации с FAISS (если доступен)"""
        try:
            ann = SemanticCacheANN(index_type="faiss", dimension=5)
            # Если FAISS доступен, индекс должен быть создан
            # Если нет - fallback на linear
            assert ann.index_type in ["faiss", "linear"]
        except Exception:
            pytest.skip("FAISS not available")

    def test_add(self):
        """Тест добавления embedding"""
        ann = SemanticCacheANN(index_type="linear", dimension=5)
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        text = "test text"

        ann.add(embedding, text)

        assert len(ann.embeddings) == 1
        assert len(ann.texts) == 1
        assert ann.texts[0] == text

    def test_add_multiple(self):
        """Тест добавления нескольких embeddings"""
        ann = SemanticCacheANN(index_type="linear", dimension=5)

        for i in range(5):
            embedding = [float(j) for j in range(5)]
            ann.add(embedding, f"text {i}")

        assert len(ann.embeddings) == 5
        assert len(ann.texts) == 5

    def test_add_dimension_mismatch(self):
        """Тест добавления embedding с неправильной размерностью"""
        ann = SemanticCacheANN(index_type="linear", dimension=5)
        embedding = [0.1, 0.2, 0.3]  # Неправильная размерность

        # Не должно вызывать ошибку, но должно логировать предупреждение
        ann.add(embedding, "text")
        assert len(ann.embeddings) == 0

    def test_search_exact_match(self):
        """Тест поиска точного совпадения"""
        ann = SemanticCacheANN(index_type="linear", dimension=5)
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        ann.add(embedding, "test text")

        result = ann.search(embedding, k=1, threshold=0.95)

        assert result is not None
        found_embedding, similarity, text = result
        assert similarity >= 0.95
        assert text == "test text"

    def test_search_similar(self):
        """Тест поиска похожего embedding"""
        ann = SemanticCacheANN(index_type="linear", dimension=5)
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        ann.add(embedding, "test text")

        # Похожий embedding
        query = [0.11, 0.21, 0.31, 0.41, 0.51]
        result = ann.search(query, k=1, threshold=0.95)

        assert result is not None
        found_embedding, similarity, text = result
        assert similarity >= 0.95

    def test_search_not_similar(self):
        """Тест поиска непохожего embedding"""
        ann = SemanticCacheANN(index_type="linear", dimension=5)
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        ann.add(embedding, "test text")

        # Совсем другой embedding
        query = [0.9, 0.8, 0.7, 0.6, 0.5]
        result = ann.search(query, k=1, threshold=0.95)

        # Не должно найти (similarity < threshold)
        assert result is None

    def test_search_empty(self):
        """Тест поиска в пустом индексе"""
        ann = SemanticCacheANN(index_type="linear", dimension=5)
        query = [0.1, 0.2, 0.3, 0.4, 0.5]

        result = ann.search(query, k=1, threshold=0.95)
        assert result is None

    def test_search_zero_vector(self):
        """Тест поиска с нулевым вектором"""
        ann = SemanticCacheANN(index_type="linear", dimension=5)
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        ann.add(embedding, "test text")

        query = [0.0, 0.0, 0.0, 0.0, 0.0]
        result = ann.search(query, k=1, threshold=0.95)

        # Нулевой вектор не должен находить совпадений
        assert result is None

    def test_clear(self):
        """Тест очистки индекса"""
        ann = SemanticCacheANN(index_type="linear", dimension=5)
        ann.add([0.1, 0.2, 0.3, 0.4, 0.5], "text")

        ann.clear()

        assert len(ann.embeddings) == 0
        assert len(ann.texts) == 0

    def test_search_multiple_results(self):
        """Тест поиска нескольких результатов"""
        ann = SemanticCacheANN(index_type="linear", dimension=5)

        # Добавляем несколько похожих embeddings
        for i in range(3):
            embedding = [0.1 + i * 0.01, 0.2, 0.3, 0.4, 0.5]
            ann.add(embedding, f"text {i}")

        query = [0.1, 0.2, 0.3, 0.4, 0.5]
        result = ann.search(query, k=3, threshold=0.9)

        # Должен найти хотя бы один
        assert result is not None
