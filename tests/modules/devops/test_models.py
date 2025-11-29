"""
Tests for DevOps Domain Models

Unit tests for Pydantic models validation and edge cases.
"""

import pytest
from pydantic import ValidationError

from src.modules.devops.domain.models import (
    PipelineConfig,
    PipelineMetrics,
    PipelineOptimization,
    PipelineStage,
    OptimizationEffort,
    LogAnalysisResult,
    LogAnomaly,
    LogSeverity,
    CostOptimization,
    CostOptimizationResult,
    InfrastructureConfig,
    UsageMetrics,
)


class TestPipelineConfig:
    """Tests for PipelineConfig model"""

    def test_valid_pipeline_config(self):
        """Test creating valid pipeline config"""
        config = PipelineConfig(
            name="test-pipeline",
            platform="github_actions",
            config_yaml="name: CI\non: [push]",
            stages=["build", "test", "deploy"]
        )
        assert config.name == "test-pipeline"
        assert config.platform == "github_actions"
        assert len(config.stages) == 3

    def test_pipeline_config_defaults(self):
        """Test default values"""
        config = PipelineConfig(
            name="minimal",
            config_yaml="minimal: config"
        )
        assert config.platform == "github_actions"
        assert config.stages == []

    def test_pipeline_config_missing_required(self):
        """Test missing required fields"""
        with pytest.raises(ValidationError):
            PipelineConfig(name="test")  # Missing config_yaml


class TestPipelineMetrics:
    """Tests for PipelineMetrics model"""

    def test_valid_metrics(self):
        """Test creating valid metrics"""
        metrics = PipelineMetrics(
            total_duration=1500,
            build_time=300,
            test_time=900,
            deploy_time=300,
            success_rate=0.95
        )
        assert metrics.total_duration == 1500
        assert metrics.success_rate == 0.95

    def test_metrics_validation_positive(self):
        """Test that durations must be positive"""
        with pytest.raises(ValidationError):
            PipelineMetrics(total_duration=-100)

    def test_metrics_success_rate_bounds(self):
        """Test success_rate bounds (0-1)"""
        with pytest.raises(ValidationError):
            PipelineMetrics(total_duration=100, success_rate=1.5)

        with pytest.raises(ValidationError):
            PipelineMetrics(total_duration=100, success_rate=-0.1)

    def test_metrics_optional_fields(self):
        """Test optional fields"""
        metrics = PipelineMetrics(total_duration=1000)
        assert metrics.build_time is None
        assert metrics.test_time is None


class TestPipelineOptimization:
    """Tests for PipelineOptimization model"""

    def test_valid_optimization(self):
        """Test creating valid optimization"""
        opt = PipelineOptimization(
            optimization="Docker Layer Caching",
            stage=PipelineStage.BUILD,
            description="Use Docker layer caching",
            implementation="Add cache flags",
            expected_speedup_percent=45,
            effort=OptimizationEffort.LOW,
            priority=8
        )
        assert opt.optimization == "Docker Layer Caching"
        assert opt.stage == PipelineStage.BUILD
        assert opt.priority == 8

    def test_optimization_speedup_bounds(self):
        """Test speedup percentage bounds (0-100)"""
        with pytest.raises(ValidationError):
            PipelineOptimization(
                optimization="Test",
                stage=PipelineStage.ALL,
                description="Test",
                implementation="Test",
                expected_speedup_percent=150,  # > 100
                effort=OptimizationEffort.LOW,
                priority=5
            )

    def test_optimization_priority_bounds(self):
        """Test priority bounds (0-10)"""
        with pytest.raises(ValidationError):
            PipelineOptimization(
                optimization="Test",
                stage=PipelineStage.ALL,
                description="Test",
                implementation="Test",
                expected_speedup_percent=50,
                effort=OptimizationEffort.LOW,
                priority=15  # > 10
            )


class TestLogAnalysisResult:
    """Tests for LogAnalysisResult model"""

    def test_valid_log_analysis(self):
        """Test creating valid log analysis result"""
        result = LogAnalysisResult(
            summary={"errors_found": 10, "warnings_found": 5},
            errors_by_category={"memory": 5, "network": 5},
            anomalies=[],
            patterns=[],
            recommendations=["Check memory usage"]
        )
        assert result.summary["errors_found"] == 10
        assert len(result.recommendations) == 1

    def test_log_analysis_defaults(self):
        """Test default values"""
        result = LogAnalysisResult(
            summary={"test": "data"}
        )
        assert result.errors_by_category == {}
        assert result.anomalies == []
        assert result.patterns == []
        assert result.recommendations == []
        assert "timestamp" in result.model_dump()

    def test_log_anomaly(self):
        """Test LogAnomaly model"""
        anomaly = LogAnomaly(
            type="High error rate",
            timestamp="2025-11-27T10:00:00",
            severity=LogSeverity.ERROR,
            possible_cause="System degradation"
        )
        assert anomaly.type == "High error rate"
        assert anomaly.severity == LogSeverity.ERROR


