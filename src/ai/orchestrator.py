# [NEXUS IDENTITY] ID: -6726814223650585514 | DATE: 2025-11-19

"""
AI Orchestrator - Intelligent routing of queries to AI services
Версия: 3.1.0
Refactored: API endpoints moved to src/api/orchestrator_api.py
"""

import asyncio
from typing import Dict, Any, Optional

from src.utils.structured_logging import StructuredLogger
from src.monitoring.prometheus_metrics import (
    orchestrator_cache_hits_total,
    orchestrator_cache_misses_total,
)

# Import extracted classifier
from src.ai.query_classifier import QueryClassifier, AIService, QueryIntent

# Import strategies
from src.ai.strategies.qwen import QwenStrategy
from src.ai.strategies.kimi import KimiStrategy
from src.ai.strategies.graph import Neo4jStrategy
from src.ai.strategies.semantic import QdrantStrategy
from src.ai.strategies.llm_providers import (
    GigaChatStrategy,
    YandexGPTStrategy,
    NaparnikStrategy,
    OllamaStrategy,
    TabnineStrategy,
)

logger = StructuredLogger(__name__).logger


class AIOrchestrator:
    """Main AI orchestrator - routes queries to appropriate services using Strategy Pattern"""

    def __init__(self):
        self.classifier = QueryClassifier()

        # Initialize strategies
        self.strategies = {
            AIService.QWEN_CODER: QwenStrategy(),
            AIService.KIMI_K2: KimiStrategy(),
            AIService.NEO4J: Neo4jStrategy(),
            AIService.QDRANT: QdrantStrategy(),
            AIService.GIGACHAT: GigaChatStrategy(),
            AIService.OPENAI: YandexGPTStrategy(),  # Mapping Yandex to OpenAI slot as per original
            AIService.NAPARNIK: NaparnikStrategy(),
            AIService.TABNINE: TabnineStrategy(),
        }
        self.ollama_strategy = OllamaStrategy()

        # Initialize Cache
        try:
            from src.ai.intelligent_cache import IntelligentCache

            self.cache = IntelligentCache(max_size=1000, default_ttl_seconds=300)
        except Exception:
            self.cache = {}

        # Graph Helper
        self.graph_helper = None
        try:
            from src.ai.code_graph import InMemoryCodeGraphBackend
            from src.ai.code_graph_query_helper import GraphQueryHelper

            self.graph_helper = GraphQueryHelper(InMemoryCodeGraphBackend())
        except Exception:
            pass

    def _get_strategy(self, service: AIService, context: Dict) -> Any:
        """Get strategy for service"""
        if service == AIService.EXTERNAL_AI:
            # Fallback or specific logic
            return self.strategies.get(AIService.QWEN_CODER)

        # Special handling for Ollama if requested
        if context.get("use_local_models") or context.get("max_cost") == 0.0:
            if self.ollama_strategy.is_available:
                return self.ollama_strategy

        return self.strategies.get(service)

    async def process_query(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process query and return response"""
        if not query:
            raise ValueError("Query must be a non-empty string")

        context = context or {}

        # Check cache
        cached_value = None
        if isinstance(self.cache, dict):
            cache_key = f"{query}:{context}"
            cached_value = self.cache.get(cache_key)
        else:
            cached_value = self.cache.get(query, context)

        if cached_value:
            try:
                orchestrator_cache_hits_total.inc()
            except:
                pass
            return cached_value

        try:
            orchestrator_cache_misses_total.inc()
        except:
            pass

        # Classify
        intent = self.classifier.classify(query, context)

        # Select Provider via Abstraction (optional, updates context)
        if self.classifier.llm_abstraction:
            # ... (logic to select provider and update context, similar to original)
            pass

        logger.info(
            f"Query classified: {intent.query_type.value}",
            extra={"confidence": intent.confidence},
        )

        # Execute Strategy
        response = await self._execute_strategies(query, intent, context)

        # Enrich response
        if isinstance(response, dict):
            self._enrich_response(response, query, intent)

        # Cache result
        if isinstance(self.cache, dict):
            cache_key = f"{query}:{context}"
            self.cache[cache_key] = response
        else:
            self.cache.set(query, response, context, query_type=intent.query_type.value)

        return response

    async def _execute_strategies(
        self, query: str, intent: QueryIntent, context: Dict
    ) -> Dict:
        """Execute strategies based on intent"""

        # Single service optimization
        if len(intent.preferred_services) == 1:
            service = intent.preferred_services[0]
            strategy = self._get_strategy(service, context)
            if strategy:
                return await strategy.execute(query, context)

        # Parallel execution
        tasks = []
        service_names = []

        for service in intent.preferred_services:
            strategy = self._get_strategy(service, context)
            if strategy:
                tasks.append(strategy.execute(query, context))
                service_names.append(strategy.service_name)

        if not tasks:
            return {"error": "No suitable services found"}

        results = await asyncio.gather(*tasks, return_exceptions=True)

        combined_results = {}
        successful_count = 0

        for name, result in zip(service_names, results):
            if isinstance(result, Exception):
                combined_results[name] = {"status": "failed", "error": str(result)}
            else:
                combined_results[name] = {**result, "status": "success"}
                successful_count += 1

        return {
            "type": "multi_service",
            "execution": "parallel",
            "services_called": service_names,
            "successful": successful_count,
            "detailed_results": combined_results,
        }

    def _enrich_response(self, response: Dict, query: str, intent: QueryIntent):
        """Add metadata to response"""
        meta = response.get("_meta", {})
        meta["intent"] = {
            "query_type": intent.query_type.value,
            "confidence": intent.confidence,
        }
        response["_meta"] = meta


# Orchestrator instance
orchestrator = AIOrchestrator()

# DEPRECATED: app is moved to src/api/orchestrator_api.py
# We keep a dummy app here if needed for imports, but ideally imports should be fixed.
# For now, we do NOT export app to force fixing imports or to signal the change.
