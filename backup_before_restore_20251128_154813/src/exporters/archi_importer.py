"""
ArchiMate Importer - Import ArchiMate models into Unified Change Graph

Imports ArchiMate XML files with transaction support and rollback.
"""

import logging
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from src.modules.graph_api.services.graph_service import GraphService

logger = logging.getLogger(__name__)


class ArchiImporter:
    """Import ArchiMate models into Neo4j with transaction support"""

    # Mapping from ArchiMate element types to Neo4j labels
    ELEMENT_LABEL_MAP = {
        "ApplicationComponent": "Module",
        "ApplicationFunction": "Function",
        "BusinessProcess": "Process",
        "DataObject": "Document",
        "ApplicationInterface": "Interface",
        "ApplicationService": "Service",
    }

    # Mapping from ArchiMate relationship types to Neo4j types
    RELATIONSHIP_TYPE_MAP = {
        "Composition": "CONTAINS",
        "Aggregation": "HAS",
        "Assignment": "ASSIGNED_TO",
        "Realization": "IMPLEMENTS",
        "Serving": "SERVES",
        "Access": "ACCESSES",
        "Flow": "FLOWS_TO",
        "Triggering": "TRIGGERS",
        "Association": "RELATED_TO",
    }

    def __init__(self, graph_service: GraphService):
        """Initialize importer with graph service"""
        self.graph_service = graph_service

    async def import_from_archimate(self, file_path: str) -> Dict[str, Any]:
        """
        Import ArchiMate XML file with transaction support

        Args:
            file_path: Path to .archimate file

        Returns:
            Statistics about import
        """
        logger.info("Importing ArchiMate from: %s")

        # Parse XML
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Extract elements and relationships
        elements = root.findall(".//{*}element")
        relationships = root.findall(".//{*}relationship")

        element_map = {}
        nodes_created = 0
        relationships_created = 0

        # Use transaction for atomicity
        async with self.graph_service.neo4j.driver.session() as session:
            async with session.begin_transaction() as tx:
                try:
