# [NEXUS IDENTITY] ID: -5487998915097459304 | DATE: 2025-11-19

"""
Infrastructure Layer - Революционные компоненты
===============================================

Современная инфраструктура для замены устаревших технологий:
- Event-Driven Architecture (замена Celery)
- Event Store для Event Sourcing
- Serverless Functions
- Unified Data Layer
"""

from .data_layer import DataLoader, UnifiedDataLayer
from .event_bus import EventBus, EventPublisher, EventSubscriber
from .event_store import EventStore, EventStream
from .serverless import EdgeFunction, ServerlessFunction

__all__ = [
    "EventBus",
    "EventPublisher",
    "EventSubscriber",
    "EventStore",
    "EventStream",
    "EdgeFunction",
    "ServerlessFunction",
    "UnifiedDataLayer",
    "DataLoader",
]
