"""
Extreme Performance Optimization
Advanced caching, query optimization, response streaming
"""

import asyncio
from typing import Dict, Any, List, AsyncIterator
from functools import lru_cache
import hashlib
import json
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class ExtremePerformanceOptimizer:
    """
    Extreme performance optimizations
    
    Features:
    - Multi-layer caching
    - Query result caching
    - Response streaming
    - Connection pooling optimization
    - Background pre-warming
    """
    
    def __init__(self):
        self.query_cache: Dict[str, Any] = {}
        self.cache_hits = 0
        self.cache_misses = 0
    
    # ===== Smart Caching =====
    
    def cache_key(self, query: str, params: tuple) -> str:
        """Generate cache key from query and params"""
        key_str = f"{query}:{params}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    async def cached_query(
        self,
        conn,
        query: str,
        *params,
        ttl_seconds: int = 300
    ) -> List[Dict]:
        """
        Execute query with caching
        
        Args:
            conn: Database connection
            query: SQL query
            params: Query parameters
            ttl_seconds: Cache TTL
            
        Returns:
            Query results (from cache or database)
        """
        cache_key = self.cache_key(query, params)
        
        # Check cache
        if cache_key in self.query_cache:
            cached_data, cached_at = self.query_cache[cache_key]
            
            # Check if still valid
            age = (datetime.now() - cached_at).total_seconds()
            if age < ttl_seconds:
                self.cache_hits += 1
                logger.debug(
                    "Cache HIT for query",
                    extra={"age_seconds": round(age, 1)}
                )
                return cached_data
        
        # Cache miss - execute query
        self.cache_misses += 1
        logger.debug("Cache MISS - executing query")
        
        result = await conn.fetch(query, *params)
        result_dicts = [dict(row) for row in result]
        
        # Store in cache
        self.query_cache[cache_key] = (result_dicts, datetime.now())
        
        return result_dicts
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get caching statistics"""
        total = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total * 100) if total > 0 else 0
        
        return {
            'cache_size': len(self.query_cache),
            'hits': self.cache_hits,
            'misses': self.cache_misses,
            'hit_rate': round(hit_rate, 2)
        }
    
    # ===== Response Streaming =====
    
    async def stream_large_response(
        self,
        data_generator: AsyncIterator[Dict]
    ) -> AsyncIterator[str]:
        """
        Stream large responses as JSON lines
        
        Better than loading everything into memory
        """
        yield "["
        first = True
        
        async for item in data_generator:
            if not first:
                yield ","
            yield json.dumps(item)
            first = False
        
        yield "]"
    
    # ===== Query Optimization =====
    
    def optimize_query(self, query: str) -> str:
        """
        Optimize SQL query
        
        Applies common optimization patterns
        """
        optimized = query
        
        # Optimization 1: Add LIMIT if missing
        if 'LIMIT' not in optimized.upper() and 'SELECT' in optimized.upper():
            optimized += '\nLIMIT 1000  -- Added for safety'
        
        # Optimization 2: Suggest indexes
        if 'WHERE' in optimized.upper() and 'INDEX' not in optimized.upper():
            # Extract WHERE conditions
            import re
            where_cols = re.findall(r'WHERE\s+(\w+)', optimized, re.IGNORECASE)
            if where_cols:
                logger.info(
                    "Suggest index",
                    extra={"columns": where_cols}
                )
        
        return optimized
    
    # ===== Background Pre-warming =====
    
    async def pre_warm_caches(self, conn):
        """
        Pre-warm caches with commonly accessed data
        
        Runs in background to improve response times
        """
        logger.info("Pre-warming caches...")
        
        try:
            # Common queries to pre-cache
            common_queries = [
                ("SELECT COUNT(*) FROM tenants WHERE active = true", ()),
                ("SELECT COUNT(*) FROM users", ()),
                ("SELECT COUNT(*) FROM projects WHERE status = 'active'", ()),
            ]
            
            for query, params in common_queries:
                await self.cached_query(conn, query, *params, ttl_seconds=600)
            
            logger.info(
                "Pre-warmed cache entries",
                extra={"entries_count": len(common_queries)}
            )
            
        except Exception as e:
            logger.error(
                "Cache pre-warming error",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
    
    # ===== Connection Pool Tuning =====
    
    def calculate_optimal_pool_size(
        self,
        cpu_count: int,
        expected_concurrent_requests: int
    ) -> Dict[str, int]:
        """
        Calculate optimal database pool size
        
        Formula: connections = ((cpu_count * 2) + effective_spindle_count)
        For cloud: connections = cpu_count * 2 to 4
        
        Args:
            cpu_count: Number of CPU cores
            expected_concurrent_requests: Expected concurrent requests
            
        Returns:
            Dict with min and max pool size
        """
        # Conservative formula
        min_size = max(5, cpu_count)
        max_size = min(50, cpu_count * 4)
        
        # Adjust for expected load
        if expected_concurrent_requests > 100:
            max_size = min(100, cpu_count * 6)
        
        return {
            'min_size': min_size,
            'max_size': max_size,
            'recommended': 'Start conservative, scale based on metrics'
        }
    
    # ===== Request Deduplication =====
    
    async def deduplicate_requests(
        self,
        request_id: str,
        executor_func,
        *args,
        **kwargs
    ) -> Any:
        """
        Deduplicate identical in-flight requests
        
        If same request is already processing, wait for it
        instead of executing again
        """
        # TODO: Implement with asyncio locks per request_id
        return await executor_func(*args, **kwargs)


# Global instance
performance_optimizer = ExtremePerformanceOptimizer()


# Helper: Batch database operations
async def batch_database_inserts(
    conn,
    table: str,
    records: List[Dict[str, Any]],
    batch_size: int = 1000
):
    """
    Insert records in batches for better performance
    
    Args:
        conn: Database connection
        table: Table name
        records: List of records to insert
        batch_size: Batch size (default 1000)
    """
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        
        # Build multi-row INSERT
        if not batch:
            continue
        
        columns = list(batch[0].keys())
        placeholders = ', '.join([
            f"({', '.join([f'${j + 1 + i * len(columns)}' for j in range(len(columns))])})"
            for i in range(len(batch))
        ])
        
        values = []
        for record in batch:
            values.extend([record[col] for col in columns])
        
        query = f"""
            INSERT INTO {table} ({', '.join(columns)})
            VALUES {placeholders}
        """
        
        await conn.execute(query, *values)
    
    logger.info(
        "Batch inserted records",
        extra={
            "records_count": len(records),
            "table": table
        }
    )


