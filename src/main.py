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
from src.infrastructure.logging.structured_logging import (
    StructuredLogger,
    set_request_context,
)
from src.infrastructure.monitoring.opentelemetry_setup import (
    instrument_asyncpg,
    instrument_fastapi_app,
    instrument_httpx,
    instrument_redis,
    setup_opentelemetry,
)
from src.infrastructure.repositories.marketplace import MarketplaceRepository
from src.middleware.jwt_user_context import JWTUserContextMiddleware
from src.middleware.metrics_middleware import MetricsMiddleware

# Middleware
from src.middleware.security_headers import SecurityHeadersMiddleware
from src.middleware.user_rate_limit import UserRateLimitMiddleware
from src.modules.admin_dashboard.api.routes import router as admin_dashboard_router

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
from src.modules.knowledge_base.api.routes import router as knowledge_base_router
from src.modules.project_manager.api.routes import router as project_manager_router
from src.modules.scenario_hub.api.routes import router as scenario_hub_router
from src.modules.technical_writer.api.routes import router as technical_writer_router
from src.modules.security.api.routes import router as security_router

# Marketplace & Analytics
from src.modules.marketplace.api.routes import router as marketplace_router
from src.modules.metrics.api.routes import router as metrics_router
from src.modules.risk.api.routes import router as risk_router
from src.modules.tenant_management.api.routes import router as tenant_router
from src.modules.test_generation.api.routes import router as test_generation_router
from src.modules.websocket.api.routes import router as websocket_router
from src.modules.wiki.api.routes import router as wiki_router
from src.modules.ml.api.routes import router as ml_router
from src.services.health_checker import get_health_checker
from src.utils.error_handling import register_error_handlers

# REMOVED: security_monitoring module doesn't exist
# from src.api.security_monitoring import router as security_monitoring_router







# Use structured logging
structured_logger = StructuredLogger(__name__)
logger = structured_logger.logger

# MCP Server (for Cursor/VSCode integration) - optional
try:
    from src.ai.mcp.server import app as mcp_app

    MCP_AVAILABLE = True