class TestCostOptimization:
    """Tests for CostOptimization model"""

    def test_valid_cost_optimization(self):
        """Test creating valid cost optimization"""
        opt = CostOptimization(
            resource="Compute instances",
            current="m5.2xlarge",
            recommended="m5.xlarge",
            current_cost=1200.0,
            optimized_cost=600.0,
            savings_month=600.0,
            savings_percent=50,
            reason="Low CPU utilization",
            risk="low",
            effort=OptimizationEffort.LOW
        )
        assert opt.savings_month == 600.0
        assert opt.savings_percent == 50

    def test_cost_validation_positive(self):
        """Test that costs must be positive"""
        with pytest.raises(ValidationError):
            CostOptimization(
                resource="Test",
                current="test",
                recommended="test",
                current_cost=-100.0,  # Negative
                optimized_cost=50.0,
                savings_month=50.0,
                savings_percent=50,
                reason="Test",
                risk="low",
                effort=OptimizationEffort.LOW
            )


class TestCostOptimizationResult:
    """Tests for CostOptimizationResult model"""

    def test_valid_result(self):
        """Test creating valid cost optimization result"""
        result = CostOptimizationResult(
            current_cost_month=2500.0,
            optimized_cost_month=1600.0,
            total_savings_month=900.0,
            savings_percent=36,
            optimizations=[],
            annual_savings=10800.0
        )
        assert result.total_savings_month == 900.0
        assert result.annual_savings == 10800.0

    def test_result_with_optimizations(self):
        """Test result with optimization list"""
        opt = CostOptimization(
            resource="Test",
            current="test",
            recommended="test",
            current_cost=100.0,
            optimized_cost=50.0,
            savings_month=50.0,
            savings_percent=50,
            reason="Test",
            risk="low",
            effort=OptimizationEffort.LOW
        )
        result = CostOptimizationResult(
            current_cost_month=100.0,
            optimized_cost_month=50.0,
            total_savings_month=50.0,
            savings_percent=50,
            optimizations=[opt],
            annual_savings=600.0
        )
        assert len(result.optimizations) == 1


class TestInfrastructureConfig:
    """Tests for InfrastructureConfig model"""

    def test_valid_config(self):
        """Test creating valid infrastructure config"""
        config = InfrastructureConfig(
            provider="aws",
            instance_type="m5.2xlarge",
            instance_count=3,
            pricing_model="on_demand",
            region="eu-west-1"
        )
        assert config.provider == "aws"
        assert config.instance_count == 3

    def test_config_defaults(self):
        """Test default values"""
        config = InfrastructureConfig(
            provider="aws",
            instance_type="m5.large"
        )
        assert config.instance_count == 1
        assert config.pricing_model == "on_demand"
        assert config.region is None

    def test_instance_count_validation(self):
        """Test instance_count must be >= 1"""
        with pytest.raises(ValidationError):
            InfrastructureConfig(
                provider="aws",
                instance_type="m5.large",
                instance_count=0  # Must be >= 1
            )


class TestUsageMetrics:
    """Tests for UsageMetrics model"""

    def test_valid_metrics(self):
        """Test creating valid usage metrics"""
        metrics = UsageMetrics(
            cpu_avg=35.5,
            memory_avg=45.2,
            storage_iops=800,
            network_throughput=150.5
        )
        assert metrics.cpu_avg == 35.5
        assert metrics.memory_avg == 45.2

    def test_metrics_bounds(self):
        """Test CPU and memory bounds (0-100)"""
        with pytest.raises(ValidationError):
            UsageMetrics(
                cpu_avg=150.0,  # > 100
                memory_avg=50.0
            )

        with pytest.raises(ValidationError):
            UsageMetrics(
                cpu_avg=50.0,
                memory_avg=-10.0  # < 0
            )

    def test_metrics_optional_fields(self):
        """Test optional fields"""
        metrics = UsageMetrics(
            cpu_avg=50.0,
            memory_avg=60.0
        )
        assert metrics.storage_iops is None
        assert metrics.network_throughput is None
