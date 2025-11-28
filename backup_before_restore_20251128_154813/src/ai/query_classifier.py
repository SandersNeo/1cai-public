import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from src.ai.scenario_hub import ScenarioRiskLevel
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class QueryType(Enum):
    """Types of queries"""

    STANDARD_1C = "standard_1c"
    GRAPH_QUERY = "graph_query"
    CODE_GENERATION = "code_generation"
    SEMANTIC_SEARCH = "semantic_search"
    ARCHITECTURE = "architecture"
    OPTIMIZATION = "optimization"
    UNKNOWN = "unknown"


class AIService(Enum):
    """Available AI services"""

    EXTERNAL_AI = "external_ai"
    QWEN_CODER = "qwen_coder"
    NEO4J = "neo4j"
    QDRANT = "qdrant"
    GIGACHAT = "gigachat"
    OPENAI = "openai"
    NAPARNIK = "naparnik"
    KIMI_K2 = "kimi_k2"
    TABNINE = "tabnine"


@dataclass
class QueryIntent:
    """Query intent analysis result"""

    query_type: QueryType
    confidence: float
    keywords: List[str]
    context_type: Optional[str]
    preferred_services: List[AIService]
    suggested_tools: List[str]


class QueryClassifier:
    """Classifies user queries to determine routing"""

    def __init__(self):
        """Инициализация QueryClassifier с поддержкой LLM Provider Abstraction."""
        self.llm_abstraction = None
        try:

        return QueryIntent(
            query_type=best_type,
            confidence=confidence,
            keywords=matched_keywords,
            context_type=context.get("type") if context else None,
            preferred_services=preferred_services,
            suggested_tools=list(set(suggested_tools)),  # Deduplicate
        )
