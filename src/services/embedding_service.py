"""
Embedding Service for Vector Search
Generates embeddings for code and documentation
"""

import importlib
import logging
from typing import Dict, List, Union
import sys
import types

logger = logging.getLogger(__name__)

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
        """Initialize embedding model"""
        
        self.model_name = model_name or self.DEFAULT_MODEL
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load embedding model"""
        try:
            logger.info("Loading embedding model: %s", self.model_name)
            module = importlib.import_module("sentence_transformers")
            transformer_cls = getattr(module, "SentenceTransformer")
            self.model = transformer_cls(self.model_name)
            logger.info(f"✓ Model loaded (dimension: {self.model.get_sentence_embedding_dimension()})")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def encode(self, text: Union[str, List[str]], 
               batch_size: int = 32,
               show_progress: bool = False) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings for text
        
        Args:
            text: Single text or list of texts
            batch_size: Batch size for encoding
            show_progress: Show progress bar
            
        Returns:
            Single embedding or list of embeddings
        """
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
            logger.error(f"Encoding error: {e}")
            return [] if isinstance(text, list) else []
    
    async def generate_embedding(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Асинхронная обертка для совместимости с остальным кодом (orchestrator).
        """
        return self.encode(text)
    
    def encode_code(self, code: str) -> List[float]:
        """
        Encode BSL code for vector search
        
        Preprocessing:
        - Remove comments
        - Normalize whitespace
        - Keep only meaningful code
        """
        # Simple preprocessing
        lines = []
        for line in code.split('\n'):
            line = line.strip()
            # Skip empty lines and comments
            if line and not line.startswith('//'):
                lines.append(line)
        
        clean_code = ' '.join(lines)
        
        # Limit length
        if len(clean_code) > 5000:
            clean_code = clean_code[:5000]
        
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







