# [NEXUS IDENTITY] ID: 2718359716558184855 | DATE: 2025-11-19

"""
Модуль HTTP кэширования с ETag для FastAPI сервера.

Реализует многоуровневое HTTP кэширование согласно стандартам RFC 7234:
- ETagManager - генерация и валидация ETag
- HTTPCacheMiddleware - middleware для FastAPI
- CacheHeaders - управление Cache-Control заголовками
- ConditionalGET - обработка If-None-Match запросов
- HTTP 304 Not Modified ответы
- Метрики производительности кэша

Основан на стандартах из docs/1c_caching_standards.md и архитектуре из 
docs/1c_mcp_structure/1c_mcp_code_structure_analysis.md
"""

import hashlib
import hmac
import json
import logging
import time
import weakref
from collections import deque
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from fastapi import Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Настройка логирования
logger = logging.getLogger(__name__)

# Context variable для передачи информации о кэше между middleware
cache_context: ContextVar[Dict[str, Any]] = field(default_factory=dict)


@dataclass
class CacheMetrics:
    """Метрики производительности кэша."""
    hits: int = 0
    misses: int = 0
    conditional_requests: int = 0
    not_modified_responses: int = 0
    cache_puts: int = 0
    cache_deletes: int = 0
    avg_cache_time: float = 0.0
    total_requests: int = 0
    
    def hit_ratio(self) -> float:
        """Вычисляет коэффициент попаданий."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def conditional_ratio(self) -> float:
        """Вычисляет долю условных запросов."""
        total = self.total_requests
        return self.conditional_requests / total if total > 0 else 0.0
    
    def not_modified_ratio(self) -> float:
        """Вычисляет долю ответов 304."""
        total = self.total_requests
        return self.not_modified_responses / total if total > 0 else 0.0


@dataclass
class CacheEntry:
    """Запись в кэше."""
    content: Any
    etag: str
    last_modified: str
    cache_control: str
    expires: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    headers: Dict[str, str] = field(default_factory=dict)
    size: int = 0
    
    def is_expired(self, now: float) -> bool:
        """Проверяет, истек ли срок действия записи."""
        if not self.expires:
            return False
        
        try:
            expires_time = datetime.fromisoformat(self.expires.replace('Z', '+00:00')).timestamp()
            return now > expires_time
        except Exception:
            return False
    
    def is_fresh(self, max_age: int = 3600) -> bool:
        """Проверяет, является ли запись свежей."""
        now = time.time()
        age = now - self.timestamp
        return age < max_age


class ETagManager:
    """
    Менеджер для генерации и валидации ETag.
    
    Реализует согласно RFC 7234:
    - Сильные валидаторы (ETag) для точного определения изменений
    - Временные метки Last-Modified как слабые валидаторы
    - Поддержка различных типов контента (JSON, текст, бинарные данные)
    """
    
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or "default_cache_secret_key"
        self._etag_cache: weakref.WeakValueDictionary = weakref.WeakValueDictionary()
    
    def generate_etag(self, content: Any, content_type: str = "application/json") -> str:
        """
        Генерирует ETag для контента.
        
        Args:
            content: Контент для которого генерируется ETag
            content_type: MIME тип контента
            
        Returns:
            ETag строка в формате "W/\"hash\""
        """
        try:
            # Для разных типов контента используем разные подходы
            if content_type == "application/json":
                content_str = json.dumps(content, sort_keys=True, ensure_ascii=False)
                content_bytes = content_str.encode('utf-8')
            elif isinstance(content, str):
                content_bytes = content.encode('utf-8')
            elif isinstance(content, bytes):
                content_bytes = content
            else:
                content_str = str(content)
                content_bytes = content_str.encode('utf-8')
            
            # Генерируем хеш
            content_hash = hashlib.sha256(content_bytes).hexdigest()
            
            # Добавляем подпись для безопасности
            signature = hmac.new(
                self.secret_key.encode('utf-8'), 
                content_hash.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()[:16]
            
            etag = f'W/"{content_hash[:16]}.{signature}"'
            
            logger.debug(f"Generated ETag {etag} for content type {content_type}")
            return etag
            
        except Exception as e:
            logger.error(f"Error generating ETag: {e}")
            # Фолбэк: используем timestamp как слабый ETag
            fallback_etag = f'W/"{int(time.time())}.fallback"'
            return fallback_etag
    
    def validate_etag(self, etag: str, content: Any, content_type: str = "application/json") -> bool:
        """
        Валидирует ETag против контента.
        
        Args:
            etag: ETag для проверки
            content: Контент для валидации
            content_type: MIME тип контента
            
        Returns:
            True если ETag соответствует контенту
        """
        try:
            if not etag.startswith('W/"') or not etag.endswith('"'):
                return False
            
            current_etag = self.generate_etag(content, content_type)
            return etag == current_etag
            
        except Exception as e:
            logger.error(f"Error validating ETag: {e}")
            return False
    
    def parse_etag(self, etag: str) -> Optional[Tuple[str, str]]:
        """
        Парсит ETag на компоненты.
        
        Returns:
            Кортеж (hash, signature) или None при ошибке
        """
        try:
            if not etag.startswith('W/"') or not etag.endswith('"'):
                return None
            
            etag_content = etag[3:-1]  # Убираем W/" и "
            
            # Проверяем наличие точки разделителя
            if '.' not in etag_content:
                return etag_content, ""
            
            parts = etag_content.rsplit('.', 1)
            return parts[0], parts[1]
            
        except Exception:
            return None


class CacheHeaders:
    """
    Класс для управления Cache-Control заголовками.
    
    Реализует директивы согласно стандартам:
    - no-cache/no-store/private/public/max-age/s-maxage
    - stale-while-revalidate/stale-if-error для отказоустойчивости
    - immutable для статических ресурсов
    """
    
    @staticmethod
    def create_cache_control(
        public: bool = True,
        private: bool = False,
        max_age: Optional[int] = None,
        s_maxage: Optional[int] = None,
        no_cache: bool = False,
        no_store: bool = False,
        immutable: bool = False,
        stale_while_revalidate: Optional[int] = None,
        stale_if_error: Optional[int] = None
    ) -> str:
        """
        Создает значение заголовка Cache-Control.
        
        Args:
            public: Разрешает кэширование в общих кэшах
            private: Только приватный кэш браузера
            max_age: TTL в секундах для браузера
            s_maxage: TTL в секундах для общих кэшей
            no_cache: Кэшировать с обязательной валидацией
            no_store: Полностью запретить кэширование
            immutable: Ресурс не меняется при свежести
            stale_while_revalidate: Отдать устаревший при валидации
            stale_if_error: Отдать устаревший при ошибке
            
        Returns:
            Строка для заголовка Cache-Control
        """
        directives = []
        
        if no_store:
            directives.append("no-store")
            # no-store перекрывает все остальные директивы
            return ", ".join(directives)
        
        # Определяем область кэширования
        if public:
            directives.append("public")
        elif private:
            directives.append("private")
        
        # Определяем политику кэширования
        if no_cache:
            directives.append("no-cache")
        
        if max_age is not None:
            directives.append(f"max-age={max_age}")
        
        if s_maxage is not None:
            directives.append(f"s-maxage={s_maxage}")
        
        if immutable:
            directives.append("immutable")
        
        if stale_while_revalidate is not None:
            directives.append(f"stale-while-revalidate={stale_while_revalidate}")
        
        if stale_if_error is not None:
            directives.append(f"stale-if-error={stale_if_error}")
        
        return ", ".join(directives)
    
    @staticmethod
    def create_expires_header(max_age: int) -> str:
        """
        Создает заголовок Expires.
        
        Args:
            max_age: TTL в секундах
            
        Returns:
            HTTP дата в формате RFC 7234
        """
        expires_time = datetime.utcnow() + timedelta(seconds=max_age)
        return expires_time.strftime("%a, %d %b %Y %H:%M:%S GMT")
    
    @staticmethod
    def create_last_modified_header() -> str:
        """
        Создает заголовок Last-Modified.
        
        Returns:
            HTTP дата последнего изменения
        """
        return datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    
    @staticmethod
    def create_age_header(content_age: int = 0) -> str:
        """
        Создает заголовок Age.
        
        Args:
            content_age: Возраст контента в секундах
            
        Returns:
            Строка с возрастом контента
        """
        return str(max(0, content_age))
    
    @staticmethod
    def parse_cache_control(cache_control: str) -> Dict[str, Any]:
        """
        Парсит заголовок Cache-Control.
        
        Args:
            cache_control: Строка Cache-Control
            
        Returns:
            Словарь с распарсенными директивами
        """
        directives = {}
        
        try:
            parts = cache_control.split(",")
            for part in parts:
                part = part.strip()
                if "=" in part:
                    key, value = part.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Обрабатываем числовые значения
                    if value.isdigit():
                        directives[key] = int(value)
                    else:
                        directives[key] = value
                else:
                    # Булевы директивы
                    directives[part.strip()] = True
            
            return directives
            
        except Exception as e:
            logger.warning(f"Error parsing Cache-Control header: {e}")
            return {}


class ConditionalGET:
    """
    Обработчик условных HTTP запросов согласно RFC 7232.
    
    Поддерживает:
    - If-None-Match для ETag валидации
    - If-Modified-Since для Last-Modified валидации
    - Генерация 304 Not Modified ответов
    """
    
    def __init__(self, etag_manager: ETagManager):
        self.etag_manager = etag_manager
    
    def check_if_none_match(self, client_etag: str, server_etag: str) -> bool:
        """
        Проверяет If-None-Match заголовок.
        
        Args:
            client_etag: ETag из заголовка If-None-Match
            server_etag: Текущий ETag сервера
            
        Returns:
            True если контент не изменился
        """
        try:
            # Поддерживаем список ETags
            if client_etag.startswith('"') and client_etag.endswith('"'):
                # Один ETag
                return client_etag == server_etag
            elif client_etag.startswith('*'):
                # Любой ETag
                return True
            else:
                # Список ETags
                client_etags = [etag.strip() for etag in client_etag.split(",")]
                return server_etag in client_etags
                
        except Exception as e:
            logger.error(f"Error checking If-None-Match: {e}")
            return False
    
    def check_if_modified_since(
        self, 
        if_modified_since: str, 
        last_modified: str
    ) -> bool:
        """
        Проверяет If-Modified-Since заголовок.
        
        Args:
            if_modified_since: Дата из заголовка If-Modified-Since
            last_modified: Последнее изменение ресурса
            
        Returns:
            True если контент не изменился
        """
        try:
            client_time = datetime.fromisoformat(
                if_modified_since.replace('Z', '+00:00')
            )
            server_time = datetime.fromisoformat(
                last_modified.replace('Z', '+00:00')
            )
            
            return server_time <= client_time
            
        except Exception:
            # Если парсинг не удался, валидация не прошла
            return False
    
    def should_return_304(
        self,
        request: Request,
        etag: str,
        last_modified: str
    ) -> Tuple[bool, Dict[str, str]]:
        """
        Определяет нужно ли вернуть 304 Not Modified.
        
        Args:
            request: HTTP запрос
            etag: ETag контента
            last_modified: Время последнего изменения
            
        Returns:
            Кортеж (нужен_304, дополнительные_заголовки)
        """
        needs_304 = False
        additional_headers = {}
        
        try:
            # Проверяем If-None-Match (приоритет у ETag)
            if_none_match = request.headers.get("If-None-Match")
            if if_none_match:
                if self.check_if_none_match(if_none_match, etag):
                    needs_304 = True
                    additional_headers["ETag"] = etag
                    logger.debug(f"Conditional GET: ETag match, returning 304")
            
            # Если ETag не указано, проверяем If-Modified-Since
            elif if_none_match is None:
                if_modified_since = request.headers.get("If-Modified-Since")
                if if_modified_since:
                    if self.check_if_modified_since(if_modified_since, last_modified):
                        needs_304 = True
                        additional_headers["Last-Modified"] = last_modified
                        logger.debug(f"Conditional GET: Last-Modified match, returning 304")
            
            return needs_304, additional_headers
            
        except Exception as e:
            logger.error(f"Error in conditional GET check: {e}")
            return needs_304, additional_headers
    
    def create_304_response(
        self,
        original_headers: Dict[str, str],
        additional_headers: Dict[str, str] = None
    ) -> Response:
        """
        Создает 304 Not Modified ответ.
        
        Args:
            original_headers: Исходные заголовки ответа
            additional_headers: Дополнительные заголовки для 304
            
        Returns:
            Response с кодом 304
        """
        # Копируем важные заголовки для 304
        headers_304 = {}
        
        for header_name, header_value in original_headers.items():
            header_name_lower = header_name.lower()
            
            # Заголовки, которые разрешены в 304 согласно RFC 7234
            if header_name_lower in [
                "cache-control", "content-location", "date", "etag",
                "expires", "last-modified", "server", "vary"
            ]:
                headers_304[header_name] = header_value
        
        # Добавляем дополнительные заголовки
        if additional_headers:
            headers_304.update(additional_headers)
        
        logger.debug(f"Creating 304 response with headers: {headers_304}")
        return Response(status_code=304, headers=headers_304)


class HTTPCacheMiddleware(BaseHTTPMiddleware):
    """
    Middleware для HTTP кэширования в FastAPI.
    
    Особенности:
    - Автоматическое добавление ETag и Cache-Control
    - Поддержка условных запросов
    - Словарь в памяти для кэширования ответов
    - Метрики производительности
    """
    
    def __init__(
        self,
        app: ASGIApp,
        etag_manager: Optional[ETagManager] = None,
        cache_ttl: int = 3600,  # 1 час по умолчанию
        max_cache_size: int = 1000,
        cache_key_func: Optional[Callable[[Request], str]] = None,
        excluded_paths: Set[str] = None
    ):
        super().__init__(app)
        
        self.etag_manager = etag_manager or ETagManager()
        self.cache_ttl = cache_ttl
        self.max_cache_size = max_cache_size
        self.cache_key_func = cache_key_func or self._default_cache_key
        self.excluded_paths = excluded_paths or set()
        
        # Кэш в памяти
        self._cache: Dict[str, CacheEntry] = {}
        self._cache_order = deque()  # Для LRU очистки
        
        # Метрики
        self.metrics = CacheMetrics()
        
        # Счетчики для отладки
        self._request_count = 0
        
        logger.info(f"Initialized HTTPCacheMiddleware with TTL={cache_ttl}s, "
                   f"max_size={max_cache_size}")
    
    def _default_cache_key(self, request: Request) -> str:
        """
        Генерирует ключ кэша на основе запроса.
        
        Args:
            request: HTTP запрос
            
        Returns:
            Ключ кэша
        """
        # Включаем в ключ: метод, путь, параметры запроса, заголовки авторизации
        key_parts = [
            request.method,
            str(request.url.path),
            str(request.query_params),
        ]
        
        # Добавляем заголовки, влияющие на контент
        auth_headers = ["authorization", "accept-language", "user-agent"]
        for header in auth_headers:
            if header in request.headers:
                key_parts.append(f"{header}:{request.headers[header]}")
        
        key_str = "|".join(key_parts)
        return hashlib.sha256(key_str.encode()).hexdigest()[:16]
    
    def _should_cache_request(self, request: Request) -> bool:
        """
        Определяет нужно ли кэшировать запрос.
        
        Args:
            request: HTTP запрос
            
        Returns:
            True если запрос нужно кэшировать
        """
        # Не кэшируем для excluded_paths
        if request.url.path in self.excluded_paths:
            return False
        
        # Кэшируем только GET запросы
        if request.method != "GET":
            return False
        
        # Не кэшируем запросы с аутентификацией в общих кэшах
        if "authorization" in request.headers:
            return False
        
        # Не кэшируем запросы с Cache-Control: no-cache
        cache_control = request.headers.get("Cache-Control", "")
        if "no-cache" in cache_control or "no-store" in cache_control:
            return False
        
        return True
    
    def _cleanup_cache(self) -> None:
        """Очищает кэш при превышении лимита (LRU)."""
        while len(self._cache) > self.max_cache_size:
            if not self._cache_order:
                break
            
            # Удаляем самый старый элемент
            oldest_key = self._cache_order.popleft()
            if oldest_key in self._cache:
                del self._cache[oldest_key]
                self.metrics.cache_deletes += 1
        
        # Удаляем истекшие записи
        now = time.time()
        expired_keys = []
        for key, entry in self._cache.items():
            if entry.is_expired(now):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
            self.cache_order.remove(key) if key in self.cache_order else None
            self.metrics.cache_deletes += 1
    
    def _get_cache_entry(self, key: str) -> Optional[CacheEntry]:
        """Получает запись из кэша."""
        if key in self._cache:
            entry = self._cache[key]
            
            # Перемещаем ключ в конец очереди (LRU)
            if key in self._cache_order:
                self._cache_order.remove(key)
            self._cache_order.append(key)
            
            return entry
        
        return None
    
    def _put_cache_entry(self, key: str, entry: CacheEntry) -> None:
        """Сохраняет запись в кэш."""
        self._cache[key] = entry
        self._cache_order.append(key)
        self.metrics.cache_puts += 1
        
        self._cleanup_cache()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Обрабатывает запрос через middleware.
        
        Args:
            request: HTTP запрос
            call_next: Следующий обработчик
            
        Returns:
            HTTP ответ
        """
        self._request_count += 1
        self.metrics.total_requests += 1
        
        start_time = time.time()
        
        try:
            # Сбрасываем контекст кэша
            cache_info = {
                "cache_hit": False,
                "cache_key": None,
                "etag": None,
                "conditional_request": False
            }
            cache_context.set(cache_info)
            
            # Проверяем условный запрос
            if_none_match = request.headers.get("If-None-Match")
            if_modified_since = request.headers.get("If-Modified-Since")
            is_conditional = bool(if_none_match or if_modified_since)
            
            if is_conditional:
                self.metrics.conditional_requests += 1
                cache_info["conditional_request"] = True
            
            # Проверяем можно ли кэшировать
            should_cache = self._should_cache_request(request)
            cache_key = None
            
            if should_cache:
                cache_key = self.cache_key_func(request)
                cache_info["cache_key"] = cache_key
                
                # Ищем в кэше
                cached_entry = self._get_cache_entry(cache_key)
                
                if cached_entry and cached_entry.is_fresh(self.cache_ttl):
                    logger.debug(f"Cache HIT for {cache_key}")
                    self.metrics.hits += 1
                    cache_info["cache_hit"] = True
                    cache_info["etag"] = cached_entry.etag
                    
                    # Проверяем условный запрос
                    if is_conditional:
                        conditional_handler = ConditionalGET(self.etag_manager)
                        needs_304, additional_headers = conditional_handler.should_return_304(
                            request,
                            cached_entry.etag,
                            cached_entry.last_modified
                        )
                        
                        if needs_304:
                            self.metrics.not_modified_responses += 1
                            cache_info["not_modified"] = True
                            
                            # Создаем 304 ответ
                            response_304 = conditional_handler.create_304_response(
                                cached_entry.headers,
                                additional_headers
                            )
                            return response_304
                    
                    # Возвращаем кэшированный ответ
                    response_headers = cached_entry.headers.copy()
                    response_headers.update({
                        "ETag": cached_entry.etag,
                        "Cache-Control": cached_entry.cache_control,
                        "Last-Modified": cached_entry.last_modified,
                        "X-Cache": "HIT"
                    })
                    
                    # Добавляем информацию о возрасте
                    age = int(time.time() - cached_entry.timestamp)
                    response_headers["Age"] = str(age)
                    
                    # Восстанавливаем тип контента из заголовков
                    media_type = response_headers.get("content-type", "application/json")
                    
                    if isinstance(cached_entry.content, dict):
                        return JSONResponse(
                            content=cached_entry.content,
                            headers=response_headers,
                            media_type=media_type
                        )
                    else:
                        return PlainTextResponse(
                            content=str(cached_entry.content),
                            headers=response_headers,
                            media_type=media_type
                        )
                
                else:
                    # Cache miss
                    logger.debug(f"Cache MISS for {cache_key}")
                    self.metrics.misses += 1
            
            # Обрабатываем запрос
            response = await call_next(request)
            
            # Обновляем метрики времени
            process_time = time.time() - start_time
            self.metrics.avg_cache_time = (
                (self.metrics.avg_cache_time * (self._request_count - 1) + process_time) 
                / self._request_count
            )
            
            # Кэшируем ответ если нужно
            if should_cache and cache_key and response.status_code == 200:
                try:
                    # Извлекаем контент
                    if isinstance(response, JSONResponse):
                        content = response.body.decode('utf-8')
                        content_data = json.loads(content)
                        content_type = response.media_type or "application/json"
                    else:
                        content = response.body.decode('utf-8')
                        content_data = content
                        content_type = response.media_type or "text/plain"
                    
                    # Генерируем ETag
                    etag = self.etag_manager.generate_etag(content_data, content_type)
                    cache_info["etag"] = etag
                    
                    # Создаем заголовки кэша
                    cache_control = CacheHeaders.create_cache_control(
                        public=True,
                        max_age=self.cache_ttl,
                        s_maxage=self.cache_ttl // 2,
                        stale_while_revalidate=60,
                        stale_if_error=300
                    )
                    
                    last_modified = CacheHeaders.create_last_modified_header()
                    expires = CacheHeaders.create_expires_header(self.cache_ttl)
                    
                    # Добавляем заголовки к ответу
                    response.headers.update({
                        "ETag": etag,
                        "Cache-Control": cache_control,
                        "Last-Modified": last_modified,
                        "Expires": expires,
                        "X-Cache": "MISS"
                    })
                    
                    # Сохраняем в кэш
                    cache_entry = CacheEntry(
                        content=content_data,
                        etag=etag,
                        last_modified=last_modified,
                        cache_control=cache_control,
                        expires=expires,
                        headers=dict(response.headers),
                        size=len(content.encode('utf-8'))
                    )
                    
                    self._put_cache_entry(cache_key, cache_entry)
                    
                except Exception as e:
                    logger.warning(f"Failed to cache response: {e}")
            
            # Добавляем информацию о кэше в заголовки
            if not should_cache:
                response.headers["X-Cache"] = "BYPASS"
            elif cache_info.get("cache_hit"):
                response.headers["X-Cache"] = "HIT"
            else:
                response.headers["X-Cache"] = "MISS"
            
            # Добавляем информацию о метриках в отладочном заголовке
            if logger.isEnabledFor(logging.DEBUG):
                metrics_info = {
                    "hit_ratio": f"{self.metrics.hit_ratio():.2%}",
                    "avg_time": f"{self.metrics.avg_cache_time:.3f}s"
                }
                response.headers["X-Cache-Metrics"] = json.dumps(metrics_info)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in HTTPCacheMiddleware: {e}")
            return await call_next(request)


