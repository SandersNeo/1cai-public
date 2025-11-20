# [NEXUS IDENTITY] ID: -7228934055341428768 | DATE: 2025-11-19

"""
Unit tests for AI Orchestrator
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.ai.orchestrator import QueryClassifier, AIOrchestrator, QueryType, AIService


class TestQueryClassifier:
    """Test query classification"""

    def test_classify_standard_1c(self):
        """Test classification of standard 1C query"""
        classifier = QueryClassifier()

        query = "Как в типовой УТ реализован расчет себестоимости?"
        intent = classifier.classify(query)

        assert intent.query_type == QueryType.STANDARD_1C
        assert intent.confidence > 0.5
        assert AIService.NAPARNIK in intent.preferred_services

    def test_classify_graph_query(self):
        """Test classification of graph query"""
        classifier = QueryClassifier()

        query = "Где используется функция РассчитатьНДС?"
        intent = classifier.classify(query)

        assert intent.query_type == QueryType.GRAPH_QUERY
        assert intent.confidence > 0.5
        assert AIService.NEO4J in intent.preferred_services

    def test_classify_code_generation(self):
        """Test classification of code generation query"""
        classifier = QueryClassifier()

        query = "Создай функцию для расчета скидки"
        intent = classifier.classify(query)

        assert intent.query_type == QueryType.CODE_GENERATION
        assert intent.confidence > 0.5
        assert AIService.QWEN_CODER in intent.preferred_services

    def test_classify_semantic_search(self):
        """Test classification of semantic search query"""
        classifier = QueryClassifier()

        query = "Найди похожий код для проверки прав доступа"
        intent = classifier.classify(query)

        assert intent.query_type == QueryType.SEMANTIC_SEARCH
        assert intent.confidence > 0.5
        assert AIService.QDRANT in intent.preferred_services

    def test_classify_optimization(self):
        """Test classification of optimization query"""
        classifier = QueryClassifier()

        query = "Оптимизируй эту функцию"
        intent = classifier.classify(query)

        assert intent.query_type == QueryType.OPTIMIZATION
        assert intent.confidence > 0.5
        # Kimi-K2-Thinking should be in preferred services for optimization
        assert (
            AIService.KIMI_K2 in intent.preferred_services
            or AIService.QWEN_CODER in intent.preferred_services
        )

    def test_classify_code_generation_with_kimi(self):
        """Test classification includes Kimi-K2-Thinking for code generation"""
        classifier = QueryClassifier()

        query = "Создай функцию для расчета скидки с использованием сложной логики"
        intent = classifier.classify(query)

        assert intent.query_type == QueryType.CODE_GENERATION
        # Kimi-K2-Thinking should be preferred for complex code generation
        assert (
            AIService.KIMI_K2 in intent.preferred_services
            or AIService.QWEN_CODER in intent.preferred_services
        )


class TestAIOrchestrator:
    """Test AI orchestration"""

    def test_register_client(self):
        """Test registering AI service client"""
        orchestrator = AIOrchestrator()
        mock_client = Mock()

        orchestrator.register_client(AIService.NEO4J, mock_client)

        assert AIService.NEO4J in orchestrator.clients
        assert orchestrator.clients[AIService.NEO4J] == mock_client

    @pytest.mark.asyncio
    async def test_process_query_caching(self):
        """Test query result caching"""
        orchestrator = AIOrchestrator()

        query = "Test query"
        # First call
        result1 = await orchestrator.process_query(query)

        # Second call (should be cached)
        result2 = await orchestrator.process_query(query)

        assert result1 == result2
        # Cache key should exist
        cache_key = f"{query}:{{}}"
        assert cache_key in orchestrator.cache

    @pytest.mark.asyncio
    async def test_orchestrator_with_kimi_client(self):
        """Test orchestrator with Kimi-K2-Thinking client"""
        orchestrator = AIOrchestrator()

        # Mock Kimi client
        mock_kimi_client = AsyncMock()
        mock_kimi_client.is_configured = True
        mock_kimi_client.generate = AsyncMock(
            return_value={"text": "Generated code", "usage": {"total_tokens": 100}}
        )

        # Set kimi_client
        orchestrator.kimi_client = mock_kimi_client

        # Test code generation query that should use Kimi
        query = "Создай функцию для расчета скидки"

        with patch.object(
            orchestrator, "_handle_code_generation", new_callable=AsyncMock
        ) as mock_handle:
            mock_handle.return_value = {"result": "success", "code": "generated code"}
            result = await orchestrator.process_query(query)

            # Should route to code generation handler
            assert result is not None

    @pytest.mark.asyncio
    async def test_orchestrator_kimi_not_configured(self):
        """Test orchestrator gracefully handles unconfigured Kimi client"""
        orchestrator = AIOrchestrator()

        # Mock unconfigured Kimi client
        mock_kimi_client = AsyncMock()
        mock_kimi_client.is_configured = False
        orchestrator.kimi_client = mock_kimi_client

        # Should fallback to other services
        query = "Создай функцию"
        result = await orchestrator.process_query(query)

        # Should still return a result (using fallback service)
        assert result is not None
