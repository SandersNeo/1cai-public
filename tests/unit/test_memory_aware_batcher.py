# [NEXUS IDENTITY] ID: -812444423539681476 | DATE: 2025-11-19

"""
Unit тесты для MemoryAwareBatcher
"""

from src.services.advanced_optimizations import MemoryAwareBatcher


class TestMemoryAwareBatcher:
    """Тесты для MemoryAwareBatcher"""

    def test_init(self):
        """Тест инициализации"""
        batcher = MemoryAwareBatcher(max_memory_mb=1024)
        assert batcher.max_memory_mb == 1024
        assert len(batcher.current_batch) == 0
        assert batcher.current_memory == 0.0

    def test_add_text_single(self):
        """Тест добавления одного текста"""
        batcher = MemoryAwareBatcher(max_memory_mb=1024)
        text = "test text"

        batch = batcher.add_text(text)

        assert batch is None  # Батч ещё не готов
        assert len(batcher.current_batch) == 1
        assert batcher.current_batch[0] == text

    def test_add_text_multiple(self):
        """Тест добавления нескольких текстов"""
        batcher = MemoryAwareBatcher(max_memory_mb=1024)

        for i in range(10):
            batch = batcher.add_text(f"text {i}")
            assert batch is None  # Батч ещё не готов

        assert len(batcher.current_batch) == 10

    def test_add_text_overflow(self):
        """Тест переполнения памяти"""
        batcher = MemoryAwareBatcher(max_memory_mb=0.01)  # Очень мало памяти

        # Первый текст должен поместиться
        batch1 = batcher.add_text("text 1")
        assert batch1 is None

        # Второй текст должен вызвать возврат батча
        batch2 = batcher.add_text("text 2" * 10000)  # Большой текст

        assert batch2 is not None
        assert len(batch2) == 1
        assert batch2[0] == "text 1"
        assert len(batcher.current_batch) == 1

    def test_flush(self):
        """Тест завершения батча"""
        batcher = MemoryAwareBatcher(max_memory_mb=1024)
        batcher.add_text("text 1")
        batcher.add_text("text 2")

        batch = batcher.flush()

        assert batch is not None
        assert len(batch) == 2
        assert len(batcher.current_batch) == 0
        assert batcher.current_memory == 0.0

    def test_flush_empty(self):
        """Тест завершения пустого батча"""
        batcher = MemoryAwareBatcher(max_memory_mb=1024)

        batch = batcher.flush()

        assert batch is None

    def test_estimate_memory(self):
        """Тест оценки памяти"""
        batcher = MemoryAwareBatcher(max_memory_mb=1024)

        memory_small = batcher._estimate_memory("small text")
        memory_large = batcher._estimate_memory("large text" * 1000)

        assert memory_small > 0
        assert memory_large > memory_small

    def test_get_stats(self):
        """Тест получения статистики"""
        batcher = MemoryAwareBatcher(max_memory_mb=1024)
        batcher.add_text("text 1")
        batcher.add_text("text 2")

        stats = batcher.get_stats()

        assert stats["current_batch_size"] == 2
        assert stats["current_memory_mb"] > 0
        assert stats["max_memory_mb"] == 1024

    def test_get_stats_empty(self):
        """Тест получения статистики для пустого batcher"""
        batcher = MemoryAwareBatcher(max_memory_mb=1024)
        stats = batcher.get_stats()

        assert stats["current_batch_size"] == 0
        assert stats["current_memory_mb"] == 0.0

    def test_multiple_batches(self):
        """Тест формирования нескольких батчей"""
        batcher = MemoryAwareBatcher(max_memory_mb=0.01)  # Мало памяти

        batches = []
        for i in range(5):
            text = f"text {i}" * 1000  # Большие тексты
            batch = batcher.add_text(text)
            if batch:
                batches.append(batch)

        # Завершаем последний батч
        final_batch = batcher.flush()
        if final_batch:
            batches.append(final_batch)

        assert len(batches) > 0
        # Все батчи должны быть непустыми
        assert all(len(b) > 0 for b in batches)
