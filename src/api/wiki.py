"""
Wiki API Routes - Backward Compatibility

This module re-exports the router from src.modules.wiki.api.routes.
"""

from src.modules.wiki.api.routes import router
from src.services.wiki.service import WikiService


def get_wiki_service() -> WikiService:
    """Dependency provider for WikiService"""
    return WikiService()


__all__ = ["router", "get_wiki_service"]
