# [NEXUS IDENTITY] ID: -3123437763713397881 | DATE: 2025-11-19

"""
Модуль базы данных (Legacy wrapper).
Перенаправляет вызовы к новой реализации в src.infrastructure.db.
"""

from src.infrastructure.db.connection import get_db_pool

__all__ = ["get_db_pool"]