except (ImportError, Exception) as e:
    logger.warning("MCP server not available: %s", e)
    mcp_app = None
    MCP_AVAILABLE = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle management with best practices

    Features:
    - OpenTelemetry setup
    - Database pool initialization
    - Redis connection
    - Graceful shutdown
    """
    pool = None
    redis_client = None
    marketplace_repo = None
    scheduler = None

    try:
        logger.info("Starting 1C AI Stack...")

        # Setup OpenTelemetry for distributed tracing
        otlp_endpoint = os.getenv("OTLP_ENDPOINT")
        if otlp_endpoint:
            try:
                setup_opentelemetry(
                    service_name="1c-ai-stack",
                    service_version="2.2.0",
                    otlp_endpoint=otlp_endpoint,
                    enable_console_exporter=os.getenv(
                        "OTEL_CONSOLE_EXPORTER", "false").lower() == "true",
                )
                instrument_fastapi_app(app)
                instrument_asyncpg()
                instrument_httpx()
                instrument_redis()
                logger.info("OpenTelemetry instrumentation enabled")
            except Exception as e:
                logger.warning("OpenTelemetry setup failed: %s", e)

        # Database pool with error handling - make it completely non-blocking
        pool = None
        try:
            logger.info("Attempting to create database pool (timeout: 5s)...")
            # Set very short timeout for DB connection attempts to prevent hanging
            pool = await asyncio.wait_for(create_pool(), timeout=5.0)
            if pool:
                logger.info("Database pool created successfully")
            else:
                logger.warning("Database pool creation returned None")
        except asyncio.TimeoutError:
            logger.warning(
                "Database connection timeout after 5s, continuing without DB")
            pool = None
        except Exception as e:
            logger.warning(
                "Database not available, continuing without DB",
                extra={"error": str(e), "error_type": type(e).__name__},
            )
            pool = None

        # Redis client with error handling - make it completely non-blocking
        redis_client = None
        try:
            # Try to connect with very short timeout
            redis_client = aioredis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                password=os.getenv("REDIS_PASSWORD"),
                db=int(os.getenv("REDIS_DB", "0")),
                decode_responses=True,
                socket_connect_timeout=2,  # Very short timeout
                socket_timeout=2,
            )
            # Try ping with timeout, but don't fail if it doesn't work
            try:
                await asyncio.wait_for(redis_client.ping(), timeout=2.0)
                app.state.redis = redis_client
                logger.info("Redis client connected")
            except Exception as ping_err:
                logger.warning(
                    f"Redis ping failed: {ping_err}, continuing without Redis")
                try:
                    await redis_client.close()
                except Exception:
                    pass
                redis_client = None
                app.state.redis = None
        except Exception as e:
            logger.warning(
                "Redis not available, continuing without cache",
                extra={"error": str(e), "error_type": type(e).__name__},
            )
            redis_client = None
            app.state.redis = None

        # Marketplace repository with error handling
        if pool:
            try:
                bucket = os.getenv("AWS_S3_BUCKET") or os.getenv(
                    "MINIO_DEFAULT_BUCKET", "")
                storage_config = {
                    "bucket": bucket,
                    "region": os.getenv("AWS_S3_REGION", ""),
                    "endpoint": os.getenv("AWS_S3_ENDPOINT") or os.getenv("MINIO_ENDPOINT"),
                    "access_key": os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("MINIO_ROOT_USER"),
                    "secret_key": os.getenv("AWS_SECRET_ACCESS_KEY") or os.getenv("MINIO_ROOT_PASSWORD"),
                    "create_bucket": os.getenv("AWS_S3_CREATE_BUCKET", "true").lower() not in {"0", "false", "no"},
                }

                marketplace_repo = MarketplaceRepository(
                    pool,
                    cache=redis_client,
                    storage_config=storage_config,
                )
                await marketplace_repo.init()
                app.state.marketplace_repo = marketplace_repo
                logger.info("Marketplace repository ready")
            except Exception as e:
                logger.error(
                    "Failed to initialize marketplace repository",
                    extra={"error": str(e), "error_type": type(e).__name__},
                    exc_info=True,
                )
                marketplace_repo = None
                app.state.marketplace_repo = None
        else:
            logger.warning("Marketplace repository skipped (no database pool)")
            app.state.marketplace_repo = None

        # Scheduler with error handling
        if marketplace_repo:
            try:
                cache_refresh_minutes = int(
                    os.getenv("MARKETPLACE_CACHE_REFRESH_MINUTES", "15"))
                scheduler = AsyncIOScheduler()
                scheduler.add_job(
                    marketplace_repo.refresh_cached_views,
                    "interval",
                    minutes=cache_refresh_minutes,
                )
                scheduler.start()
                app.state.scheduler = scheduler
                logger.info(
                    f"Marketplace cache refresh scheduler started (every {cache_refresh_minutes} min)")
            except Exception as e:
                logger.error(
                    "Failed to start scheduler",
                    extra={"error": str(e), "error_type": type(e).__name__},
                    exc_info=True,
                )
                scheduler = None
                app.state.scheduler = None

        # User rate limit middleware (only if Redis available)
        if redis_client:
            try:
                user_rate_limit = int(os.getenv("USER_RATE_LIMIT_PER_MINUTE", "60"))
                user_rate_window = int(
                    os.getenv("USER_RATE_LIMIT_WINDOW_SECONDS", "60"))
                try:
                    auth_service = get_auth_service()
                except Exception as auth_err:
                    logger.warning("Failed to get auth service: %s", auth_err)
                    auth_service = None

                if auth_service:
                    app.add_middleware(
                        UserRateLimitMiddleware,
                        redis_client=redis_client,
                        max_requests=user_rate_limit,
                        window_seconds=user_rate_window,
                        auth_service=auth_service,
                    )
                    logger.info("User rate limit middleware added")
                else:
                    logger.warning(
                        "Skipping user rate limit middleware (no auth service)")
            except Exception as e:
                logger.warning(
                    "Failed to add user rate limit middleware",
                    extra={"error": str(e), "error_type": type(e).__name__},
                )

        logger.info("Security layer initialized (Agents Rule of Two)")
        logger.info("Application startup completed successfully")

    except Exception as e:
        logger.error(
            "Critical error during startup",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        # Continue anyway - app can run in degraded mode
        logger.warning("Continuing startup in degraded mode...")

    try:
        yield
    finally:
        logger.info("Shutting down...")

        # Shutdown scheduler
        if scheduler:
            try:
                scheduler.shutdown(wait=False)
            except Exception as e:
                logger.warning("Error shutting down scheduler: %s", e)

        # Refresh marketplace cache
        if marketplace_repo:
            try:
                await marketplace_repo.refresh_cached_views()
            except Exception as e:
                logger.warning("Error refreshing marketplace cache: %s", e)

        # Close Redis
        if redis_client:
            try:
                await redis_client.close()
                # wait_closed() may not exist in all aioredis versions
                if hasattr(redis_client, "wait_closed"):
                    await redis_client.wait_closed()
            except Exception as e:
                logger.warning("Error closing Redis: %s", e)

        # Close database pool
        if pool:
            try:
                await close_pool()
            except Exception as e:
                logger.warning("Error closing database pool: %s", e)

        logger.info("Resources released")


# Application
app = FastAPI(
    title="1C AI Stack API",
    description="AI-Powered Development Platform для 1C - WITH SECURITY",
    version="2.2.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=[
        {"name": "Health", "description": "Health check endpoints"},
        {"name": "Monitoring", "description": "Monitoring and metrics"},
        {"name": "API", "description": "Core API endpoints"},
    ],
    swagger_ui_parameters={
        "displayRequestDuration": True,
        "filter": True,
        "tryItOutEnabled": True,
    },
)

api_v1_router = APIRouter(
    prefix="/api/v1",
    tags=["API v1"],
    # Changed to JSONResponse to handle list/dict returns correctly
    default_response_class=JSONResponse,
)

# Metrics instrumentation (Prometheus) - with error handling
try:
    Instrumentator().instrument(app).expose(app, include_in_schema=False)
except Exception as e:
    logger.warning("Failed to instrument Prometheus metrics: %s", e)

# Register error handlers (best practice: centralized error handling) - with error handling
try:
    register_error_handlers(app)
except Exception as e:
    logger.warning("Failed to register error handlers: %s", e)

# CORS (Best Practice: Use environment variables, not hardcoded origins)
cors_origins_env = os.getenv(
    "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
cors_origins = [origin.strip()
                             for origin in cors_origins_env.split(",") if origin.strip()]

# Security: In production, never use ["*"] for origins
if os.getenv("ENVIRONMENT") == "development" and "*" in cors_origins_env:
    logger.warning(
        "CORS allows all origins in development mode. Restrict in production!")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Security Headers (CRITICAL!)
app.add_middleware(SecurityHeadersMiddleware)

# Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Metrics
app.add_middleware(MetricsMiddleware)

# JWT User Context Middleware with error handling
try:
    auth_service = get_auth_service()
    app.add_middleware(JWTUserContextMiddleware, auth_service=auth_service)
except Exception as e:
    logger.warning("Failed to add JWT middleware: %s", e)


LEGACY_API_REDIRECT_ENABLED = os.getenv(
    "ENABLE_LEGACY_API_REDIRECT", "true").lower() in {"1", "true", "yes"}
LEGACY_API_PREFIX = "/api/"
VERSIONED_API_PREFIX = "/api/v1"

if LEGACY_API_REDIRECT_ENABLED:

    @app.middleware("http")
    async def legacy_api_redirect_middleware(request: Request, call_next):
        path = request.url.path or ""
        if path.startswith(LEGACY_API_PREFIX) and not path.startswith(VERSIONED_API_PREFIX):
            trimmed = path[len(LEGACY_API_PREFIX) :]
            new_path = f"{VERSIONED_API_PREFIX}/{trimmed}" if trimmed else VERSIONED_API_PREFIX
            new_url = request.url.replace(path=new_path)
            structured_logger.warning(
                "Legacy API path accessed",
                legacy_path=path,
                redirected_path=new_path,
            )
            response = RedirectResponse(
                url=str(new_url),
                status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            )
            response.headers["X-API-Version"] = "v1"
            return response
        return await call_next(request)


# Logging middleware with structured logging and context propagation
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """
    Enhanced logging middleware with best practices

    Features:
    - Correlation ID generation/propagation
    - Structured logging with contextvars
    - Request/response timing
    - Error tracking
    """
    # Get or generate request ID
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    start_time = time.time()

    # Set request context for structured logging
    set_request_context(request_id=request_id)

    # Add request ID to state
    request.state.request_id = request_id

    # Extract user info if available (from JWT middleware)
    user_id = getattr(request.state, "user_id", None)
    tenant_id = getattr(request.state, "tenant_id", None)
    if user_id:
        set_request_context(user_id=user_id, tenant_id=tenant_id)

    try:
        # Process request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        # Calculate processing time
        process_time = time.time() - start_time

        # Structured logging
        structured_logger.info(
            f"{request.method} {request.url.path}",
            request_id=request_id,
            user_id=user_id,
            tenant_id=tenant_id,
            method=request.method,
            path=str(request.url.path),
            status_code=response.status_code,
            process_time_ms=round(process_time * 1000, 2),
            client_ip=request.client.host if request.client else None,
        )

        return response

    except Exception as e:
        # Log errors with full context
        process_time = time.time() - start_time
        structured_logger.error(
            f"Request failed: {request.method} {request.url.path}",
            request_id=request_id,
            user_id=user_id,
            tenant_id=tenant_id,
            method=request.method,
            path=str(request.url.path),
            process_time_ms=round(process_time * 1000, 2),
            error=str(e),
            error_type=type(e).__name__,
        )
        raise


# Health check
@app.get("/health", tags=["Health"], summary="Health check endpoint")
async def health_check():
    """
    Health check endpoint

    Returns comprehensive health status of all system dependencies:
    - PostgreSQL
    - Redis
    - Neo4j
    - Qdrant
    - Elasticsearch
    - OpenAI API
    """
    health_checker = get_health_checker()
    health = await health_checker.check_all()
    return health


# Include routers with error handling
routers = [
    # Core Module Routers
    ("dashboard", dashboard_router),
    ("monitoring", monitoring_router),
    ("copilot", copilot_router),
    ("marketplace", marketplace_router),
    ("code_review", code_review_router),
    ("test_generation", test_generation_router),
    ("websocket", websocket_router),
    ("bpmn", bpmn_router),
    # Auth & Admin
    ("auth", auth_router),
    ("oauth", oauth_router),
    ("admin_roles", admin_roles_router),
    ("admin_audit", admin_audit_router),
    ("code_approval", code_approval_router),
    # Infrastructure
    ("orchestrator", orchestrator_router),
    ("wiki", wiki_router),
    ("devops", devops_router),
    ("analytics", analytics_router),
    ("council", council_router),
    # Previously Unused Modules - Now Active
    ("gateway", gateway_router),
    ("graph", graph_router),
    ("github", github_router),
    ("knowledge_base", knowledge_base_router),
    ("metrics", metrics_router),
    ("risk", risk_router),
    ("tenants", tenant_router),
    ("ba_sessions", ba_sessions_router),
    ("admin_dashboard", admin_dashboard_router),
    ("assistants", assistants_router),
    ("project_manager", project_manager_router),
    ("scenario_hub", scenario_hub_router),
    ("technical_writer", technical_writer_router),
    ("security", security_router),
    ("ml", ml_router),
]

# Try to import and add revolutionary router
try:
    from src.modules.revolutionary.api.routes import router as revolutionary_router
    routers.append(("revolutionary", revolutionary_router))
    logger.info("Revolutionary Components router loaded successfully")
except ImportError as e:
    logger.warning("Revolutionary Components not available: %s", e)
except Exception as e:
    logger.error("Failed to load Revolutionary Components: %s", e)

# Try to import and add archi_api
try:
    from src.api.archi_api import router as archi_router

    routers.append(("archi", archi_router))
    logger.info("Archi API router loaded successfully")
except ImportError as e:
    logger.warning("Archi API not available: %s", e)
except Exception as e:
    logger.error("Failed to load Archi API: %s", e)

for name, router in routers:
    try:
        api_v1_router.include_router(router)
    except Exception as e:
        logger.warning("Failed to register %s router in v1: {e}", name)

# CRITICAL: Mount api_v1_router to app (was missing!)
app.include_router(api_v1_router)
logger.info(f"Registered {len(routers)} routers under /api/v1")

# API v2 Router
try:
    from src.api.v2.router import router as api_v2_router_impl

    api_v2_router = APIRouter(
        prefix="/api/v2",
        tags=["API v2"],
        default_response_class=JSONResponse,
    )
    api_v2_router.include_router(api_v2_router_impl)
    app.include_router(api_v2_router)
    logger.info("API v2 router registered successfully")
except ImportError as e:
    logger.warning("API v2 not available: %s", e)
except Exception as e:
    logger.error("Failed to load API v2: %s", e)

# Mount MCP server (для Cursor/VSCode) - only if available
if MCP_AVAILABLE and mcp_app:
    try:
        app.mount("/mcp", mcp_app)
        logger.info("MCP server mounted at /mcp")
    except Exception as e:
        logger.warning("Failed to mount MCP server: %s", e)

# Mount Wiki Static UI (Only in Dev/Demo mode)
try:
    wiki_static_path = os.path.join(os.path.dirname(__file__), "static/wiki")
    if os.path.exists(wiki_static_path):
        app.mount(
            "/wiki-ui",
            StaticFiles(directory=wiki_static_path, html=True),
            name="wiki-ui",
        )
        logger.info("Wiki UI mounted at /wiki-ui (from %s)", wiki_static_path)
except Exception as e:
    logger.warning("Failed to mount Wiki UI: %s", e)


# Root
@app.get("/", tags=["API"], summary="API root endpoint")
async def root():
    """
    API root endpoint

    Returns basic information about the API including:
    - API name and version
    - Security status
    - Available integrations
    - Links to documentation
    """
    return {
        "name": "1C AI Stack API",
        "version": "2.2.0",
        "status": "running",
        "security": "Agents Rule of Two Enabled",
        "integrations": {
            "mcp": "/mcp (Cursor/VSCode)",
            "telegram": "Available via bot",
            "wiki": "/wiki-ui (Web Interface)",
            "archi": "/api/v1/archi (ArchiMate Export/Import)",
        },
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "openapi": "/openapi.json",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
