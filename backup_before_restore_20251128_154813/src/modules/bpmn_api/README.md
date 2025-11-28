# BPMN API Module

## Overview

Backend for BPMN diagram management.

## Architecture

- **Domain Layer**: Pydantic models for diagrams
- **Services Layer**: `BPMNService` with PostgreSQL storage
- **API Layer**: FastAPI CRUD endpoints

## Features

- BPMN diagram CRUD operations
- Project-based filtering
- XML content storage
- Tenant isolation

## Usage

```python
from src.modules.bpmn_api import router

app.include_router(router)
```
