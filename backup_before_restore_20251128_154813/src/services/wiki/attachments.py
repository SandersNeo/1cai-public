"""
Wiki Attachment Storage
Handles file uploads to S3-compatible storage (MinIO/AWS)
"""

import os
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class WikiAttachmentStorage:
    """
    Service for managing wiki attachments.
    """

    def __init__(self):
        self.bucket_name = os.getenv(
            "WIKI_ATTACHMENTS_BUCKET",
            "wiki-attachments")
        self.s3_client = self._init_client()

    def _init_client(self):
        endpoint = os.getenv("S3_ENDPOINT")
        access_key = os.getenv("S3_ACCESS_KEY")
        secret_key = os.getenv("S3_SECRET_KEY")

        if not endpoint or not access_key:
            logger.warning("S3 configuration missing. Attachments will fail.")
            return None

        return boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

    async def upload_file(
        self, file_content: bytes, filename: str, content_type: str
    ) -> Optional[str]:
        """
        Upload file to S3 and return public URL.
        """
        if not self.s3_client:
            raise RuntimeError("S3 client not configured")

        try:
