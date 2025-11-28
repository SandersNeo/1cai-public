# Test Generation Module

## Overview

The Test Generation module provides automated test generation capabilities for multiple programming languages, including BSL (1C:Enterprise), Python, JavaScript, and TypeScript.

## Architecture

Refactored from `src/api/test_generation.py` into Clean Architecture:

- **Domain**: Pydantic models (`models.py`) for requests, responses, and test cases.
- **Services**:
  - `TestGeneratorService`: Main orchestrator.
  - `generators/`: Language-specific generators:
    - `BSLTestGenerator`: BSL (1C) tests using `xUnitFor1C`.
    - `PythonTestGenerator`: Python tests using `pytest`.
    - `JSTestGenerator`: JavaScript/TypeScript tests using `Jest`.
- **API**: FastAPI routes (`routes.py`) exposing `/generate` endpoint.

## Features

- **Multi-language Support**: BSL, Python, JavaScript, TypeScript.
- **AI Integration**: Uses OpenAI (if enabled) to generate context-aware test cases.
- **Fallback Logic**: Generates basic template tests if AI is unavailable.
- **Edge Cases**: Option to include edge case tests (null inputs, invalid types).
- **Coverage Estimation**: Basic estimation of code coverage.

## Usage

The module is exposed via `src.modules.test_generation.api.routes`.
Legacy imports from `src.api.test_generation` are supported via a proxy file.
