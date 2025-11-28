"""AI Issue Classifier API Routes."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..domain import Issue, IssueType, SeverityFactors
from ..services import IssueClassifier, SeverityEstimator, SolutionRecommender


# Pydantic models
class IssueRequest(BaseModel):
    """Request model for issue."""
    issue_id: str
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=5000)
    source: Optional[str] = None
    stack_trace: Optional[str] = None
    error_code: Optional[str] = None
    affected_users: int = 0


class SeverityFactorsRequest(BaseModel):
    """Request model for severity factors."""
    affects_production: bool = False
    affects_multiple_users: bool = False
    data_loss_risk: bool = False
    security_risk: bool = False
    blocks_critical_function: bool = False
    has_workaround: bool = True
    affected_users_count: int = 0
    affected_systems_count: int = 1


# Initialize router
router = APIRouter(
    prefix="/api/v1/issue-classifier",
    tags=["issue-classifier"])

# Initialize services
classifier = IssueClassifier()
severity_estimator = SeverityEstimator()
solution_recommender = SolutionRecommender()


@router.post("/classify")
async def classify_issue(request: IssueRequest):
    """Classify issue by type."""
    try:


@router.post("/estimate-severity")
async def estimate_severity(
    issue: IssueRequest,
    factors: SeverityFactorsRequest
):
    """Estimate issue severity."""
    try:


@router.post("/recommend-solutions")
async def recommend_solutions(request: IssueRequest):
    """Recommend solutions for issue."""
    try:


@router.post("/analyze-complete")
async def analyze_complete(
    issue: IssueRequest,
    factors: SeverityFactorsRequest
):
    """Complete issue analysis: classify, estimate severity, and recommend solutions."""
    try:
