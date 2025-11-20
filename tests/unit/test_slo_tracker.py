# [NEXUS IDENTITY] ID: -4098716116121159475 | DATE: 2025-11-19

"""
Unit тесты для SLOTracker
"""

import time
from src.services.advanced_optimizations import SLOTracker


class TestSLOTracker:
    """Тесты для SLOTracker"""

    def test_init(self):
        """Тест инициализации"""
        tracker = SLOTracker()
        assert tracker.slos is not None
        assert "latency_p95" in tracker.slos
        assert "error_rate" in tracker.slos
        assert "availability" in tracker.slos
        assert "cache_hit_rate" in tracker.slos

    def test_record_metric(self):
        """Тест записи метрики"""
        tracker = SLOTracker()
        tracker.record_metric("latency_p95", 0.1)
        assert len(tracker.sli_history["latency_p95"]) == 1
        assert tracker.sli_history["latency_p95"][0]["value"] == 0.1

    def test_record_multiple_metrics(self):
        """Тест записи нескольких метрик"""
        tracker = SLOTracker()
        for i in range(10):
            tracker.record_metric("latency_p95", 0.1 + i * 0.01)

        assert len(tracker.sli_history["latency_p95"]) == 10

    def test_calculate_sli_latency(self):
        """Тест вычисления SLI для latency"""
        tracker = SLOTracker()
        # Добавляем значения
        values = [0.05, 0.08, 0.1, 0.12, 0.15]
        for v in values:
            tracker.record_metric("latency_p95", v)

        sli = tracker._calculate_sli("latency_p95")
        assert sli > 0
        # P95 должен быть около 0.15
        assert sli >= 0.12

    def test_calculate_sli_availability(self):
        """Тест вычисления SLI для availability"""
        tracker = SLOTracker()
        # Добавляем успешные запросы
        for _ in range(9):
            tracker.record_metric("availability", 1.0)
        # Один неуспешный
        tracker.record_metric("availability", 0.0)

        sli = tracker._calculate_sli("availability")
        assert sli == 0.9  # 9 из 10 успешных

    def test_calculate_sli_error_rate(self):
        """Тест вычисления SLI для error_rate"""
        tracker = SLOTracker()
        # Добавляем ошибки
        for _ in range(2):
            tracker.record_metric("error_rate", 1.0)  # Ошибка
        for _ in range(8):
            tracker.record_metric("error_rate", 0.0)  # Успех

        sli = tracker._calculate_sli("error_rate")
        assert sli == 0.2  # 2 ошибки из 10

    def test_check_slo_violation(self):
        """Тест проверки нарушений SLO"""
        tracker = SLOTracker()
        # Добавляем значения, превышающие target
        for _ in range(10):
            tracker.record_metric("latency_p95", 0.2)  # Target: 0.1

        violations = tracker.check_slo_violation()
        assert (
            violations["latency_p95"] == True
        )  # Используем == вместо is для numpy bool

    def test_check_slo_no_violation(self):
        """Тест отсутствия нарушений SLO"""
        tracker = SLOTracker()
        # Добавляем значения в пределах target
        for _ in range(10):
            tracker.record_metric("latency_p95", 0.05)  # Target: 0.1

        violations = tracker.check_slo_violation()
        assert (
            violations["latency_p95"] == False
        )  # Используем == вместо is для numpy bool

    def test_get_error_budgets(self):
        """Тест получения error budgets"""
        tracker = SLOTracker()
        tracker.record_metric("latency_p95", 0.1)

        budgets = tracker.get_error_budgets()
        assert "latency_p95" in budgets
        assert isinstance(budgets["latency_p95"], float)

    def test_get_sli_status(self):
        """Тест получения статуса SLI"""
        tracker = SLOTracker()
        tracker.record_metric("latency_p95", 0.1)

        status = tracker.get_sli_status()
        assert "latency_p95" in status
        assert "sli" in status["latency_p95"]
        assert "target" in status["latency_p95"]
        assert "error_budget" in status["latency_p95"]
        assert "violation" in status["latency_p95"]

    def test_window_cleanup(self):
        """Тест очистки старых записей"""
        tracker = SLOTracker()
        # Добавляем старую запись
        old_time = time.time() - 4000  # 4000 секунд назад
        tracker.record_metric("latency_p95", 0.1, timestamp=old_time)

        # Добавляем новую запись
        tracker.record_metric("latency_p95", 0.1)

        # Старая запись должна быть удалена (window = 3600)
        assert len(tracker.sli_history["latency_p95"]) == 1

    def test_unknown_slo_name(self):
        """Тест обработки неизвестного SLO"""
        tracker = SLOTracker()
        # Не должно вызывать ошибку
        tracker.record_metric("unknown_slo", 0.1)
        assert "unknown_slo" not in tracker.sli_history
