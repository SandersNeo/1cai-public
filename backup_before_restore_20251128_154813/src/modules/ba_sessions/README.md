# BA Sessions Module

## Overview

The BA Sessions module provides functionality for Business Analyst workflows, including collaborative sessions, traceability, analytics, modeling, integrations, and documentation generation.

## Architecture

Refactored from `src/api/ba_sessions.py` into Clean Architecture:

- **Domain**: Pydantic models (`models.py`) for all requests.
- **Services**:
  - `SessionService`: Manages WebSocket connections and session state.
  - `TraceabilityService`: Handles traceability matrix, risk register, and reports.
  - `AnalyticsService`: Generates KPIs for initiatives.
  - `ModelingService`: Generates and validates BPMN models and Journey Maps.
  - `IntegrationService`: Syncs data to Jira and Confluence.
  - `DocumentationService`: Generates enablement plans, guides, and presentations.
- **API**: FastAPI routes (`routes.py`) exposing endpoints for all services.

## Features

- **Collaborative Sessions**: Real-time WebSocket communication.
- **Traceability**: Link requirements to code, tests, and incidents.
- **Analytics**: Automated KPI generation based on graph data.
- **Modeling**: AI-driven generation of process models and journey maps.
- **Integrations**: Seamless sync with Jira and Confluence.
- **Enablement**: Auto-generation of training materials and documentation.

## Usage

The module is exposed via `src.modules.ba_sessions.api.routes`.
Legacy imports from `src.api.ba_sessions` are supported via a proxy file.
