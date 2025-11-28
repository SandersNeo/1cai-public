# Risk Management Module

## Overview

Risk management for 1C AI ecosystem projects.

## Architecture

- **Domain Layer**: Pydantic models for risk assessment
- **Services Layer**: `RiskService` with in-memory database
- **API Layer**: FastAPI routes

## Features

- Project risk assessment with ML-based scoring
- Risk tracking and management
- Mitigation strategy generation
- Risk metrics and analytics

## Usage

```python
from src.modules.risk import router

app.include_router(router)
```
