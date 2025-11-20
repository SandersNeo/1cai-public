# [NEXUS IDENTITY] ID: 8770812172298470509 | DATE: 2025-11-19

"""
Unit тесты для WeightedGPUScheduler
"""

from src.services.advanced_optimizations import WeightedGPUScheduler


class TestWeightedGPUScheduler:
    """Тесты для WeightedGPUScheduler"""

    def test_init(self):
        """Тест инициализации"""
        scheduler = WeightedGPUScheduler([0, 1])
        assert scheduler.gpu_devices == [0, 1]
        assert len(scheduler.gpu_weights) == 2
        assert len(scheduler.gpu_load) == 2
        assert scheduler.gpu_weights[0] == 1.0
        assert scheduler.gpu_weights[1] == 1.0

    def test_init_single_gpu(self):
        """Тест инициализации с одним GPU"""
        scheduler = WeightedGPUScheduler([0])
        assert scheduler.gpu_devices == [0]
        assert scheduler.gpu_weights[0] == 1.0

    def test_select_gpu_single(self):
        """Тест выбора GPU (один GPU)"""
        scheduler = WeightedGPUScheduler([0])

        gpu_id = scheduler.select_gpu()

        assert gpu_id == 0
        assert scheduler.gpu_request_count[0] == 1

    def test_select_gpu_multiple(self):
        """Тест выбора GPU (несколько GPU)"""
        scheduler = WeightedGPUScheduler([0, 1])

        gpu_id = scheduler.select_gpu()

        assert gpu_id in [0, 1]
        assert scheduler.gpu_request_count[gpu_id] == 1

    def test_select_gpu_weighted(self):
        """Тест взвешенного выбора GPU"""
        scheduler = WeightedGPUScheduler([0, 1])
        # Устанавливаем разные веса
        scheduler.gpu_weights[0] = 2.0
        scheduler.gpu_weights[1] = 1.0

        # GPU 0 должен выбираться чаще
        selections = [scheduler.select_gpu() for _ in range(10)]
        assert 0 in selections

    def test_update_performance(self):
        """Тест обновления производительности"""
        scheduler = WeightedGPUScheduler([0])

        scheduler.update_performance(gpu_id=0, actual_time=0.5, items_processed=10)

        assert scheduler.gpu_load[0] > 0
        assert scheduler.gpu_performance[0] > 0

    def test_update_performance_multiple(self):
        """Тест множественных обновлений производительности"""
        scheduler = WeightedGPUScheduler([0])

        for i in range(10):
            scheduler.update_performance(gpu_id=0, actual_time=0.5, items_processed=10)

        assert scheduler.gpu_load[0] > 0
        assert scheduler.gpu_performance[0] > 0

    def test_update_performance_unknown_gpu(self):
        """Тест обновления производительности для неизвестного GPU"""
        scheduler = WeightedGPUScheduler([0])

        # Не должно вызывать ошибку
        scheduler.update_performance(gpu_id=999, actual_time=0.5, items_processed=10)

    def test_get_stats(self):
        """Тест получения статистики"""
        scheduler = WeightedGPUScheduler([0, 1])
        scheduler.select_gpu()
        scheduler.update_performance(0, 0.5, 10)

        stats = scheduler.get_stats()

        assert "gpu_weights" in stats
        assert "gpu_load" in stats
        assert "gpu_performance" in stats
        assert "gpu_request_count" in stats
        assert len(stats["gpu_weights"]) == 2

    def test_get_stats_empty(self):
        """Тест получения статистики для пустого scheduler"""
        scheduler = WeightedGPUScheduler([0])
        stats = scheduler.get_stats()

        assert stats["gpu_weights"][0] == 1.0
        assert stats["gpu_load"][0] == 0.0

    def test_load_balancing(self):
        """Тест балансировки нагрузки"""
        scheduler = WeightedGPUScheduler([0, 1])

        # GPU 0 быстрее
        scheduler.update_performance(0, 0.1, 10)
        scheduler.update_performance(1, 0.5, 10)

        # GPU 0 должен выбираться чаще
        selections = [scheduler.select_gpu() for _ in range(20)]
        gpu_0_count = selections.count(0)
        gpu_1_count = selections.count(1)

        # GPU 0 должен выбираться чаще (но не всегда)
        assert gpu_0_count >= gpu_1_count
