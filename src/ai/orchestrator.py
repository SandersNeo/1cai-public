# AI Orchestrator - Intelligent routing of queries to AI services
# Версия: 3.1.0
# Refactored: API endpoints moved to src/api/orchestrator_api.py

import asyncio
from typing import Any, Dict, Optional, TYPE_CHECKING

from src.ai.query_classifier import QueryClassifier, QueryIntent, QueryType, AIService
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

if TYPE_CHECKING:
    pass

class AIOrchestrator:
    # Main AI orchestrator - routes queries to appropriate services using Strategy Pattern

    def __init__(self):
        self.classifier = QueryClassifier()

        # Initialize strategies (Lazy Loading)
        from src.ai.strategies.graph import Neo4jStrategy
        from src.ai.strategies.kimi import KimiStrategy
        from src.ai.strategies.llm_providers import (
            GigaChatStrategy,
            NaparnikStrategy,
            OllamaStrategy,
            TabnineStrategy,
            YandexGPTStrategy,
        )
        from src.ai.strategies.qwen import QwenStrategy
        from src.ai.strategies.semantic import QdrantStrategy

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
            from src.ai.code_analysis.graph import InMemoryCodeGraphBackend
            from src.ai.code_analysis.graph_query_helper import GraphQueryHelper

            self.graph_helper = GraphQueryHelper(InMemoryCodeGraphBackend())
        except Exception:
            pass

        # Council Orchestrator
        self.council = None
        try:
            from src.ai.council import CouncilOrchestrator

            self.council = CouncilOrchestrator(self)
            logger.info("Council orchestrator initialized")
        except Exception as e:
            logger.warning("Council orchestrator not available: %s", e)

    def _get_strategy(self, service: AIService, context: Dict) -> Any:
        # Get strategy for service
        if service == AIService.EXTERNAL_AI:
            # Fallback or specific logic
            return self.strategies.get(AIService.QWEN_CODER)

        # Special handling for Ollama if requested
        if context.get("use_local_models") or context.get("max_cost") == 0.0:
            if self.ollama_strategy.is_available:
                return self.ollama_strategy

        return self.strategies.get(service)

    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Process query and return response
        if not query:
            raise ValueError("Query must be a non-empty string")

        context = context or {}

        # Security validation (poetic jailbreak detection)
        if context.get("enable_security_validation", True):
            try:
                from src.security.poetic_detection import MultiStageValidator

                validator = MultiStageValidator(self)
                validation_result = await validator.validate(query, context)

                if not validation_result.allowed:
                    logger.warning(
                        f"Query blocked by security validation: {validation_result.reason}",
                        extra={"query_length": len(query)},
                    )
                    return {
                        "error": "Query blocked by security filters",
                        "reason": validation_result.reason,
                        "details": {
                            "poetic_detected": validation_result.poetic_analysis is not None,
                            "stage": validation_result.stage_completed,
                        },
                    }

                # If poetic form detected, force council mode for extra safety
                if validation_result.poetic_analysis and validation_result.poetic_analysis.is_poetic:
                    context["use_council"] = True
                    logger.info("Poetic form detected, forcing council mode for safety")

            except Exception as e:
                logger.error("Security validation error: %s", e)
                # Continue without security validation on error

        # Check if council mode requested
        if context.get("use_council", False) and self.council:
            logger.info("Using council mode for query")
            return await self.process_query_with_council(query, context)

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
            except Exception:
                pass
            return cached_value

        try:
            orchestrator_cache_misses_total.inc()
        except Exception:
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

    async def process_query_with_council(
        self, query: str, context: Optional[Dict[str, Any]] = None, council_config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        # Process query with LLM Council consensus.
        # Args:
        #     query: User query
        #     context: Optional context
        #     council_config: Optional council configuration
        # Returns:
        #     Council response with all stages
        if not self.council:
            raise ValueError("Council orchestrator not available")

        from src.ai.council import CouncilConfig

        # Create council config
        if council_config:
            config = CouncilConfig(**council_config)
        else:
            config = None

        # Process with council
        council_response = await self.council.process_query(query=query, context=context, config=config)

        return council_response.to_dict()

    def _get_provider(self, model_name: str):
        # Get provider for model name.
        # Args:
        #     model_name: Model name (kimi, qwen, gigachat, yandexgpt)
        # Returns:
        #     Provider strategy
        # Map model names to strategies
        model_map = {
            "kimi": AIService.KIMI_K2,
            "qwen": AIService.QWEN_CODER,
            "gigachat": AIService.GIGACHAT,
            "yandexgpt": AIService.OPENAI,  # Mapped to YandexGPT
        }

        service = model_map.get(model_name)
        if not service:
            raise ValueError(f"Unknown model: {model_name}")

        return self.strategies.get(service)

    async def _execute_strategies(self, query: str, intent: QueryIntent, context: Dict) -> Dict:
        # Execute strategies based on intent

        # Single service optimization
        if len(intent.preferred_services) == 1:
            service = intent.preferred_services[0]
            strategy = self._get_strategy(service, context)
            if strategy:
                try:
                    return await strategy.execute(query, context)
                except Exception as e:
                    logger.error(f"Service {service} failed: {e}")
                    return {
                        "error": str(e),
                        "detailed_results": {
                            service: {"error": str(e)}
                        }
                    }

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

        # Aggregate results
        successful_count = 0
        combined_results = {}

        for i, result in enumerate(results):
            service_name = service_names[i]
            if isinstance(result, Exception):
                logger.error(f"Service {service_name} failed: {result}")
                combined_results[service_name] = {"error": str(result)}
            else:
                combined_results[service_name] = result
                successful_count += 1

        return {
            "type": "multi_service",
            "execution": "parallel",
            "services_called": service_names,
            "successful": successful_count,
            "detailed_results": combined_results,
        }

    def _enrich_response(self, response: Dict, query: str, intent: QueryIntent):
        # Add metadata to response
        meta = response.get("_meta", {})
        meta["intent"] = {
            "query_type": intent.query_type.value,
            "confidence": intent.confidence,
        }
        response["_meta"] = meta


# Global instance is removed to prevent import-time initialization
# Use get_orchestrator() to access the singleton instance

_orchestrator_instance = None

def get_orchestrator() -> AIOrchestrator:
    # Get or create the global AIOrchestrator instance
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = AIOrchestrator()
    return _orchestrator_instance


# DEPRECATED: app is moved to src/api/orchestrator_api.py
# We keep a dummy app here if needed for imports, but ideally imports should be fixed.
# For now, we do NOT export app to force fixing imports or to signal the change.

# Re-export for backward compatibility with tests
from src.ai.query_classifier import QueryType

__all__ = ["AIOrchestrator", "AIService", "QueryType", "orchestrator"]
