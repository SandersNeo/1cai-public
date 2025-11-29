# [NEXUS IDENTITY] ID: 8687112711746672089 | DATE: 2025-11-19

"""
MCP Tools Cache - Модуль кэширования результатов MCP tools для 1C MCP сервера

Основан на стандартах кэширования из docs/1c_caching_standards.md и анализе
производительности из docs/1c_mcp_performance/1c_mcp_performance_bottlenecks.md

Ключевые возможности:
- Кэширование результатов MCP tools с TTL стратегиями
- LRU и TTL-based стратегии кэширования
- Механизмы инвалидации кэша
- Persistent cache на диске
- Метрики попаданий/промахов
- Интеграция с mcp_server.py и onec_client.py

Версия: 1.0.0
"""

import asyncio
import hashlib
import json
import logging
import pickle
import time
from abc import ABC, abstractmethod
from collections import OrderedDict
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from threading import RLock
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Union

# Настройка логирования
logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Запись кэша с метаданными"""
    data: Any
    timestamp: float
    ttl: float
    access_count: int = 0
    last_access: float = field(default_factory=time.time)
    size_bytes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_expired(self) -> bool:
        """Проверяет, истёк ли TTL записи"""
        return time.time() - self.timestamp > self.ttl
    
    @property
    def age(self) -> float:
        """Возраст записи в секундах"""
        return time.time() - self.timestamp
    
    def access(self) -> None:
        """Обновляет счётчик доступа при чтении"""
        self.access_count += 1
        self.last_access = time.time()


@dataclass
class CacheMetrics:
    """Метрики кэша"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    errors: int = 0
    total_requests: int = 0
    hit_ratio: float = 0.0
    avg_response_time: float = 0.0
    
    def record_hit(self, response_time: float = 0.0) -> None:
        """Записывает попадание в кэш"""
        self.hits += 1
        self.total_requests += 1
        if self.total_requests > 0:
            self.hit_ratio = self.hits / self.total_requests
    
    def record_miss(self, response_time: float = 0.0) -> None:
        """Записывает промах кэша"""
        self.misses += 1
        self.total_requests += 1
        if self.total_requests > 0:
            self.hit_ratio = self.hits / self.total_requests
    
    def record_eviction(self) -> None:
        """Записывает вытеснение записи"""
        self.evictions += 1
    
    def record_error(self) -> None:
        """Записывает ошибку"""
        self.errors += 1


class CacheStrategy(ABC):
    """Абстрактный базовый класс для стратегий кэширования"""
    
    @abstractmethod
    def should_evict(self, cache: 'MCPToolsCache', key: str, entry: CacheEntry) -> bool:
        """Определяет, нужно ли вытеснить запись"""
    
    @abstractmethod
    def select_eviction_target(self, cache: 'MCPToolsCache') -> Optional[str]:
        """Выбирает запись для вытеснения"""


class LRUStrategy(CacheStrategy):
    """Least Recently Used - вытесняет давно неиспользуемые записи"""
    
    def should_evict(self, cache: 'MCPToolsCache', key: str, entry: CacheEntry) -> bool:
        """Проверяет, нужно ли вытеснить запись по LRU"""
        if not cache._is_full():
            return False
        
        # Если кэш полон, найти самую старую запись
        oldest_key = min(cache._cache.keys(), 
                        key=lambda k: cache._cache[k].last_access)
        return key == oldest_key
    
    def select_eviction_target(self, cache: 'MCPToolsCache') -> Optional[str]:
        """Выбирает запись для вытеснения (самую старуую)"""
        if not cache._cache:
            return None
        
        return min(cache._cache.keys(), 
                  key=lambda k: cache._cache[k].last_access)


