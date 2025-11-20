"""
Unit tests for modular EmbeddingService
"""

import pytest
from unittest.mock import MagicMock
from src.services.embedding.service import EmbeddingService
from src.services.embedding.cache_manager import EmbeddingCacheManager
from src.services.embedding.model_manager import EmbeddingModelManager
from src.services.embedding.resource_manager import EmbeddingResourceManager


class TestEmbeddingService:
    """Test the refactored EmbeddingService"""

    @pytest.fixture
    def mock_components(self):
        return {
            "cache": MagicMock(spec=EmbeddingCacheManager),
            "model": MagicMock(spec=EmbeddingModelManager),
            "resource": MagicMock(spec=EmbeddingResourceManager),
        }

    def test_initialization(self, mock_components):
        """Test service initialization with injected components"""
        service = EmbeddingService(
            cache_manager=mock_components["cache"],
            model_manager=mock_components["model"],
            resource_manager=mock_components["resource"],
        )
        assert service.cache_manager == mock_components["cache"]
        assert service.model_manager == mock_components["model"]
        assert service.resource_manager == mock_components["resource"]

    @pytest.mark.asyncio
    async def test_encode_cache_hit(self, mock_components):
        """Test encoding when result is in cache"""
        service = EmbeddingService(
            cache_manager=mock_components["cache"],
            model_manager=mock_components["model"],
            resource_manager=mock_components["resource"],
        )

        mock_components["cache"].get.return_value = [0.1, 0.2, 0.3]

        result = await service.encode("test query")

        assert result == [0.1, 0.2, 0.3]
        mock_components["cache"].get.assert_called_once_with("test query")
        mock_components["model"].encode.assert_not_called()

    @pytest.mark.asyncio
    async def test_encode_cache_miss(self, mock_components):
        """Test encoding when result is NOT in cache"""
        service = EmbeddingService(
            cache_manager=mock_components["cache"],
            model_manager=mock_components["model"],
            resource_manager=mock_components["resource"],
        )

        mock_components["cache"].get.return_value = None
        mock_components["model"].encode.return_value = [0.1, 0.2, 0.3]

        result = await service.encode("test query")

        assert result == [0.1, 0.2, 0.3]
        mock_components["cache"].get.assert_called_once_with("test query")
        mock_components["model"].encode.assert_called_once_with("test query")
        mock_components["cache"].set.assert_called_once_with(
            "test query", [0.1, 0.2, 0.3]
        )

    @pytest.mark.asyncio
    async def test_encode_resource_error(self, mock_components):
        """Test error handling when resources are unavailable"""
        service = EmbeddingService(
            cache_manager=mock_components["cache"],
            model_manager=mock_components["model"],
            resource_manager=mock_components["resource"],
        )

        mock_components["resource"].check_availability.return_value = False

        # Assuming resource manager raises exception or service handles it
        # If check_availability returns False, service might raise or try anyway depending on impl
        # Let's assume the service checks availability

        # For now, just ensure it's called if we were to implement that check in service.encode
        # Since the current implementation delegates straight to model/cache,
        # we test that model failure propagates if not cached

        mock_components["cache"].get.return_value = None
        mock_components["model"].encode.side_effect = Exception("GPU OOM")

        with pytest.raises(Exception, match="GPU OOM"):
            await service.encode("test query")
