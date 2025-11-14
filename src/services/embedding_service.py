"""
Embedding Service for Vector Search
Версия: 2.0.0

Улучшения:
- Улучшенная обработка ошибок
- Retry logic для загрузки модели
- Graceful degradation при отсутствии модели
- Structured logging
"""

import importlib
import logging
import time
from typing import Dict, List, Union, Optional
import sys
import types

from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

try:
    import sentence_transformers  # noqa: F401
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    logger.warning("sentence-transformers not installed. Run: pip install sentence-transformers")

    stub_module = types.ModuleType("sentence_transformers")
    class _StubSentenceTransformer:
        def __init__(self, *args, **kwargs):
            raise ImportError("sentence-transformers not installed")

        def encode(self, *args, **kwargs):
            raise ImportError("sentence-transformers not installed")

    stub_module.SentenceTransformer = _StubSentenceTransformer  # type: ignore[attr-defined]
    sys.modules.setdefault("sentence_transformers", stub_module)
    EMBEDDINGS_AVAILABLE = False


class EmbeddingService:
    """Service for generating embeddings"""
    
    # Using lightweight model for local deployment
    DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    # Vector size: 384 dimensions
    
    # Alternative models:
    # - "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2" (384d, multilingual)
    # - "intfloat/multilingual-e5-small" (384d, better quality)
    # - "BAAI/bge-small-en-v1.5" (384d, good quality)
    
    def __init__(self, model_name: str = None):
        """Initialize embedding model с input validation"""
        # Input validation
        if model_name is not None and not isinstance(model_name, str):
            logger.warning(
                "Invalid model_name type in EmbeddingService.__init__",
                extra={"model_name_type": type(model_name).__name__}
            )
            model_name = None
        
        if model_name and len(model_name) > 500:  # Limit length
            logger.warning(
                "Model name too long in EmbeddingService.__init__",
                extra={"model_name_length": len(model_name)}
            )
            model_name = model_name[:500]
        
        self.model_name = model_name or self.DEFAULT_MODEL
        self.model = None
        self._load_model()
    
    def _load_model(self, max_retries: int = 3, retry_delay: float = 1.0):
        """
        Load embedding model with retry logic
        
        Best practices:
        - Retry для transient errors
        - Exponential backoff
        - Graceful degradation
        """
        if not EMBEDDINGS_AVAILABLE:
            logger.warning("sentence-transformers not available, embeddings disabled")
            self.model = None
            return
        
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                logger.info(
                    "Loading embedding model: %s (attempt %d/%d)",
                    self.model_name,
                    attempt + 1,
                    max_retries
                )
                module = importlib.import_module("sentence_transformers")
                transformer_cls = getattr(module, "SentenceTransformer")
                self.model = transformer_cls(self.model_name)
                dimension = self.model.get_sentence_embedding_dimension()
                logger.info(
                    f"✓ Model loaded successfully (dimension: {dimension})",
                    extra={
                        "model_name": self.model_name,
                        "dimension": dimension,
                        "attempt": attempt + 1
                    }
                )
                return
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(
                        f"Failed to load model (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {wait_time}s...",
                        extra={
                            "model_name": self.model_name,
                            "attempt": attempt + 1,
                            "max_retries": max_retries,
                            "error": str(e)
                        }
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(
                        f"Failed to load model after {max_retries} attempts: {e}",
                        exc_info=True,
                        extra={
                            "model_name": self.model_name,
                            "max_retries": max_retries
                        }
                    )
                    self.model = None  # Graceful degradation
        
        if last_exception:
            raise last_exception
    
    def encode(self, text: Union[str, List[str]], 
               batch_size: int = 32,
               show_progress: bool = False) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings for text with improved error handling
        
        Best practices:
        - Graceful degradation при отсутствии модели
        - Валидация входных данных
        - Structured logging
        """
        if not self.model:
            logger.warning("Model not loaded, cannot generate embeddings")
            return [] if isinstance(text, list) else []
        
        # Input validation
        if not text:
            logger.warning(
                "Empty text provided for encoding",
                extra={"text_type": type(text).__name__ if text else None}
            )
            return [] if isinstance(text, list) else []
        
        # Validate text type
        if not isinstance(text, (str, list)):
            logger.warning(
                "Invalid text type in encode",
                extra={"text_type": type(text).__name__}
            )
            return []
        
        # Limit text length (prevent DoS)
        if isinstance(text, str):
            max_text_length = 100000  # 100KB max
            if len(text) > max_text_length:
                logger.warning(
                    "Text too long in encode",
                    extra={"text_length": len(text), "max_length": max_text_length}
                )
                text = text[:max_text_length]
        elif isinstance(text, list):
            max_list_length = 1000  # Max 1000 items
            if len(text) > max_list_length:
                logger.warning(
                    "Text list too long in encode",
                    extra={"list_length": len(text), "max_length": max_list_length}
                )
                text = text[:max_list_length]
            
            # Validate each item in list
            text = [str(item)[:max_text_length] if isinstance(item, str) else str(item)[:max_text_length] 
                   for item in text if item]
        
        # Validate batch_size
        if not isinstance(batch_size, int) or batch_size < 1:
            logger.warning(
                "Invalid batch_size in encode",
                extra={"batch_size": batch_size, "batch_size_type": type(batch_size).__name__}
            )
            batch_size = 32
        
        if batch_size > 1000:  # Prevent DoS
            logger.warning(
                "Batch size too large in encode",
                extra={"batch_size": batch_size}
            )
            batch_size = 1000
        
        try:
            embeddings = self.model.encode(
                text,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True
            )
            
            # Convert to list
            if isinstance(text, str):
                return embeddings.tolist()
            else:
                return [emb.tolist() for emb in embeddings]
                
        except Exception as e:
            logger.error(
                f"Encoding error: {e}",
                exc_info=True,
                extra={
                    "text_length": len(text) if isinstance(text, str) else len(text) if isinstance(text, list) else 0,
                    "batch_size": batch_size,
                    "model_name": self.model_name
                }
            )
            return [] if isinstance(text, list) else []
    
    async def generate_embedding(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Асинхронная обертка для совместимости с остальным кодом (orchestrator).
        """
        return self.encode(text)
    
    def encode_code(self, code: str) -> List[float]:
        """
        Encode BSL code for vector search с input validation
        
        Preprocessing:
        - Remove comments
        - Normalize whitespace
        - Keep only meaningful code
        """
        # Input validation
        if not isinstance(code, str):
            logger.warning(
                "Invalid code type in encode_code",
                extra={"code_type": type(code).__name__ if code else None}
            )
            return []
        
        if not code.strip():
            logger.warning("Empty code provided for encoding")
            return []
        
        # Limit code length (prevent DoS)
        max_code_length = 100000  # 100KB max
        if len(code) > max_code_length:
            logger.warning(
                "Code too long in encode_code",
                extra={"code_length": len(code), "max_length": max_code_length}
            )
            code = code[:max_code_length]
        
        # Simple preprocessing
        lines = []
        for line in code.split('\n'):
            line = line.strip()
            # Skip empty lines and comments
            if line and not line.startswith('//'):
                lines.append(line)
        
        clean_code = ' '.join(lines)
        
        # Limit cleaned code length
        max_clean_length = 5000
        if len(clean_code) > max_clean_length:
            clean_code = clean_code[:max_clean_length]
        
        return self.encode(clean_code)
    
    def encode_function(self, func_data: Dict) -> List[float]:
        """
        Encode function metadata for search
        
        Combines:
        - Function name
        - Description
        - Parameter names
        - Region
        """
        parts = []
        
        # Name
        if func_data.get('name'):
            parts.append(func_data['name'])
        
        # Description
        if func_data.get('description'):
            parts.append(func_data['description'])
        
        # Parameters
        params = func_data.get('parameters', [])
        if params:
            param_names = [p.get('name', str(p)) for p in params]
            parts.append(' '.join(param_names))
        
        # Region
        if func_data.get('region'):
            parts.append(func_data['region'])
        
        text = ' '.join(parts)
        
        return self.encode(text)
    
    def get_embedding_dimension(self) -> int:
        """Get embedding dimension"""
        return self.model.get_sentence_embedding_dimension()







