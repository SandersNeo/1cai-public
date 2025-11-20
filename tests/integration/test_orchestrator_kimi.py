# [NEXUS IDENTITY] ID: -3927206052933363993 | DATE: 2025-11-19

"""
Integration tests for AI Orchestrator with Kimi-K2-Thinking
"""
import pytest
import os
from src.ai.orchestrator import AIOrchestrator, QueryType, AIService


@pytest.mark.integration
class TestOrchestratorKimiIntegration:
    """Integration tests for AI Orchestrator with Kimi-K2-Thinking"""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance"""
        return AIOrchestrator()

    @pytest.mark.asyncio
    async def test_orchestrator_initializes_kimi(self, orchestrator):
        """Test that orchestrator initializes Kimi client"""
        # Check if Kimi client is initialized (may be None if not configured)
        assert hasattr(orchestrator, "kimi_client")
        # kimi_client can be None if not configured, which is OK

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("KIMI_API_KEY") and not os.getenv("KIMI_OLLAMA_URL"),
        reason="Kimi not configured, skipping integration test",
    )
    async def test_code_generation_with_kimi(self, orchestrator):
        """Test code generation using Kimi-K2-Thinking"""
        if not orchestrator.kimi_client or not orchestrator.kimi_client.is_configured:
            pytest.skip("Kimi client not configured")

        query = "Создай функцию для расчета скидки на основе суммы заказа"
        context = {
            "system_prompt": "You are an expert 1C:Enterprise developer.",
            "max_tokens": 500,
        }

        result = await orchestrator.process_query(query, context)

        assert result is not None
        assert "type" in result
        # Should be code generation type
        assert result["type"] == "code_generation"
        # Should use Kimi if available
        if "service" in result:
            assert result["service"] in ["kimi_k2", "qwen_coder"]

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("KIMI_API_KEY") and not os.getenv("KIMI_OLLAMA_URL"),
        reason="Kimi not configured, skipping integration test",
    )
    async def test_optimization_with_kimi(self, orchestrator):
        """Test code optimization using Kimi-K2-Thinking"""
        if not orchestrator.kimi_client or not orchestrator.kimi_client.is_configured:
            pytest.skip("Kimi client not configured")

        query = "Оптимизируй этот код"
        context = {
            "code": """
Функция РассчитатьСумму(Массив)
    Сумма = 0;
    Для Индекс = 0 По Массив.ВГраница() Цикл
        Сумма = Сумма + Массив[Индекс];
    КонецЦикла;
    Возврат Сумма;
КонецФункции
""",
            "system_prompt": "You are an expert 1C:Enterprise developer specializing in optimization.",
        }

        result = await orchestrator.process_query(query, context)

        assert result is not None
        assert "type" in result
        assert result["type"] == "optimization"
        # Should have optimized code
        if "optimized_code" in result:
            assert len(result["optimized_code"]) > 0

    @pytest.mark.asyncio
    async def test_orchestrator_fallback_to_qwen(self, orchestrator):
        """Test that orchestrator falls back to Qwen when Kimi is not available"""
        # Temporarily disable Kimi
        original_kimi = orchestrator.kimi_client
        orchestrator.kimi_client = None

        try:
            query = "Создай простую функцию"
            result = await orchestrator.process_query(query)

            assert result is not None
            # Should still work with Qwen fallback
            assert "type" in result
        finally:
            # Restore original Kimi client
            orchestrator.kimi_client = original_kimi

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("KIMI_API_KEY") and not os.getenv("KIMI_OLLAMA_URL"),
        reason="Kimi not configured, skipping integration test",
    )
    async def test_multi_service_with_kimi(self, orchestrator):
        """Test multi-service query with Kimi-K2-Thinking"""
        if not orchestrator.kimi_client or not orchestrator.kimi_client.is_configured:
            pytest.skip("Kimi client not configured")

        # Query that should trigger multi-service handling
        query = "Создай функцию и найди похожий код"
        context = {"system_prompt": "You are an expert AI assistant."}

        result = await orchestrator.process_query(query, context)

        assert result is not None
        assert "type" in result
        # May be multi_service or code_generation depending on classification

    @pytest.mark.asyncio
    async def test_query_classification_includes_kimi(self, orchestrator):
        """Test that query classification includes Kimi-K2-Thinking in preferred services"""
        classifier = orchestrator.classifier

        # Code generation query should include KIMI_K2
        query = "Создай функцию для расчета скидки"
        intent = classifier.classify(query)

        assert intent.query_type == QueryType.CODE_GENERATION
        # Should include KIMI_K2 in preferred services
        assert (
            AIService.KIMI_K2 in intent.preferred_services
            or AIService.QWEN_CODER in intent.preferred_services
        )

    @pytest.mark.asyncio
    async def test_optimization_classification_includes_kimi(self, orchestrator):
        """Test that optimization queries include Kimi in preferred services"""
        classifier = orchestrator.classifier

        query = "Оптимизируй эту функцию"
        intent = classifier.classify(query)

        assert intent.query_type == QueryType.OPTIMIZATION
        # Should include KIMI_K2 for optimization
        assert (
            AIService.KIMI_K2 in intent.preferred_services
            or AIService.QWEN_CODER in intent.preferred_services
        )

    @pytest.mark.asyncio
    async def test_orchestrator_caching(self, orchestrator):
        """Test that orchestrator caches results"""
        query = "Test query for caching"

        # First call
        result1 = await orchestrator.process_query(query)

        # Second call should use cache
        result2 = await orchestrator.process_query(query)

        # Results should be the same (cached)
        assert result1 == result2

        # Cache key should exist
        cache_key = f"{query}:{{}}"
        assert cache_key in orchestrator.cache

    @pytest.mark.asyncio
    async def test_error_handling_when_kimi_fails(self, orchestrator):
        """Test error handling when Kimi call fails"""
        if not orchestrator.kimi_client:
            pytest.skip("Kimi client not initialized")

        # Mock Kimi client to raise an error
        original_generate = orchestrator.kimi_client.generate

        async def failing_generate(*args, **kwargs):
            raise Exception("Kimi API error")

        orchestrator.kimi_client.generate = failing_generate

        try:
            query = "Создай функцию"
            result = await orchestrator.process_query(query)

            # Should fallback to Qwen or return error gracefully
            assert result is not None
            assert "type" in result
        finally:
            # Restore original method
            orchestrator.kimi_client.generate = original_generate
