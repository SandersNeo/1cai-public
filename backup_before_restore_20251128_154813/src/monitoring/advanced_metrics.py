# [NEXUS IDENTITY] ID: -1915020291377000184 | DATE: 2025-11-19

"""
Advanced Metrics - Monitoring for all advanced components
=================================================================

Metrics system for:
- Event-Driven Architecture
- Self-Evolving AI
- Self-Healing Code
- Distributed Network
- Code DNA
- Predictive Generation

Integration with Prometheus, Grafana, and other monitoring systems
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from prometheus_client import Counter, Gauge, Histogram

logger = None  # Will be initialized on import


class MetricType(str, Enum):
    """Metric types"""

    COUNTER = "counter"
    HISTOGRAM = "histogram"
    GAUGE = "gauge"
    SUMMARY = "summary"


# Prometheus metrics for Event-Driven
event_published_total = Counter(
    "advanced_events_published_total",
    "Total events published",
    ["event_type", "source"],
)

event_processed_duration = Histogram(
    "advanced_events_processed_duration_seconds",
    "Time spent processing events",
    ["event_type"],
)

event_queue_size = Gauge("advanced_events_queue_size", "Current event queue size")

# Prometheus metrics for Self-Evolving AI
evolution_cycles_total = Counter(
    "advanced_evolution_cycles_total", "Total evolution cycles", ["status"]
)

improvements_generated_total = Counter(
    "advanced_improvements_generated_total", "Total improvements generated"
)

improvements_applied_total = Counter(
    "advanced_improvements_applied_total", "Total improvements applied"
)

evolution_fitness = Gauge("advanced_evolution_fitness", "Current evolution fitness")

# Prometheus metrics for Self-Healing Code
errors_detected_total = Counter(
    "advanced_errors_detected_total",
    "Total errors detected",
    ["error_type", "severity"],
)

fixes_generated_total = Counter(
    "advanced_fixes_generated_total", "Total fixes generated"
)

fixes_applied_total = Counter("advanced_fixes_applied_total", "Total fixes applied")

healing_success_rate = Gauge(
    "advanced_healing_success_rate", "Self-healing success rate"
)

# Prometheus metrics for Distributed Network
agents_total = Gauge("advanced_agents_total", "Total agents in network", ["role"])

tasks_submitted_total = Counter(
    "advanced_tasks_submitted_total", "Total tasks submitted"
)

tasks_completed_total = Counter(
    "advanced_tasks_completed_total", "Total tasks completed", ["status"]
)

consensus_reached_total = Counter(
    "advanced_consensus_reached_total", "Total consensus reached"
)

# Prometheus metrics for Code DNA
dna_evolutions_total = Counter("advanced_dna_evolutions_total", "Total DNA evolutions")

dna_mutations_total = Counter("advanced_dna_mutations_total", "Total DNA mutations")

dna_fitness = Gauge("advanced_dna_fitness", "Current DNA fitness")

# Prometheus metrics for Predictive Generation
predictions_generated_total = Counter(
    "advanced_predictions_generated_total",
    "Total predictions generated",
    ["category"],
)

code_generated_ahead_total = Counter(
    "advanced_code_generated_ahead_total", "Total code generated ahead of time"
)

prediction_accuracy = Gauge("advanced_prediction_accuracy", "Prediction accuracy")


@dataclass
class ComponentMetrics:
    """Component metrics"""

    component_name: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize metrics"""
        return {
            "component_name": self.component_name,
            "metrics": self.metrics,
            "timestamp": self.timestamp.isoformat(),
        }


