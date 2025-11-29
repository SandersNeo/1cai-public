from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from src.modules.security.domain.models import ComplianceFramework

class ScanType(str, Enum):
    """Type of security scan."""
    VULNERABILITY = "vulnerability"
    SECRETS = "secrets"
    COMPLIANCE = "compliance"
    DEPENDENCY = "dependency"

class ScanRequest(BaseModel):
    """Request to perform a security scan."""
    scan_type: ScanType = Field(..., description="Type of scan to perform")
    target_path: str = Field(..., description="Path to scan (file or directory)")
    compliance_framework: Optional[ComplianceFramework] = Field(None, description="Framework for compliance scan")

class ScanResponse(BaseModel):
    """Response with scan results."""
    scan_id: str = Field(..., description="Unique scan ID")
    status: str = Field(..., description="Scan status")
    result: dict = Field(..., description="Scan result details")
