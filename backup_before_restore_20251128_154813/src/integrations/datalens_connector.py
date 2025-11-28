"""
Yandex DataLens connector for BA Integration.

Provides integration with Yandex DataLens for:
- Dataset operations
- Dashboard management
- Connection management
- Data export

Features:
- API token authentication
- Retry logic with exponential backoff
- DLQ for failed operations
"""

import logging
from typing import Any, Dict, List, Optional

from src.integrations.base_connector import BaseConnector
from src.integrations.config.ba_config import config

logger = logging.getLogger(__name__)


class DataLensConnector(BaseConnector):
    """
    Yandex DataLens connector for BA Integration.

    Provides methods to:
    - Manage datasets
    - Create/update dashboards
    - Export BA metrics
    - Manage connections

    SLA: Operations < 5 minutes
    """

    def __init__(
        self,
        api_token: str,
        folder_id: str,
        dataset_id: Optional[str] = None
    ):
        """
        Initialize DataLens connector.

        Args:
            api_token: Yandex Cloud API token
            folder_id: DataLens folder ID
            dataset_id: Default dataset ID (optional)
        """
        base_url = "https://datalens.yandex.ru/api/v1"
        super().__init__(base_url)

        self.api_token = api_token
        self.folder_id = folder_id
        self.dataset_id = dataset_id

    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authorization token."""
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

    async def create_dataset(
        self,
        name: str,
        connection_id: str,
        source_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create new dataset.

        Args:
            name: Dataset name
            connection_id: Connection ID
            source_config: Source configuration (table, query, etc.)

        Returns:
            Created dataset information
        """
        url = f"{self.base_url}/datasets"

        payload = {
            "name": name,
            "folderId": self.folder_id,
            "connectionId": connection_id,
            "source": source_config
        }

        try:
