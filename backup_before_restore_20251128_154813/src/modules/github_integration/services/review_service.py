"""
Review Service
Orchestrates code review process
"""
from typing import Any, Dict, List

from src.ai.agents.code_review.ai_reviewer import AICodeReviewer
from src.infrastructure.logging.structured_logging import StructuredLogger
from src.modules.github_integration.domain.models import (PRFile,
                                                          ReviewComment,
                                                          ReviewResult)
from src.modules.github_integration.services.github_client import GitHubClient

logger = StructuredLogger(__name__).logger


class ReviewService:
    """Orchestrates code review process"""

    def __init__(self, github_client: GitHubClient):
        """
        Initialize review service

        Args:
            github_client: GitHub API client
        """
        self.github_client = github_client
        self.ai_reviewer = AICodeReviewer()

    async def review_pull_request(
            self, repo_full_name: str, pr_number: int) -> Dict[str, Any]:
        """
        Review a Pull Request

        Args:
            repo_full_name: Repository full name (owner/repo)
            pr_number: Pull request number

        Returns:
            Review result dictionary
        """
        logger.info(
            "Starting PR review",
            extra={"repo": repo_full_name, "pr_number": pr_number},
        )

        # Fetch PR files
        pr_files = await self.github_client.fetch_pr_files(repo_full_name, pr_number)

        if not pr_files:
            logger.warning(
                "No .bsl files found in PR",
                extra={"repo": repo_full_name, "pr_number": pr_number},
            )
            return {
                "status": "skipped",
                "reason": "No .bsl files to review",
                "pr_number": pr_number,
            }

        # Convert PRFile objects to format expected by AI reviewer
        files_for_review = []
        for pr_file in pr_files:
            files_for_review.append(
                {
                    "filename": pr_file.filename,
                    "content": getattr(pr_file, "content", ""),
                    "status": pr_file.status,
                    "additions": pr_file.additions,
                    "deletions": pr_file.deletions,
                }
            )

        # Perform AI review
        try:
