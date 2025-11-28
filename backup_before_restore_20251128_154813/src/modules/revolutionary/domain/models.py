"""
Revolutionary Components Domain Models

Pydantic models for revolutionary AI components following Clean Architecture.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ComponentStatus(str, Enum):
    """Status of revolutionary component"""

    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"


class EventBusMetrics(BaseModel):
    """Event Bus metrics"""

    messages_published: int = Field(default=0, description="Total messages published")
    messages_consumed: int = Field(default=0, description="Total messages consumed")
    avg_latency_ms: float = Field(
        default=0.0, description="Average latency in milliseconds"
    )
    throughput_per_sec: float = Field(default=0.0, description="Messages per second")


class SelfEvolvingMetrics(BaseModel):
    """Self-Evolving AI metrics"""

    evolution_cycles: int = Field(default=0, description="Number of evolution cycles")
    improvements_applied: int = Field(default=0, description="Improvements applied")
    performance_score: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Performance score (0-100)"
    )
    last_evolution: Optional[datetime] = Field(
        default=None, description="Last evolution timestamp"
    )


class SelfHealingMetrics(BaseModel):
    """Self-Healing Code metrics"""

    bugs_detected: int = Field(default=0, description="Bugs detected")
    bugs_fixed: int = Field(default=0, description="Bugs fixed")
    success_rate: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Healing success rate (0-100)"
    )
    avg_healing_time_ms: float = Field(
        default=0.0, description="Average healing time in milliseconds"
    )


class DistributedAgentMetrics(BaseModel):
    """Distributed Agent Network metrics"""

    active_agents: int = Field(default=0, description="Number of active agents")
    tasks_completed: int = Field(default=0, description="Tasks completed")
    avg_consensus_time_ms: float = Field(
        default=0.0, description="Average consensus time in milliseconds"
    )


class CodeDNAMetrics(BaseModel):
    """Code DNA System metrics"""

    generations: int = Field(default=0, description="Number of generations")
    fitness_score: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Fitness score (0-100)"
    )
    mutations_applied: int = Field(default=0, description="Mutations applied")


class PredictiveGenerationMetrics(BaseModel):
    """Predictive Code Generation metrics"""

    predictions_made: int = Field(default=0, description="Predictions made")
    accuracy: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Prediction accuracy (0-100)"
    )
    avg_lead_time_hours: float = Field(
        default=0.0, description="Average lead time in hours"
    )


class RevolutionaryComponentState(BaseModel):
    """State of a revolutionary component"""

    name: str = Field(..., description="Component name")
    status: ComponentStatus = Field(
        default=ComponentStatus.INITIALIZING, description="Component status"
    )
    enabled: bool = Field(default=False, description="Whether component is enabled")
    metrics: Dict[str, Any] = Field(
        default_factory=dict, description="Component metrics"
    )
    last_update: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message if status is ERROR"
    )


class RevolutionaryOrchestratorState(BaseModel):
    """Overall state of revolutionary orchestrator"""

    components: List[RevolutionaryComponentState] = Field(
        default_factory=list, description="Component states"
    )
    total_enabled: int = Field(default=0, description="Number of enabled components")
    overall_health: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Overall health score (0-100)"
    )
    started_at: datetime = Field(
        default_factory=datetime.utcnow, description="Orchestrator start time"
    )
