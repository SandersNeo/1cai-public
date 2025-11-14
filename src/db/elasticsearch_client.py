"""
Elasticsearch Client for Full-text Search
Версия: 2.1.0

Улучшения:
- Retry logic для подключения
- Structured logging
- Улучшена обработка ошибок
- Input validation
"""

import os
import logging
import asyncio
import time
from typing import Dict, List, Any, Optional

try:
    from elasticsearch import AsyncElasticsearch
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False

from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

if not ELASTICSEARCH_AVAILABLE:
    logger.warning(
        "elasticsearch not installed. Run: pip install elasticsearch",
        extra={"suggestion": "pip install elasticsearch"}
    )


class ElasticsearchClient:
    """Elasticsearch client for full-text search"""
    
    INDEX_CODE = "1c_code"
    INDEX_DOCS = "1c_documentation"
    
    def __init__(self, 
                 host: str = "localhost",
                 port: int = 9200,
                 user: Optional[str] = None,
                 password: Optional[str] = None):
        """Initialize Elasticsearch client"""
        
        if not ELASTICSEARCH_AVAILABLE:
            raise ImportError("elasticsearch not available")
        
        self.host = host
        self.port = port
        self.user = user or os.getenv("ELASTIC_USER")
        self.password = password or os.getenv("ELASTIC_PASSWORD")
        self.client: Optional[AsyncElasticsearch] = None
    
    async def connect(self, max_retries: int = 3, retry_delay: float = 1.0) -> bool:
        """
        Connect to Elasticsearch with retry logic
        
        Args:
            max_retries: Maximum retry attempts
            retry_delay: Base delay for exponential backoff (seconds)
        """
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                if self.user and self.password:
                    self.client = AsyncElasticsearch(
                        [f"http://{self.host}:{self.port}"],
                        basic_auth=(self.user, self.password),
                        request_timeout=10.0
                    )
                else:
                    self.client = AsyncElasticsearch(
                        [f"http://{self.host}:{self.port}"],
                        request_timeout=10.0
                    )
                
                # Test connection with timeout
                info = await asyncio.wait_for(
                    self.client.info(),
                    timeout=5.0
                )
                
                logger.info(
                    f"Connected to Elasticsearch {info['version']['number']}",
                    extra={
                        "host": self.host,
                        "port": self.port,
                        "version": info['version']['number'],
                        "attempt": attempt + 1
                    }
                )
                return True
                
            except asyncio.TimeoutError as e:
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    logger.warning(
                        f"Elasticsearch connection timeout (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s",
                        extra={
                            "host": self.host,
                            "port": self.port,
                            "attempt": attempt + 1,
                            "delay": wait_time
                        }
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(
                        f"Failed to connect to Elasticsearch after {max_retries} attempts: timeout",
                        extra={
                            "host": self.host,
                            "port": self.port,
                            "max_retries": max_retries
                        },
                        exc_info=True
                    )
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    logger.warning(
                        f"Failed to connect to Elasticsearch (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {wait_time}s...",
                        extra={
                            "host": self.host,
                            "port": self.port,
                            "attempt": attempt + 1,
                            "delay": wait_time,
                            "error_type": type(e).__name__
                        }
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(
                        f"Failed to connect to Elasticsearch after {max_retries} attempts: {e}",
                        extra={
                            "host": self.host,
                            "port": self.port,
                            "max_retries": max_retries,
                            "error_type": type(e).__name__
                        },
                        exc_info=True
                    )
        
        return False
    
    async def create_indexes(self):
        """Create indexes with mappings"""
        try:
            # Code index
            if not await self.client.indices.exists(index=self.INDEX_CODE):
                await self.client.indices.create(
                    index=self.INDEX_CODE,
                    body={
                        "settings": {
                            "number_of_shards": 1,
                            "number_of_replicas": 0,
                            "analysis": {
                                "analyzer": {
                                    "bsl_analyzer": {
                                        "type": "standard",
                                        "stopwords": "_russian_"
                                    }
                                }
                            }
                        },
                        "mappings": {
                            "properties": {
                                "code": {
                                    "type": "text",
                                    "analyzer": "bsl_analyzer"
                                },
                                "function_name": {"type": "keyword"},
                                "module_name": {"type": "keyword"},
                                "configuration": {"type": "keyword"},
                                "object_type": {"type": "keyword"},
                                "description": {
                                    "type": "text",
                                    "analyzer": "bsl_analyzer"
                                },
                                "is_exported": {"type": "boolean"},
                                "complexity": {"type": "integer"}
                            }
                        }
                    }
                )
                logger.info(
                    "Created index",
                    extra={"index_name": self.INDEX_CODE}
                )
        
        except Exception as e:
            logger.error(
                "Error creating indexes",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
    
    async def index_code(self, 
                        doc_id: str,
                        code: str,
                        metadata: Dict[str, Any]):
        """Index code for full-text search"""
        try:
            document = {
                'code': code,
                **metadata
            }
            
            await self.client.index(
                index=self.INDEX_CODE,
                id=doc_id,
                document=document
            )
            return True
            
        except Exception as e:
            logger.error(
                "Error indexing code",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "doc_id": doc_id if 'doc_id' in locals() else None
                },
                exc_info=True
            )
            return False
    
    async def search_code(self, 
                         query: str,
                         config_filter: Optional[str] = None,
                         limit: int = 10) -> List[Dict[str, Any]]:
        """Full-text search for code с input validation"""
        # Input validation
        if not query or not isinstance(query, str):
            logger.warning(
                "Invalid query in search_code",
                extra={"query_type": type(query).__name__ if query else None}
            )
            return []
        
        # Validate query length (prevent DoS)
        max_query_length = 5000
        if len(query) > max_query_length:
            logger.warning(
                "Query too long in search_code",
                extra={"query_length": len(query), "max_length": max_query_length}
            )
            query = query[:max_query_length]
        
        # Validate limit
        if not isinstance(limit, int) or limit < 1 or limit > 100:
            logger.warning(
                "Invalid limit in search_code",
                extra={"limit": limit, "limit_type": type(limit).__name__}
            )
            limit = 10  # Default limit
        
        # Validate config_filter
        if config_filter and not isinstance(config_filter, str):
            logger.warning(
                "Invalid config_filter type in search_code",
                extra={"config_filter_type": type(config_filter).__name__}
            )
            config_filter = None
        
        if not self.client:
            logger.warning("Elasticsearch client not connected")
            return []
        
        try:
            # Build query
            must_queries = [
                {
                    "multi_match": {
                        "query": query,
                        "fields": ["code^2", "description", "function_name"],
                        "type": "best_fields"
                    }
                }
            ]
            
            # Add configuration filter
            if config_filter:
                must_queries.append({
                    "term": {"configuration": config_filter}
                })
            
            # Execute search with timeout
            response = await asyncio.wait_for(
                self.client.search(
                    index=self.INDEX_CODE,
                    body={
                        "query": {
                            "bool": {
                                "must": must_queries
                            }
                        },
                        "size": limit,
                        "highlight": {
                            "fields": {
                                "code": {},
                                "description": {}
                            }
                        }
                    }
                ),
                timeout=10.0
            )
            
            # Format results
            results = []
            for hit in response['hits']['hits']:
                results.append({
                    'id': hit['_id'],
                    'score': hit['_score'],
                    'source': hit['_source'],
                    'highlight': hit.get('highlight', {})
                })
            
            logger.debug(
                f"Search completed: {len(results)} results",
                extra={
                    "query_length": len(query),
                    "results_count": len(results),
                    "config_filter": config_filter
                }
            )
            
            return results
            
        except asyncio.TimeoutError:
            logger.error(
                "Search timeout in search_code",
                extra={"query_length": len(query), "timeout": 10.0}
            )
            return []
        except Exception as e:
            logger.error(
                f"Search error: {e}",
                extra={
                    "query_length": len(query),
                    "config_filter": config_filter,
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            return []
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get index statistics"""
        try:
            stats = {}
            
            if await self.client.indices.exists(index=self.INDEX_CODE):
                count = await self.client.count(index=self.INDEX_CODE)
                stats[self.INDEX_CODE] = {
                    'document_count': count['count']
                }
            
            return stats
            
        except Exception as e:
            logger.error(
                "Statistics error",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            return {}
    
    async def close(self):
        """Close connection"""
        if self.client:
            await self.client.close()
            logger.info("Elasticsearch connection closed")







