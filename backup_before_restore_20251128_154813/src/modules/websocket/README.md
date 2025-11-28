# WebSocket Module

## Overview

Real-time WebSocket notifications for build status, code reviews, and system alerts.

## Architecture

- **Domain Layer**: Message models
- **Services Layer**: `WebSocketService` with connection management
- **API Layer**: WebSocket endpoint

## Features

- Real-time notifications
- Room-based subscriptions
- Input validation and sanitization
- Timeout handling
- Ping/pong keepalive

## Usage

```python
from src.modules.websocket import router, notify_user

app.include_router(router)

# Send notification
await notify_user("user_123", "build_complete", {"status": "success"})
```
