# [NEXUS IDENTITY] ID: -8082040495095274735 | DATE: 2025-11-19

"""
OAuth2 Cache Manager - Модуль кэширования OAuth2 токенов и сессий
Реализует безопасное кэширование с шифрованием и автоматической очисткой

Основные компоненты:
- SecureStorage: шифрование и безопасное хранение чувствительных данных
- OAuthTokenCache: кэширование access и refresh токенов
- SessionManager: управление пользовательскими сессиями
- TokenValidator: валидация и автоматическое обновление токенов
"""

import asyncio
import base64
import json
import logging
import pickle
import secrets
import threading
import time
from collections import OrderedDict, defaultdict
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from hashlib import sha256
from typing import Any, Dict, List, Optional, Set

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class CacheStrategy(Enum):
    """Стратегии кэширования."""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live


class SecurityLevel(Enum):
    """Уровни безопасности."""
    BASIC = 1
    ENHANCED = 2
    MAXIMUM = 3


@dataclass
class CachedToken:
    """Структура кэшированного токена."""
    access_token: str
    refresh_token: Optional[str]
    token_type: str
    expires_in: int
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    user_data: Optional[Dict[str, Any]] = None
    
    @property
    def is_expired(self) -> bool:
        """Проверка истечения срока действия токена."""
        expiry_time = self.created_at + timedelta(seconds=self.expires_in)
        return datetime.now() > expiry_time
    
    @property
    def time_to_live(self) -> int:
        """Оставшееся время жизни токена в секундах."""
        expiry_time = self.created_at + timedelta(seconds=self.expires_in)
        remaining = expiry_time - datetime.now()
        return max(0, int(remaining.total_seconds()))


@dataclass
class UserSession:
    """Структура пользовательской сессии."""
    session_id: str
    user_identifier: str
    login: str
    created_at: datetime
    last_activity: datetime
    access_count: int = 0
    metadata: Optional[Dict[str, Any]] = None
    active: bool = True
    
    @property
    def age(self) -> int:
        """Возраст сессии в секундах."""
        return int((datetime.now() - self.created_at).total_seconds())
    
    @property
    def inactive_time(self) -> int:
        """Время неактивности в секундах."""
        return int((datetime.now() - self.last_activity).total_seconds())


