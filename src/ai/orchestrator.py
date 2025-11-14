"""
AI Orchestrator - Intelligent routing of queries to AI services
Версия: 2.1.0

Улучшения:
- Structured logging
- Улучшена обработка ошибок
- Input validation
"""

import re
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

from fastapi import FastAPI, HTTPException
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


app = FastAPI(title="AI Orchestrator API")


class QueryType(Enum):
    """Types of queries"""
    STANDARD_1C = "standard_1c"
    GRAPH_QUERY = "graph_query"
    CODE_GENERATION = "code_generation"
    SEMANTIC_SEARCH = "semantic_search"
    ARCHITECTURE = "architecture"
    OPTIMIZATION = "optimization"
    UNKNOWN = "unknown"


class AIService(Enum):
    """Available AI services"""
    EXTERNAL_AI = "external_ai"
    QWEN_CODER = "qwen_coder"
    NEO4J = "neo4j"
    QDRANT = "qdrant"
    GIGACHAT = "gigachat"
    OPENAI = "openai"
    NAPARNIK = "naparnik"
    KIMI_K2 = "kimi_k2"  # Kimi-K2-Thinking for complex reasoning and tool orchestration


@dataclass
class QueryIntent:
    """Query intent analysis result"""
    query_type: QueryType
    confidence: float
    keywords: List[str]
    context_type: Optional[str]
    preferred_services: List[AIService]


class QueryClassifier:
    """Classifies user queries to determine routing"""
    
    # Classification rules
    RULES = {
        QueryType.STANDARD_1C: {
            'keywords': [
                'типовая', 'типовой', 'стандартн',
                'в УТ', 'в ERP', 'в ЗУП', 'в БУХ',
                'как сделано', 'как реализовано'
            ],
            'patterns': [
                r'как\s+(сделано|реализовано)\s+в\s+(УТ|ERP|ЗУП|БУХ)',
                r'типов(ая|ой|ое|ые)\s+',
                r'стандартн(ый|ая|ое|ые)\s+'
            ],
            'services': [AIService.NAPARNIK, AIService.EXTERNAL_AI, AIService.QWEN_CODER]
        },
        
        QueryType.UNKNOWN: {
            'keywords': [],
            'patterns': [],
            'services': [AIService.NAPARNIK]
        },
        
        QueryType.GRAPH_QUERY: {
            'keywords': [
                'зависимости', 'связи', 'где используется',
                'кто вызывает', 'граф', 'иерархия',
                'найди все связи'
            ],
            'patterns': [
                r'где\s+использу(ется|ют|ется)',
                r'кто\s+вызывает',
                r'найди\s+(все\s+)?(связи|зависимости)',
                r'граф\s+вызовов'
            ],
            'services': [AIService.NEO4J]
        },
        
        QueryType.CODE_GENERATION: {
            'keywords': [
                'создай', 'напиши', 'сгенерируй',
                'добавь', 'реализуй', 'функция',
                'процедура', 'метод'
            ],
            'patterns': [
                r'(создай|напиши|сгенерируй)\s+(функци|процедур)',
                r'реализуй\s+',
                r'добавь\s+(функци|процедур|метод)'
            ],
            'services': [AIService.QWEN_CODER, AIService.EXTERNAL_AI]
        },
        
        QueryType.SEMANTIC_SEARCH: {
            'keywords': [
                'похожий', 'похожая', 'подобн',
                'аналогичный', 'есть ли',
                'найди код'
            ],
            'patterns': [
                r'найди\s+похож',
                r'есть\s+ли\s+(похож|аналог)',
                r'покажи\s+(похож|аналог)'
            ],
            'services': [AIService.QDRANT, AIService.NEO4J]
        },
        
        QueryType.OPTIMIZATION: {
            'keywords': [
                'оптимизируй', 'ускорь', 'улучш',
                'рефакторинг', 'производительность'
            ],
            'patterns': [
                r'(оптимизируй|улучш|ускор)',
                r'рефакторинг',
                r'как\s+улучшить'
            ],
            'services': [AIService.QWEN_CODER, AIService.NEO4J]
        }
    }
    
    def classify(self, query: str, context: Dict[str, Any] = None) -> QueryIntent:
        """
        Classify query with input validation
        
        Args:
            query: User query string
            context: Optional context dictionary
        
        Returns:
            QueryIntent with classification result
        """
        # Input validation
        if not query or not isinstance(query, str):
            logger.warning(
                "Invalid query in classify",
                extra={"query_type": type(query).__name__ if query else None}
            )
            # Return default intent for invalid query
            return QueryIntent(
                query_type=QueryType.UNKNOWN,
                confidence=0.0,
                keywords=[],
                context_type=None,
                preferred_services=[AIService.NAPARNIK]
            )
        
        # Validate query length
        max_query_length = 10000
        if len(query) > max_query_length:
            logger.warning(
                "Query too long in classify",
                extra={"query_length": len(query), "max_length": max_query_length}
            )
            query = query[:max_query_length]  # Truncate
        
        if context is None:
            context = {}
        elif not isinstance(context, dict):
            logger.warning(
                "Invalid context type in classify",
                extra={"context_type": type(context).__name__}
            )
            context = {}
        
        query_lower = query.lower()
        scores: Dict[QueryType, float] = {}
        matched_keywords: List[str] = []
        
        # Score each query type
        for query_type, rules in self.RULES.items():
            score = 0.0
            
            # Check keywords
            for keyword in rules['keywords']:
                if keyword.lower() in query_lower:
                    score += 1.0
                    matched_keywords.append(keyword)
            
            # Check patterns
            for pattern in rules['patterns']:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    score += 2.0
            
            scores[query_type] = score
        
        # Determine best match
        if scores:
            best_type = max(scores, key=scores.get)
            confidence = min(scores[best_type] / 5.0, 1.0)  # Normalize to 0-1
        else:
            best_type = QueryType.UNKNOWN
            confidence = 0.0
        
        # Get preferred services
        preferred_services = []
        if best_type != QueryType.UNKNOWN:
            preferred_services = self.RULES[best_type]['services']
        else:
            preferred_services = self.RULES.get(QueryType.UNKNOWN, {}).get('services', [])
        
        return QueryIntent(
            query_type=best_type,
            confidence=confidence,
            keywords=matched_keywords,
            context_type=context.get('type') if context else None,
            preferred_services=preferred_services
        )


class AIOrchestrator:
    """Main AI orchestrator - routes queries to appropriate services"""
    
    def __init__(self):
        self.classifier = QueryClassifier()
        self.clients = {}
        self.cache = {}  # Simple in-memory cache
        
        # Initialize Qwen client
        try:
            from src.ai.qwen_client import QwenCoderClient
            self.qwen_client = QwenCoderClient()
            logger.info("✓ Qwen3-Coder client initialized")
        except Exception as e:
            logger.warning(
                "Qwen client not available",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            self.qwen_client = None
    
    def register_client(self, service: AIService, client: Any):
        """Register AI service client"""
        self.clients[service] = client
        logger.info(
            "Registered client",
            extra={"service": service.value}
        )
    
    async def process_query(self, 
                          query: str, 
                          context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process query and return response
        
        Args:
            query: User query string
            context: Optional context dictionary
        
        Returns:
            Response dictionary with results
        """
        # Input validation
        if not query or not isinstance(query, str):
            logger.warning(
                f"Invalid query provided: {query}",
                extra={"query_type": type(query).__name__}
            )
            raise ValueError("Query must be a non-empty string")
        
        # Validate query length (prevent DoS)
        max_query_length = 10000  # 10KB max
        if len(query) > max_query_length:
            logger.warning(
                f"Query too long: {len(query)} characters",
                extra={"query_length": len(query), "max_length": max_query_length}
            )
            raise ValueError(f"Query too long. Maximum length: {max_query_length} characters")
        
        if context is None:
            context = {}
        elif not isinstance(context, dict):
            logger.warning(
                f"Invalid context type: {type(context)}",
                extra={"context_type": type(context).__name__}
            )
            context = {}
        
        try:
            # Check cache
            cache_key = f"{query}:{context}"
            if cache_key in self.cache:
                logger.info(
                    "Cache hit",
                    extra={"query_length": len(query)}
                )
                return self.cache[cache_key]
            
            # Classify query
            intent = self.classifier.classify(query, context)
            
            logger.info(
                f"Query classified: {intent.query_type.value}",
                extra={
                    "query_type": intent.query_type.value,
                    "confidence": intent.confidence,
                    "preferred_services": [s.value for s in intent.preferred_services],
                    "query_length": len(query)
                }
            )
            
            # Route to appropriate service(s)
            if intent.query_type == QueryType.GRAPH_QUERY:
                response = await self._handle_graph_query(query, context)
            
            elif intent.query_type == QueryType.SEMANTIC_SEARCH:
                response = await self._handle_semantic_search(query, context)
            
            elif intent.query_type == QueryType.CODE_GENERATION:
                response = await self._handle_code_generation(query, context)
            
            elif intent.query_type == QueryType.OPTIMIZATION:
                response = await self._handle_optimization(query, context)
            
            else:
                # Default: use multiple services and combine
                response = await self._handle_multi_service(query, intent, context)
            
            # Cache result
            self.cache[cache_key] = response
            
            logger.debug(
                "Query processed successfully",
                extra={
                    "query_type": intent.query_type.value,
                    "response_type": response.get("type", "unknown")
                }
            )
            
            return response
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(
                f"Error processing query: {e}",
                extra={
                    "query_length": len(query),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            return {
                "type": "error",
                "error": str(e),
                "query": query[:100]  # Truncate for safety
            }
    
    async def _handle_graph_query(self, query: str, context: Dict) -> Dict:
        """
        Handle graph database queries
        Converts natural language to Cypher and executes on Neo4j
        """
        try:
            # Convert NL to Cypher
            from src.ai.nl_to_cypher import get_nl_to_cypher_converter
            
            converter = get_nl_to_cypher_converter()
            cypher_result = converter.convert(query)
            
            # Validate cypher is safe
            if not converter.validate_cypher(cypher_result['cypher']):
                logger.warning(
                    "Unsafe Cypher query detected",
                    extra={"cypher_preview": cypher_result['cypher'][:100]}
                )
                return {
                    "type": "graph_query",
                    "error": "Unsafe query detected. Only read operations allowed.",
                    "service": "neo4j"
                }
            
            logger.info(
                "Generated Cypher query",
                extra={
                    "cypher_length": len(cypher_result['cypher']),
                    "confidence": cypher_result.get('confidence', 0.0)
                }
            )
            
            # Execute on Neo4j (if available)
            try:
                from src.db.neo4j_client import Neo4jClient
                
                neo4j_client = Neo4jClient()
                results = await asyncio.to_thread(
                    neo4j_client.execute_query,
                    cypher_result['cypher']
                )
                
                logger.info(
                    "Graph query executed successfully",
                    extra={
                        "results_count": len(results) if results else 0,
                        "service": "neo4j"
                    }
                )
                
                return {
                    "type": "graph_query",
                    "service": "neo4j",
                    "cypher": cypher_result['cypher'],
                    "confidence": cypher_result['confidence'],
                    "results": results,
                    "count": len(results) if results else 0,
                    "explanation": cypher_result['explanation']
                }
                
            except ImportError:
                logger.warning(
                    "Neo4j client not available",
                    extra={"service": "neo4j"}
                )
                return {
                    "type": "graph_query",
                    "service": "neo4j",
                    "cypher": cypher_result['cypher'],
                    "confidence": cypher_result['confidence'],
                    "message": "Neo4j not configured. Cypher generated but not executed.",
                    "explanation": cypher_result['explanation']
                }
            
        except Exception as e:
            logger.error(
                "Error in graph query",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            return {
                "type": "graph_query",
                "error": str(e),
                "service": "neo4j"
            }
    
    async def _handle_semantic_search(self, query: str, context: Dict) -> Dict:
        """
        Handle semantic code search using Qdrant vector database
        Generates embedding and finds similar code snippets
        """
        try:
            # Generate embedding for the query
            from src.services.embedding_service import EmbeddingService
            
            embedding_service = EmbeddingService()
            query_embedding = await embedding_service.generate_embedding(query)
            
            logger.info(
                "Generated embedding for query",
                extra={"embedding_dimension": len(query_embedding)}
            )
            
            # Search in Qdrant
            try:
                from src.db.qdrant_client import QdrantClient
                
                qdrant_client = QdrantClient()
                
                # Search for similar code
                search_results = await asyncio.to_thread(
                    qdrant_client.search,
                    collection_name="code_snippets",
                    query_vector=query_embedding,
                    limit=context.get('limit', 10)
                )
                
                # Format results
                formatted_results = []
                for result in search_results:
                    formatted_results.append({
                        "code": result.payload.get('code', ''),
                        "function_name": result.payload.get('function_name', 'Unknown'),
                        "module": result.payload.get('module', 'Unknown'),
                        "score": float(result.score),
                        "description": result.payload.get('description', '')
                    })
                
                logger.info(
                    "Found similar code snippets",
                    extra={"results_count": len(formatted_results)}
                )
                
                return {
                    "type": "semantic_search",
                    "service": "qdrant",
                    "query": query,
                    "results": formatted_results,
                    "count": len(formatted_results),
                    "explanation": f"Found {len(formatted_results)} code snippets similar to your query"
                }
                
            except ImportError:
                logger.warning("Qdrant client not available")
                return {
                    "type": "semantic_search",
                    "service": "qdrant",
                    "message": "Qdrant not configured. Install and configure Qdrant for semantic search.",
                    "query": query
                }
            
        except Exception as e:
            logger.error(
                "Error in semantic search",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            return {
                "type": "semantic_search",
                "error": str(e),
                "service": "qdrant"
            }
    
    async def _handle_code_generation(self, query: str, context: Dict) -> Dict:
        """Handle code generation requests"""
        if not self.qwen_client:
            return {
                "type": "code_generation",
                "service": "qwen_coder",
                "error": "Qwen3-Coder not available. Start Ollama with: ollama pull qwen2.5-coder:7b"
            }
        
        try:
            # Extract function details from query if present
            function_name = context.get('function_name')
            parameters = context.get('parameters', [])
            
            if function_name:
                # Generate specific function
                result = await self.qwen_client.generate_function(
                    description=query,
                    function_name=function_name,
                    parameters=parameters
                )
            else:
                # General code generation
                result = await self.qwen_client.generate_code(
                    prompt=query,
                    context=context
                )
            
            return {
                "type": "code_generation",
                "service": "qwen_coder",
                "code": result.get('code'),
                "full_response": result.get('full_response'),
                "model": result.get('model')
            }
            
        except Exception as e:
            logger.error(
                "Code generation error",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            return {
                "type": "code_generation",
                "service": "qwen_coder",
                "error": str(e)
            }
    
    async def _handle_optimization(self, query: str, context: Dict) -> Dict:
        """Handle code optimization requests"""
        if not self.qwen_client:
            return {
                "type": "optimization",
                "error": "Qwen3-Coder not available"
            }
        
        try:
            code = context.get('code')
            if not code:
                return {
                    "type": "optimization",
                    "error": "No code provided in context"
                }
            
            # TODO: Get dependencies from Neo4j if available
            dependencies = None
            if AIService.NEO4J in self.clients:
                # Get function dependencies
                pass
            
            # Optimize with Qwen3-Coder
            result = await self.qwen_client.optimize_code(
                code=code,
                context={'dependencies': dependencies}
            )
            
            return {
                "type": "optimization",
                "services": ["qwen_coder"],
                "original_code": code,
                "optimized_code": result.get('optimized_code'),
                "explanation": result.get('explanation'),
                "improvements": result.get('improvements'),
                "model": result.get('model')
            }
            
        except Exception as e:
            logger.error(
                "Optimization error",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            return {
                "type": "optimization",
                "error": str(e)
            }
    
    async def _handle_multi_service(self, query: str, 
                                    intent: QueryIntent, 
                                    context: Dict) -> Dict:
        """
        Handle query using multiple services IN PARALLEL!
        
        Executes all required services simultaneously for better performance
        """
        try:
            # Prepare async tasks based on preferred services
            tasks = []
            service_names = []
            combined_results: Dict[str, Dict[str, Any]] = {}
            
            for service in intent.preferred_services:
                if service == AIService.NEO4J and hasattr(self, "query_neo4j_async"):
                    tasks.append(self.query_neo4j_async(query, context))
                    service_names.append("neo4j")
                elif service == AIService.QDRANT and hasattr(self, "query_qdrant_async"):
                    tasks.append(self.query_qdrant_async(query, context))
                    service_names.append("qdrant")
                elif service == AIService.QWEN_CODER and hasattr(self, "query_qwen"):
                    tasks.append(asyncio.to_thread(self.query_qwen, query, context))
                    service_names.append("qwen_coder")
                else:
                    combined_results[service.value] = {
                        "status": "skipped",
                        "message": "handler not available in offline mode"
                    }
            
            if not tasks:
                return {
                    "type": "multi_service",
                    "execution": "parallel",
                    "services_called": service_names,
                    "successful": 0,
                    "failed": 0,
                    "execution_time_seconds": 0.0,
                    "response": "No handlers executed",
                    "detailed_results": combined_results or {
                        "naparnik": {
                            "status": "success",
                            "result": "Консультация: используйте готовые регламенты и best practices 1C.",
                        }
                    },
                }
            
            # Execute ALL services in PARALLEL!
            logger.info(
                "Executing services in parallel",
                extra={
                    "services_count": len(tasks),
                    "service_names": service_names
                }
            )
            start_time = asyncio.get_event_loop().time()
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            execution_time = asyncio.get_event_loop().time() - start_time
            logger.info(
                "Parallel execution completed",
                extra={"execution_time_seconds": round(execution_time, 3)}
            )
            
            # Combine results
            successful_count = 0
            
            for service_name, result in zip(service_names, results):
                if isinstance(result, Exception):
                    combined_results[service_name] = {
                        "error": str(result),
                        "status": "failed"
                    }
                    logger.warning(
                        "Service failed",
                        extra={
                            "service_name": service_name,
                            "error": str(result),
                            "error_type": type(result).__name__
                        }
                    )
                else:
                    combined_results[service_name] = {
                        **result,
                        "status": "success"
                    }
                    successful_count += 1
            
            # Build response
            response_parts = []
            for service_name, result in combined_results.items():
                if result.get("status") == "success":
                    response_parts.append(f"[{service_name}]: {result.get('result', 'N/A')}")
            
            return {
                "type": "multi_service",
                "execution": "parallel",
                "services_called": service_names,
                "successful": successful_count,
                "failed": len(tasks) - successful_count,
                "execution_time_seconds": round(execution_time, 3),
                "response": "\n".join(response_parts) if response_parts else "No successful results",
                "detailed_results": combined_results
            }
            
        except Exception as e:
            logger.error(
                "Error in parallel multi-service query",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            return {
                "type": "multi_service",
                "error": str(e),
                "services": [s.value for s in intent.preferred_services]
            }


# Orchestrator endpoints
orchestrator = AIOrchestrator()

@app.post("/api/ai/query")
async def ai_query(query: str, context: Optional[Dict] = None):
    """Main AI query endpoint"""
    try:
        response = await orchestrator.process_query(query, context or {})
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

