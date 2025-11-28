# Gateway Module

## Overview

The Gateway module serves as the single entry point for the 1C AI Ecosystem. It handles request routing, authentication, logging, and service health monitoring.

## Architecture

Refactored from a monolithic `gateway.py` into Clean Architecture:

- **Domain**: Configuration (`config.py`) and Pydantic models (`models.py`).
- **Services**:
  - `ServiceHealthChecker`: Monitors health of downstream microservices.
  - `ProxyService`: Handles request proxying with validation and error handling.
  - `Middleware`: Authentication (`auth.py`) and Request Logging (`logging.py`).
- **API**: FastAPI routes (`routes.py`) exposing health and proxy endpoints.

## Features

- **Unified Entry Point**: Single API for all microservices.
- **Authentication**: API key validation via `AuthenticationMiddleware`.
- **Observability**: Structured logging via `RequestLoggingMiddleware`.
- **Resilience**: Timeouts, error handling, and health checks.
- **Security**: Input sanitization and validation.

## Usage

The module is exposed via `src.modules.gateway.api.routes`.
Legacy imports from `src.api.gateway` are supported via a proxy file.