class AdvancedMetricsCollector:
    """
    Metrics collector for all advanced components

    Collects metrics from:
    - Event-Driven Architecture
    - Self-Evolving AI
    - Self-Healing Code
    - Distributed Network
    - Code DNA
    - Predictive Generation
    """

    def __init__(self):
        self._components_metrics: Dict[str, ComponentMetrics] = {}
        self._start_time = datetime.utcnow()

    def collect_event_metrics(
        self, event_type: str, source: str, processing_time: float
    ) -> None:
        """Сбор метрик Event-Driven"""
        event_published_total.labels(event_type=event_type, source=source).inc()
        event_processed_duration.labels(event_type=event_type).observe(processing_time)

        if "event_driven" not in self._components_metrics:
            self._components_metrics["event_driven"] = ComponentMetrics("event_driven")

        self._components_metrics["event_driven"].metrics.update(
            {
                "events_published": event_published_total.labels(
                    event_type=event_type, source=source
                )._value.get(),
                "avg_processing_time": processing_time,
            }
        )

    def collect_evolution_metrics(
        self,
        status: str,
        improvements_generated: int,
        improvements_applied: int,
        fitness: float,
    ) -> None:
        """Сбор метрик Self-Evolving AI"""
        evolution_cycles_total.labels(status=status).inc()
        improvements_generated_total.inc(improvements_generated)
        improvements_applied_total.inc(improvements_applied)
        evolution_fitness.set(fitness)

        if "self_evolving" not in self._components_metrics:
            self._components_metrics["self_evolving"] = ComponentMetrics(
                "self_evolving"
            )

        self._components_metrics["self_evolving"].metrics.update(
            {
                "cycles_total": evolution_cycles_total.labels(
                    status=status
                )._value.get(),
                "improvements_generated": improvements_generated,
                "improvements_applied": improvements_applied,
                "fitness": fitness,
            }
        )

    def collect_healing_metrics(
        self,
        error_type: str,
        severity: str,
        fix_generated: bool,
        fix_applied: bool,
        success_rate: float,
    ) -> None:
        """Сбор метрик Self-Healing Code"""
        errors_detected_total.labels(error_type=error_type, severity=severity).inc()

        if fix_generated:
            fixes_generated_total.inc()
        if fix_applied:
            fixes_applied_total.inc()

        healing_success_rate.set(success_rate)

        if "self_healing" not in self._components_metrics:
            self._components_metrics["self_healing"] = ComponentMetrics("self_healing")

        self._components_metrics["self_healing"].metrics.update(
            {
                "errors_detected": errors_detected_total.labels(
                    error_type=error_type, severity=severity
                )._value.get(),
                "fixes_generated": (
                    fixes_generated_total._value.get() if fix_generated else 0
                ),
                "fixes_applied": fixes_applied_total._value.get() if fix_applied else 0,
                "success_rate": success_rate,
            }
        )

    def collect_network_metrics(
        self,
        agents_count: Dict[str, int],
        tasks_submitted: int,
        tasks_completed: int,
        consensus_reached: int,
    ) -> None:
        """Сбор метрик Distributed Network"""
        for role, count in agents_count.items():
            agents_total.labels(role=role).set(count)

        tasks_submitted_total.inc(tasks_submitted)
        tasks_completed_total.labels(status="completed").inc(tasks_completed)
        consensus_reached_total.inc(consensus_reached)

        if "distributed_network" not in self._components_metrics:
            self._components_metrics["distributed_network"] = ComponentMetrics(
                "distributed_network"
            )

        self._components_metrics["distributed_network"].metrics.update(
            {
                "agents_total": sum(agents_count.values()),
                "tasks_submitted": tasks_submitted,
                "tasks_completed": tasks_completed,
                "consensus_reached": consensus_reached,
            }
        )

    def collect_dna_metrics(
        self, evolutions: int, mutations: int, fitness: float
    ) -> None:
        """Сбор метрик Code DNA"""
        dna_evolutions_total.inc(evolutions)
        dna_mutations_total.inc(mutations)
        dna_fitness.set(fitness)

        if "code_dna" not in self._components_metrics:
            self._components_metrics["code_dna"] = ComponentMetrics("code_dna")

        self._components_metrics["code_dna"].metrics.update(
            {"evolutions": evolutions, "mutations": mutations, "fitness": fitness}
        )

    def collect_predictive_metrics(
        self,
        predictions_generated: int,
        code_generated: int,
        accuracy: float,
        category: str = "all",
    ) -> None:
        """Сбор метрик Predictive Generation"""
        predictions_generated_total.labels(category=category).inc(predictions_generated)
        code_generated_ahead_total.inc(code_generated)
        prediction_accuracy.set(accuracy)

        if "predictive" not in self._components_metrics:
            self._components_metrics["predictive"] = ComponentMetrics("predictive")

        self._components_metrics["predictive"].metrics.update(
            {
                "predictions_generated": predictions_generated,
                "code_generated": code_generated,
                "accuracy": accuracy,
            }
        )

    def get_all_metrics(self) -> Dict[str, ComponentMetrics]:
        """Получение всех метрик"""
        return self._components_metrics.copy()

    def get_component_metrics(self, component_name: str) -> Optional[ComponentMetrics]:
        """Получение метрик компонента"""
        return self._components_metrics.get(component_name)

    def get_summary(self) -> Dict[str, Any]:
        """Получение сводки метрик"""
        uptime = (datetime.utcnow() - self._start_time).total_seconds()

        return {
            "uptime_seconds": uptime,
            "components_count": len(self._components_metrics),
            "components": {
                name: metrics.to_dict()
                for name, metrics in self._components_metrics.items()
            },
        }