class TTLCacheStrategy(CacheStrategy):
    """TTL-based стратегия - вытесняет истёкшие записи"""
    
    def should_evict(self, cache: 'MCPToolsCache', key: str, entry: CacheEntry) -> bool:
        """Проверяет, истёк ли TTL записи"""
        return entry.is_expired
    
    def select_eviction_target(self, cache: 'MCPToolsCache') -> Optional[str]:
        """Выбирает истёкшую запись для вытеснения"""
        expired_keys = [k for k, entry in cache._cache.items() 
                       if entry.is_expired]
        return expired_keys[0] if expired_keys else None


class CacheInvalidation:
    """Механизмы инвалидации кэша"""
    
    def __init__(self):
        self._invalidation_rules: Dict[str, Callable[[str], bool]] = {}
        self._versioned_keys: Dict[str, str] = {}  # key -> version
        self._change_listeners: List[Callable[[str], None]] = []
    
    def add_invalidation_rule(self, pattern: str, rule: Callable[[str], bool]) -> None:
        """
        Добавляет правило инвалидации
        
        Args:
            pattern: Шаблон ключа (например, "metadata:*", "tool:*:config")
            rule: Функция, которая определяет, нужно ли инвалидировать ключ
        """
        self._invalidation_rules[pattern] = rule
    
    def register_change_listener(self, callback: Callable[[str], None]) -> None:
        """Регистрирует слушатель изменений данных"""
        self._change_listeners.append(callback)
    
    def invalidate_by_pattern(self, cache: 'MCPToolsCache', pattern: str) -> int:
        """
        Инвалидирует ключи по шаблону
        
        Args:
            cache: Экземпляр кэша
            pattern: Шаблон ключа
            
        Returns:
            Количество инвалидированных записей
        """
        count = 0
        keys_to_invalidate = []
        
        # Простая реализация с wildcard поддержкой
        pattern_parts = pattern.split('*')
        
        for key in list(cache._cache.keys()):
            if self._matches_pattern(key, pattern, pattern_parts):
                keys_to_invalidate.append(key)
        
        for key in keys_to_invalidate:
            if cache.delete(key):
                count += 1
        
        logger.info(f"Инвалидировано {count} записей по шаблону '{pattern}'")
        return count
    
    def invalidate_by_entity(self, cache: 'MCPToolsCache', entity: str, entity_type: str = 'metadata') -> int:
        """
        Инвалидирует записи, связанные с сущностью
        
        Args:
            cache: Экземпляр кэша
            entity: Идентификатор сущности (например, "Справочник.Номенклатура")
            entity_type: Тип сущности
        """
        pattern = f"{entity_type}:{entity}:*"
        return self.invalidate_by_pattern(cache, pattern)
    
    def invalidate_all(self, cache: 'MCPToolsCache') -> int:
        """Инвалидирует весь кэш"""
        count = len(cache._cache)
        cache.clear()
        
        # Уведомляем слушателей
        for listener in self._change_listeners:
            try:
                listener('all')
            except Exception as e:
                logger.error(f"Ошибка в слушателе изменений: {e}")
        
        logger.info(f"Инвалидирован весь кэш ({count} записей)")
        return count
    
    def _matches_pattern(self, key: str, pattern: str, pattern_parts: List[str]) -> bool:
        """Простая проверка соответствия шаблону с wildcard"""
        if len(pattern_parts) == 1:
            return key == pattern_parts[0]
        
        if not key.startswith(pattern_parts[0]):
            return False
        
        remaining_key = key[len(pattern_parts[0]):]
        remaining_pattern = '*'.join(pattern_parts[1:])
        
        if not remaining_pattern:
            return remaining_key == ''
        
        return remaining_key.endswith(pattern_parts[-1])


