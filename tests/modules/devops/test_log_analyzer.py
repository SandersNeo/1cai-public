"""
Tests for LogAnalyzer Service

Unit tests for log analysis with pattern matching and anomaly detection.
"""

import pytest
from pathlib import Path
import tempfile

from src.modules.devops.services.log_analyzer import LogAnalyzer


@pytest.fixture
def analyzer():
    """Fixture for LogAnalyzer instance"""
    return LogAnalyzer()


@pytest.fixture
def sample_logs():
    """Fixture for sample log content"""
    return """
2025-11-27 10:00:00 INFO Application started
2025-11-27 10:00:01 INFO Processing request
2025-11-27 10:00:02 ERROR OutOfMemoryError: Java heap space
2025-11-27 10:00:03 WARN Low memory warning
2025-11-27 10:00:04 ERROR Connection refused to database
2025-11-27 10:00:05 ERROR Connection timeout
2025-11-27 10:00:06 INFO Request completed
2025-11-27 10:00:07 ERROR Deadlock detected in transaction
2025-11-27 10:00:08 ERROR Permission denied for user
2025-11-27 10:00:09 ERROR NullPointerException in handler
"""


@pytest.fixture
def temp_log_file(sample_logs):
    """Fixture for temporary log file"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        f.write(sample_logs)
        temp_path = f.name
    yield temp_path
    # Cleanup
    Path(temp_path).unlink()


class TestLogAnalyzer:
    """Tests for LogAnalyzer service"""

    @pytest.mark.asyncio
    async def test_analyze_logs_from_file(self, analyzer, temp_log_file):
        """Test log analysis from file"""
        result = await analyzer.analyze_logs(temp_log_file, "application")

        assert result.summary["log_type"] == "application"
        assert result.summary["errors_found"] > 0
        assert result.summary["warnings_found"] > 0

    @pytest.mark.asyncio
    async def test_analyze_logs_from_string(self, analyzer, sample_logs):
        """Test log analysis from string content"""
        result = await analyzer.analyze_logs(sample_logs, "application")

        assert result.summary["errors_found"] == 6  # 6 ERROR lines
        assert result.summary["warnings_found"] == 1  # 1 WARN line

    @pytest.mark.asyncio
    async def test_error_categorization(self, analyzer, sample_logs):
        """Test that errors are correctly categorized"""
        result = await analyzer.analyze_logs(sample_logs, "application")

        # Should detect different categories
        assert "memory" in result.errors_by_category
        assert "network" in result.errors_by_category
        assert "database" in result.errors_by_category
        assert "security" in result.errors_by_category
        assert "code" in result.errors_by_category

    @pytest.mark.asyncio
    async def test_memory_error_detection(self, analyzer):
        """Test memory error pattern matching"""
        logs = "ERROR OutOfMemoryError: heap space exhausted"
        result = await analyzer.analyze_logs(logs, "application")

        assert result.errors_by_category.get("memory", 0) > 0

    @pytest.mark.asyncio
    async def test_network_error_detection(self, analyzer):
        """Test network error pattern matching"""
        logs = """
ERROR Connection refused to server
ERROR Connection timeout after 30s
"""
        result = await analyzer.analyze_logs(logs, "application")

        assert result.errors_by_category.get("network", 0) == 2

    @pytest.mark.asyncio
    async def test_database_error_detection(self, analyzer):
        """Test database error pattern matching"""
        logs = """
ERROR Deadlock detected
ERROR Lock wait timeout exceeded
"""
        result = await analyzer.analyze_logs(logs, "application")

        assert result.errors_by_category.get("database", 0) == 2

    @pytest.mark.asyncio
    async def test_anomaly_detection_high_error_rate(self, analyzer):
        """Test anomaly detection for high error rate"""
        # Create logs with high error rate (> 10%)
        error_logs = "\n".join([f"ERROR Error {i}" for i in range(15)])
        info_logs = "\n".join([f"INFO Info {i}" for i in range(85)])
        logs = error_logs + "\n" + info_logs

        result = await analyzer.analyze_logs(logs, "application")

        # Should detect high error rate anomaly
        # Note: anomaly detection checks error_rate > 10%
        assert len(result.anomalies) > 0
        assert result.anomalies[0].type == "High error rate"

    @pytest.mark.asyncio
    async def test_no_anomaly_low_error_rate(self, analyzer):
        """Test no anomaly for low error rate"""
        # Create logs with low error rate (< 10%)
        error_logs = "\n".join([f"ERROR Error {i}" for i in range(5)])
        info_logs = "\n".join([f"INFO Info {i}" for i in range(95)])
        logs = error_logs + "\n" + info_logs

        result = await analyzer.analyze_logs(logs, "application")

        # Should not detect anomaly
        assert len(result.anomalies) == 0

    @pytest.mark.asyncio
    async def test_pattern_detection(self, analyzer, sample_logs):
        """Test pattern detection in errors"""
        result = await analyzer.analyze_logs(sample_logs, "application")

        # Should detect patterns if enough errors in same category
        # (sample_logs has 6 errors total, distributed across categories)
        assert isinstance(result.patterns, list)

    @pytest.mark.asyncio
    async def test_recommendations_generation(self, analyzer):
        """Test recommendations based on error categories"""
        # Logs with many memory errors
        logs = "\n".join([f"ERROR OutOfMemoryError {i}" for i in range(10)])
        result = await analyzer.analyze_logs(logs, "application")

        # Should recommend investigating memory
        assert len(result.recommendations) > 0
        assert any("memory" in rec.lower() for rec in result.recommendations)

    @pytest.mark.asyncio
    async def test_recommendations_for_database_errors(self, analyzer):
        """Test recommendations for database errors"""
        logs = "\n".join([f"ERROR Deadlock detected {i}" for i in range(15)])
        result = await analyzer.analyze_logs(logs, "application")

        # Should recommend database review
        assert any("database" in rec.lower() for rec in result.recommendations)

    @pytest.mark.asyncio
    async def test_recommendations_for_network_errors(self, analyzer):
        """Test recommendations for network errors"""
        logs = "\n".join([f"ERROR Connection refused {i}" for i in range(10)])
        result = await analyzer.analyze_logs(logs, "application")

        # Should recommend network check
        assert any("network" in rec.lower() for rec in result.recommendations)

    @pytest.mark.asyncio
    async def test_clean_logs_no_errors(self, analyzer):
        """Test analysis of clean logs with no errors"""
        logs = """
INFO Application started
INFO Processing request 1
INFO Processing request 2
INFO Request completed
"""
        result = await analyzer.analyze_logs(logs, "application")

        assert result.summary["errors_found"] == 0
        assert result.summary["warnings_found"] == 0
        assert len(result.anomalies) == 0
        assert len(result.recommendations) == 0

    def test_error_patterns_loaded(self, analyzer):
        """Test that error patterns are loaded"""
        assert len(analyzer.error_patterns) > 0

        # Check pattern structure
        for pattern in analyzer.error_patterns:
            assert "pattern" in pattern
            assert "category" in pattern
            assert "severity" in pattern
            assert "diagnosis" in pattern

    @pytest.mark.asyncio
    async def test_timestamp_in_result(self, analyzer, sample_logs):
        """Test that result includes timestamp"""
        result = await analyzer.analyze_logs(sample_logs, "application")

        assert "timestamp" in result.model_dump()
        assert result.timestamp is not None
