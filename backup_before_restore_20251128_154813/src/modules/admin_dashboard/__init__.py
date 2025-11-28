# [NEXUS IDENTITY] ID: 8105445309231271486 | DATE: 2025-11-19

"""
Admin Dashboard API (Legacy)

DEPRECATED: This module has been refactored into Clean Architecture.
Use src.modules.admin_dashboard instead.
"""
from src.modules.admin_dashboard.api.routes import router

__all__ = ["router"]
