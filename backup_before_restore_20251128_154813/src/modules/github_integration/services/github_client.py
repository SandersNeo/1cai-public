"""
GitHub API Client
Handles all interactions with GitHub API with retry logic and error handling
"""
import asyncio
import hashlib
import hmac
import os
from typing import Any, Dict, List, Optional

import httpx

from src.infrastructure.logging.structured_logging import StructuredLogger
from src.modules.github_integration.domain.models import PRFile

logger = StructuredLogger(__name__).logger


class GitHubClient:
    """GitHub API client with retry logic and error handling"""

    def __init__(
        self,
        github_token: Optional[str] = None,
        webhook_secret: Optional[str] = None,
    ):
        """
        Initialize GitHub client

        Args:
            github_token: GitHub API token (defaults to GITHUB_TOKEN env var)
            webhook_secret: Webhook secret for signature verification
        """
        self.github_token = github_token or os.getenv("GITHUB_TOKEN", "")
        self.webhook_secret = webhook_secret or os.getenv(
            "GITHUB_WEBHOOK_SECRET", "")

        if not self.github_token:
            logger.warning(
                "GITHUB_TOKEN not set - GitHub integration disabled")

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify GitHub webhook signature

        Args:
            payload: Raw webhook payload
            signature: X-Hub-Signature-256 header value

        Returns:
            True if signature is valid, False otherwise
        """
        if not self.webhook_secret:
            logger.warning(
                "Webhook secret not configured - skipping verification")
            return True  # Allow in development

        mac = hmac.new(
            self.webhook_secret.encode(),
            msg=payload,
            digestmod=hashlib.sha256)
        expected_signature = "sha256=" + mac.hexdigest()

        return hmac.compare_digest(expected_signature, signature)

    async def fetch_pr_files(
            self,
            repo_full_name: str,
            pr_number: int,
            max_retries: int = 3) -> List[PRFile]:
        """
        Fetch changed files from a Pull Request

        Args:
            repo_full_name: Repository full name (owner/repo)
            pr_number: Pull request number
            max_retries: Maximum retry attempts

        Returns:
            List of PRFile objects

        Raises:
            ValueError: If input validation fails
        """
        # Input validation
        if not repo_full_name or not isinstance(repo_full_name, str):
            raise ValueError(f"Invalid repo_full_name: {repo_full_name}")
        if not isinstance(pr_number, int) or pr_number <= 0:
            raise ValueError(f"Invalid pr_number: {pr_number}")

        # Sanitize repo name (prevent path traversal)
        repo_full_name = repo_full_name.replace("..", "").replace("//", "/")

        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        url = f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}/files"

        # Fetch files with retry logic
        files_data = await self._make_request_with_retry("GET", url, headers=headers, max_retries=max_retries)

        if not files_data:
            return []

        # Convert to PRFile objects and download content for .bsl files
        pr_files = []
        for file_data in files_data:
            # Only process .bsl files
            if not file_data.get("filename", "").endswith(".bsl"):
                continue

            # Download raw content
            raw_url = file_data.get("raw_url")
            if not raw_url:
                logger.warning(
                    f"No raw_url for file {file_data.get('filename')}",
                    extra={"repo": repo_full_name, "pr_number": pr_number},
                )
                continue

            content = await self._download_file_content(raw_url, headers)
            if content is None:
                continue

            try:
                if attempt == max_retries - 1:
                    logger.error(
                        f"Request error: {exc}",
                        extra={
                            "url": url,
                            "method": method,
                            "error_type": type(exc).__name__,
                            "attempt": attempt + 1,
                        },
                        exc_info=True,
                    )
                    return None

                delay = base_delay * (2**attempt)
                logger.warning(
                    f"Request error, retrying in {delay}s: {exc}",
                    extra={
                        "url": url,
                        "method": method,
                        "error_type": type(exc).__name__,
                        "attempt": attempt + 1,
                        "delay": delay,
                    },
                )
                await asyncio.sleep(delay)

        return None

    async def _download_file_content(
            self, url: str, headers: Dict[str, str]) -> Optional[str]:
        """
        Download file content from URL

        Args:
            url: File URL
            headers: Request headers

        Returns:
            File content as string or None on failure
        """
        try:
