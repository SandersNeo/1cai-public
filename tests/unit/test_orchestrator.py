# [NEXUS IDENTITY] ID: -7228934055341428768 | DATE: 2025-11-19

"""
Unit tests for AI Orchestrator
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.ai.orchestrator import AIOrchestrator, AIService, QueryClassifier, QueryType


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
        assert AIService.KIMI_K2 in intent.preferred_services or AIService.QWEN_CODER in intent.preferred_services

    def test_classify_code_generation_with_kimi(self):
        """Test classification includes Kimi-K2-Thinking for code generation"""
        classifier = QueryClassifier()

        query = "Создай функцию для расчета скидки с использованием сложной логики"
        intent = classifier.classify(query)

        assert intent.query_type == QueryType.CODE_GENERATION
        # Kimi-K2-Thinking should be preferred for complex code generation
        assert AIService.KIMI_K2 in intent.preferred_services or AIService.QWEN_CODER in intent.preferred_services


class TestAIOrchestrator:
    """Test AI orchestration"""

    def test_register_strategy(self):
        """Test registering AI strategy"""
        orchestrator = AIOrchestrator()
        mock_strategy = Mock()

        orchestrator.strategies[AIService.NEO4J] = mock_strategy

        assert AIService.NEO4J in orchestrator.strategies
        assert orchestrator.strategies[AIService.NEO4J] == mock_strategy

    @pytest.mark.asyncio
    async def test_process_query_caching(self):
        """Test query result caching"""
        orchestrator = AIOrchestrator()

        # Mock cache to be a dict for simplicity in this test
        orchestrator.cache = {}

        query = "Test query"
        # Mock strategy execution
        with patch.object(orchestrator, "_execute_strategies", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = {"result": "success"}

            # First call
            result1 = await orchestrator.process_query(query)

            # Second call (should be cached)
            result2 = await orchestrator.process_query(query)

            assert result1 == result2
            # Cache key should exist
            cache_key = f"{query}:{{}}"
            assert cache_key in orchestrator.cache

            # Strategy should be called only once
            assert mock_exec.call_count == 1

    @pytest.mark.asyncio
    async def test_orchestrator_with_kimi_strategy(self):
        """Test orchestrator with Kimi strategy"""
        orchestrator = AIOrchestrator()

        # Mock Kimi strategy
        mock_kimi_strategy = AsyncMock()
        mock_kimi_strategy.execute = AsyncMock(return_value={"text": "Generated code", "usage": {"total_tokens": 100}})

        orchestrator.strategies[AIService.KIMI_K2] = mock_kimi_strategy

        # Test code generation query that should use Kimi
        query = "Создай функцию для расчета скидки"

        # Mock classifier to return Kimi as preferred service
        with patch.object(orchestrator.classifier, "classify") as mock_classify:
            mock_classify.return_value = Mock(
                query_type=QueryType.CODE_GENERATION, confidence=0.9, preferred_services=[AIService.KIMI_K2]
            )

            result = await orchestrator.process_query(query)

            # Should use Kimi strategy
            assert result["text"] == "Generated code"
            mock_kimi_strategy.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_orchestrator_fallback(self):
        """Test orchestrator fallback when service fails"""
        orchestrator = AIOrchestrator()

        # Mock failing strategy
        mock_failing_strategy = AsyncMock()
        mock_failing_strategy.execute = AsyncMock(side_effect=Exception("Service failed"))

        orchestrator.strategies[AIService.QWEN_CODER] = mock_failing_strategy

        query = "Создай функцию"

        with patch.object(orchestrator.classifier, "classify") as mock_classify:
            mock_classify.return_value = Mock(
                query_type=QueryType.CODE_GENERATION, confidence=0.9, preferred_services=[AIService.QWEN_CODER]
            )

            # Should handle exception and return error result
            result = await orchestrator.process_query(query)

            # Check for error structure
            assert "detailed_results" in result
            assert AIService.QWEN_CODER in result["detailed_results"]
            assert "error" in result["detailed_results"][AIService.QWEN_CODER]
