"""
Dashboard Domain Models
Pydantic models for all dashboard responses
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# ==================== COMMON MODELS ====================


class HealthScore(BaseModel):
    """System health score model"""

    status: str = Field(..., description="Health status: healthy, warning, critical")
    score: int = Field(..., ge=0, le=100, description="Health score 0-100")
    message: str = Field(..., description="Health status message")


class Metric(BaseModel):
    """Generic metric model"""

    value: float = Field(..., description="Metric value")
    previous_value: Optional[float] = Field(None, description="Previous period value")
    change: Optional[float] = Field(None, description="Percentage change")
    trend: Optional[str] = Field(None, description="Trend: up, down, stable")
    status: Optional[str] = Field(None, description="Status: good, warning, critical")
    format: str = Field(
        default="number", description="Format: number, currency, percentage"
    )


# ==================== EXECUTIVE DASHBOARD ====================


class Alert(BaseModel):
    """Alert model"""

    id: str
    type: str = Field(..., description="Alert type: info, warning, error")
    title: str
    message: str
    timestamp: str
    read: bool = Field(default=False)


class Objective(BaseModel):
    """Business objective model"""

    id: str
    title: str
    progress: int = Field(..., ge=0, le=100)
    status: str = Field(..., description="Status: on_track, behind, at_risk")
    target_date: str


class Initiative(BaseModel):
    """Top initiative model"""

    id: str
    name: str
    status: str
    users: int = Field(default=0)
    eta: Optional[str] = None


class UsageStats(BaseModel):
    """Usage statistics model"""

    api_calls: int
    ai_queries: int
    storage_gb: float
    uptime: float


class ExecutiveDashboard(BaseModel):
    """Executive dashboard response model"""

    health: HealthScore
    roi: Metric
    users: Metric
    growth: Metric
    revenue_trend: List[Dict[str, Any]]
    alerts: List[Alert]
    objectives: List[Objective]
    top_initiatives: List[Initiative]
    usage_stats: UsageStats


# ==================== PM DASHBOARD ====================


class ProjectsSummary(BaseModel):
    """Projects summary model"""

    active: int
    completed: int
    paused: int
    at_risk: int


class ProjectTimeline(BaseModel):
    """Project timeline item"""

    project_id: str
    project_name: str
    progress: int = Field(..., ge=0, le=100)
    status: str
    current_phase: str


class TeamMemberWorkload(BaseModel):
    """Team member workload"""

    member_id: str
    member_name: str
    workload: int = Field(..., ge=0, le=100)
    tasks_count: int
    status: str


class SprintProgress(BaseModel):
    """Sprint progress model"""

    sprint_number: int
    tasks_total: int
    tasks_done: int
    progress: int = Field(..., ge=0, le=100)
    blockers: int
    end_date: str


class Activity(BaseModel):
    """Activity model"""

    id: str
    type: str
    actor: str
    description: str
    timestamp: str
    project_id: str


class PMDashboard(BaseModel):
    """PM dashboard response model"""

    projects_summary: ProjectsSummary
    timeline: List[ProjectTimeline]
    team_workload: List[TeamMemberWorkload]
    sprint_progress: SprintProgress
    recent_activity: List[Activity]


# ==================== DEVELOPER DASHBOARD ====================


class Task(BaseModel):
    """Task model"""

    id: str
    title: str
    description: str
    status: str
    priority: str
    assignee: str
    due_date: str
    project_id: str


class CodeReview(BaseModel):
    """Code review model"""

    id: str
    pr_number: int
    title: str
    author: str
    status: str
    comments_count: int
    created_at: str


class BuildStatus(BaseModel):
    """Build status model"""

    status: str
    last_build_at: str
    duration_seconds: int
    tests_passed: int
    tests_total: int


class CodeQuality(BaseModel):
    """Code quality metrics"""

    coverage: int = Field(..., ge=0, le=100)
    complexity: int
    maintainability: int = Field(..., ge=0, le=100)
    security_score: int = Field(..., ge=0, le=100)
    issues: Dict[str, int]


class AISuggestion(BaseModel):
    """AI suggestion model"""

    id: str
    type: str
    title: str
    description: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class DeveloperDashboard(BaseModel):
    """Developer dashboard response model"""

    assigned_tasks: List[Task]
    code_reviews: List[CodeReview]
    build_status: BuildStatus
    code_quality: CodeQuality
    ai_suggestions: List[AISuggestion]


# ==================== TEAM LEAD DASHBOARD ====================


class TeamMetrics(BaseModel):
    """Team metrics model"""

    velocity: int = Field(..., ge=0, le=100)
    code_quality: int = Field(..., ge=0, le=100)
    bug_rate: float
    deployment_frequency: int


class TeamPerformance(BaseModel):
    """Team member performance"""

    name: str
    role: str
    workload: int = Field(..., ge=0, le=100)
    tasks_active: int
    tasks_completed_week: int
    status: str


class TrendData(BaseModel):
    """Trend data point"""

    week: str
    quality: Optional[int] = None
    completed: Optional[int] = None


class TechnicalDebt(BaseModel):
    """Technical debt metrics"""

    total_debt_hours: int
    critical_items: int
    blocked_tasks: int
    trend: str


class TeamLeadDashboard(BaseModel):
    """Team Lead dashboard response model"""

    team_metrics: TeamMetrics
    code_quality_trends: List[TrendData]
    velocity_chart: List[TrendData]
    technical_debt: TechnicalDebt
    team_performance: List[TeamPerformance]


# ==================== BA DASHBOARD ====================


class RequirementsSummary(BaseModel):
    """Requirements summary"""

    total: int
    approved: int
    pending: int
    rejected: int


class Requirement(BaseModel):
    """Requirement model"""

    id: str
    title: str
    status: str
    priority: str
    stakeholder: str
    created_at: str


class TraceabilityMatrix(BaseModel):
    """Traceability matrix item"""

    requirement_id: str
    requirement_title: str
    linked_tasks: int
    test_coverage: int = Field(..., ge=0, le=100)
    status: str


class GapAnalysis(BaseModel):
    """Gap analysis item"""

    area: str
    current_state: str
    desired_state: str
    gap_severity: str
    recommendations: List[str]


class ProcessDiagram(BaseModel):
    """Process diagram model"""

    id: str
    name: str
    type: str
    url: str
    last_updated: str


class BADashboard(BaseModel):
    """BA dashboard response model"""

    requirements_summary: RequirementsSummary
    recent_requirements: List[Requirement]
    traceability_matrix: List[TraceabilityMatrix]
    gap_analysis: List[GapAnalysis]
    process_diagrams: List[ProcessDiagram]


# ==================== OWNER DASHBOARD ====================


class BusinessMetric(BaseModel):
    """Business metric for owner"""

    label: str
    value: str
    trend: str
    explanation: str


class OwnerDashboard(BaseModel):
    """Owner dashboard response model (simple)"""

    business_health: str
    key_metrics: List[BusinessMetric]
    summary: str
    recommendations: List[str]
