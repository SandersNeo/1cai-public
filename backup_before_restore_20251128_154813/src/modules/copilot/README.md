# Copilot Module

## Overview

1C:Copilot API for VSCode extension - code completion, generation, and optimization.

## Status

✅ **Fully Refactored**: Complete Clean Architecture implementation.

## Architecture

- **Domain Layer**: `domain/models.py` - Pydantic request/response models
- **Services Layer**: `services/copilot_service.py` - CopilotService with all business logic
- **API Layer**: `api/routes.py` - FastAPI routes with rate limiting

## Features

- Code completion with context awareness
- Code generation from natural language (functions, procedures, tests)
- Code optimization and best practices detection
- BSL-specific heuristics
- Rate limiting (60/min completions, 10/min generations)
- Timeout handling
- Input validation

## Usage

```python
from src.modules.copilot import router
app.include_router(router)
```
