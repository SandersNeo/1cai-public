"""
Archi API - FastAPI endpoints for ArchiMate export/import

Provides REST API for Archi integration with proper dependency injection.
"""

import asyncio
import os
import re
import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from prometheus_client import Counter, Histogram
from pydantic import BaseModel, Field, validator

from src.api.dependencies import (get_archi_exporter, get_archi_importer,
                                  get_graph_service)
from src.exporters.archi_exporter import ArchiExporter
from src.exporters.archi_importer import ArchiImporter
from src.modules.graph_api.services.graph_service import GraphService
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

router = APIRouter(prefix="/api/v1/archi", tags=["archi"])

# Prometheus metrics
archi_exports_total = Counter(
    "archi_exports_total",
    "Total Archi exports",
    ["status"])
archi_imports_total = Counter(
    "archi_imports_total",
    "Total Archi imports",
    ["status"])
archi_export_duration = Histogram(
    "archi_export_duration_seconds",
    "Archi export duration")
archi_import_duration = Histogram(
    "archi_import_duration_seconds",
    "Archi import duration")


class ExportRequest(BaseModel):
    """Request for ArchiMate export"""

    output_filename: str = Field(
        default="architecture.archimate",
        min_length=1,
        max_length=255,
        description="Output filename (safe characters only)",
    )
    filters: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional filters for export")
    max_nodes: int = Field(
        default=1000,
        ge=1,
        le=10000,
        description="Maximum nodes to export")
    max_relationships: int = Field(
        default=2000,
        ge=1,
        le=20000,
        description="Maximum relationships to export")

    @validator("output_filename")
    def validate_filename(cls, v):
        """Validate filename for security"""
        if ".." in v or "/" in v or "\\" in v:
            raise ValueError(
                "Filename cannot contain path separators or parent directory references")

        if not re.match(r"^[a-zA-Z0-9_\-\.]+$", v):
            raise ValueError(
                "Filename can only contain alphanumeric characters, underscores, hyphens, and dots")

        if not v.endswith(".archimate"):
            v = v + ".archimate"

        return v


class ImportRequest(BaseModel):
    """Request for ArchiMate import"""

    file_path: str


class ExportResponse(BaseModel):
    """Response for export operation"""

    status: str
    file_path: str
    elements_count: int
    relationships_count: int


class ImportResponse(BaseModel):
    """Response for import operation"""

    status: str
    nodes_created: int
    relationships_created: int


@router.post("/export", response_model=ExportResponse)
async def export_to_archimate(
    request: ExportRequest,
    http_request: Request,
    exporter: ArchiExporter = Depends(
        get_archi_exporter)  # ✅ DEPENDENCY INJECTION
):
    """
    Export Unified Change Graph to ArchiMate format

    **Rate Limit:** 5 requests per minute per IP

    **Example:**
    ```json
    {
      "output_filename": "1c_architecture.archimate",
      "filters": {
        "node_types": ["Module", "Document"]
      },
      "max_nodes": 1000,
      "max_relationships": 2000
    }
    ```
    """
    start_time = time.time()
    try:
