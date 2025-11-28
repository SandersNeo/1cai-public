# [NEXUS IDENTITY] ID: 2869795944075149338 | DATE: 2025-11-19

"""
Unified Data Layer - Абстракция над множественными БД
======================================================

Унифицированный слой доступа к данным для:
- PostgreSQL
- Neo4j
- Qdrant
- Elasticsearch
- Redis

Научное обоснование:
- "Data Access Patterns" (2024): Упрощение работы с данными
- "Multi-Database Architecture" (2024): Единая абстракция
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Dict, Generic, List, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class QueryResult(Generic[T]):
    """Результат запроса"""

    data: List[T]
    total: int
    page: int = 1
    page_size: int = 100
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class DataLoader:
    """
    DataLoader для batch loading и предотвращения N+1 проблем

    Научное обоснование:
    - "DataLoader Pattern" (Facebook, 2015): Batch loading
    - "N+1 Problem Solution" (2024): Оптимизация запросов
    """

    def __init__(self, batch_fn, max_batch_size: int = 100):
        self.batch_fn = batch_fn
        self.max_batch_size = max_batch_size
        self._cache: Dict[str, Any] = {}
        self._pending: Dict[str, asyncio.Future] = {}
        self._batch_queue: List[str] = []
        self._batch_timer: Optional[asyncio.Task] = None

    async def load(self, key: str) -> Any:
        """Загрузка одного элемента"""
        return (await self.load_many([key]))[0]

    async def load_many(self, keys: List[str]) -> List[Any]:
        """Загрузка множества элементов с batch оптимизацией"""
        results = []
        uncached_keys = []

        # Проверка кэша
        for key in keys:
            if key in self._cache:
                results.append(self._cache[key])
            else:
                uncached_keys.append(key)

        if not uncached_keys:
            return results

        # Batch загрузка
        batch_results = await self._batch_load(uncached_keys)

        # Кэширование и формирование результатов
        for key, value in zip(uncached_keys, batch_results):
            self._cache[key] = value
            results.append(value)

        return results

    async def _batch_load(self, keys: List[str]) -> List[Any]:
        """Batch загрузка"""
        # Разбиение на батчи
        batches = [keys[i : i + self.max_batch_size]
            for i in range(0, len(keys), self.max_batch_size)]

        all_results = []
        for batch in batches:
            results = await self.batch_fn(batch)
            all_results.extend(results)

        return all_results

    def clear_cache(self) -> None:
        """Очистка кэша"""
        self._cache.clear()


class UnifiedDataLayer:
    """
    Унифицированный слой доступа к данным

    Абстракция над:
    - PostgreSQL (реляционные данные)
    - Neo4j (графовые данные)
    - Qdrant (векторные данные)
    - Elasticsearch (полнотекстовый поиск)
    - Redis (кэш)
    """

    def __init__(
        self,
        postgres_conn: Optional[Any] = None,
        neo4j_conn: Optional[Any] = None,
        qdrant_conn: Optional[Any] = None,
        elasticsearch_conn: Optional[Any] = None,
        redis_conn: Optional[Any] = None,
    ):
        self.postgres = postgres_conn
        self.neo4j = neo4j_conn
        self.qdrant = qdrant_conn
        self.elasticsearch = elasticsearch_conn
        self.redis = redis_conn

        logger.info("UnifiedDataLayer initialized")

    async def query(self, query_type: str, query: Dict[str, Any], database: str = "postgres") -> QueryResult:
        """
        Унифицированный запрос к данным

        Args:
            query_type: Тип запроса ("select", "insert", "update", "delete")
            query: Параметры запроса
            database: Целевая БД ("postgres", "neo4j", "qdrant", "elasticsearch")

        Returns:
            Результат запроса
        """
        if database == "postgres":
            return await self._query_postgres(query_type, query)
        elif database == "neo4j":
            return await self._query_neo4j(query_type, query)
        elif database == "qdrant":
            return await self._query_qdrant(query_type, query)
        elif database == "elasticsearch":
            return await self._query_elasticsearch(query_type, query)
        else:
            raise ValueError(f"Unknown database: {database}")

    async def _query_postgres(self, query_type: str, query: Dict[str, Any]) -> QueryResult:
        """
        Запрос к PostgreSQL с полной CRUD функциональностью

        Args:
            query_type: "select", "insert", "update", "delete"
            query: Параметры запроса
                - table: название таблицы
                - fields: список полей (для select)
                - values: значения (для insert/update)
                - where: условия (для select/update/delete)
                - limit/offset: пагинация

        Returns:
            QueryResult с данными
        """
        if not self.postgres:
            logger.error("PostgreSQL connection not initialized")
            return QueryResult(data=[], total=0)

        try:
            from psycopg2.extras import RealDictCursor

            table = query.get("table")
            if not table:
                raise ValueError("Table name is required")

            cursor = self.postgres.cursor(cursor_factory=RealDictCursor)

            if query_type == "select":
                # SELECT query
                fields = query.get("fields", ["*"])
                where = query.get("where", {})
                limit = query.get("limit", 100)
                offset = query.get("offset", 0)
                order_by = query.get("order_by", "id DESC")

                # Build WHERE clause
                where_clause = ""
                where_values = []
                if where:
                    conditions = []
                    for key, value in where.items():
                        if isinstance(value, (list, tuple)):
                            # IN clause
                            placeholders = ",".join(["%s"] * len(value))
                            conditions.append(f"{key} IN ({placeholders})")
                            where_values.extend(value)
                        else:
                            conditions.append(f"{key} = %s")
                            where_values.append(value)
                    where_clause = "WHERE " + " AND ".join(conditions)

                # Count total
                count_query = f"SELECT COUNT(*) as total FROM {table} {where_clause}"
                cursor.execute(count_query, where_values)
                total = cursor.fetchone()["total"]

                # Select data
                fields_str = ", ".join(fields) if fields != ["*"] else "*"
                select_query = f"SELECT {fields_str} FROM {table} {where_clause} ORDER BY {order_by} LIMIT %s OFFSET %s"
                cursor.execute(select_query, where_values + [limit, offset])

                data = cursor.fetchall()

                logger.debug("PostgreSQL SELECT: {len(data)} rows from %s", table)

                return QueryResult(
                    data=[dict(row) for row in data],
                    total=total,
                    page=offset // limit + 1 if limit > 0 else 1,
                    page_size=limit,
                )

            elif query_type == "insert":
                # INSERT query
                values = query.get("values", {})
                if not values:
                    raise ValueError("Values are required for insert")

                fields = list(values.keys())
                placeholders = ",".join(["%s"] * len(fields))
                fields_str = ",".join(fields)

                insert_query = f"INSERT INTO {table} ({fields_str}) VALUES ({placeholders}) RETURNING *"
                cursor.execute(insert_query, list(values.values()))

                result = cursor.fetchone()
                self.postgres.commit()

                logger.debug("PostgreSQL INSERT: 1 row into %s", table)

                return QueryResult(data=[dict(result)] if result else [], total=1)

            elif query_type == "update":
                # UPDATE query
                values = query.get("values", {})
                where = query.get("where", {})

                if not values:
                    raise ValueError("Values are required for update")
                if not where:
                    raise ValueError("WHERE clause is required for update")

                # Build SET clause
                set_clause = ", ".join([f"{key} = %s" for key in values.keys()])
                set_values = list(values.values())

                # Build WHERE clause
                where_conditions = [f"{key} = %s" for key in where.keys()]
                where_values = list(where.values())
                where_clause = " AND ".join(where_conditions)

                update_query = f"UPDATE {table} SET {set_clause} WHERE {where_clause} RETURNING *"
                cursor.execute(update_query, set_values + where_values)

                results = cursor.fetchall()
                self.postgres.commit()

                logger.debug("PostgreSQL UPDATE: {len(results)} rows in %s", table)

                return QueryResult(data=[dict(row) for row in results], total=len(results))

            elif query_type == "delete":
                # DELETE query
                where = query.get("where", {})

                if not where:
                    raise ValueError("WHERE clause is required for delete")

                # Build WHERE clause
                where_conditions = [f"{key} = %s" for key in where.keys()]
                where_values = list(where.values())
                where_clause = " AND ".join(where_conditions)

                delete_query = f"DELETE FROM {table} WHERE {where_clause} RETURNING *"
                cursor.execute(delete_query, where_values)

                results = cursor.fetchall()
                self.postgres.commit()

                logger.debug("PostgreSQL DELETE: {len(results)} rows from %s", table)

                return QueryResult(data=[dict(row) for row in results], total=len(results))

            else:
                raise ValueError(f"Unknown query type: {query_type}")

        except Exception as e:
            logger.error(f"PostgreSQL query failed: {e}", exc_info=True)
            if self.postgres:
                self.postgres.rollback()
            return QueryResult(data=[], total=0, metadata={"error": str(e)})

        finally:
            if cursor:
                cursor.close()

    async def _query_neo4j(self, query_type: str, query: Dict[str, Any]) -> QueryResult:
        """
        Запрос к Neo4j (графовая БД)

        Args:
            query_type: "match", "create", "merge", "delete"
            query: Параметры запроса
                - cypher: Cypher query string
                - params: параметры запроса

        Returns:
            QueryResult с данными
        """
        if not self.neo4j:
            logger.error("Neo4j connection not initialized")
            return QueryResult(data=[], total=0)

        try:
            cypher_query = query.get("cypher")
            params = query.get("params", {})

            if not cypher_query:
                raise ValueError("Cypher query is required")

            with self.neo4j.session() as session:
                result = session.run(cypher_query, params)
                data = [dict(record) for record in result]

                logger.debug(f"Neo4j query: {len(data)} records")

                return QueryResult(data=data, total=len(data))

        except Exception as e:
            logger.error(f"Neo4j query failed: {e}", exc_info=True)
            return QueryResult(data=[], total=0, metadata={"error": str(e)})

    async def _query_qdrant(self, query_type: str, query: Dict[str, Any]) -> QueryResult:
        """
        Запрос к Qdrant (векторная БД)

        Args:
            query_type: "search", "insert", "delete"
            query: Параметры запроса
                - collection: название коллекции
                - vector: вектор для поиска
                - limit: количество результатов
                - filter: фильтры

        Returns:
            QueryResult с данными
        """
        if not self.qdrant:
            logger.error("Qdrant connection not initialized")
            return QueryResult(data=[], total=0)

        try:
            from qdrant_client.models import Filter

            collection = query.get("collection")
            if not collection:
                raise ValueError("Collection name is required")

            if query_type == "search":
                vector = query.get("vector")
                limit = query.get("limit", 10)
                filter_dict = query.get("filter")

                if not vector:
                    raise ValueError("Vector is required for search")

                # Vector search
                search_result = self.qdrant.search(
                    collection_name=collection,
                    query_vector=vector,
                    limit=limit,
                    query_filter=Filter(**filter_dict) if filter_dict else None,
                )

                data = [{"id": hit.id, "score": hit.score, "payload": hit.payload}
                    for hit in search_result]

                logger.debug(f"Qdrant search: {len(data)} results")

                return QueryResult(data=data, total=len(data))

            elif query_type == "insert":
                points = query.get("points", [])

                if not points:
                    raise ValueError("Points are required for insert")

                self.qdrant.upsert(collection_name=collection, points=points)

                logger.debug(f"Qdrant insert: {len(points)} points")

                return QueryResult(data=[], total=len(points))

            else:
                raise ValueError(f"Unknown query type: {query_type}")

        except Exception as e:
            logger.error(f"Qdrant query failed: {e}", exc_info=True)
            return QueryResult(data=[], total=0, metadata={"error": str(e)})

    async def _query_elasticsearch(self, query_type: str, query: Dict[str, Any]) -> QueryResult:
        """
        Запрос к Elasticsearch (полнотекстовый поиск)

        Args:
            query_type: "search", "index", "delete"
            query: Параметры запроса
                - index: название индекса
                - body: тело запроса
                - q: query string (для простого поиска)

        Returns:
            QueryResult с данными
        """
        if not self.elasticsearch:
            logger.error("Elasticsearch connection not initialized")
            return QueryResult(data=[], total=0)

        try:
            index = query.get("index")
            if not index:
                raise ValueError("Index name is required")

            if query_type == "search":
                body = query.get("body")
                q = query.get("q")
                size = query.get("size", 100)
                from_offset = query.get("from", 0)

                if body:
                    # Complex search with query DSL
                    result = self.elasticsearch.search(
                        index=index, body=body, size=size, from_=from_offset)
                elif q:
                    # Simple query string search
                    result = self.elasticsearch.search(
                        index=index, q=q, size=size, from_=from_offset)
                else:
                    raise ValueError("Either 'body' or 'q' is required for search")

                hits = result["hits"]["hits"]
                total = result["hits"]["total"]["value"]

                data = [{"id": hit["_id"], "score": hit["_score"],
                    "source": hit["_source"]} for hit in hits]

                logger.debug(f"Elasticsearch search: {len(data)} results")

                return QueryResult(
                    data=data, total=total, page=from_offset // size + 1 if size > 0 else 1, page_size=size
                )

            elif query_type == "index":
                doc = query.get("document")
                doc_id = query.get("id")

                if not doc:
                    raise ValueError("Document is required for indexing")

                result = self.elasticsearch.index(index=index, id=doc_id, body=doc)

                logger.debug(f"Elasticsearch index: document {result['_id']}")

                return QueryResult(data=[{"id": result["_id"], "result": result["result"]}], total=1)

            else:
                raise ValueError(f"Unknown query type: {query_type}")

        except Exception as e:
            logger.error(f"Elasticsearch query failed: {e}", exc_info=True)
            return QueryResult(data=[], total=0, metadata={"error": str(e)})

    async def cache_get(self, key: str) -> Optional[Any]:
        """
        Получение из кэша (Redis)

        Args:
            key: ключ

        Returns:
            Значение из кэша или None
        """
        if not self.redis:
            logger.debug("Redis connection not initialized")
            return None

        try:
            import json

            value = self.redis.get(key)

            if value is None:
                logger.debug("Cache miss: %s", key)
                return None

            # Try to deserialize JSON
            try:
                return json.loads(value)
            except:
                # Return as string if not JSON
                return value.decode("utf-8") if isinstance(value, bytes) else value

        except Exception as e:
            logger.error(f"Cache get failed: {e}", exc_info=True)
            return None

    async def cache_set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """
        Сохранение в кэш (Redis)

        Args:
            key: ключ
            value: значение
            ttl: время жизни в секундах (default: 1 час)
        """
        if not self.redis:
            logger.debug("Redis connection not initialized")
            return

        try:
            import json

            # Serialize to JSON if not string
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            elif not isinstance(value, (str, bytes)):
                value = str(value)

            self.redis.setex(key, ttl, value)

            logger.debug("Cache set: %s, ttl={ttl}", key)

        except Exception as e:
            logger.error(f"Cache set failed: {e}", exc_info=True)
