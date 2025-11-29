"""
Wiki API Routes - Backward Compatibility

This module re-exports the router from src.modules.wiki.api.routes.
"""

from src.modules.wiki.api.routes import router

__all__ = ["router"]