class CacheMetricsCollector:
    """
    Сборщик и экспортер метрик кэширования.
    
    Функции:
    - Сбор метрик из middleware
    - Экспорт в Prometheus формате
    - Логирование статистики
    """
    
    def __init__(self):
        self.middlewares: List[HTTPCacheMiddleware] = []
    
    def register_middleware(self, middleware: HTTPCacheMiddleware) -> None:
        """Регистрирует middleware для сбора метрик."""
        self.middlewares.append(middleware)
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Возвращает сводку метрик по всем middleware.
        
        Returns:
            Словарь с метриками
        """
        total_metrics = CacheMetrics()
        
        for middleware in self.middlewares:
            m = middleware.metrics
            total_metrics.hits += m.hits
            total_metrics.misses += m.misses
            total_metrics.conditional_requests += m.conditional_requests
            total_metrics.not_modified_responses += m.not_modified_responses
            total_metrics.cache_puts += m.cache_puts
            total_metrics.cache_deletes += m.cache_deletes
            total_metrics.total_requests += m.total_requests
            total_metrics.avg_cache_time += m.avg_cache_time
        
        # Усредняем время
        if self.middlewares:
            total_metrics.avg_cache_time /= len(self.middlewares)
        
        return {
            "hits": total_metrics.hits,
            "misses": total_metrics.misses,
            "hit_ratio": total_metrics.hit_ratio(),
            "conditional_requests": total_metrics.conditional_requests,
            "conditional_ratio": total_metrics.conditional_ratio(),
            "not_modified_responses": total_metrics.not_modified_responses,
            "not_modified_ratio": total_metrics.not_modified_ratio(),
            "cache_puts": total_metrics.cache_puts,
            "cache_deletes": total_metrics.cache_deletes,
            "avg_cache_time": total_metrics.avg_cache_time,
            "total_requests": total_metrics.total_requests,
            "active_middlewares": len(self.middlewares)
        }
    
    def export_prometheus(self) -> str:
        """
        Экспортирует метрики в формате Prometheus.
        
        Returns:
            Метрики в формате Prometheus text format
        """
        summary = self.get_summary()
        
        lines = [
            "# HELP http_cache_hits_total Total cache hits",
            "# TYPE http_cache_hits_total counter",
            f"http_cache_hits_total {summary['hits']}",
            "",
            "# HELP http_cache_misses_total Total cache misses",
            "# TYPE http_cache_misses_total counter",
            f"http_cache_misses_total {summary['misses']}",
            "",
            "# HELP http_cache_hit_ratio Cache hit ratio",
            "# TYPE http_cache_hit_ratio gauge",
            f"http_cache_hit_ratio {summary['hit_ratio']}",
            "",
            "# HELP http_cache_conditional_requests_total Total conditional requests",
            "# TYPE http_cache_conditional_requests_total counter",
            f"http_cache_conditional_requests_total {summary['conditional_requests']}",
            "",
            "# HELP http_cache_not_modified_responses_total Total 304 responses",
            "# TYPE http_cache_not_modified_responses_total counter",
            f"http_cache_not_modified_responses_total {summary['not_modified_responses']}",
            "",
            "# HELP http_cache_avg_time_seconds Average cache processing time",
            "# TYPE http_cache_avg_time_seconds gauge",
            f"http_cache_avg_time_seconds {summary['avg_cache_time']}",
            "",
            "# HELP http_cache_total_requests Total HTTP requests processed",
            "# TYPE http_cache_total_requests counter",
            f"http_cache_total_requests {summary['total_requests']}",
        ]
        
        return "\n".join(lines)
    
    def log_summary(self) -> None:
        """Логирует сводку метрик."""
        summary = self.get_summary()
        
        logger.info("HTTP Cache Metrics Summary:")
        logger.info(f"  Total requests: {summary['total_requests']}")
        logger.info(f"  Cache hits: {summary['hits']}")
        logger.info(f"  Cache misses: {summary['misses']}")
        logger.info(f"  Hit ratio: {summary['hit_ratio']:.2%}")
        logger.info(f"  Conditional requests: {summary['conditional_requests']}")
        logger.info(f"  304 responses: {summary['not_modified_responses']}")
        logger.info(f"  Average cache time: {summary['avg_cache_time']:.3f}s")
        logger.info(f"  Active middlewares: {summary['active_middlewares']}")


# Глобальный сборщик метрик
metrics_collector = CacheMetricsCollector()


def setup_cache_middleware(
    app: FastAPI,
    secret_key: Optional[str] = None,
    cache_ttl: int = 3600,
    max_cache_size: int = 1000,
    excluded_paths: Set[str] = None
) -> HTTPCacheMiddleware:
    """
    Удобная функция для настройки кэширования на FastAPI приложении.
    
    Args:
        app: FastAPI приложение
        secret_key: Секретный ключ для ETag
        cache_ttl: TTL кэша в секундах
        max_cache_size: Максимальный размер кэша
        excluded_paths: Пути для исключения из кэширования
        
    Returns:
        Настроенный middleware
    """

    # Создаем middleware
    middleware = HTTPCacheMiddleware(
        app=app,
        etag_manager=ETagManager(secret_key),
        cache_ttl=cache_ttl,
        max_cache_size=max_cache_size,
        excluded_paths=excluded_paths
    )
    
    # Регистрируем для сбора метрик
    metrics_collector.register_middleware(middleware)
    
    # Добавляем роуты для метрик
    @app.get("/cache/metrics")
    async def get_cache_metrics():
        """Возвращает метрики кэша."""
        return metrics_collector.get_summary()
    
    @app.get("/cache/metrics.prometheus")
    async def get_cache_metrics_prometheus():
        """Возвращает метрики в формате Prometheus."""
        return PlainTextResponse(
            content=metrics_collector.export_prometheus(),
            media_type="text/plain"
        )
    
    logger.info("Cache middleware configured successfully")
    return middleware