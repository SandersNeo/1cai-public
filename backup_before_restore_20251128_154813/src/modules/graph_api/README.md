# Graph API Module

## Overview

The Graph API module provides endpoints for interacting with Neo4j graph database, Qdrant vector store, and PostgreSQL. It supports semantic code search, graph queries, and dependency analysis.

## Architecture

- **Domain Layer** (`domain/`): Pydantic models for request validation.
- **Services Layer** (`services/`): `GraphService` and `VectorSearchService`.
- **API Layer** (`api/`): FastAPI routes with dependency injection.

## Key Features

- **Graph Queries**: Execute Cypher queries with security validation.
- **Semantic Search**: Vector-based code search using embeddings.
- **Dependency Analysis**: Function call graphs and dependencies.
- **Statistics**: Database statistics and health checks.

## Usage

```python
from src.modules.graph_api import router

app.include_router(router)
```
