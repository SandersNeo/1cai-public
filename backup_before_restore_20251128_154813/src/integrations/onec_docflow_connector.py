"""
1С:Документооборот connector for BA Integration.

Provides integration with 1С:Документооборот for:
- Document management (create, update, search)
- File attachments
- Workflow operations
- BA requirements export

Features:
- HTTP Basic authentication
- Retry logic with exponential backoff
- DLQ for failed operations
- Prometheus metrics
"""

import base64
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.integrations.base_connector import BaseConnector
from src.integrations.config.ba_config import config

logger = logging.getLogger(__name__)


class OneCDocflowConnector(BaseConnector):
    """
    1С:Документооборот connector for BA Integration.

    Provides methods to:
    - Create and update documents
    - Upload/download file attachments
    - Manage workflows (approve, reject)
    - Export BA artifacts

    SLA: Document operations < 5 minutes
    """

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str
    ):
        """
        Initialize 1С:Документооборот connector.

        Args:
            base_url: 1С:Документооборот base URL
            username: HTTP Basic Auth username
            password: HTTP Basic Auth password
        """
        super().__init__(base_url)

        self.username = username
        self.password = password

    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers with HTTP Basic Auth.

        Returns:
            Headers with Authorization
        """
        # Create Basic Auth header
        credentials = f"{self.username}:{self.password}"
        encoded = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        return headers

    async def create_document(
        self,
        document_type: str,
        title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create new document in 1С:Документооборот.

        Args:
            document_type: Document type (Requirement, Analysis, Project)
            title: Document title
            content: Document content (HTML or plain text)
            metadata: Additional metadata

        Returns:
            Created document information

        Raises:
            Exception: If creation fails
        """
        url = f"{self.base_url}/documents"

        payload = {
            "type": document_type,
            "title": title,
            "content": content,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat()
        }

        try:
