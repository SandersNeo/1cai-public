"""
Power BI connector for BA Integration.

Provides integration with Microsoft Power BI for:
- Dataset refresh
- Embed link generation
- Workspace management
- SLA monitoring

Features:
- OAuth 2.0 / Service Principal authentication
- Retry logic with exponential backoff
- DLQ for failed operations
- Prometheus metrics
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.integrations.base_connector import BaseConnector
from src.integrations.config.ba_config import config

logger = logging.getLogger(__name__)


class PowerBIConnector(BaseConnector):
    """
    Power BI connector for BA Integration.

    Provides methods to:
    - Refresh datasets
    - Generate embed tokens
    - Monitor refresh status
    - Export BA metrics

    SLA: Dataset refresh < 10 minutes
    """

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        workspace_id: str,
        dataset_id: Optional[str] = None
    ):
        """
        Initialize Power BI connector.

        Args:
            tenant_id: Azure AD tenant ID
            client_id: Service Principal client ID
            client_secret: Service Principal client secret
            workspace_id: Power BI workspace ID
            dataset_id: Default dataset ID (optional)
        """
        base_url = "https://api.powerbi.com/v1.0/myorg"
        super().__init__(base_url)

        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.workspace_id = workspace_id
        self.dataset_id = dataset_id

        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

    async def _get_access_token(self) -> str:
        """
        Get OAuth access token for Power BI API.

        Uses Service Principal authentication.

        Returns:
            Access token
        """
        # Check if token is still valid
        if self._access_token and self._token_expires_at:
            if datetime.utcnow() < self._token_expires_at - timedelta(minutes=5):
                return self._access_token

        # Request new token
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"

        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "https://analysis.windows.net/powerbi/api/.default"
        }

        response = await self._request(
            "POST",
            token_url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        token_data = response.json()
        self._access_token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 3600)
        self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        logger.info("Power BI access token obtained")
        return self._access_token

    async def _get_headers(self) -> Dict[str, str]:
        """Get headers with authorization token."""
        token = await self._get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    async def refresh_dataset(
        self,
        dataset_id: Optional[str] = None,
        notify_option: str = "NoNotification"
    ) -> Dict[str, Any]:
        """
        Trigger dataset refresh.

        Args:
            dataset_id: Dataset ID (uses default if not provided)
            notify_option: Notification option (NoNotification, MailOnFailure, MailOnCompletion)

        Returns:
            Refresh request ID and status

        Raises:
            Exception: If refresh fails
        """
        dataset_id = dataset_id or self.dataset_id
        if not dataset_id:
            raise ValueError("Dataset ID is required")

        url = f"{self.base_url}/groups/{self.workspace_id}/datasets/{dataset_id}/refreshes"

        headers = await self._get_headers()

        payload = {
            "notifyOption": notify_option
        }

        try:
