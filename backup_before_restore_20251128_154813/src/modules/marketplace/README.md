# Marketplace Module

## Overview

The Marketplace module manages the ecosystem of plugins for the 1cAI platform. It handles plugin submission, moderation, search, installation, and reviews.

## Architecture

This module follows Clean Architecture principles:

- **Domain Layer** (`domain/`): Defines core entities and Pydantic models (`PluginResponse`, `PluginSubmitRequest`, etc.).
- **Services Layer** (`services/`): Encapsulates business logic (`MarketplaceService`).
- **API Layer** (`api/`): FastAPI routes and dependency injection.

## Key Features

- **Plugin Management**: Submit, update, delete plugins.
- **Search & Discovery**: Full-text search, filtering by category/author, sorting.
- **Moderation**: Approval workflow for new plugins.
- **Reviews**: User ratings and reviews.
- **Artifacts**: Secure upload and download of plugin bundles (S3/MinIO).
- **Statistics**: Download counts, ratings, trending algorithms.

## Usage

```python
from src.modules.marketplace import router

# Include in main FastAPI app
app.include_router(router)
```
