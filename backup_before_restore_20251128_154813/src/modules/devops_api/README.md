# DevOps & AI Evolution Module

## Overview

DevOps Agent for infrastructure analysis and Self-Evolving AI for automatic system improvements.

## Architecture

- **Domain Layer**: Pydantic models
- **Services Layer**: `DevOpsService` and `AIEvolutionService`
- **API Layer**: FastAPI routes

## Features

- Docker infrastructure analysis
- Runtime container monitoring
- Self-evolving AI with performance metrics
- Automatic system improvements

## Usage

```python
from src.modules.devops_api import router

app.include_router(router)
```
