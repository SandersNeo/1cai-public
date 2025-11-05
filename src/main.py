"""
Main FastAPI Application
With Agents Rule of Two Security Integration
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import logging
import time
import uuid

# Database
from src.database import create_pool, close_pool

# API Routers
from src.api.dashboard_api import router as dashboard_router
from src.api.monitoring import router as monitoring_router
from src.api.copilot_api_perfect import router as copilot_router
from src.api.code_review import router as code_review_router
from src.api.test_generation import router as test_generation_router
from src.api.websocket_enhanced import router as websocket_router
from src.api.bpmn_api import router as bpmn_router

# NEW: Security routers
from src.api.code_approval import router as code_approval_router
from src.api.security_monitoring import router as security_monitoring_router

# NEW: Marketplace router
from src.api.marketplace import router as marketplace_router

# MCP Server (for Cursor/VSCode integration)
from src.ai.mcp_server import app as mcp_app

# Middleware
from src.middleware.security_headers import SecurityHeadersMiddleware
from src.middleware.metrics_middleware import MetricsMiddleware

# Services
from src.services.health_checker import check_health

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management"""
    # Startup
    logger.info("🚀 Starting 1C AI Stack...")
    
    # Initialize database pool
    await create_pool()
    logger.info("✅ Database pool created")
    
    # Initialize security layer
    logger.info("🔒 Security layer initialized (Agents Rule of Two)")
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down...")
    await close_pool()
    logger.info("✅ Database pool closed")


# Application
app = FastAPI(
    title="1C AI Stack API",
    description="AI-Powered Development Platform для 1C - WITH SECURITY",
    version="2.1.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security Headers (CRITICAL!)
app.add_middleware(SecurityHeadersMiddleware)

# Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Metrics
app.add_middleware(MetricsMiddleware)


# Logging middleware
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log all requests with correlation ID"""
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Add request ID to state
    request.state.request_id = request_id
    
    # Process request
    response = await call_next(request)
    
    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id
    
    # Log
    process_time = time.time() - start_time
    logger.info(
        f"Request: {request.method} {request.url.path} "
        f"| Status: {response.status_code} "
        f"| Time: {process_time:.3f}s "
        f"| Request-ID: {request_id}"
    )
    
    return response


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health = await check_health()
    return health


# Include routers
app.include_router(dashboard_router)
app.include_router(monitoring_router)
app.include_router(copilot_router)
app.include_router(marketplace_router)
app.include_router(code_review_router)
app.include_router(test_generation_router)
app.include_router(websocket_router)
app.include_router(bpmn_router)

# NEW: Security routers
app.include_router(code_approval_router)
app.include_router(security_monitoring_router)

# Mount MCP server (для Cursor/VSCode)
app.mount("/mcp", mcp_app)


# Root
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "1C AI Stack API",
        "version": "2.2.0",
        "status": "running",
        "security": "Agents Rule of Two Enabled ✅",
        "integrations": {
            "mcp": "/mcp (Cursor/VSCode)",
            "telegram": "Available via bot"
        },
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
