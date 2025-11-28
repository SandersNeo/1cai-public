# Code Review Module

## Overview

The Code Review module provides real-time code analysis and automated fixing capabilities for multiple programming languages, with a focus on BSL (1C:Enterprise).

## Architecture

Refactored from `src/api/code_review.py` into Clean Architecture:

- **Domain**: Pydantic models (`models.py`) for requests, responses, and metrics.
- **Services**:
  - `CodeAnalyzer`: Core analysis logic, including BSL static analysis.
  - `CodeFixer`: "SMART Auto-Fix" logic for applying automated corrections.
- **API**: FastAPI routes (`routes.py`) exposing `/analyze` and `/auto-fix` endpoints.

## Features

- **Multi-language Support**: BSL, TypeScript, JavaScript, Python.
- **Static Analysis**: Detection of performance issues, security vulnerabilities, and best practice violations.
- **AI Integration**: Optional integration with OpenAI for advanced analysis.
- **Auto-Fix**: Automated correction of common issues (e.g., type checking, null safety).
- **Caching**: Results are cached to improve performance.

## Usage

The module is exposed via `src.modules.code_review.api.routes`.
Legacy imports from `src.api.code_review` are supported via a proxy file.
