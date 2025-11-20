# [NEXUS IDENTITY] ID: -2793510460550915683 | DATE: 2025-11-19

"""
Unit tests for EmbeddingService
"""

from unittest.mock import Mock, patch
from src.services.embedding_service import EmbeddingService


class TestEmbeddingService:
    """Test embedding service"""

    @patch("sentence_transformers.SentenceTransformer")
    def test_initialization(self, mock_transformer):
        """Test service initialization"""
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_transformer.return_value = mock_model

        service = EmbeddingService()

        assert service.model is not None
        mock_transformer.assert_called_once()

    @patch("sentence_transformers.SentenceTransformer")
    def test_encode_single_text(self, mock_transformer):
        """Test encoding single text"""
        mock_model = Mock()
        mock_model.encode.return_value = Mock(tolist=lambda: [0.1] * 384)
        mock_transformer.return_value = mock_model

        service = EmbeddingService()
        embedding = service.encode("Test text")

        assert isinstance(embedding, list)
        assert len(embedding) == 384
        mock_model.encode.assert_called_once()

    @patch("sentence_transformers.SentenceTransformer")
    def test_encode_multiple_texts(self, mock_transformer):
        """Test encoding multiple texts"""
        mock_model = Mock()
        mock_embeddings = [Mock(tolist=lambda: [0.1] * 384) for _ in range(3)]
        mock_model.encode.return_value = mock_embeddings
        mock_transformer.return_value = mock_model

        service = EmbeddingService()
        embeddings = service.encode(["Text 1", "Text 2", "Text 3"])

        assert isinstance(embeddings, list)
        assert len(embeddings) == 3
        mock_model.encode.assert_called_once()

    @patch("sentence_transformers.SentenceTransformer")
    def test_encode_list_truncates_items_and_length(self, mock_transformer):
        """List inputs should truncate per-item length and total list size"""
        mock_model = Mock()
        mock_model.encode.return_value = [
            Mock(tolist=lambda: [0.1] * 384) for _ in range(1000)
        ]
        mock_transformer.return_value = mock_model

        service = EmbeddingService()
        long_item = "a" * 200000
        large_list = [long_item for _ in range(1200)]
        service.encode(large_list)

        called_text = mock_model.encode.call_args[0][0]
        assert len(called_text) == 1000  # trimmed to max_list_length
        assert all(len(item) == 100000 for item in called_text)

    @patch("sentence_transformers.SentenceTransformer")
    def test_encode_list_filters_empty_items(self, mock_transformer):
        """Empty items should be skipped"""
        mock_model = Mock()
        mock_model.encode.return_value = [Mock(tolist=lambda: [0.1] * 384)]
        mock_transformer.return_value = mock_model

        service = EmbeddingService()
        embeddings = service.encode(["", None, "valid"])

        mock_model.encode.assert_called_once()
        called_text = mock_model.encode.call_args[0][0]
        assert called_text == ["valid"]
        assert len(embeddings) == 1

    @patch("sentence_transformers.SentenceTransformer")
    def test_encode_code(self, mock_transformer):
        """Test encoding BSL code"""
        mock_model = Mock()
        mock_model.encode.return_value = Mock(tolist=lambda: [0.1] * 384)
        mock_transformer.return_value = mock_model

        service = EmbeddingService()

        code = """
        // Комментарий
        Функция Тест()
            Возврат 1;
        КонецФункции
        """

        embedding = service.encode_code(code)

        assert isinstance(embedding, list)
        assert len(embedding) == 384
        # Should remove comments
        call_args = mock_model.encode.call_args[0][0]
        assert "//" not in call_args

    @patch("sentence_transformers.SentenceTransformer")
    def test_encode_function(self, mock_transformer):
        """Test encoding function metadata"""
        mock_model = Mock()
        mock_model.encode.return_value = Mock(tolist=lambda: [0.1] * 384)
        mock_transformer.return_value = mock_model

        service = EmbeddingService()

        func_data = {
            "name": "РассчитатьСумму",
            "description": "Расчет суммы двух чисел",
            "parameters": [{"name": "Значение1"}, {"name": "Значение2"}],
            "region": "ПрограммныйИнтерфейс",
        }

        embedding = service.encode_function(func_data)

        assert isinstance(embedding, list)
        assert len(embedding) == 384
