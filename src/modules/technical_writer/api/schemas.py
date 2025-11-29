from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from src.modules.technical_writer.domain.models import DocumentationType, Audience

class GenerateDocRequest(BaseModel):
    """Request to generate documentation."""
    doc_type: DocumentationType = Field(..., description="Type of documentation to generate")
    source_code: Optional[str] = Field(None, description="Source code to document (for CODE type)")
    openapi_spec: Optional[Dict[str, Any]] = Field(None, description="OpenAPI spec (for API type)")
    feature_name: Optional[str] = Field(None, description="Feature name (for USER_GUIDE type)")
    target_audience: Optional[Audience] = Field(Audience.END_USER, description="Target audience (for USER_GUIDE type)")
    version: Optional[str] = Field(None, description="Version (for RELEASE_NOTES type)")
    release_date: Optional[str] = Field(None, description="Release date (for RELEASE_NOTES type)")
    features: Optional[list[str]] = Field(None, description="List of features (for RELEASE_NOTES type)")
    fixes: Optional[list[str]] = Field(None, description="List of fixes (for RELEASE_NOTES type)")

class GenerateDocResponse(BaseModel):
    """Response with generated documentation."""
    content: str = Field(..., description="Generated documentation content (Markdown)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
