# [NEXUS IDENTITY] ID: -2074763370872536037 | DATE: 2025-11-19

"""
Main FastAPI Application
With Agents Rule of Two Security Integration
"""

import asyncio
import os
import sys
import time
import uuid
from contextlib import asynccontextmanager

if os.getenv("IGNORE_PY_VERSION_CHECK") != "1" and sys.version_info[:2] != (
    3,
    11,
):  # pragma: no cover
    raise RuntimeError(
        f"Python 3.11.x is required to run 1C AI Stack (detected {sys.version.split()[0]}).")

import redis.asyncio as aioredis
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import APIRouter, FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles  # Import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator

from src.api.admin_audit import router as admin_audit_router
from src.api.admin_roles import router as admin_roles_router
# NEW: Council Router
from src.api.council_api import router as council_router
# Infrastructure Routers
from src.api.monitoring import router as monitoring_router
from src.api.orchestrator_api import router as orchestrator_router
# Database
from src.infrastructure.db.connection import close_pool, create_pool
from src.infrastructure.logging.structured_logging import (StructuredLogger,
                                                           set_request_context)
from src.infrastructure.monitoring.opentelemetry_setup import (
    instrument_asyncpg, instrument_fastapi_app, instrument_httpx,
    instrument_redis, setup_opentelemetry)
from src.infrastructure.repositories.marketplace import MarketplaceRepository
from src.middleware.jwt_user_context import JWTUserContextMiddleware
from src.middleware.metrics_middleware import MetricsMiddleware
# Middleware
from src.middleware.security_headers import SecurityHeadersMiddleware
from src.middleware.user_rate_limit import UserRateLimitMiddleware
from src.modules.admin_dashboard.api.routes import \
    router as admin_dashboard_router
# NEW: Analytics Router
from src.modules.analytics.api.routes import router as analytics_router
from src.modules.assistants.api.routes import router as assistants_router
from src.modules.auth.api.dependencies import get_auth_service
from src.modules.auth.api.oauth_routes import router as oauth_router
from src.modules.auth.api.routes import router as auth_router
from src.modules.ba_sessions.api.routes import router as ba_sessions_router
# Module Routers (Direct Imports)
from src.modules.bpmn_api.api.routes import router as bpmn_router
from src.modules.code_approval.api.routes import router as code_approval_router
from src.modules.code_review.api.routes import router as code_review_router
from src.modules.copilot.api.routes import router as copilot_router
from src.modules.dashboard.api.routes import router as dashboard_router
from src.modules.devops_api.api.routes import router as devops_router
# NEW: Previously Unused Modules - Now Integrated
from src.modules.gateway.api.routes import router as gateway_router
from src.modules.github_integration.api.routes import router as github_router
from src.modules.graph_api.api.routes import router as graph_router
from src.modules.knowledge_base.api.routes import \
    router as knowledge_base_router
# Marketplace & Analytics
from src.modules.marketplace.api.routes import router as marketplace_router
from src.modules.metrics.api.routes import router as metrics_router
from src.modules.risk.api.routes import router as risk_router
from src.modules.tenant_management.api.routes import router as tenant_router
from src.modules.test_generation.api.routes import \
    router as test_generation_router
from src.modules.websocket.api.routes import router as websocket_router
from src.modules.wiki.api.routes import router as wiki_router
from src.services.health_checker import get_health_checker
from src.utils.error_handling import register_error_handlers

# REMOVED: security_monitoring module doesn't exist
# from src.api.security_monitoring import router as security_monitoring_router


# Use structured logging
structured_logger = StructuredLogger(__name__)
logger = structured_logger.logger

# MCP Server (for Cursor/VSCode integration) - optional
try:

    # Try to import and add archi_api
try:

for name, router in routers:
    try:
