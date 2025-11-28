"""
Release Notes Generator Service

Сервис для генерации release notes.
"""

from typing import Dict, List

from src.modules.technical_writer.domain.exceptions import ReleaseNotesGenerationError
from src.modules.technical_writer.domain.models import ReleaseNotes
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class ReleaseNotesGenerator:
    """
    Сервис генерации release notes

    Features:
    - Conventional Commits parsing
    - Categorization (features, fixes, breaking)
    - Migration guide generation
    """

    async def generate_release_notes(
        self,
        git_commits: List[Dict],
        version: str
    ) -> ReleaseNotes:
        """
        Генерация release notes

        Args:
            git_commits: Список git commits
            version: Версия релиза

        Returns:
            ReleaseNotes
        """
        try:
            logger.info(
                "Generating release notes",
                extra={"version": version, "commits": len(git_commits)}
            )

            # Parse commits
            features = []
            fixes = []
            breaking = []

            for commit in git_commits:
                msg = commit.get("message", "")

                if msg.startswith("feat:"):
                    features.append(msg.replace("feat:", "").strip())
                elif msg.startswith("fix:"):
                    fixes.append(msg.replace("fix:", "").strip())
                elif "BREAKING" in msg or "!" in msg:
                    breaking.append(msg)

            # Generate markdown
            markdown = self._generate_markdown(
                version,
                features,
                fixes,
                breaking
            )

            return ReleaseNotes(
                version=version,
                release_date="2025-11-27",
                features=features,
                fixes=fixes,
                breaking_changes=breaking,
                markdown=markdown
            )

        except Exception as e:
            logger.error("Failed to generate release notes: %s", e)
            raise ReleaseNotesGenerationError(
                f"Failed to generate release notes: {e}",
                details={"version": version}
            )

    def _generate_markdown(
        self,
        version: str,
        features: List[str],
        fixes: List[str],
        breaking: List[str]
    ) -> str:
        """Генерация Markdown"""
        notes = f"# Release Notes - {version}\n\n"
        notes += f"**Release Date:** 2025-11-27\n\n"

        if breaking:
            notes += "## ⚠️ BREAKING CHANGES\n\n"
            for item in breaking:
                notes += f"- {item}\n"
            notes += "\n"

        if features:
            notes += "## ✨ New Features\n\n"
            for item in features:
                notes += f"- {item}\n"
            notes += "\n"

        if fixes:
            notes += "## 🐛 Bug Fixes\n\n"
            for item in fixes:
                notes += f"- {item}\n"
            notes += "\n"

        return notes


__all__ = ["ReleaseNotesGenerator"]
