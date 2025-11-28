# Metrics Module

## Overview

The Metrics module provides a system for collecting, storing, and analyzing metrics from various components of the 1C AI ecosystem. It supports collecting custom metrics, performance tracking, dashboard generation, and alerting.

## Architecture

Refactored from `src/api/metrics.py` into Clean Architecture:

- **Domain**: Pydantic models (`models.py`) for metrics (`MetricRecord`, `MetricCollectionRequest`).
- **Services**:
  - `MetricsService`: Singleton service that manages in-memory storage of metrics. Handles collection, retrieval, aggregation, and alerting logic.
- **API**: FastAPI routes (`routes.py`) exposing endpoints.

## Features

- **Collection**: Accepts metrics from any service via REST API.
- **Performance Tracking**: Automatically tracks latency and processing times.
- **Dashboard**: Provides aggregated overview of system health.
- **Alerting**: Detects anomalies like error spikes or high latency.
- **Management**: Supports clearing old metrics to manage memory usage.

## Usage

The module is exposed via `src.modules.metrics.api.routes`.
Legacy imports from `src.api.metrics` are supported via a proxy file.
