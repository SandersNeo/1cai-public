"""
Code Sync Service
Scans the repository and updates Wiki pages to reflect the codebase structure and documentation.
"""

import ast
import os
import uuid
from pathlib import Path
from typing import List, Optional, Set

from src.database import get_db_connection
from src.services.wiki.models import WikiPageCreate, WikiPageUpdate
from src.services.wiki.service import WikiService
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

IGNORED_DIRS = {
    ".git",
    "__pycache__",
    "venv",
    "node_modules",
    ".idea",
    ".vscode",
    "tests",
    "migrations",
}
IGNORED_FILES = {"__init__.py"}


class ImportVisitor(ast.NodeVisitor):
    """Extracts imports from AST"""

    def __init__(self):
        self.imports: Set[str] = set()

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.add(node.module)
        self.generic_visit(node)


class CodeSyncService:
    def __init__(self, root_path: str, wiki_service: WikiService):
        self.root_path = Path(root_path)
        self.wiki_service = wiki_service
        self.namespace_cache = {}  # path -> namespace_id

    async def sync_all(self):
        """
        Full synchronization of the codebase into Wiki.
        """
        logger.info("Starting CodeSync from {self.root_path}")

        # 1. Ensure 'Codebase' root namespace exists
        root_ns_id = await self._get_or_create_namespace("Codebase", "codebase")
        self.namespace_cache["."] = root_ns_id

        # 2. Walk the tree
        for root, dirs, files in os.walk(self.root_path):
            # Filter ignored
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

            rel_path = Path(root).relative_to(self.root_path)
            if str(rel_path) == ".":
                current_ns_id = root_ns_id
            else:
                # Create namespace for this directory
                parent_path = rel_path.parent
                parent_ns_id = self.namespace_cache.get(
                    str(parent_path), root_ns_id)
                current_ns_id = await self._get_or_create_namespace(
                    rel_path.name, str(rel_path), parent_ns_id
                )
                self.namespace_cache[str(rel_path)] = current_ns_id

            # Process Python files
            for file in files:
                if file.endswith(".py") and file not in IGNORED_FILES:
                    await self._process_python_file(Path(root) / file, current_ns_id)

        logger.info("CodeSync completed")

    async def _process_python_file(self, file_path: Path, namespace_id: str):
        """
        Parse Python file and update Wiki page.
        """
        try:
