# Assistants Module

## Overview

The Assistants module provides a REST API for interacting with various AI assistants, primarily the Architect Assistant. It supports chat, requirements analysis, architectural diagram generation, and risk assessment.

## Architecture

Refactored from `src/api/assistants.py` into Clean Architecture:

- **Domain**: Pydantic models (`models.py`) for requests (`ChatRequest`, `AnalyzeRequirementsRequest`, etc.).
- **Services**:
  - `ArchitectService`: Encapsulates logic for interacting with the `ArchitectAssistant`. Handles query processing, analysis, and diagram generation.
- **API**: FastAPI routes (`routes.py`) exposing endpoints.

## Features

- **Chat**: Interactive chat with AI assistants.
- **Requirements Analysis**: Analyzes business requirements for architectural implications.
- **Diagram Generation**: Generates Mermaid diagrams (flowcharts, sequence diagrams, etc.) based on architecture proposals.
- **Comprehensive Analysis**: Performs a full analysis including requirements, architecture, and risks.
- **Risk Assessment**: Identifies potential risks in architectural solutions.
- **Knowledge Management**: Allows adding documents to the assistant's knowledge base.

## Usage

The module is exposed via `src.modules.assistants.api.routes`.
Legacy imports from `src.api.assistants` are supported via a proxy file.