class PersistentCache:
    """Persistent cache для долговременного хранения на диске"""
    
    def __init__(self, cache_dir: Union[str, Path], max_size_mb: int = 100):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self._index_file = self.cache_dir / "cache_index.json"
        self._lock = RLock()
        self._load_index()
    
    def store(self, key: str, entry: CacheEntry) -> bool:
        """Сохраняет запись на диск"""
        try:
            with self._lock:
                # Проверяем размер кэша
                if self._get_total_size() + entry.size_bytes > self.max_size_bytes:
                    self._cleanup_oldest()
                
                # Создаём файл для записи
                file_path = self.cache_dir / f"{self._hash_key(key)}.cache"
                
                # Сериализуем данные
                data = {
                    'data': entry.data,
                    'timestamp': entry.timestamp,
                    'ttl': entry.ttl,
                    'access_count': entry.access_count,
                    'last_access': entry.last_access,
                    'size_bytes': entry.size_bytes,
                    'metadata': entry.metadata
                }
                
                with open(file_path, 'wb') as f:
                    pickle.dump(data, f)
                
                # Обновляем индекс
                self._index[key] = {
                    'file': str(file_path),
                    'timestamp': entry.timestamp,
                    'size_bytes': entry.size_bytes
                }
                self._save_index()
                
                return True
                
        except Exception as e:
            logger.error(f"Ошибка при сохранении кэша для ключа {key}: {e}")
            return False
    
    def load(self, key: str) -> Optional[CacheEntry]:
        """Загружает запись с диска"""
        try:
            with self._lock:
                if key not in self._index:
                    return None
                
                entry_info = self._index[key]
                file_path = Path(entry_info['file'])
                
                if not file_path.exists():
                    # Удаляем из индекса, если файл не найден
                    del self._index[key]
                    self._save_index()
                    return None
                
                # Загружаем данные
                with open(file_path, 'rb') as f:
                    data = pickle.load(f)
                
                # Создаём объект записи
                entry = CacheEntry(
                    data=data['data'],
                    timestamp=data['timestamp'],
                    ttl=data['ttl'],
                    access_count=data['access_count'],
                    last_access=data['last_access'],
                    size_bytes=data['size_bytes'],
                    metadata=data['metadata']
                )
                
                return entry
                
        except Exception as e:
            logger.error(f"Ошибка при загрузке кэша для ключа {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Удаляет запись с диска"""
        try:
            with self._lock:
                if key not in self._index:
                    return False
                
                entry_info = self._index[key]
                file_path = Path(entry_info['file'])
                
                # Удаляем файл
                if file_path.exists():
                    file_path.unlink()
                
                # Удаляем из индекса
                del self._index[key]
                self._save_index()
                
                return True
                
        except Exception as e:
            logger.error(f"Ошибка при удалении кэша для ключа {key}: {e}")
            return False
    
    def clear(self) -> None:
        """Очищает весь кэш"""
        try:
            with self._lock:
                for file_path in self.cache_dir.glob("*.cache"):
                    file_path.unlink()
                
                self._index.clear()
                self._save_index()
                
        except Exception as e:
            logger.error(f"Ошибка при очистке кэша: {e}")
    
    def _hash_key(self, key: str) -> str:
        """Создаёт хеш для ключа (безопасные имена файлов)"""
        return hashlib.sha256(key.encode()).hexdigest()
    
    def _get_total_size(self) -> int:
        """Возвращает общий размер кэша в байтах"""
        return sum(info['size_bytes'] for info in self._index.values())
    
    def _cleanup_oldest(self) -> None:
        """Удаляет самые старые записи до освобождения места"""
        if not self._index:
            return
        
        # Сортируем по timestamp (самые старые первые)
        sorted_keys = sorted(self._index.keys(), 
                           key=lambda k: self._index[k]['timestamp'])
        
        # Удаляем 25% самых старых записей
        keys_to_remove = sorted_keys[:max(1, len(sorted_keys) // 4)]
        
        for key in keys_to_remove:
            self.delete(key)
    
    def _load_index(self) -> None:
        """Загружает индекс из файла"""
        try:
            if self._index_file.exists():
                with open(self._index_file, 'r') as f:
                    self._index = json.load(f)
            else:
                self._index = {}
        except Exception as e:
            logger.error(f"Ошибка при загрузке индекса: {e}")
            self._index = {}
    
    def _save_index(self) -> None:
        """Сохраняет индекс в файл"""
        try:
            with open(self._index_file, 'w') as f:
                json.dump(self._index, f, indent=2)
        except Exception as e:
            logger.error(f"Ошибка при сохранении индекса: {e}")


class MCPToolsCache:
    """
    Основной класс для кэширования результатов MCP tools
    
    Особенности:
    - TTL: 30 минут для стабильных данных, 5 минут для динамических
    - Максимальный размер: 100MB
    - Кэширование только успешных запросов
    - Метрики попаданий/промахов
    - Интеграция с mcp_server.py и onec_client.py
    """
    
    def __init__(self, 
                 max_size_mb: int = 100,
                 default_ttl_stable: float = 30 * 60,  # 30 минут
                 default_ttl_dynamic: float = 5 * 60,  # 5 минут
                 persistent_cache_dir: Optional[Union[str, Path]] = None,
                 strategy: Optional[CacheStrategy] = None):
        
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.default_ttl_stable = default_ttl_stable
        self.default_ttl_dynamic = default_ttl_dynamic
        self.strategy = strategy or TTLCacheStrategy()
        self.metrics = CacheMetrics()
        
        # In-memory кэш
        self._cache: Dict[str, CacheEntry] = OrderedDict()
        self._lock = RLock()
        
        # Persistent cache (опционально)
        self.persistent_cache = None
        if persistent_cache_dir:
            self.persistent_cache = PersistentCache(persistent_cache_dir, max_size_mb)
        
        # Механизмы инвалидации
        self.invalidation = CacheInvalidation()
        self._setup_default_invalidation_rules()
        
        # Поддержка разных типов данных
        self._data_type_configs = {
            'metadata': {'ttl': default_ttl_stable, 'persistent': True},
            'aggregates': {'ttl': default_ttl_dynamic, 'persistent': False},
            'tool_config': {'ttl': default_ttl_stable, 'persistent': True},
            'api_response': {'ttl': default_ttl_dynamic, 'persistent': False},
            'stable': {'ttl': default_ttl_stable, 'persistent': True},
            'dynamic': {'ttl': default_ttl_dynamic, 'persistent': False}
        }
        
        logger.info(f"Инициализирован MCP Tools Cache: {max_size_mb}MB, "
                   f"TTL стабильных: {default_ttl_stable}s, "
                   f"TTL динамических: {default_ttl_dynamic}s")
    
    def get(self, key: str, data_type: str = 'stable') -> Optional[Any]:
        """
        Получает данные из кэша
        
        Args:
            key: Ключ кэша
            data_type: Тип данных (stable/dynamic/metadata/aggregates/tool_config/api_response)
            
        Returns:
            Закэшированные данные или None
        """
        start_time = time.time()
        
        try:
            with self._lock:
                # Проверяем in-memory кэш
                if key in self._cache:
                    entry = self._cache[key]
                    
                    # Проверяем TTL
                    if entry.is_expired:
                        del self._cache[key]
                        if self.persistent_cache:
                            self.persistent_cache.delete(key)
                        self.metrics.record_miss()
                        return None
                    
                    # Обновляем статистику
                    entry.access()
                    
                    # Перемещаем в конец (для LRU)
                    self._cache.move_to_end(key)
                    
                    self.metrics.record_hit()
                    return entry.data
                
                # Проверяем persistent cache
                if self.persistent_cache:
                    entry = self.persistent_cache.load(key)
                    if entry and not entry.is_expired:
                        # Восстанавливаем в память
                        self._cache[key] = entry
                        entry.access()
                        self.metrics.record_hit()
                        return entry.data
                
                # Промах кэша
                self.metrics.record_miss()
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при получении из кэша (key={key}): {e}")
            self.metrics.record_error()
            return None
    
    async def get_async(self, key: str, data_type: str = 'stable') -> Optional[Any]:
        """Асинхронная версия get"""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.get, key, data_type
        )
    
    def set(self, key: str, data: Any, 
            ttl: Optional[float] = None, 
            data_type: str = 'stable',
            metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Сохраняет данные в кэш
        
        Args:
            key: Ключ кэша
            data: Данные для кэширования
            ttl: Время жизни (в секундах), если None - используется тип данных
            data_type: Тип данных
            metadata: Дополнительные метаданные
            
        Returns:
            True если сохранение успешно
        """
        try:
            with self._lock:
                # Определяем TTL
                if ttl is None:
                    config = self._data_type_configs.get(data_type, {})
                    ttl = config.get('ttl', self.default_ttl_stable)
                
                # Создаём запись
                entry = CacheEntry(
                    data=data,
                    timestamp=time.time(),
                    ttl=ttl,
                    metadata=metadata or {}
                )
                
                # Оцениваем размер
                entry.size_bytes = self._estimate_size(data)
                
                # Проверяем размер кэша
                if self._is_full() and key not in self._cache:
                    self._evict_entries()
                
                # Сохраняем в память
                self._cache[key] = entry
                
                # Сохраняем в persistent cache если нужно
                config = self._data_type_configs.get(data_type, {})
                if config.get('persistent', False) and self.persistent_cache:
                    self.persistent_cache.store(key, entry)
                
                logger.debug(f"Закэшированы данные (key={key}, type={data_type}, "
                           f"ttl={ttl}s, size={entry.size_bytes}B)")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка при сохранении в кэш (key={key}): {e}")
            self.metrics.record_error()
            return False
    
    async def set_async(self, key: str, data: Any, 
                       ttl: Optional[float] = None,
                       data_type: str = 'stable',
                       metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Асинхронная версия set"""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.set, key, data, ttl, data_type, metadata
        )
    
    def delete(self, key: str) -> bool:
        """Удаляет запись из кэша"""
        try:
            with self._lock:
                # Удаляем из памяти
                if key in self._cache:
                    del self._cache[key]
                
                # Удаляем из persistent cache
                if self.persistent_cache:
                    self.persistent_cache.delete(key)
                
                return True
                
        except Exception as e:
            logger.error(f"Ошибка при удалении из кэша (key={key}): {e}")
            return False
    
    def clear(self) -> None:
        """Очищает весь кэш"""
        try:
            with self._lock:
                self._cache.clear()
                if self.persistent_cache:
                    self.persistent_cache.clear()
                logger.info("Кэш очищен")
        except Exception as e:
            logger.error(f"Ошибка при очистке кэша: {e}")
    
    def has(self, key: str) -> bool:
        """Проверяет наличие ключа в кэше"""
        return self.get(key) is not None
    
    async def has_async(self, key: str) -> bool:
        """Асинхронная версия has"""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.has, key
        )
    
    def size(self) -> int:
        """Возвращает количество записей в кэше"""
        return len(self._cache)
    
    def memory_usage_mb(self) -> float:
        """Возвращает использование памяти в MB"""
        return sum(entry.size_bytes for entry in self._cache.values()) / (1024 * 1024)
    
    def get_metrics(self) -> CacheMetrics:
        """Возвращает метрики кэша"""
        return self.metrics
    
    @asynccontextmanager
    async def cache_context(self) -> AsyncIterator[None]:
        """Контекстный менеджер для групповых операций кэширования"""
        logger.debug("Начат контекст кэширования")
        try:
            yield
        finally:
            logger.debug("Завершён контекст кэширования")
    
    def invalidate_by_type(self, data_type: str) -> int:
        """Инвалидирует кэш по типу данных"""
        patterns = [
            f"{data_type}:*",
            f"*{data_type}*"
        ]
        
        count = 0
        for pattern in patterns:
            count += self.invalidation.invalidate_by_pattern(self, pattern)
        
        return count
    
    def _is_full(self) -> bool:
        """Проверяет, заполнен ли кэш"""
        return self.memory_usage_mb() * 1024 * 1024 >= self.max_size_bytes
    
    def _evict_entries(self) -> None:
        """Вытесняет записи из кэша согласно стратегии"""
        evicted = 0
        max_evictions = max(1, len(self._cache) // 4)  # Вытесняем 25%
        
        while self._is_full() and evicted < max_evictions and self._cache:
            target_key = self.strategy.select_eviction_target(self)
            if target_key:
                del self._cache[target_key]
                if self.persistent_cache:
                    self.persistent_cache.delete(target_key)
                self.metrics.record_eviction()
                evicted += 1
            else:
                break
        
        logger.debug(f"Вытеснено {evicted} записей из кэша")
    
    def _estimate_size(self, data: Any) -> int:
        """Оценивает размер данных в байтах"""
        try:
            if isinstance(data, (str, bytes)):
                return len(data.encode() if isinstance(data, str) else data)
            elif isinstance(data, (int, float, bool)):
                return 8
            elif isinstance(data, (list, tuple)):
                return sum(self._estimate_size(item) for item in data)
            elif isinstance(data, dict):
                return sum(len(str(k).encode()) + self._estimate_size(v) 
                          for k, v in data.items())
            else:
                # Сериализуем для оценки
                serialized = json.dumps(data, default=str)
                return len(serialized.encode())
        except Exception:
            return 1024  # Консервативная оценка
    
    def _setup_default_invalidation_rules(self) -> None:
        """Настраивает стандартные правила инвалидации"""
        
        # Инвалидация при изменении метаданных 1С
        self.invalidation.add_invalidation_rule(
            "metadata:*", 
            lambda key: "metadata_updated" in key
        )
        
        # Инвалидация при изменении конфигурации инструментов
        self.invalidation.add_invalidation_rule(
            "tool_config:*",
            lambda key: "config_changed" in key
        )
        
        # Инвалидация агрегатов при изменении периодов
        self.invalidation.add_invalidation_rule(
            "aggregates:*",
            lambda key: "period_changed" in key
        )
        
        # Регистрируем слушатель изменений
        self.invalidation.register_change_listener(
            self._on_data_changed
        )
    
    def _on_data_changed(self, change_type: str) -> None:
        """Обработчик изменений данных"""
        logger.info(f"Получено уведомление об изменении: {change_type}")
        
        if change_type == "all":
            self.clear()
        elif change_type.startswith("metadata"):
            self.invalidate_by_type("metadata")
        elif change_type.startswith("tool"):
            self.invalidate_by_type("tool_config")


# Глобальный экземпляр кэша
_global_cache: Optional[MCPToolsCache] = None


def get_cache() -> MCPToolsCache:
    """Возвращает глобальный экземпляр кэша"""
    global _global_cache
    if _global_cache is None:
        raise RuntimeError("Кэш не инициализирован. Вызовите init_cache()")
    return _global_cache


def init_cache(max_size_mb: int = 100,
               default_ttl_stable: float = 30 * 60,
               default_ttl_dynamic: float = 5 * 60,
               persistent_cache_dir: Optional[str] = None,
               strategy: Optional[CacheStrategy] = None) -> MCPToolsCache:
    """
    Инициализирует глобальный экземпляр кэша
    
    Args:
        max_size_mb: Максимальный размер кэша в MB
        default_ttl_stable: TTL для стабильных данных (по умолчанию 30 минут)
        default_ttl_dynamic: TTL для динамических данных (по умолчанию 5 минут)
        persistent_cache_dir: Директория для persistent cache
        strategy: Стратегия кэширования
        
    Returns:
        Экземпляр кэша
    """
    global _global_cache
    
    _global_cache = MCPToolsCache(
        max_size_mb=max_size_mb,
        default_ttl_stable=default_ttl_stable,
        default_ttl_dynamic=default_ttl_dynamic,
        persistent_cache_dir=persistent_cache_dir,
        strategy=strategy
    )
    
    logger.info(f"Инициализирован глобальный MCP Tools Cache")
    return _global_cache


# Декораторы для удобного использования

def cached(key_func: Optional[Callable] = None, 
           ttl: Optional[float] = None,
           data_type: str = 'stable'):
    """
    Декоратор для кэширования результатов функций
    
    Args:
        key_func: Функция для генерации ключа кэша
        ttl: Время жизни кэша
        data_type: Тип данных
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            # Генерируем ключ кэша
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Стандартная генерация ключа
                key_parts = [func.__name__, str(args), str(sorted(kwargs.items()))]
                cache_key = hashlib.sha256('|'.join(key_parts).encode()).hexdigest()
            
            cache = get_cache()
            
            # Проверяем кэш
            result = cache.get(cache_key, data_type)
            if result is not None:
                return result
            
            # Выполняем функцию и кэшируем результат
            result = func(*args, **kwargs)
            if result is not None:  # Кэшируем только успешные результаты
                cache.set(cache_key, result, ttl, data_type)
            
            return result
        
        return wrapper
    return decorator


async def cached_async(key_func: Optional[Callable] = None,
                      ttl: Optional[float] = None,
                      data_type: str = 'stable'):
    """
    Асинхронный декоратор для кэширования результатов функций
    """
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            # Генерируем ключ кэша
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                key_parts = [func.__name__, str(args), str(sorted(kwargs.items()))]
                cache_key = hashlib.sha256('|'.join(key_parts).encode()).hexdigest()
            
            cache = get_cache()
            
            # Проверяем кэш
            result = await cache.get_async(cache_key, data_type)
            if result is not None:
                return result
            
            # Выполняем функцию и кэшируем результат
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            if result is not None:
                await cache.set_async(cache_key, result, ttl, data_type)
            
            return result
        
        return wrapper
    return decorator


# Специализированные функции для интеграции с MCP сервером

def cache_tool_result(tool_name: str, 
                     args: Dict[str, Any],
                     result: Any,
                     ttl: Optional[float] = None) -> bool:
    """
    Кэширует результат выполнения MCP tool
    
    Args:
        tool_name: Имя инструмента
        args: Аргументы инструмента
        result: Результат выполнения
        ttl: Время жизни кэша
        
    Returns:
        True если кэширование успешно
    """
    cache = get_cache()
    
    # Генерируем ключ кэша на основе инструмента и аргументов
    key_data = f"tool:{tool_name}:{json.dumps(args, sort_keys=True)}"
    cache_key = hashlib.sha256(key_data.encode()).hexdigest()
    
    return cache.set(cache_key, result, ttl, 'tool_config')


def get_cached_tool_result(tool_name: str, 
                          args: Dict[str, Any]) -> Optional[Any]:
    """
    Получает закэшированный результат MCP tool
    
    Args:
        tool_name: Имя инструмента
        args: Аргументы инструмента
        
    Returns:
        Закэшированный результат или None
    """
    cache = get_cache()
    
    key_data = f"tool:{tool_name}:{json.dumps(args, sort_keys=True)}"
    cache_key = hashlib.sha256(key_data.encode()).hexdigest()
    
    return cache.get(cache_key, 'tool_config')


def cache_metadata_1c(entity_type: str, 
                     entity_id: str,
                     metadata: Any,
                     ttl: Optional[float] = None) -> bool:
    """
    Кэширует метаданные 1С
    
    Args:
        entity_type: Тип сущности (справочник, документ, регистр)
        entity_id: Идентификатор сущности
        metadata: Метаданные
        ttl: Время жизни кэша
        
    Returns:
        True если кэширование успешно
    """
    cache = get_cache()
    
    cache_key = f"metadata:{entity_type}:{entity_id}"
    config_ttl = ttl or cache._data_type_configs['metadata']['ttl']
    
    return cache.set(cache_key, metadata, config_ttl, 'metadata')


def get_cached_metadata_1c(entity_type: str, entity_id: str) -> Optional[Any]:
    """
    Получает закэшированные метаданные 1С
    
    Args:
        entity_type: Тип сущности
        entity_id: Идентификатор сущности
        
    Returns:
        Закэшированные метаданные или None
    """
    cache = get_cache()
    cache_key = f"metadata:{entity_type}:{entity_id}"
    return cache.get(cache_key, 'metadata')


def cache_aggregates(aggregate_type: str,
                    period: str,
                    filters: Dict[str, Any],
                    data: Any,
                    ttl: Optional[float] = None) -> bool:
    """
    Кэширует агрегированные данные
    
    Args:
        aggregate_type: Тип агрегата
        period: Период агрегации
        filters: Фильтры
        data: Данные агрегата
        ttl: Время жизни кэша
        
    Returns:
        True если кэширование успешно
    """
    cache = get_cache()
    
    filter_key = json.dumps(filters, sort_keys=True)
    cache_key = f"aggregates:{aggregate_type}:{period}:{hashlib.md5(filter_key.encode()).hexdigest()}"
    config_ttl = ttl or cache._data_type_configs['aggregates']['ttl']
    
    return cache.set(cache_key, data, config_ttl, 'aggregates')


def get_cached_aggregates(aggregate_type: str,
                         period: str,
                         filters: Dict[str, Any]) -> Optional[Any]:
    """
    Получает закэшированные агрегированные данные
    
    Args:
        aggregate_type: Тип агрегата
        period: Период агрегации
        filters: Фильтры
        
    Returns:
        Закэшированные данные или None
    """
    cache = get_cache()
    
    filter_key = json.dumps(filters, sort_keys=True)
    cache_key = f"aggregates:{aggregate_type}:{period}:{hashlib.md5(filter_key.encode()).hexdigest()}"
    
    return cache.get(cache_key, 'aggregates')


# Функции для мониторинга и администрирования

def get_cache_stats() -> Dict[str, Any]:
    """
    Возвращает статистику кэша для мониторинга
    
    Returns:
        Словарь со статистикой
    """
    cache = get_cache()
    metrics = cache.get_metrics()
    
    return {
        'total_entries': cache.size(),
        'memory_usage_mb': cache.memory_usage_mb(),
        'hits': metrics.hits,
        'misses': metrics.misses,
        'hit_ratio': metrics.hit_ratio,
        'evictions': metrics.evictions,
        'errors': metrics.errors,
        'max_size_mb': cache.max_size_bytes / (1024 * 1024),
        'persistent_cache_enabled': cache.persistent_cache is not None
    }


def cleanup_expired() -> int:
    """
    Очищает истёкшие записи из кэша
    
    Returns:
        Количество очищенных записей
    """
    cache = get_cache()
    expired_keys = []
    
    with cache._lock:
        for key, entry in cache._cache.items():
            if entry.is_expired:
                expired_keys.append(key)
        
        for key in expired_keys:
            del cache._cache[key]
            if cache.persistent_cache:
                cache.persistent_cache.delete(key)
    
    logger.info(f"Очищено {len(expired_keys)} истёкших записей из кэша")
    return len(expired_keys)


# Экспорт основных классов и функций
__all__ = [
    'MCPToolsCache',
    'CacheStrategy',
    'LRUStrategy', 
    'TTLCacheStrategy',
    'CacheInvalidation',
    'PersistentCache',
    'CacheEntry',
    'CacheMetrics',
    'get_cache',
    'init_cache',
    'cached',
    'cached_async',
    'cache_tool_result',
    'get_cached_tool_result',
    'cache_metadata_1c',
    'get_cached_metadata_1c',
    'cache_aggregates',
    'get_cached_aggregates',
    'get_cache_stats',
    'cleanup_expired'
]
