# Documentation Module

## Overview

Automatic documentation generation from source code using AI.

## Architecture

- **Domain Layer**: Pydantic models for requests/responses
- **Services Layer**: `DocumentationService` with timeout handling
- **API Layer**: FastAPI routes with rate limiting

## Features

- Multi-language support (BSL, TypeScript, Python, JavaScript)
- Multiple output formats (Markdown, HTML, Plain text)
- Rate limiting (5 requests/minute)
- Timeout protection (max 5 minutes)

## Usage

```python
from src.modules.documentation import router

app.include_router(router)
```
