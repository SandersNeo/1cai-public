"""PostgreSQL repository for marketplace data with caching and storage helpers."""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

try:
    import asyncpg  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    asyncpg = None  # type: ignore

from redis.asyncio import Redis

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:  # pragma: no cover
    boto3 = None  # type: ignore

if asyncpg is not None:  # pragma: no branch
    AsyncpgPool = asyncpg.Pool
    AsyncpgRecord = asyncpg.Record
else:  # pragma: no cover
    AsyncpgPool = Any
    AsyncpgRecord = Dict[str, Any]


class MarketplaceRepository:
    """CRUD/access layer for marketplace entities."""

    CACHE_TTL_SECONDS = 300
    FEATURED_CACHE_KEY = "marketplace:featured:{limit}"
    TRENDING_CACHE_KEY = "marketplace:trending:{limit}"
    CATEGORY_CACHE_KEY = "marketplace:category-counts"

    def __init__(
        self,
        pool: AsyncpgPool,
        cache: Optional[Redis] = None,
        storage_config: Optional[Dict[str, str]] = None,
    ) -> None:
        self.pool = pool
        self.cache = cache
        self.storage_config = storage_config or {}
        self._s3_client = None

    async def init(self) -> None:
        if asyncpg is None:
            raise RuntimeError("asyncpg is required for MarketplaceRepository.init")
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS marketplace_plugins (
                    id SERIAL PRIMARY KEY,
                    plugin_id TEXT UNIQUE NOT NULL,
                    owner_id TEXT NOT NULL,
                    owner_username TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT NOT NULL,
                    version TEXT NOT NULL,
                    status TEXT NOT NULL,
                    visibility TEXT NOT NULL,
                    homepage TEXT,
                    repository TEXT,
                    download_url TEXT,
                    icon_url TEXT,
                    changelog TEXT,
                    readme TEXT,
                    artifact_path TEXT,
                    screenshot_urls JSONB DEFAULT '[]',
                    keywords JSONB DEFAULT '[]',
                    license TEXT,
                    min_version TEXT,
                    supported_platforms JSONB DEFAULT '[]',
                    rating NUMERIC DEFAULT 0,
                    ratings_count INT DEFAULT 0,
                    downloads INT DEFAULT 0,
                    installs INT DEFAULT 0,
                    featured BOOLEAN DEFAULT FALSE,
                    verified BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    published_at TIMESTAMPTZ
                );
                """
            )
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS marketplace_reviews (
                    id SERIAL PRIMARY KEY,
                    review_id TEXT UNIQUE NOT NULL,
                    plugin_id TEXT NOT NULL REFERENCES marketplace_plugins(plugin_id) ON DELETE CASCADE,
                    user_id TEXT NOT NULL,
                    user_name TEXT,
                    rating INT NOT NULL,
                    comment TEXT,
                    pros TEXT,
                    cons TEXT,
                    helpful_count INT DEFAULT 0,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                """
            )
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS marketplace_installs (
                    plugin_id TEXT NOT NULL REFERENCES marketplace_plugins(plugin_id) ON DELETE CASCADE,
                    user_id TEXT NOT NULL,
                    installed_at TIMESTAMPTZ DEFAULT NOW(),
                    PRIMARY KEY (plugin_id, user_id)
                );
                """
            )
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS marketplace_favorites (
                    plugin_id TEXT NOT NULL REFERENCES marketplace_plugins(plugin_id) ON DELETE CASCADE,
                    user_id TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    PRIMARY KEY (plugin_id, user_id)
                );
                """
            )
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS marketplace_complaints (
                    id SERIAL PRIMARY KEY,
                    complaint_id TEXT UNIQUE NOT NULL,
                    plugin_id TEXT NOT NULL REFERENCES marketplace_plugins(plugin_id) ON DELETE CASCADE,
                    user_id TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    details TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                """
            )

    async def close(self) -> None:
        if self.cache:
            await self.cache.close()

    async def create_plugin(
        self,
        plugin_id: str,
        owner_id: str,
        owner_username: str,
        payload: Dict[str, Any],
        download_url: str,
    ) -> Dict[str, Any]:
        category_value = payload.get("category")
        if hasattr(category_value, "value"):
            category_value = category_value.value
        visibility_value = payload.get("visibility", "public")
        if hasattr(visibility_value, "value"):
            visibility_value = visibility_value.value

        query = """
            INSERT INTO marketplace_plugins (
                plugin_id,
                owner_id,
                owner_username,
                name,
                description,
                category,
                version,
                status,
                visibility,
                homepage,
                repository,
                download_url,
                icon_url,
                changelog,
                readme,
                artifact_path,
                screenshot_urls,
                keywords,
                license,
                min_version,
                supported_platforms,
                rating,
                ratings_count,
                downloads,
                installs,
                featured,
                verified,
                created_at,
                updated_at,
                published_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13,
                $14, $15, $16, $17, $18, $19, $20, $21, 0, 0, 0, 0, FALSE, FALSE, NOW(), NOW(), NULL
            )
            RETURNING *
        """

        screenshot_urls = payload.get("screenshot_urls", [])
        keywords = payload.get("keywords", [])
        supported_platforms = payload.get("supported_platforms", [])

        values = (
            plugin_id,
            owner_id,
            owner_username,
            payload["name"],
            payload["description"],
            category_value,
            payload["version"],
            payload.get("status", "pending"),
            visibility_value,
            payload.get("homepage"),
            payload.get("repository"),
            download_url,
            payload.get("icon_url"),
            payload.get("changelog"),
            payload.get("readme"),
            payload.get("artifact_path"),
            json.dumps(screenshot_urls),
            json.dumps(keywords),
            payload.get("license"),
            payload.get("min_version"),
            json.dumps(supported_platforms),
        )

        async with self.pool.acquire() as conn:
            record = await conn.fetchrow(query, *values)
        await self._invalidate_caches()
        return self._record_to_plugin(record)

    async def get_plugin(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow(
                "SELECT * FROM marketplace_plugins WHERE plugin_id = $1",
                plugin_id,
            )
        if record:
            return self._record_to_plugin(record)
        return None

    async def update_plugin(self, plugin_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not update_data:
            return await self.get_plugin(plugin_id)

        set_parts: List[str] = ["updated_at = NOW()"]
        values: List[Any] = [plugin_id]
        idx = 1

        for key, value in update_data.items():
            column = self._map_field_to_column(key)
            if column is None:
                continue
            idx += 1
            set_parts.append(f"{column} = ${idx}")
            if key in {"keywords", "supported_platforms", "screenshot_urls"}:
                values.append(json.dumps(value))
            else:
                values.append(value)

        if len(set_parts) == 1:
            return await self.get_plugin(plugin_id)

        query = (
            "UPDATE marketplace_plugins SET "
            + ", ".join(set_parts)
            + " WHERE plugin_id = $1 RETURNING *"
        )

        async with self.pool.acquire() as conn:
            record = await conn.fetchrow(query, *values)
        if record:
            await self._invalidate_caches(plugin_id)
            return self._record_to_plugin(record)
        return None

    async def soft_delete_plugin(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow(
                """
                UPDATE marketplace_plugins
                SET status = 'removed', updated_at = NOW()
                WHERE plugin_id = $1
                RETURNING *
                """,
                plugin_id,
            )
        if record:
            await self._invalidate_caches(plugin_id)
            return self._record_to_plugin(record)
        return None

    async def search_plugins(
        self,
        query_text: Optional[str],
        category: Optional[str],
        author: Optional[str],
        sort_by: str,
        order: str,
        page: int,
        page_size: int,
    ) -> Tuple[List[Dict[str, Any]], int]:
        conditions = ["status = 'approved'", "visibility = 'public'"]
        params: List[Any] = []

        if query_text:
            conditions.append(
                "(LOWER(name) LIKE $1 OR LOWER(description) LIKE $1 OR EXISTS (SELECT 1 FROM jsonb_array_elements_text(keywords) kw WHERE LOWER(kw) LIKE $1))"
            )
            params.append(f"%{query_text.lower()}%")
        if category:
            conditions.append(f"category = ${len(params)+1}")
            params.append(category)
        if author:
            conditions.append(f"owner_username = ${len(params)+1}")
            params.append(author)

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

        order_column = {
            "rating": "rating",
            "downloads": "downloads",
            "updated": "updated_at",
            "name": "name",
        }.get(sort_by, "rating")
        order_value = "DESC" if order.lower() == "desc" else "ASC"

        offset = (page - 1) * page_size

        sql = f"""
            SELECT *, COUNT(*) OVER() AS total_count
            FROM marketplace_plugins
            {where_clause}
            ORDER BY {order_column} {order_value}
            LIMIT $${len(params)+1} OFFSET $${len(params)+2}
        """

        params.extend([page_size, offset])

        async with self.pool.acquire() as conn:
            records = await conn.fetch(sql, *params)

        if not records:
            return [], 0

        total = records[0]["total_count"]
        return [self._record_to_plugin(rec) for rec in records], total

    async def record_install(self, plugin_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                plugin = await conn.fetchrow(
                    "SELECT * FROM marketplace_plugins WHERE plugin_id = $1",
                    plugin_id,
                )
                if not plugin:
                    return None
                await conn.execute(
                    """
                    INSERT INTO marketplace_installs (plugin_id, user_id)
                    VALUES ($1, $2)
                    ON CONFLICT DO NOTHING
                    """,
                    plugin_id,
                    user_id,
                )
                await conn.execute(
                    """
                    UPDATE marketplace_plugins
                    SET downloads = downloads + 1,
                        installs = (SELECT COUNT(*) FROM marketplace_installs WHERE plugin_id = $1),
                        updated_at = NOW()
                    WHERE plugin_id = $1
                    """,
                    plugin_id,
                )
                record = await conn.fetchrow(
                    "SELECT * FROM marketplace_plugins WHERE plugin_id = $1",
                    plugin_id,
                )
        await self._invalidate_caches(plugin_id)
        if record:
            return self._record_to_plugin(record)
        return None

    async def remove_install(self, plugin_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                plugin = await conn.fetchrow(
                    "SELECT * FROM marketplace_plugins WHERE plugin_id = $1",
                    plugin_id,
                )
                if not plugin:
                    return None
                await conn.execute(
                    "DELETE FROM marketplace_installs WHERE plugin_id = $1 AND user_id = $2",
                    plugin_id,
                    user_id,
                )
                await conn.execute(
                    """
                    UPDATE marketplace_plugins
                    SET installs = (SELECT COUNT(*) FROM marketplace_installs WHERE plugin_id = $1),
                        updated_at = NOW()
                    WHERE plugin_id = $1
                    """,
                    plugin_id,
                )
                record = await conn.fetchrow(
                    "SELECT * FROM marketplace_plugins WHERE plugin_id = $1",
                    plugin_id,
                )
        await self._invalidate_caches(plugin_id)
        if record:
            return self._record_to_plugin(record)
        return None

    async def user_has_installed(self, plugin_id: str, user_id: str) -> bool:
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT 1 FROM marketplace_installs WHERE plugin_id = $1 AND user_id = $2",
                plugin_id,
                user_id,
            )
        return result is not None

    async def add_favorite(self, plugin_id: str, user_id: str) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO marketplace_favorites (plugin_id, user_id)
                VALUES ($1, $2)
                ON CONFLICT DO NOTHING
                """,
                plugin_id,
                user_id,
            )
        await self._invalidate_caches(plugin_id)

    async def remove_favorite(self, plugin_id: str, user_id: str) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM marketplace_favorites WHERE plugin_id = $1 AND user_id = $2",
                plugin_id,
                user_id,
            )
        await self._invalidate_caches(plugin_id)

    async def create_review(
        self,
        review_id: str,
        plugin_id: str,
        user_id: str,
        user_name: str,
        payload: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                plugin = await conn.fetchrow(
                    "SELECT * FROM marketplace_plugins WHERE plugin_id = $1",
                    plugin_id,
                )
                if not plugin:
                    return None
                record = await conn.fetchrow(
                    """
                    INSERT INTO marketplace_reviews (
                        review_id, plugin_id, user_id, user_name, rating, comment, pros, cons
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    RETURNING *
                    """,
                    review_id,
                    plugin_id,
                    user_id,
                    user_name,
                    payload["rating"],
                    payload.get("comment"),
                    payload.get("pros"),
                    payload.get("cons"),
                )
                await conn.execute(
                    """
                    UPDATE marketplace_plugins
                    SET rating = sub.avg_rating,
                        ratings_count = sub.total_reviews,
                        updated_at = NOW()
                    FROM (
                        SELECT plugin_id,
                               AVG(rating) AS avg_rating,
                               COUNT(*) AS total_reviews
                        FROM marketplace_reviews
                        WHERE plugin_id = $1
                        GROUP BY plugin_id
                    ) AS sub
                    WHERE marketplace_plugins.plugin_id = sub.plugin_id
                    """,
                    plugin_id,
                )
        await self._invalidate_caches(plugin_id)
        if record:
            return self._record_to_review(record)
        return None

    async def list_reviews(
        self,
        plugin_id: str,
        page: int,
        page_size: int,
    ) -> Tuple[List[Dict[str, Any]], int]:
        offset = (page - 1) * page_size
        async with self.pool.acquire() as conn:
            records = await conn.fetch(
                """
                SELECT *, COUNT(*) OVER() AS total_count
                FROM marketplace_reviews
                WHERE plugin_id = $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
                """,
                plugin_id,
                page_size,
                offset,
            )
        if not records:
            return [], 0
        total = records[0]["total_count"]
        return [self._record_to_review(record) for record in records], total

    async def get_plugin_stats(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            plugin = await conn.fetchrow(
                "SELECT * FROM marketplace_plugins WHERE plugin_id = $1",
                plugin_id,
            )
            if not plugin:
                return None
            reviews_count = await conn.fetchval(
                "SELECT COUNT(*) FROM marketplace_reviews WHERE plugin_id = $1",
                plugin_id,
            )
            rating_distribution_records = await conn.fetch(
                """
                SELECT rating, COUNT(*) AS count
                FROM marketplace_reviews
                WHERE plugin_id = $1
                GROUP BY rating
                """,
                plugin_id,
            )
            rating_distribution = {i: 0 for i in range(1, 6)}
            for rec in rating_distribution_records:
                rating_distribution[rec["rating"]] = rec["count"]
            favorites_count = await conn.fetchval(
                "SELECT COUNT(*) FROM marketplace_favorites WHERE plugin_id = $1",
                plugin_id,
            )
            installs_active = await conn.fetchval(
                "SELECT COUNT(*) FROM marketplace_installs WHERE plugin_id = $1",
                plugin_id,
            )
        stats = {
            "plugin_id": plugin_id,
            "downloads_total": plugin["downloads"],
            "downloads_last_30_days": plugin["downloads"],
            "installs_active": installs_active,
            "rating_average": float(plugin["rating"] or 0),
            "rating_distribution": rating_distribution,
            "reviews_count": reviews_count,
            "favorites_count": favorites_count,
            "downloads_trend": "stable",
            "rating_trend": "stable",
        }
        return stats

    async def get_category_counts(self) -> Dict[str, int]:
        if self.cache:
            cached = await self.cache.get(self.CATEGORY_CACHE_KEY)
            if cached:
                return json.loads(cached)
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT category, COUNT(*) AS count
                FROM marketplace_plugins
                WHERE status = 'approved'
                GROUP BY category
                """
            )
        counts = {row["category"]: row["count"] for row in rows}
        if self.cache:
            await self.cache.set(self.CATEGORY_CACHE_KEY, json.dumps(counts), ex=self.CACHE_TTL_SECONDS)
        return counts

    async def get_featured_plugins(self, limit: int) -> List[Dict[str, Any]]:
        cache_key = self.FEATURED_CACHE_KEY.format(limit=limit)
        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached:
                return json.loads(cached)
        async with self.pool.acquire() as conn:
            records = await conn.fetch(
                """
                SELECT * FROM marketplace_plugins
                WHERE status = 'approved' AND featured = TRUE
                ORDER BY rating DESC, updated_at DESC
                LIMIT $1
                """,
                limit,
            )
        plugins = [self._record_to_plugin(record) for record in records]
        if self.cache:
            await self.cache.set(cache_key, json.dumps(plugins, default=str), ex=self.CACHE_TTL_SECONDS)
        return plugins

    async def get_trending_plugins(self, limit: int) -> List[Dict[str, Any]]:
        cache_key = self.TRENDING_CACHE_KEY.format(limit=limit)
        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached:
                return json.loads(cached)
        async with self.pool.acquire() as conn:
            records = await conn.fetch(
                """
                SELECT * FROM marketplace_plugins
                WHERE status = 'approved' AND visibility = 'public'
                ORDER BY downloads DESC, rating DESC
                LIMIT $1
                """,
                limit,
            )
        plugins = [self._record_to_plugin(record) for record in records]
        if self.cache:
            await self.cache.set(cache_key, json.dumps(plugins, default=str), ex=self.CACHE_TTL_SECONDS)
        return plugins

    async def add_complaint(
        self,
        complaint_id: str,
        plugin_id: str,
        user_id: str,
        reason: str,
        details: Optional[str],
    ) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO marketplace_complaints (complaint_id, plugin_id, user_id, reason, details)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (complaint_id) DO NOTHING
                """,
                complaint_id,
                plugin_id,
                user_id,
                reason,
                details,
            )

    async def refresh_cached_views(self) -> None:
        if not self.cache:
            return
        await self.get_category_counts()  # refresh
        for limit in (5, 10):
            await self.get_featured_plugins(limit)
            await self.get_trending_plugins(limit)

    async def build_download_payload(self, plugin: Dict[str, Any]) -> Dict[str, Any]:
        artifact_path = plugin.get("artifact_path")
        presigned_url: Optional[str] = None
        if artifact_path and self._s3_available:
            try:
                client = self._get_s3_client()
                if client:
                    presigned_url = client.generate_presigned_url(
                        "get_object",
                        Params={
                            "Bucket": self.storage_config["bucket"],
                            "Key": artifact_path,
                        },
                        ExpiresIn=300,
                    )
            except (ClientError, BotoCoreError):  # pragma: no cover
                presigned_url = None
        return {
            "status": "ready",
            "plugin_id": plugin["plugin_id"],
            "download_url": presigned_url or plugin.get("download_url"),
            "message": "Download link generated" if presigned_url else "Download will be implemented in production",
            "files": ["manifest.json", "README.md", "plugin.py"],
        }

    def _record_to_plugin(self, record: AsyncpgRecord) -> Dict[str, Any]:
        screenshot_urls = self._ensure_list(record["screenshot_urls"])
        keywords = self._ensure_list(record["keywords"])
        supported_platforms = self._ensure_list(record["supported_platforms"])

        return {
            "id": record["plugin_id"],
            "plugin_id": record["plugin_id"],
            "name": record["name"],
            "description": record["description"],
            "category": record["category"],
            "version": record["version"],
            "author": record["owner_username"],
            "status": record["status"],
            "visibility": record["visibility"],
            "downloads": record["downloads"],
            "rating": float(record["rating"] or 0),
            "ratings_count": record["ratings_count"],
            "installs": record["installs"],
            "homepage": record["homepage"],
            "repository": record["repository"],
            "download_url": record["download_url"],
            "icon_url": record["icon_url"],
            "changelog": record["changelog"],
            "readme": record["readme"],
            "artifact_path": record["artifact_path"],
            "screenshot_urls": screenshot_urls,
            "keywords": keywords,
            "license": record["license"],
            "min_version": record["min_version"],
            "supported_platforms": supported_platforms,
            "created_at": record["created_at"],
            "updated_at": record["updated_at"],
            "published_at": record["published_at"],
            "featured": record["featured"],
            "verified": record["verified"],
            "owner_id": record["owner_id"],
            "owner_username": record["owner_username"],
        }

    def _record_to_review(self, record: AsyncpgRecord) -> Dict[str, Any]:
        return {
            "id": record["review_id"],
            "plugin_id": record["plugin_id"],
            "user_id": record["user_id"],
            "user_name": record["user_name"],
            "rating": record["rating"],
            "comment": record["comment"],
            "pros": record["pros"],
            "cons": record["cons"],
            "helpful_count": record["helpful_count"],
            "created_at": record["created_at"],
        }

    def _map_field_to_column(self, field: str) -> Optional[str]:
        mapping = {
            "version": "version",
            "description": "description",
            "changelog": "changelog",
            "homepage": "homepage",
            "repository": "repository",
            "keywords": "keywords",
            "icon_url": "icon_url",
            "screenshot_urls": "screenshot_urls",
            "readme": "readme",
            "status": "status",
            "visibility": "visibility",
            "featured": "featured",
            "verified": "verified",
            "published_at": "published_at",
            "artifact_path": "artifact_path",
        }
        return mapping.get(field)

    def _ensure_list(self, value: Any) -> List[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return [value]
        return list(value)

    async def _invalidate_caches(self, plugin_id: Optional[str] = None) -> None:
        if not self.cache:
            return
        keys = [self.CATEGORY_CACHE_KEY]
        for limit in (5, 10):
            keys.append(self.FEATURED_CACHE_KEY.format(limit=limit))
            keys.append(self.TRENDING_CACHE_KEY.format(limit=limit))
        await self.cache.delete(*keys)

    @property
    def _s3_available(self) -> bool:
        has_bucket = bool(self.storage_config.get("bucket"))
        return has_bucket and (boto3 is not None or self._s3_client is not None)

    def _get_s3_client(self):
        if not self._s3_available:
            return None
        if self._s3_client is None:
            session = boto3.session.Session(
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=self.storage_config.get("region"),
            )
            endpoint_url = self.storage_config.get("endpoint")
            self._s3_client = session.client("s3", endpoint_url=endpoint_url)
        return self._s3_client
