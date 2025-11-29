# [NEXUS IDENTITY] ID: 6044785199435457687 | DATE: 2025-11-19

"""
Tool Indexer

Индексирование MCP tools в Qdrant для semantic search
Позволяет агентам находить нужные tools по смыслу запроса
"""

import hashlib
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ToolIndexer:
    """
    Индексация MCP tools в Qdrant для semantic search
    
    Позволяет агентам:
    - Искать tools по semantic query ("1c metadata tools")
    - Загружать только нужные tools (progressive disclosure)
    - Фильтровать по server
    - Получать разные уровни детализации
    
    Usage:
        indexer = ToolIndexer(qdrant_url="http://localhost:6333")
        
        # Проиндексировать tools
        await indexer.index_tools(all_tools)
        
        # Поиск
        results = await indexer.search_tools(
            query="get 1C configuration",
            server="1c",
            limit=5
        )
    """
    
    def __init__(
        self,
        qdrant_url: str = "http://localhost:6333",
        collection_name: str = "mcp_tools",
        embedding_model: str = "text-embedding-ada-002"
    ):
        """
        Args:
            qdrant_url: URL Qdrant server
            collection_name: Имя collection для tools
            embedding_model: Модель для embeddings
        """
        self.qdrant_url = qdrant_url
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        
        # Lazy init (только когда нужно)
        self._client = None
        self._embedding_service = None
    
    @property
    def client(self):
        """Lazy initialization Qdrant client"""
        if self._client is None:
            try:
                from qdrant_client import QdrantClient
                self._client = QdrantClient(url=self.qdrant_url)
                logger.info(f"Connected to Qdrant at {self.qdrant_url}")
            except ImportError:
                logger.error("qdrant-client not installed. Run: pip install qdrant-client")
                raise
            except Exception as e:
                logger.error(f"Failed to connect to Qdrant: {e}")
                raise
        
        return self._client
    
    def _ensure_collection(self):
        """Создать collection если не существует"""
        from qdrant_client.models import Distance, VectorParams
        
        try:
            self.client.get_collection(self.collection_name)
            logger.info(f"Collection '{self.collection_name}' already exists")
        except:
            logger.info(f"Creating collection '{self.collection_name}'...")
            
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=1536,  # OpenAI ada-002 embedding size
                    distance=Distance.COSINE
                )
            )
            
            logger.info(f"✅ Collection '{self.collection_name}' created")
    
    async def index_tools(self, tools: List[Dict[str, Any]]):
        """
        Проиндексировать все tools в Qdrant
        
        Args:
            tools: Список tool definitions
        """
        from qdrant_client.models import PointStruct

        # Ensure collection exists
        self._ensure_collection()
        
        logger.info(f"Indexing {len(tools)} tools...")
        
        points = []
        
        for tool in tools:
            # Создать текстовое описание для embedding
            text = self._tool_to_text(tool)
            
            # Получить embedding
            embedding = await self._get_embedding(text)
            
            # Создать point
            point_id = self._generate_id(tool['name'])
            
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    'name': tool['name'],
                    'server': tool.get('server', 'unknown'),
                    'description': tool.get('description', ''),
                    'input_schema': tool.get('inputSchema', {}),
                    'output_schema': tool.get('outputSchema', {}),
                    'full_definition': tool,
                    'indexed_at': self._get_timestamp(),
                }
            )
            
            points.append(point)
        
        # Batch upload to Qdrant
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        logger.info(f"✅ Indexed {len(tools)} tools in Qdrant")
    
    async def search_tools(
        self,
        query: str,
        server: Optional[str] = None,
        detail_level: str = "name_and_description",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Semantic search для tools
        
        Args:
            query: Поисковый запрос ("get 1C configuration metadata")
            server: Фильтр по server ("1c", "neo4j", etc.)
            detail_level: 
                - "name_only": только имя и server
                - "name_and_description": имя, server, description
                - "full": полное определение tool
            limit: Максимум результатов
        
        Returns:
            Список найденных tools с relevance score
        """
        
        # Получить embedding для query
        query_embedding = await self._get_embedding(query)
        
        # Построить filter
        query_filter = None
        if server:
            from qdrant_client.models import FieldCondition, Filter, MatchValue
            
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="server",
                        match=MatchValue(value=server)
                    )
                ]
            )
        
        # Search в Qdrant
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=limit,
            query_filter=query_filter
        )
        
        # Форматировать результаты по detail_level
        formatted = []
        
        for result in results:
            payload = result.payload
            
            if detail_level == "name_only":
                formatted.append({
                    'name': payload['name'],
                    'server': payload['server'],
                    'score': result.score,
                })
            
            elif detail_level == "name_and_description":
                formatted.append({
                    'name': payload['name'],
                    'server': payload['server'],
                    'description': payload['description'],
                    'score': result.score,
                })
            
            else:  # "full"
                formatted.append({
                    **payload['full_definition'],
                    'score': result.score,
                })
        
        logger.info(
            f"Found {len(formatted)} tools for query '{query}' "
            f"(server: {server or 'all'})"
        )
        
        return formatted
    
    def _tool_to_text(self, tool: Dict[str, Any]) -> str:
        """
        Конвертировать tool definition в текст для embedding
        
        Создаём rich description включая:
        - Name
        - Description
        - Parameters
        - Server
        """
        
        parts = [
            f"Tool: {tool['name']}",
            f"Server: {tool.get('server', 'unknown')}",
            f"Description: {tool.get('description', 'No description')}",
        ]
        
        # Добавить параметры
        input_schema = tool.get('inputSchema', {})
        if 'properties' in input_schema:
            properties = input_schema['properties']
            param_descriptions = []
            
            for param_name, param_schema in properties.items():
                param_desc = param_schema.get('description', param_name)
                param_type = param_schema.get('type', 'any')
                param_descriptions.append(f"{param_name} ({param_type}): {param_desc}")
            
            parts.append("Parameters:\n  " + "\n  ".join(param_descriptions))
        
        return '\n'.join(parts)
    
    async def _get_embedding(self, text: str) -> List[float]:
        """
        Получить embedding для текста
        
        Supports:
        - OpenAI API (text-embedding-ada-002)
        - Local model (sentence-transformers)
        """
        
        if self._embedding_service is None:
            # Попробовать OpenAI
            try:
                self._embedding_service = 'openai'
                logger.info("Using OpenAI for embeddings")
            except ImportError:
                # Fallback на local model
                try:
                    from sentence_transformers import SentenceTransformer
                    self._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                    self._embedding_service = 'local'
                    logger.info("Using local model for embeddings")
                except ImportError:
                    logger.error(
                        "No embedding service available. "
                        "Install: pip install openai OR pip install sentence-transformers"
                    )
                    raise
        
        # Get embedding
        if self._embedding_service == 'openai':
            return await self._get_openai_embedding(text)
        else:
            return await self._get_local_embedding(text)
    
    async def _get_openai_embedding(self, text: str) -> List[float]:
        """Получить embedding через OpenAI API"""
        import openai
        
        response = await openai.Embedding.acreate(
            model=self.embedding_model,
            input=text
        )
        
        return response['data'][0]['embedding']
    
    async def _get_local_embedding(self, text: str) -> List[float]:
        """Получить embedding через local model"""
        embedding = self._embedding_model.encode(text)
        return embedding.tolist()
    
    def _generate_id(self, tool_name: str) -> int:
        """Генерировать numeric ID из имени tool"""
        # MD5 hash → integer
        hash_hex = hashlib.md5(tool_name.encode()).hexdigest()[:8]
        return int(hash_hex, 16)
    
    def _get_timestamp(self) -> str:
        """Получить текущий timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_indexer():
        print("=" * 60)
        print("Тест Tool Indexer")
        print("=" * 60)
        
        # Mock tools
        tools = [
            {
                'name': 'get_configuration',
                'server': '1c',
                'description': 'Получить метаданные конфигурации 1С',
                'inputSchema': {
                    'properties': {
                        'name': {'type': 'string', 'description': 'Имя конфигурации'}
                    }
                }
            },
            {
                'name': 'run_cypher',
                'server': 'neo4j',
                'description': 'Выполнить Cypher запрос в Neo4j',
                'inputSchema': {
                    'properties': {
                        'query': {'type': 'string', 'description': 'Cypher query'}
                    }
                }
            },
            {
                'name': 'search',
                'server': 'qdrant',
                'description': 'Семантический поиск в Qdrant',
                'inputSchema': {
                    'properties': {
                        'query': {'type': 'string', 'description': 'Search query'}
                    }
                }
            }
        ]
        
        # Initialize indexer
        try:
            indexer = ToolIndexer()
            
            print("\n📦 Indexing tools...")
            await indexer.index_tools(tools)
            
            print("\n🔍 Searching tools...")
            
            # Test search
            results = await indexer.search_tools(
                query="get 1C configuration metadata",
                limit=3
            )
            
            print(f"\nFound {len(results)} tools:")
            for i, tool in enumerate(results, 1):
                print(f"{i}. {tool['name']} (server: {tool['server']}, score: {tool['score']:.2f})")
                print(f"   {tool['description']}")
            
            print("\n✅ Test passed!")
            
        except Exception as e:
            print(f"\n⚠️  Test skipped (Qdrant not available): {e}")
            print("   Install: pip install qdrant-client")
            print("   Or start Qdrant: docker run -p 6333:6333 qdrant/qdrant")
    
    asyncio.run(test_indexer())