class SecureStorage:
    """
    Безопасное хранилище для чувствительных данных.
    Обеспечивает шифрование, хеширование и защиту от несанкционированного доступа.
    """
    
    def __init__(self, master_password: Optional[str] = None, security_level: SecurityLevel = SecurityLevel.MAXIMUM):
        """
        Инициализация безопасного хранилища.
        
        Args:
            master_password: Главный пароль для шифрования (генерируется автоматически если не указан)
            security_level: Уровень безопасности
        """
        self.security_level = security_level
        self._lock = threading.RLock()
        
        # Генерация или использование предоставленного мастер-пароля
        if master_password:
            self._master_password = master_password.encode('utf-8')
        else:
            self._master_password = secrets.token_bytes(32)
            logger.warning("Автоматически сгенерирован мастер-пароль для SecureStorage")
        
        # Инициализация шифрования
        self._cipher = self._create_cipher(self._master_password)
        
        # Отслеживание попыток доступа
        self._access_attempts: Dict[str, List[float]] = defaultdict(list)
        self._max_attempts = 5
        self._block_duration = 300  # 5 минут
        
        # Счетчики для статистики безопасности
        self._access_count = 0
        self._failed_attempts = 0
        
    def _create_cipher(self, password: bytes) -> Fernet:
        """Создание шифра на основе пароля."""
        # Соль для PBKDF2
        salt = b'oauth_cache_salt_v1'  # Фиксированная соль для совместимости
        
        # PBKDF2 для получения ключа
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000 if self.security_level == SecurityLevel.MAXIMUM else 50000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return Fernet(key)
    
    def _check_rate_limit(self, identifier: str) -> bool:
        """Проверка ограничения скорости доступа."""
        now = time.time()
        
        with self._lock:
            attempts = self._access_attempts[identifier]
            # Удаляем старые попытки
            attempts[:] = [t for t in attempts if now - t < self._block_duration]
            
            if len(attempts) >= self._max_attempts:
                logger.warning(f"Превышен лимит доступа для {identifier}")
                return False
            
            attempts.append(now)
            return True
    
    def _generate_storage_key(self, key: str) -> str:
        """Генерация безопасного ключа для хранения."""
        return sha256(f"{key}:{self._master_password[:16].hex()}".encode()).hexdigest()[:32]
    
    def encrypt(self, data: str) -> str:
        """
        Шифрование данных.
        
        Args:
            data: Строка для шифрования
            
        Returns:
            Зашифрованная строка в base64
        """
        try:
            encrypted = self._cipher.encrypt(data.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted).decode('ascii')
        except Exception as e:
            logger.error(f"Ошибка шифрования: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Расшифровка данных.
        
        Args:
            encrypted_data: Зашифрованная строка в base64
            
        Returns:
            Расшифрованная строка
        """
        try:
            decoded = base64.urlsafe_b64decode(encrypted_data.encode('ascii'))
            decrypted = self._cipher.decrypt(decoded)
            return decrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"Ошибка расшифровки: {e}")
            self._failed_attempts += 1
            raise
    
    def hash_secret(self, secret: str) -> str:
        """
        Безопасное хеширование секрета.
        
        Args:
            secret: Секрет для хеширования
            
        Returns:
            SHA256 хеш
        """
        return sha256(secret.encode('utf-8')).hexdigest()
    
    def store_secure_data(self, key: str, data: Any, identifier: str = "default") -> bool:
        """
        Безопасное сохранение данных.
        
        Args:
            key: Ключ данных
            data: Данные для сохранения
            identifier: Идентификатор доступа
            
        Returns:
            True если успешно
        """
        if not self._check_rate_limit(identifier):
            raise PermissionError("Превышен лимит попыток доступа")
        
        try:
            with self._lock:
                storage_key = self._generate_storage_key(key)
                serialized_data = json.dumps(asdict(data) if hasattr(data, '__dict__') else data, 
                                           default=str, separators=(',', ':'))
                encrypted_data = self.encrypt(serialized_data)
                
                # Сохраняем зашифрованные данные (в реальной реализации - в файл/БД)
                self._secure_storage: Dict[str, str] = getattr(self, '_secure_storage', {})
                self._secure_storage[storage_key] = encrypted_data
                
                self._access_count += 1
                logger.debug(f"Безопасные данные сохранены под ключом {key}")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка сохранения данных: {e}")
            return False
    
    def retrieve_secure_data(self, key: str, identifier: str = "default") -> Optional[Any]:
        """
        Безопасное получение данных.
        
        Args:
            key: Ключ данных
            identifier: Идентификатор доступа
            
        Returns:
            Данные или None
        """
        if not self._check_rate_limit(identifier):
            raise PermissionError("Превышен лимит попыток доступа")
        
        try:
            with self._lock:
                storage_key = self._generate_storage_key(key)
                encrypted_data = self._secure_storage.get(storage_key)
                
                if not encrypted_data:
                    return None
                
                decrypted_data = self.decrypt(encrypted_data)
                return json.loads(decrypted_data)
                
        except Exception as e:
            logger.error(f"Ошибка получения данных: {e}")
            return None
    
    def delete_secure_data(self, key: str, identifier: str = "default") -> bool:
        """
        Безопасное удаление данных.
        
        Args:
            key: Ключ данных
            identifier: Идентификатор доступа
            
        Returns:
            True если успешно
        """
        if not self._check_rate_limit(identifier):
            raise PermissionError("Превышен лимит попыток доступа")
        
        try:
            with self._lock:
                storage_key = self._generate_storage_key(key)
                if storage_key in self._secure_storage:
                    del self._secure_storage[storage_key]
                    logger.debug(f"Безопасные данные удалены: {key}")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Ошибка удаления данных: {e}")
            return False
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Получение статистики безопасности."""
        with self._lock:
            return {
                "access_count": self._access_count,
                "failed_attempts": self._failed_attempts,
                "security_level": self.security_level.name,
                "max_attempts": self._max_attempts,
                "block_duration": self._block_duration
            }


class OAuthTokenCache:
    """
    Кэш для OAuth2 токенов с автоматической очисткой и стратегиями управления.
    Поддерживает TTL, LRU/LFU алгоритмы и автоматическое обновление.
    """
    
    def __init__(self, 
                 max_size: int = 1000,
                 default_ttl: int = 3600,
                 strategy: CacheStrategy = CacheStrategy.LRU,
                 auto_cleanup: bool = True,
                 secure_storage: Optional[SecureStorage] = None):
        """
        Инициализация кэша токенов.
        
        Args:
            max_size: Максимальное количество токенов в кэше
            default_ttl: TTL по умолчанию в секундах
            strategy: Стратегия кэширования
            auto_cleanup: Автоматическая очистка
            secure_storage: Безопасное хранилище
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.strategy = strategy
        self.auto_cleanup = auto_cleanup
        self.secure_storage = secure_storage or SecureStorage()
        
        # Основное хранилище токенов
        self._tokens: OrderedDict[str, CachedToken] = OrderedDict()
        
        # Статистика использования для LFU
        self._access_counts: Dict[str, int] = defaultdict(int)
        
        # Поисковые индексы
        self._token_by_user: Dict[str, str] = {}  # user_id -> access_token
        self._refresh_to_access: Dict[str, str] = {}  # refresh_token -> access_token
        
        # Синхронизация
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Статистика
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "cleanups": 0,
            "total_tokens": 0
        }
        
        logger.info(f"OAuthTokenCache инициализирован (max_size={max_size}, strategy={strategy.name})")
    
    async def start_cleanup_task(self, interval: int = 300):
        """Запуск задачи автоматической очистки."""
        if self.auto_cleanup and not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop(interval))
            logger.info(f"Запущена задача очистки кэша (интервал: {interval}s)")
    
    async def stop_cleanup_task(self):
        """Остановка задачи очистки."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            logger.info("Задача очистки кэша остановлена")
    
    async def _cleanup_loop(self, interval: int):
        """Цикл автоматической очистки."""
        while True:
            try:
                await asyncio.sleep(interval)
                cleaned = await self._cleanup_expired()
                if cleaned > 0:
                    self._stats["cleanups"] += cleaned
                    logger.debug(f"Очищено истекших токенов: {cleaned}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Ошибка в цикле очистки: {e}")
    
    async def _cleanup_expired(self) -> int:
        """Очистка истекших токенов."""
        async with self._lock:
            now = datetime.now()
            expired_tokens = []
            
            for token_key, token_data in self._tokens.items():
                if token_data.is_expired:
                    expired_tokens.append(token_key)
            
            for token_key in expired_tokens:
                await self._remove_token_internal(token_key)
            
            return len(expired_tokens)
    
    def _apply_eviction_strategy(self):
        """Применение стратегии вытеснения при превышении лимита."""
        if len(self._tokens) <= self.max_size:
            return
        
        if self.strategy == CacheStrategy.LRU:
            # Удаляем наименее недавно используемые
            while len(self._tokens) > self.max_size:
                oldest_key = next(iter(self._tokens))
                asyncio.create_task(self._remove_token_internal(oldest_key))
        
        elif self.strategy == CacheStrategy.LFU:
            # Удаляем наименее часто используемые
            while len(self._tokens) > self.max_size:
                min_access_key = min(self._tokens.keys(), 
                                   key=lambda k: self._access_counts.get(k, 0))
                asyncio.create_task(self._remove_token_internal(min_access_key))
        
        self._stats["evictions"] += 1
    
    async def store_token(self, 
                         user_id: str,
                         access_token: str,
                         refresh_token: Optional[str] = None,
                         token_type: str = "Bearer",
                         expires_in: Optional[int] = None,
                         user_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Сохранение токена в кэш.
        
        Args:
            user_id: Идентификатор пользователя
            access_token: Access токен
            refresh_token: Refresh токен (опционально)
            token_type: Тип токена
            expires_in: Время жизни в секундах
            user_data: Дополнительные данные пользователя
            
        Returns:
            True если успешно
        """
        async with self._lock:
            try:
                # Создаем объект токена
                token_data = CachedToken(
                    access_token=access_token,
                    refresh_token=refresh_token,
                    token_type=token_type,
                    expires_in=expires_in or self.default_ttl,
                    created_at=datetime.now(),
                    last_accessed=datetime.now(),
                    access_count=1,
                    user_data=user_data
                )
                
                # Если у пользователя уже есть токен, удаляем старый
                if user_id in self._token_by_user:
                    old_token = self._token_by_user[user_id]
                    if old_token in self._tokens:
                        await self._remove_token_internal(old_token)
                
                # Сохраняем новый токен
                self._tokens[access_token] = token_data
                self._token_by_user[user_id] = access_token
                
                if refresh_token:
                    self._refresh_to_access[refresh_token] = access_token
                
                # Применяем стратегию вытеснения при необходимости
                self._apply_eviction_strategy()
                
                logger.debug(f"Токен сохранен для пользователя {user_id}")
                return True
                
            except Exception as e:
                logger.error(f"Ошибка сохранения токена: {e}")
                return False
    
    async def get_token(self, access_token: str) -> Optional[CachedToken]:
        """
        Получение токена из кэша.
        
        Args:
            access_token: Access токен
            
        Returns:
            CachedToken или None
        """
        async with self._lock:
            token_data = self._tokens.get(access_token)
            
            if not token_data:
                self._stats["misses"] += 1
                return None
            
            # Проверяем истечение
            if token_data.is_expired:
                await self._remove_token_internal(access_token)
                self._stats["misses"] += 1
                return None
            
            # Обновляем статистику использования
            token_data.last_accessed = datetime.now()
            token_data.access_count += 1
            self._access_counts[access_token] += 1
            
            # Перемещаем в конец для LRU
            if self.strategy == CacheStrategy.LRU:
                self._tokens.move_to_end(access_token)
            
            self._stats["hits"] += 1
            return token_data
    
    async def get_token_by_user(self, user_id: str) -> Optional[CachedToken]:
        """
        Получение токена по идентификатору пользователя.
        
        Args:
            user_id: Идентификатор пользователя
            
        Returns:
            CachedToken или None
        """
        async with self._lock:
            access_token = self._token_by_user.get(user_id)
            if access_token:
                return await self.get_token(access_token)
            return None
    
    async def refresh_token(self, refresh_token: str) -> Optional[CachedToken]:
        """
        Обновление токена по refresh token.
        
        Args:
            refresh_token: Refresh токен
            
        Returns:
            Обновленный CachedToken или None
        """
        async with self._lock:
            access_token = self._refresh_to_access.get(refresh_token)
            if access_token:
                token_data = await self.get_token(access_token)
                return token_data
            return None
    
    async def revoke_token(self, access_token: str) -> bool:
        """
        Отзыв токена.
        
        Args:
            access_token: Access токен для отзыва
            
        Returns:
            True если успешно
        """
        async with self._lock:
            return await self._remove_token_internal(access_token)
    
    async def revoke_user_tokens(self, user_id: str) -> bool:
        """
        Отзыв всех токенов пользователя.
        
        Args:
            user_id: Идентификатор пользователя
            
        Returns:
            True если успешно
        """
        async with self._lock:
            access_token = self._token_by_user.get(user_id)
            if access_token:
                result = await self._remove_token_internal(access_token)
                if access_token in self._token_by_user:
                    del self._token_by_user[user_id]
                return result
            return False
    
    async def _remove_token(self, access_token: str) -> bool:
        """
        Удаление токена (публичный метод).
        
        Args:
            access_token: Access токен
            
        Returns:
            True если успешно
        """
        async with self._lock:
            return await self._remove_token_internal(access_token)
    
    async def _remove_token_internal(self, access_token: str) -> bool:
        """Внутренний метод удаления токена."""
        try:
            token_data = self._tokens.pop(access_token, None)
            if token_data:
                # Удаляем из индексов
                for user_id, token in list(self._token_by_user.items()):
                    if token == access_token:
                        del self._token_by_user[user_id]
                        break
                
                if token_data.refresh_token:
                    self._refresh_to_access.pop(token_data.refresh_token, None)
                
                # Удаляем из статистики
                self._access_counts.pop(access_token, None)
                self._stats["total_tokens"] -= 1
                
                return True
            return False
            
        except Exception as e:
            logger.error(f"Ошибка удаления токена {access_token}: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Получение статистики кэша."""
        async with self._lock:
            hit_rate = (self._stats["hits"] / 
                       (self._stats["hits"] + self._stats["misses"]) * 100 
                       if (self._stats["hits"] + self._stats["misses"]) > 0 else 0)
            
            return {
                **self._stats,
                "current_size": len(self._tokens),
                "max_size": self.max_size,
                "hit_rate": round(hit_rate, 2),
                "memory_usage_mb": self._calculate_memory_usage()
            }
    
    def _calculate_memory_usage(self) -> float:
        """Расчет использования памяти в MB."""
        total_size = 0
        for token_data in self._tokens.values():
            total_size += len(pickle.dumps(token_data))
        return round(total_size / (1024 * 1024), 2)
    
    async def cleanup(self) -> int:
        """Принудительная очистка кэша."""
        cleaned = await self._cleanup_expired()
        logger.info(f"Принудительная очистка завершена: очищено {cleaned} токенов")
        return cleaned


class SessionManager:
    """
    Менеджер пользовательских сессий с поддержкой безопасного хранения и отслеживания активности.
    """
    
    def __init__(self,
                 max_sessions: int = 10000,
                 session_timeout: int = 3600,
                 max_concurrent_sessions: int = 5,
                 secure_storage: Optional[SecureStorage] = None):
        """
        Инициализация менеджера сессий.
        
        Args:
            max_sessions: Максимальное количество активных сессий
            session_timeout: Таймаут сессии в секундах
            max_concurrent_sessions: Максимальное количество одновременных сессий на пользователя
            secure_storage: Безопасное хранилище
        """
        self.max_sessions = max_sessions
        self.session_timeout = session_timeout
        self.max_concurrent_sessions = max_concurrent_sessions
        self.secure_storage = secure_storage or SecureStorage()
        
        # Хранилище сессий
        self._sessions: Dict[str, UserSession] = {}
        self._user_sessions: Dict[str, Set[str]] = defaultdict(set)  # user_id -> session_ids
        
        # Синхронизация
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Статистика
        self._stats = {
            "created_sessions": 0,
            "expired_sessions": 0,
            "active_sessions": 0,
            "total_users": 0
        }
        
        logger.info(f"SessionManager инициализирован (max_sessions={max_sessions})")
    
    async def start_cleanup_task(self, interval: int = 300):
        """Запуск задачи очистки сессий."""
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop(interval))
            logger.info(f"Запущена задача очистки сессий (интервал: {interval}s)")
    
    async def stop_cleanup_task(self):
        """Остановка задачи очистки."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            logger.info("Задача очистки сессий остановлена")
    
    async def _cleanup_loop(self, interval: int):
        """Цикл очистки устаревших сессий."""
        while True:
            try:
                await asyncio.sleep(interval)
                expired_count = await self._cleanup_expired_sessions()
                if expired_count > 0:
                    self._stats["expired_sessions"] += expired_count
                    logger.debug(f"Очищено устаревших сессий: {expired_count}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Ошибка в цикле очистки сессий: {e}")
    
    async def _cleanup_expired_sessions(self) -> int:
        """Очистка устаревших сессий."""
        async with self._lock:
            now = datetime.now()
            expired_sessions = []
            
            for session_id, session_data in self._sessions.items():
                if session_data.inactive_time > self.session_timeout:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                await self._remove_session_internal(session_id)
            
            return len(expired_sessions)
    
    def _generate_session_id(self) -> str:
        """Генерация уникального ID сессии."""
        return f"session_{secrets.token_urlsafe(24)}"
    
    async def create_session(self,
                           user_identifier: str,
                           login: str,
                           metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Создание новой сессии.
        
        Args:
            user_identifier: Уникальный идентификатор пользователя
            login: Логин пользователя
            metadata: Дополнительные метаданные
            
        Returns:
            ID сессии или None при ошибке
        """
        async with self._lock:
            try:
                # Проверяем лимит одновременных сессий пользователя
                user_active_sessions = self._user_sessions.get(user_identifier, set())
                if len(user_active_sessions) >= self.max_concurrent_sessions:
                    logger.warning(f"Превышен лимит сессий для пользователя {user_identifier}")
                    return None
                
                # Проверяем общий лимит сессий
                if len(self._sessions) >= self.max_sessions:
                    # Удаляем наиболее старую сессию
                    oldest_session = min(self._sessions.items(), 
                                       key=lambda x: x[1].created_at)
                    await self._remove_session_internal(oldest_session[0])
                
                # Создаем новую сессию
                session_id = self._generate_session_id()
                now = datetime.now()
                
                session_data = UserSession(
                    session_id=session_id,
                    user_identifier=user_identifier,
                    login=login,
                    created_at=now,
                    last_activity=now,
                    metadata=metadata or {}
                )
                
                # Сохраняем сессию
                self._sessions[session_id] = session_data
                self._user_sessions[user_identifier].add(session_id)
                
                # Обновляем статистику
                self._stats["created_sessions"] += 1
                self._stats["active_sessions"] += 1
                if len(self._user_sessions) > self._stats["total_users"]:
                    self._stats["total_users"] = len(self._user_sessions)
                
                logger.debug(f"Создана сессия {session_id} для пользователя {user_identifier}")
                return session_id
                
            except Exception as e:
                logger.error(f"Ошибка создания сессии: {e}")
                return None
    
    async def get_session(self, session_id: str) -> Optional[UserSession]:
        """
        Получение сессии.
        
        Args:
            session_id: ID сессии
            
        Returns:
            UserSession или None
        """
        async with self._lock:
            session_data = self._sessions.get(session_id)
            if not session_data:
                return None
            
            # Проверяем не истекла ли сессия
            if session_data.inactive_time > self.session_timeout:
                await self._remove_session_internal(session_id)
                return None
            
            return session_data
    
    async def update_activity(self, session_id: str) -> bool:
        """
        Обновление времени активности сессии.
        
        Args:
            session_id: ID сессии
            
        Returns:
            True если успешно
        """
        async with self._lock:
            session_data = self._sessions.get(session_id)
            if session_data:
                session_data.last_activity = datetime.now()
                session_data.access_count += 1
                return True
            return False
    
    async def close_session(self, session_id: str) -> bool:
        """
        Закрытие сессии.
        
        Args:
            session_id: ID сессии
            
        Returns:
            True если успешно
        """
        async with self._lock:
            return await self._remove_session_internal(session_id)
    
    async def close_user_sessions(self, user_identifier: str) -> int:
        """
        Закрытие всех сессий пользователя.
        
        Args:
            user_identifier: Идентификатор пользователя
            
        Returns:
            Количество закрытых сессий
        """
        async with self._lock:
            session_ids = self._user_sessions.get(user_identifier, set()).copy()
            closed_count = 0
            
            for session_id in session_ids:
                if await self._remove_session_internal(session_id):
                    closed_count += 1
            
            return closed_count
    
    async def _remove_session_internal(self, session_id: str) -> bool:
        """Внутренний метод удаления сессии."""
        try:
            session_data = self._sessions.pop(session_id, None)
            if session_data:
                # Удаляем из индекса пользователя
                user_sessions = self._user_sessions.get(session_data.user_identifier, set())
                user_sessions.discard(session_id)
                if not user_sessions:
                    self._user_sessions.pop(session_data.user_identifier, None)
                
                # Обновляем статистику
                self._stats["active_sessions"] -= 1
                
                return True
            return False
            
        except Exception as e:
            logger.error(f"Ошибка удаления сессии {session_id}: {e}")
            return False
    
    async def get_active_sessions(self, user_identifier: Optional[str] = None) -> List[UserSession]:
        """
        Получение активных сессий.
        
        Args:
            user_identifier: Фильтр по пользователю (опционально)
            
        Returns:
            Список активных сессий
        """
        async with self._lock:
            if user_identifier:
                session_ids = self._user_sessions.get(user_identifier, set())
                return [self._sessions[sid] for sid in session_ids if sid in self._sessions]
            else:
                return list(self._sessions.values())
    
    async def get_stats(self) -> Dict[str, Any]:
        """Получение статистики сессий."""
        async with self._lock:
            return {
                **self._stats,
                "current_active": len(self._sessions),
                "max_sessions": self.max_sessions,
                "total_users_with_sessions": len(self._user_sessions),
                "avg_sessions_per_user": (
                    len(self._sessions) / len(self._user_sessions) 
                    if self._user_sessions else 0
                )
            }
    
    async def cleanup(self) -> int:
        """Принудительная очистка сессий."""
        cleaned = await self._cleanup_expired_sessions()
        logger.info(f"Принудительная очистка сессий завершена: очищено {cleaned} сессий")
        return cleaned


class TokenValidator:
    """
    Валидатор токенов с автоматическим обновлением и проверкой валидности.
    Интегрируется с OAuthTokenCache и SessionManager для полного цикла управления токенами.
    """
    
    def __init__(self,
                 token_cache: OAuthTokenCache,
                 session_manager: SessionManager,
                 refresh_threshold: int = 300,
                 auto_refresh: bool = True):
        """
        Инициализация валидатора.
        
        Args:
            token_cache: Кэш токенов
            session_manager: Менеджер сессий
            refresh_threshold: Порог обновления в секундах
            auto_refresh: Автоматическое обновление токенов
        """
        self.token_cache = token_cache
        self.session_manager = session_manager
        self.refresh_threshold = refresh_threshold
        self.auto_refresh = auto_refresh
        
        # Статистика валидации
        self._stats = {
            "validations": 0,
            "refreshes": 0,
            "rejections": 0,
            "errors": 0
        }
        
        logger.info("TokenValidator инициализирован")
    
    async def validate_token(self, 
                           access_token: str,
                           session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Валидация access токена.
        
        Args:
            access_token: Access токен для проверки
            session_id: Опциональный ID сессии
            
        Returns:
            Словарь с данными валидного токена или None
        """
        try:
            self._stats["validations"] += 1
            
            # Получаем токен из кэша
            token_data = await self.token_cache.get_token(access_token)
            if not token_data:
                self._stats["rejections"] += 1
                logger.debug(f"Токен не найден в кэше: {access_token[:16]}...")
                return None
            
            # Проверяем срок действия
            if token_data.is_expired:
                self._stats["rejections"] += 1
                logger.debug(f"Токен истек: {access_token[:16]}...")
                await self.token_cache.revoke_token(access_token)
                return None
            
            # Проверяем необходимость обновления
            if self.auto_refresh and token_data.time_to_live < self.refresh_threshold:
                logger.debug(f"Токен требует обновления: {access_token[:16]}...")
                # В реальной реализации здесь был бы вызов к OAuth серверу
                # Пока возвращаем текущий токен
                self._stats["refreshes"] += 1
            
            # Обновляем активность сессии если указан session_id
            if session_id:
                await self.session_manager.update_activity(session_id)
            
            result = {
                "access_token": token_data.access_token,
                "token_type": token_data.token_type,
                "expires_in": token_data.time_to_live,
                "user_data": token_data.user_data,
                "access_count": token_data.access_count,
                "created_at": token_data.created_at.isoformat(),
                "last_accessed": token_data.last_accessed.isoformat()
            }
            
            logger.debug(f"Токен успешно валидирован: {access_token[:16]}...")
            return result
            
        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Ошибка валидации токена: {e}")
            return None
    
    async def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Валидация пользовательской сессии.
        
        Args:
            session_id: ID сессии для проверки
            
        Returns:
            Словарь с данными сессии или None
        """
        try:
            session_data = await self.session_manager.get_session(session_id)
            if not session_data:
                logger.debug(f"Сессия не найдена или истекла: {session_id}")
                return None
            
            result = {
                "session_id": session_data.session_id,
                "user_identifier": session_data.user_identifier,
                "login": session_data.login,
                "age": session_data.age,
                "inactive_time": session_data.inactive_time,
                "access_count": session_data.access_count,
                "active": session_data.active,
                "metadata": session_data.metadata
            }
            
            logger.debug(f"Сессия успешно валидирована: {session_id}")
            return result
            
        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Ошибка валидации сессии: {e}")
            return None
    
    async def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Принудительное обновление access токена.
        
        Args:
            refresh_token: Refresh токен
            
        Returns:
            Новые данные токена или None
        """
        try:
            # В реальной реализации здесь был бы вызов к OAuth серверу
            # Пока возвращаем None как заглушку
            logger.debug(f"Запрос обновления токена по refresh_token: {refresh_token[:16]}...")
            return None
            
        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Ошибка обновления токена: {e}")
            return None
    
    async def revoke_access(self, 
                          access_token: Optional[str] = None,
                          session_id: Optional[str] = None,
                          user_identifier: Optional[str] = None) -> bool:
        """
        Отзыв доступа по различным критериям.
        
        Args:
            access_token: Access токен для отзыва
            session_id: ID сессии для отзыва
            user_identifier: Идентификатор пользователя
            
        Returns:
            True если успешно
        """
        try:
            success = True
            
            if access_token:
                cache_success = await self.token_cache.revoke_token(access_token)
                success &= cache_success
            
            if session_id:
                session_success = await self.session_manager.close_session(session_id)
                success &= session_success
            
            if user_identifier:
                cache_success = await self.token_cache.revoke_user_tokens(user_identifier)
                session_success = await self.session_manager.close_user_sessions(user_identifier)
                success &= (cache_success or session_success)
            
            logger.debug(f"Отзыв доступа завершен: {success}")
            return success
            
        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Ошибка отзыва доступа: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Получение статистики валидации."""
        cache_stats = await self.token_cache.get_stats()
        session_stats = await self.session_manager.get_stats()
        
        return {
            "validation_stats": self._stats,
            "cache_stats": cache_stats,
            "session_stats": session_stats
        }
    
    async def cleanup(self) -> Dict[str, int]:
        """Принудительная очистка всех компонентов."""
        cache_cleaned = await self.token_cache.cleanup()
        session_cleaned = await self.session_manager.cleanup()
        
        logger.info(f"Принудительная очистка завершена: кэш={cache_cleaned}, сессии={session_cleaned}")
        
        return {
            "tokens_cleaned": cache_cleaned,
            "sessions_cleaned": session_cleaned
        }


class OAuthCacheManager:
    """
    Главный менеджер кэша OAuth2, объединяющий все компоненты.
    Предоставляет единый интерфейс для работы с кэшем токенов и сессиями.
    """
    
    def __init__(self,
                 max_token_cache_size: int = 1000,
                 max_sessions: int = 10000,
                 token_ttl: int = 3600,
                 session_timeout: int = 3600,
                 security_level: SecurityLevel = SecurityLevel.MAXIMUM,
                 auto_start_tasks: bool = True):
        """
        Инициализация главного менеджера.
        
        Args:
            max_token_cache_size: Максимальный размер кэша токенов
            max_sessions: Максимальное количество сессий
            token_ttl: TTL токенов
            session_timeout: Таймаут сессий
            security_level: Уровень безопасности
            auto_start_tasks: Автоматический запуск фоновых задач
        """
        # Инициализация компонентов
        self.secure_storage = SecureStorage(security_level=security_level)
        self.token_cache = OAuthTokenCache(
            max_size=max_token_cache_size,
            default_ttl=token_ttl,
            secure_storage=self.secure_storage
        )
        self.session_manager = SessionManager(
            max_sessions=max_sessions,
            session_timeout=session_timeout,
            secure_storage=self.secure_storage
        )
        self.token_validator = TokenValidator(
            token_cache=self.token_cache,
            session_manager=self.session_manager
        )
        
        # Статус инициализации
        self._initialized = False
        self._tasks_started = False
        
        if auto_start_tasks:
            asyncio.create_task(self._start_tasks())
    
    async def _start_tasks(self):
        """Запуск фоновых задач."""
        await self.token_cache.start_cleanup_task()
        await self.session_manager.start_cleanup_task()
        self._tasks_started = True
        self._initialized = True
        logger.info("OAuthCacheManager полностью инициализирован")
    
    async def initialize(self) -> bool:
        """Принудительная инициализация."""
        if not self._initialized:
            await self._start_tasks()
        return self._initialized
    
    # Методы для работы с токенами
    async def store_oauth_token(self,
                              user_id: str,
                              access_token: str,
                              refresh_token: Optional[str] = None,
                              token_type: str = "Bearer",
                              expires_in: Optional[int] = None,
                              user_data: Optional[Dict[str, Any]] = None) -> bool:
        """Сохранение OAuth токена."""
        return await self.token_cache.store_token(
            user_id, access_token, refresh_token, token_type, expires_in, user_data
        )
    
    async def get_oauth_token(self, access_token: str) -> Optional[CachedToken]:
        """Получение OAuth токена."""
        return await self.token_cache.get_token(access_token)
    
    async def get_token_by_user(self, user_id: str) -> Optional[CachedToken]:
        """Получение токена по ID пользователя."""
        return await self.token_cache.get_token_by_user(user_id)
    
    # Методы для работы с сессиями
    async def create_user_session(self,
                                user_identifier: str,
                                login: str,
                                metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Создание пользовательской сессии."""
        return await self.session_manager.create_session(user_identifier, login, metadata)
    
    async def get_session(self, session_id: str) -> Optional[UserSession]:
        """Получение сессии."""
        return await self.session_manager.get_session(session_id)
    
    async def update_session_activity(self, session_id: str) -> bool:
        """Обновление активности сессии."""
        return await self.session_manager.update_activity(session_id)
    
    # Методы валидации
    async def validate_access_token(self, access_token: str, session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Валидация access токена."""
        return await self.token_validator.validate_token(access_token, session_id)
    
    async def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Валидация сессии."""
        return await self.token_validator.validate_session(session_id)
    
    # Методы отзыва
    async def revoke_token(self, access_token: str) -> bool:
        """Отзыв токена."""
        return await self.token_cache.revoke_token(access_token)
    
    async def revoke_session(self, session_id: str) -> bool:
        """Отзыв сессии."""
        return await self.session_manager.close_session(session_id)
    
    async def revoke_user_access(self, user_identifier: str) -> bool:
        """Отзыв доступа пользователя."""
        cache_result = await self.token_cache.revoke_user_tokens(user_identifier)
        session_result = await self.session_manager.close_user_sessions(user_identifier)
        return cache_result or session_result
    
    # Методы статистики и мониторинга
    async def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Получение всеобъемлющей статистики."""
        validator_stats = await self.token_validator.get_stats()
        security_stats = self.secure_storage.get_security_stats()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "security": security_stats,
            "validation": validator_stats,
            "summary": {
                "total_active_tokens": validator_stats["cache_stats"]["current_size"],
                "total_active_sessions": validator_stats["session_stats"]["current_active"],
                "total_users": validator_stats["session_stats"]["total_users_with_sessions"],
                "cache_hit_rate": validator_stats["cache_stats"]["hit_rate"]
            }
        }
    
    async def cleanup_all(self) -> Dict[str, int]:
        """Принудительная очистка всех компонентов."""
        return await self.token_validator.cleanup()
    
    async def shutdown(self):
        """Корректное завершение работы."""
        logger.info("Начало завершения работы OAuthCacheManager")
        
        await self.token_cache.stop_cleanup_task()
        await self.session_manager.stop_cleanup_task()
        
        self._initialized = False
        self._tasks_started = False
        
        logger.info("OAuthCacheManager корректно завершил работу")
    
    @asynccontextmanager
    async def lifecycle_context(self):
        """Контекстный менеджер для управления жизненным циклом."""
        try:
            await self.initialize()
            yield self
        finally:
            await self.shutdown()


# Фабрика для создания экземпляров кэша
class OAuthCacheFactory:
    """
    Фабрика для создания настроенных экземпляров OAuthCacheManager.
    """
    
    @staticmethod
    def create_production_cache(max_tokens: int = 5000, max_sessions: int = 50000) -> OAuthCacheManager:
        """Создание кэша для production окружения."""
        return OAuthCacheManager(
            max_token_cache_size=max_tokens,
            max_sessions=max_sessions,
            token_ttl=3600,
            session_timeout=7200,
            security_level=SecurityLevel.MAXIMUM,
            auto_start_tasks=True
        )
    
    @staticmethod
    def create_development_cache(max_tokens: int = 100, max_sessions: int = 1000) -> OAuthCacheManager:
        """Создание кэша для development окружения."""
        return OAuthCacheManager(
            max_token_cache_size=max_tokens,
            max_sessions=max_sessions,
            token_ttl=1800,
            session_timeout=3600,
            security_level=SecurityLevel.ENHANCED,
            auto_start_tasks=True
        )
    
    @staticmethod
    def create_test_cache(max_tokens: int = 50, max_sessions: int = 100) -> OAuthCacheManager:
        """Создание кэша для testing окружения."""
        return OAuthCacheManager(
            max_token_cache_size=max_tokens,
            max_sessions=max_sessions,
            token_ttl=300,
            session_timeout=600,
            security_level=SecurityLevel.BASIC,
            auto_start_tasks=False
        )


# Экспорт основных классов и функций
__all__ = [
    'OAuthCacheManager',
    'OAuthTokenCache', 
    'SessionManager',
    'TokenValidator',
    'SecureStorage',
    'CachedToken',
    'UserSession',
    'CacheStrategy',
    'SecurityLevel',
    'OAuthCacheFactory'
]

logger.info("Модуль oauth_cache успешно загружен")