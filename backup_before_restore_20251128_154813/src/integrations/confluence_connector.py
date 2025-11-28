"""
Enhanced Confluence connector for BA Integration.

Extends the base Confluence client with BA-specific functionality:
- Markdown to Confluence Storage Format conversion
- Discovery canvas and BPMN diagram publishing
- ACL management
- Attachment handling
- Batch publishing
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base_client import BaseIntegrationClient
from .exceptions import IntegrationConfigError

logger = logging.getLogger(__name__)


class ConfluenceConnector(BaseIntegrationClient):
    """
    Enhanced Confluence client for BA Integration.

    Features:
    - Create/update pages
    - Markdown to Storage Format conversion
    - Attachment upload
    - ACL management
    - Batch operations
    """

    PAGES_ENDPOINT = "/wiki/api/v2/pages"
    ATTACHMENTS_ENDPOINT = "/wiki/rest/api/content"

    def __init__(
        self,
        *,
        base_url: str,
        token: str,
        space_key: str,
        transport: Optional[Any] = None,
    ) -> None:
        """
        Initialize Confluence connector.

        Args:
            base_url: Confluence instance URL
            token: API token or OAuth token
            space_key: Default space key for BA documentation
            transport: Optional HTTP transport
        """
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        super().__init__(base_url=base_url, headers=headers, transport=transport)
        self.space_key = space_key

    @classmethod
    def from_env(
        cls,
        *,
            transport: Optional[Any] = None) -> "ConfluenceConnector":
        """Create connector from environment variables."""
        base_url = os.getenv("BA_CONFLUENCE_BASE_URL")
        token = os.getenv("BA_CONFLUENCE_TOKEN")
        space_key = os.getenv("BA_CONFLUENCE_SPACE_KEY", "BA")

        if not base_url or not token:
            raise IntegrationConfigError(
                "BA_CONFLUENCE_BASE_URL and BA_CONFLUENCE_TOKEN must be configured."
            )
        return cls(
            base_url=base_url,
            token=token,
            space_key=space_key,
            transport=transport)

    def markdown_to_storage_format(self, markdown: str) -> str:
        """
        Convert Markdown to Confluence Storage Format.

        Args:
            markdown: Markdown content

        Returns:
            Confluence Storage Format HTML

        Note:
            This is a simplified conversion. For production, consider using
            a library like python-markdown with Confluence extensions.
        """
        # Basic conversion (headers, bold, italic, code)
        html = markdown

        # Headers
        html = html.replace("### ", "<h3>").replace("\n", "</h3>\n", 1)
        html = html.replace("## ", "<h2>").replace("\n", "</h2>\n", 1)
        html = html.replace("# ", "<h1>").replace("\n", "</h1>\n", 1)

        # Bold
        html = html.replace("**", "<strong>", 1).replace("**", "</strong>", 1)

        # Italic
        html = html.replace("*", "<em>", 1).replace("*", "</em>", 1)

        # Code blocks
        if "```" in html:
            parts = html.split("```")
            for i in range(1, len(parts), 2):
                lang = parts[i].split("\n")[0] if "\n" in parts[i] else ""
                code = parts[i][len(lang):].strip(
                ) if lang else parts[i].strip()
                parts[i] = (
                    f'<ac:structured-macro ac:name="code"><ac:parameter ac:name="language">{lang}</ac:parameter><ac:plain-text-body><![CDATA[{code}]]></ac:plain-text-body></ac:structured-macro>'
                )
            html = "".join(parts)

        # Paragraphs
        html = f"<p>{html}</p>"

        return html

    async def create_page_from_markdown(
        self,
        *,
        title: str,
        markdown_content: str,
        parent_id: Optional[str] = None,
        labels: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create Confluence page from Markdown content.

        Args:
            title: Page title
            markdown_content: Markdown content
            parent_id: Parent page ID
            labels: Page labels

        Returns:
            Created page data
        """
        storage_content = self.markdown_to_storage_format(markdown_content)

        payload: Dict[str, Any] = {
            "spaceId": self.space_key,
            "status": "current",
            "title": title,
            "body": {
                "representation": "storage",
                "value": storage_content,
            },
        }

        if parent_id:
            payload["parentId"] = parent_id

        response = await self._request("POST", self.PAGES_ENDPOINT, json=payload)

        page_data = response.json()
        page_id = page_data.get("id")

        # Add labels if provided
        if labels and page_id:
            await self.add_labels(page_id, labels)

        logger.info("Created Confluence page: %s (ID: %s)")
        return page_data

    async def update_page(
        self,
        *,
        page_id: str,
        title: str,
        content: str,
        version: int,
    ) -> Dict[str, Any]:
        """
        Update existing Confluence page.

        Args:
            page_id: Page ID
            title: Updated title
            content: Updated content (Storage Format)
            version: Current version number

        Returns:
            Updated page data
        """
        payload = {
            "id": page_id,
            "status": "current",
            "title": title,
            "body": {
                "representation": "storage",
                "value": content,
            },
            "version": {
                "number": version + 1,
            },
        }

        response = await self._request(
            "PUT", f"{self.PAGES_ENDPOINT}/{page_id}", json=payload
        )

        logger.info("Updated Confluence page: %s")
        return response.json()

    async def get_page(self, page_id: str) -> Dict[str, Any]:
        """Get page details."""
        response = await self._request(
            "GET", f"{self.PAGES_ENDPOINT}/{page_id}", params={"body-format": "storage"}
        )
        return response.json()

    async def upload_attachment(
        self,
        *,
        page_id: str,
        file_path: Path,
        comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upload attachment to Confluence page.

        Args:
            page_id: Page ID
            file_path: Path to file
            comment: Optional comment

        Returns:
            Attachment data
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Read file
        with open(file_path, "rb") as f:
            file_data = f.read()

        # Prepare multipart form data
        files = {
            "file": (file_path.name, file_data),
        }

        data = {}
        if comment:
            data["comment"] = comment

        # Note: This endpoint uses v1 API for attachments
        response = await self._request(
            "POST",
            f"{self.ATTACHMENTS_ENDPOINT}/{page_id}/child/attachment",
            files=files,
            data=data,
        )

        logger.info("Uploaded attachment {file_path.name} to page %s")
        return response.json()

    async def add_labels(self, page_id: str, labels: List[str]) -> None:
        """
        Add labels to page.

        Args:
            page_id: Page ID
            labels: List of label names
        """
        for label in labels:
            await self._request(
                "POST",
                f"{self.ATTACHMENTS_ENDPOINT}/{page_id}/label",
                json={"name": label},
            )

        logger.info("Added {len(labels)} labels to page %s")

    async def set_page_permissions(
        self,
        *,
        page_id: str,
        read_groups: Optional[List[str]] = None,
        edit_groups: Optional[List[str]] = None,
    ) -> None:
        """
        Set page permissions (ACL).

        Args:
            page_id: Page ID
            read_groups: Groups with read access
            edit_groups: Groups with edit access
        """
        # Get current restrictions
        response = await self._request(
            "GET", f"{self.ATTACHMENTS_ENDPOINT}/{page_id}/restriction"
        )

        response.json().get("restrictions", {})

        # Update read restrictions
        if read_groups:
            read_restriction = {"operation": "read", "restrictions": {
                "group": [{"name": group} for group in read_groups]}, }
            await self._request(
                "PUT",
                f"{self.ATTACHMENTS_ENDPOINT}/{page_id}/restriction",
                json=read_restriction,
            )

        # Update edit restrictions
        if edit_groups:
            edit_restriction = {"operation": "update", "restrictions": {
                "group": [{"name": group} for group in edit_groups]}, }
            await self._request(
                "PUT",
                f"{self.ATTACHMENTS_ENDPOINT}/{page_id}/restriction",
                json=edit_restriction,
            )

        logger.info("Updated permissions for page %s")

    async def search_pages(
        self,
        *,
        cql: str,
        limit: int = 25,
    ) -> List[Dict[str, Any]]:
        """
        Search pages using CQL (Confluence Query Language).

        Args:
            cql: CQL query string
            limit: Maximum results

        Returns:
            List of matching pages
        """
        response = await self._request(
            "GET",
            "/wiki/rest/api/content/search",
            params={
                "cql": cql,
                "limit": limit,
            },
        )

        return response.json().get("results", [])

    async def publish_discovery_canvas(
        self,
        *,
        requirement_id: str,
        canvas_data: Dict[str, Any],
        parent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Publish BA discovery canvas to Confluence.

        Args:
            requirement_id: BA requirement ID
            canvas_data: Discovery canvas data
            parent_id: Parent page ID

        Returns:
            Created page data
        """
        title = f"Discovery Canvas: {canvas_data.get('title', requirement_id)}"

        # Convert canvas to Markdown
        markdown = self._canvas_to_markdown(canvas_data)

        # Create page
        page = await self.create_page_from_markdown(
            title=title,
            markdown_content=markdown,
            parent_id=parent_id,
            labels=["ba", "discovery", f"req:{requirement_id}"],
        )

        logger.info("Published discovery canvas for %s")
        return page

    def _canvas_to_markdown(self, canvas_data: Dict[str, Any]) -> str:
        """Convert discovery canvas to Markdown."""
        md_parts = [
            f"# {canvas_data.get('title', 'Discovery Canvas')}",
            "",
            f"**Requirement ID:** {canvas_data.get('requirement_id', 'N/A')}",
            f"**Created:** {canvas_data.get('created_at', 'N/A')}",
            "",
            "## Problem Statement",
            canvas_data.get("problem_statement", ""),
            "",
            "## Proposed Solution",
            canvas_data.get("solution", ""),
            "",
            "## Stakeholders",
            ", ".join(canvas_data.get("stakeholders", [])),
            "",
        ]

        return "\n".join(md_parts)


# Legacy compatibility
ConfluenceClient = ConfluenceConnector
