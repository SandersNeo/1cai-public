"""
Wiki Service Implementation
Handles logic for page management, versioning, rendering, and advanced features (Blueprints, AI)
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional

from src.database import get_db_connection
from src.utils.structured_logging import StructuredLogger

# Import DTOs
from .models import WikiPage as PageDTO
from .models import WikiPageCreate, WikiPageUpdate
# Import Renderer
from .renderer import WikiRenderer

logger = StructuredLogger(__name__).logger


class WikiService:
    """
    Service for managing Wiki pages with versioning, code integration, and AI features.
    """

    def __init__(self, db_session=None):
        self.renderer = WikiRenderer()
        # Stub Qdrant integration for now
        self.qdrant = None

    async def get_page(
        self, slug: str, version: Optional[int] = None
    ) -> Optional[PageDTO]:
        """
        Retrieve a wiki page by slug from DB.
        """
        query = """
            SELECT
                p.id, p.slug, p.title, p.namespace_id, p.version, p.created_at, p.updated_at,
                r.content
            FROM wiki_pages p
            LEFT JOIN wiki_revisions r ON p.current_revision_id = r.id
            WHERE p.slug = $1 AND p.is_deleted = FALSE
        """
        params = [slug]

        if version:
            query = """
                SELECT
                    p.id, p.slug, p.title, p.namespace_id, p.version, p.created_at, p.updated_at,
                    r.content
                FROM wiki_pages p
                JOIN wiki_revisions r ON r.page_id = p.id
                WHERE p.slug = $1 AND r.version = $2
            """
            params = [slug, version]

        async with get_db_connection() as conn:
            row = await conn.fetchrow(query, *params)

            if not row:
                return None

            # Render content on the fly (or cache it in future)
            html_content = (
                self.renderer.render(row["content"]) if row["content"] else ""
            )

            # Construct DTO
            page_dto = PageDTO(
                id=row["id"],
                slug=row["slug"],
                namespace="default",  # STUB
                title=row["title"],
                current_revision_id="stub",
                version=row["version"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            page_dto.html_content = html_content  # Attach rendered content
            return page_dto

    async def create_page(
            self,
            data: WikiPageCreate,
            author_id: str,
            blueprint_id: Optional[str] = None) -> PageDTO:
        """
        Create a new wiki page with initial revision in DB.
        """
        content = data.content
        if blueprint_id:
            logger.info(
                f"Applying blueprint {blueprint_id} to page {data.slug}")
            content = f"# {data.title}\n\nGenerated from blueprint..."

        page_id = str(uuid.uuid4())
        revision_id = str(uuid.uuid4())

        # If namespace is not a valid UUID (e.g. "default"), treat it as a name or handle properly
        # For now, if it looks like a UUID, use it; otherwise generate a stub
        # ID or lookup.
        try:
