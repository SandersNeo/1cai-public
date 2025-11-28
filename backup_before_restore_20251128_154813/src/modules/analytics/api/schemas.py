from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

# --- Dashboard Schemas ---


class RevenueData(BaseModel):
    this_month: float
    last_month: float
    change_percent: float
    trend: str  # "up" or "down"


class CustomersData(BaseModel):
    total: int
    new_this_month: int


class MetricData(BaseModel):
    value: float
    change: float
    trend: str
    status: str


class OwnerDashboardResponse(BaseModel):
    revenue: RevenueData
    customers: CustomersData
    growth_percent: float
    system_status: str  # "healthy", "warning", "critical"
    recent_activities: List[Dict[str, Any]]


class ExecutiveDashboardResponse(BaseModel):
    id: str
    health: Dict[str, str]
    roi: MetricData
    users: MetricData
    growth: MetricData
    revenue_trend: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]
    objectives: List[Dict[str, Any]]
    metrics: Dict[str, Any]


class SprintProgress(BaseModel):
    sprint_number: int
    tasks_done: int
    tasks_total: int
    progress: float
    blockers: int
    end_date: str


class PMDashboardResponse(BaseModel):
    id: str
    projects: List[Dict[str, Any]]
    projects_summary: Dict[str, Any]
    timeline: List[Dict[str, Any]]
    team_workload: List[Dict[str, Any]]
    sprint_progress: SprintProgress


class DeveloperDashboardResponse(BaseModel):
    id: str
    name: str
    assigned_tasks: List[Dict[str, Any]]
    code_reviews: List[Dict[str, Any]]
    build_status: Dict[str, Any]
    code_quality: Dict[str, Any]
    ai_suggestions: Optional[List[Dict[str, Any]]] = None


# --- Analytics Report Schemas ---


class ReportRequest(BaseModel):
    title: str
    period_days: int = 7
    components: Optional[List[str]] = None


class ReportResponse(BaseModel):
    id: str
    title: str
    period_start: datetime
    period_end: datetime
    metrics: Dict[str, Any]
    insights: List[str]
    recommendations: List[str]
    timestamp: datetime
