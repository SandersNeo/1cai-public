# [NEXUS IDENTITY] ID: -8805889344508544138 | DATE: 2025-11-19

"""
Тесты для модуля OAuth Cache

Тестирует основные функции:
- SecureStorage: шифрование/расшифровка, хеширование
- OAuthTokenCache: кэширование токенов, стратегии вытеснения
- SessionManager: управление сессиями
- TokenValidator: валидация токенов
- OAuthCacheManager: интеграция компонентов
"""

import asyncio

import pytest

# Импорты тестируемых модулей
from cache.oauth_cache import (CacheStrategy, OAuthCacheFactory, OAuthCacheManager,
                               OAuthTokenCache, SecureStorage,
                               SecurityLevel, SessionManager, TokenValidator)


class TestSecureStorage:
    """Тесты для SecureStorage."""
    
    def test_initialization(self):
        """Тест инициализации."""
        storage = SecureStorage(security_level=SecurityLevel.BASIC)
        assert storage.security_level == SecurityLevel.BASIC
        assert storage._master_password is not None
    
    def test_encryption_decryption(self):
        """Тест шифрования и расшифровки."""
        storage = SecureStorage()
        original_data = "test_sensitive_data"
        
        # Шифрование
        encrypted = storage.encrypt(original_data)
        assert encrypted != original_data
        assert isinstance(encrypted, str)
        
        # Расшифровка
        decrypted = storage.decrypt(encrypted)
        assert decrypted == original_data
    
    def test_hash_secret(self):
        """Тест хеширования секретов."""
        storage = SecureStorage()
        secret = "my_secret"
        
        hash1 = storage.hash_secret(secret)
        hash2 = storage.hash_secret(secret)
        
        assert hash1 == hash2  # Одинаковые секреты -> одинаковые хеши
        assert len(hash1) == 64  # SHA256 -> 64 hex символа
    
    def test_rate_limiting(self):
        """Тест ограничения скорости доступа."""
        storage = SecureStorage()
        storage._max_attempts = 2  # Уменьшаем для теста
        
        # Первая попытка должна пройти
        assert storage._check_rate_limit("test_user") == True
        
        # Вторая попытка должна пройти
        assert storage._check_rate_limit("test_user") == True
        
        # Третья попытка должна быть заблокирована
        assert storage._check_rate_limit("test_user") == False
    
    def test_store_retrieve_data(self):
        """Тест сохранения и получения данных."""
        storage = SecureStorage()
        test_data = {"key": "value", "number": 42}
        
        # Сохранение
        result = storage.store_secure_data("test_key", test_data)
        assert result == True
        
        # Получение
        retrieved = storage.retrieve_secure_data("test_key")
        assert retrieved == test_data
        
        # Несуществующий ключ
        not_found = storage.retrieve_secure_data("nonexistent")
        assert not_found is None


class TestOAuthTokenCache:
    """Тесты для OAuthTokenCache."""
    
    @pytest.fixture
    async def token_cache(self):
        """Фикстура для создания кэша токенов."""
        cache = OAuthTokenCache(
            max_size=100,
            default_ttl=3600,
            strategy=CacheStrategy.LRU,
            auto_cleanup=False  # Отключаем автоочистку для тестов
        )
        await cache.initialize()
        yield cache
        await cache.stop_cleanup_task()
    
    async def test_store_and_retrieve_token(self, token_cache):
        """Тест сохранения и получения токена."""
        # Сохранение токена
        result = await token_cache.store_token(
            user_id="user1",
            access_token="access_token_1",
            refresh_token="refresh_token_1",
            expires_in=3600
        )
        assert result == True
        
        # Получение токена
        token = await token_cache.get_token("access_token_1")
        assert token is not None
        assert token.access_token == "access_token_1"
        assert token.refresh_token == "refresh_token_1"
        assert token.expires_in == 3600
        assert token.user_data is None
    
    async def test_get_token_by_user(self, token_cache):
        """Тест получения токена по ID пользователя."""
        await token_cache.store_token(
            user_id="user2",
            access_token="access_token_2"
        )
        
        token = await token_cache.get_token_by_user("user2")
        assert token is not None
        assert token.access_token == "access_token_2"
    
    async def test_expired_token_cleanup(self, token_cache):
        """Тест очистки истекших токенов."""
        # Сохраняем токен с коротким TTL
        await token_cache.store_token(
            user_id="user3",
            access_token="expired_token",
            expires_in=1  # 1 секунда
        )
        
        # Проверяем что токен есть
        token = await token_cache.get_token("expired_token")
        assert token is not None
        
        # Ждем истечения
        await asyncio.sleep(2)
        
        # Проверяем что токен удален
        token = await token_cache.get_token("expired_token")
        assert token is None
        
        # Проверяем очистку
        cleaned = await token_cache.cleanup()
        assert cleaned == 0  # Токен уже удален при обращении
    
    async def test_lru_eviction(self, token_cache):
        """Тест LRU стратегии вытеснения."""
        cache = OAuthTokenCache(
            max_size=2,  # Маленький размер для теста
            strategy=CacheStrategy.LRU,
            auto_cleanup=False
        )
        await cache.initialize()
        
        try:
            # Добавляем 3 токена (больше лимита)
            for i in range(3):
                await cache.store_token(
                    user_id=f"user{i}",
                    access_token=f"token{i}"
                )
            
            # Проверяем что остался только последний (LRU)
            token2 = await cache.get_token("token2")  # Обращаемся к последнему
            assert token2 is not None
            
            token0 = await cache.get_token("token0")  # Первый должен быть вытеснен
            assert token0 is None
            
        finally:
            await cache.stop_cleanup_task()
    
    async def test_token_revocation(self, token_cache):
        """Тест отзыва токена."""
        await token_cache.store_token(
            user_id="user4",
            access_token="token_to_revoke"
        )
        
        # Проверяем что токен есть
        token = await cache.get_token("token_to_revoke")
        assert token is not None
        
        # Отзываем токен
        result = await cache.revoke_token("token_to_revoke")
        assert result == True
        
        # Проверяем что токен удален
        token = await cache.get_token("token_to_revoke")
        assert token is None
    
    async def test_stats(self, token_cache):
        """Тест получения статистики."""
        # Сохраняем токен
        await token_cache.store_token(
            user_id="user5",
            access_token="token_for_stats"
        )
        
        # Получаем токен (hit)
        await token_cache.get_token("token_for_stats")
        
        # Пытаемся получить несуществующий токен (miss)
        await token_cache.get_token("nonexistent")
        
        stats = await token_cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["current_size"] == 1
        assert 0 <= stats["hit_rate"] <= 100


class TestSessionManager:
    """Тесты для SessionManager."""
    
    @pytest.fixture
    async def session_manager(self):
        """Фикстура для создания менеджера сессий."""
        manager = SessionManager(
            max_sessions=1000,
            session_timeout=3600,
            max_concurrent_sessions=5,
            secure_storage=SecureStorage()
        )
        await manager.initialize()
        yield manager
        await manager.stop_cleanup_task()
    
    async def test_create_session(self, session_manager):
        """Тест создания сессии."""
        session_id = await session_manager.create_session(
            user_identifier="user1",
            login="test_user",
            metadata={"role": "admin"}
        )
        
        assert session_id is not None
        assert session_id.startswith("session_")
        
        # Проверяем что сессия создана
        session = await session_manager.get_session(session_id)
        assert session is not None
        assert session.user_identifier == "user1"
        assert session.login == "test_user"
        assert session.metadata["role"] == "admin"
    
    async def test_session_activity(self, session_manager):
        """Тест обновления активности сессии."""
        session_id = await session_manager.create_session(
            user_identifier="user2",
            login="test_user2"
        )
        
        initial_activity = session_manager._sessions[session_id].last_activity
        
        # Обновляем активность
        result = await session_manager.update_activity(session_id)
        assert result == True
        
        # Проверяем что время обновилось
        updated_session = await session_manager.get_session(session_id)
        assert updated_session.last_activity > initial_activity
    
    async def test_session_concurrent_limit(self, session_manager):
        """Тест лимита одновременных сессий."""
        # Уменьшаем лимит для теста
        session_manager.max_concurrent_sessions = 2
        
        # Создаем максимальное количество сессий
        session_ids = []
        for i in range(2):
            session_id = await session_manager.create_session(
                user_identifier="concurrent_user",
                login=f"user{i}"
            )
            if session_id:
                session_ids.append(session_id)
        
        assert len(session_ids) == 2
        
        # Пытаемся создать третью сессию (должна быть отклонена)
        failed_session = await session_manager.create_session(
            user_identifier="concurrent_user",
            login="user3"
        )
        assert failed_session is None
    
    async def test_close_session(self, session_manager):
        """Тест закрытия сессии."""
        session_id = await session_manager.create_session(
            user_identifier="user3",
            login="test_user3"
        )
        
        # Проверяем что сессия существует
        session = await session_manager.get_session(session_id)
        assert session is not None
        
        # Закрываем сессию
        result = await session_manager.close_session(session_id)
        assert result == True
        
        # Проверяем что сессия удалена
        session = await session_manager.get_session(session_id)
        assert session is None
    
    async def test_close_user_sessions(self, session_manager):
        """Тест закрытия всех сессий пользователя."""
        user_id = "user4"
        
        # Создаем несколько сессий для пользователя
        session_ids = []
        for i in range(3):
            session_id = await session_manager.create_session(
                user_identifier=user_id,
                login=f"user4_{i}"
            )
            if session_id:
                session_ids.append(session_id)
        
        # Закрываем все сессии пользователя
        closed_count = await session_manager.close_user_sessions(user_id)
        assert closed_count == 3
        
        # Проверяем что все сессии удалены
        for session_id in session_ids:
            session = await session_manager.get_session(session_id)
            assert session is None
    
    async def test_get_active_sessions(self, session_manager):
        """Тест получения активных сессий."""
        # Создаем сессии для разных пользователей
        await session_manager.create_session("user1", "login1")
        await session_manager.create_session("user2", "login2")
        await session_manager.create_session("user1", "login3")  # Дополнительная сессия
        
        # Получаем все активные сессии
        all_sessions = await session_manager.get_active_sessions()
        assert len(all_sessions) == 3
        
        # Получаем сессии конкретного пользователя
        user1_sessions = await session_manager.get_active_sessions("user1")
        assert len(user1_sessions) == 2
        
        user2_sessions = await session_manager.get_active_sessions("user2")
        assert len(user2_sessions) == 1


class TestTokenValidator:
    """Тесты для TokenValidator."""
    
    @pytest.fixture
    async def validator_setup(self):
        """Фикстура для настройки валидатора."""
        token_cache = OAuthTokenCache(auto_cleanup=False)
        session_manager = SessionManager(auto_cleanup=False)
        
        validator = TokenValidator(
            token_cache=token_cache,
            session_manager=session_manager,
            refresh_threshold=300,
            auto_refresh=True
        )
        
        return validator, token_cache, session_manager
    
    async def test_validate_access_token(self, validator_setup):
        """Тест валидации access токена."""
        validator, token_cache, _ = validator_setup
        
        # Сохраняем токен
        await token_cache.store_token(
            user_id="user1",
            access_token="valid_token",
            expires_in=3600
        )
        
        # Валидируем существующий токен
        result = await validator.validate_access_token("valid_token")
        assert result is not None
        assert result["valid"] == True
        assert "access_token" in result
        assert "expires_in" in result
    
    async def test_validate_expired_token(self, validator_setup):
        """Тест валидации истекшего токена."""
        validator, token_cache, _ = validator_setup
        
        # Сохраняем токен с коротким TTL
        await token_cache.store_token(
            user_id="user2",
            access_token="expired_token",
            expires_in=1
        )
        
        # Ждем истечения
        await asyncio.sleep(2)
        
        # Валидируем истекший токен
        result = await validator.validate_access_token("expired_token")
        assert result is None
    
    async def test_validate_nonexistent_token(self, validator_setup):
        """Тест валидации несуществующего токена."""
        validator, _, _ = validator_setup
        
        # Валидируем несуществующий токен
        result = await validator.validate_access_token("nonexistent_token")
        assert result is None
    
    async def test_validate_session(self, validator_setup):
        """Тест валидации сессии."""
        validator, _, session_manager = validator_setup
        
        # Создаем сессию
        session_id = await session_manager.create_session(
            user_identifier="user3",
            login="test_user"
        )
        
        # Валидируем существующую сессию
        result = await validator.validate_session(session_id)
        assert result is not None
        assert result["valid"] == True
        assert result["session"]["session_id"] == session_id
        assert result["session"]["user_identifier"] == "user3"
    
    async def test_revoke_access(self, validator_setup):
        """Тест отзыва доступа."""
        validator, token_cache, session_manager = validator_setup
        
        # Создаем токен и сессию
        await token_cache.store_token("user4", "token_to_revoke")
        session_id = await session_manager.create_session("user4", "test_user")
        
        # Отзываем доступ по токену
        result = await validator.revoke_access(access_token="token_to_revoke")
        assert result == True
        
        # Проверяем что токен отозван
        token = await token_cache.get_token("token_to_revoke")
        assert token is None
    
    async def test_stats(self, validator_setup):
        """Тест получения статистики валидатора."""
        validator, _, _ = validator_setup
        
        # Выполняем несколько валидаций
        await validator.validate_access_token("nonexistent")  # miss
        await validator.validate_access_token("nonexistent2")  # miss
        
        stats = await validator.get_stats()
        assert "validation_stats" in stats
        assert stats["validation_stats"]["validations"] == 2
        assert stats["validation_stats"]["misses"] == 2


class TestOAuthCacheManager:
    """Тесты для OAuthCacheManager."""
    
    @pytest.fixture
    async def cache_manager(self):
        """Фикстура для создания менеджера кэша."""
        manager = OAuthCacheManager(
            max_token_cache_size=100,
            max_sessions=1000,
            auto_start_tasks=False  # Отключаем автозапуск для тестов
        )
        await manager.initialize()
        yield manager
        await manager.shutdown()
    
    async def test_store_oauth_token(self, cache_manager):
        """Тест сохранения OAuth токена."""
        result = await cache_manager.store_oauth_token(
            user_id="user1",
            access_token="test_access_token",
            refresh_token="test_refresh_token",
            expires_in=3600
        )
        assert result == True
    
    async def test_get_oauth_token(self, cache_manager):
        """Тест получения OAuth токена."""
        # Сохраняем токен
        await cache_manager.store_oauth_token(
            user_id="user2",
            access_token="test_token_2",
            expires_in=3600
        )
        
        # Получаем токен
        token = await cache_manager.get_oauth_token("test_token_2")
        assert token is not None
        assert token.access_token == "test_token_2"
        assert token.expires_in == 3600
    
    async def test_get_token_by_user(self, cache_manager):
        """Тест получения токена по пользователю."""
        await cache_manager.store_oauth_token(
            user_id="user3",
            access_token="user_token_3",
            expires_in=3600
        )
        
        token = await cache_manager.get_token_by_user("user3")
        assert token is not None
        assert token.access_token == "user_token_3"
    
    async def test_create_user_session(self, cache_manager):
        """Тест создания пользовательской сессии."""
        session_id = await cache_manager.create_user_session(
            user_identifier="user4",
            login="test_user",
            metadata={"role": "admin"}
        )
        
        assert session_id is not None
        assert session_id.startswith("session_")
        
        # Получаем сессию
        session = await cache_manager.get_session(session_id)
        assert session is not None
        assert session.user_identifier == "user4"
        assert session.metadata["role"] == "admin"
    
    async def test_validate_access_token(self, cache_manager):
        """Тест валидации access токена."""
        # Сохраняем токен
        await cache_manager.store_oauth_token(
            user_id="user5",
            access_token="validation_token",
            expires_in=3600
        )
        
        # Валидируем токен
        validation = await cache_manager.validate_access_token("validation_token")
        assert validation is not None
        assert validation["valid"] == True
    
    async def test_revoke_token(self, cache_manager):
        """Тест отзыва токена."""
        await cache_manager.store_oauth_token(
            user_id="user6",
            access_token="revoke_token"
        )
        
        # Отзываем токен
        result = await cache_manager.revoke_token("revoke_token")
        assert result == True
        
        # Проверяем что токен отозван
        token = await cache_manager.get_oauth_token("revoke_token")
        assert token is None
    
    async def test_revoke_session(self, cache_manager):
        """Тест отзыва сессии."""
        session_id = await cache_manager.create_user_session("user7", "test_user")
        
        # Отзываем сессию
        result = await cache_manager.revoke_session(session_id)
        assert result == True
        
        # Проверяем что сессия отозвана
        session = await cache_manager.get_session(session_id)
        assert session is None
    
    async def test_revoke_user_access(self, cache_manager):
        """Тест отзыва доступа пользователя."""
        # Создаем токен и сессию пользователя
        await cache_manager.store_oauth_token("user8", "user_token_8")
        await cache_manager.create_user_session("user8", "test_user")
        
        # Отзываем весь доступ пользователя
        result = await cache_manager.revoke_user_access("user8")
        assert result == True
    
    async def test_comprehensive_stats(self, cache_manager):
        """Тест получения комплексной статистики."""
        # Добавляем данные
        await cache_manager.store_oauth_token("user9", "stats_token_9")
        await cache_manager.create_user_session("user9", "test_user")
        
        # Получаем статистику
        stats = await cache_manager.get_comprehensive_stats()
        
        assert "timestamp" in stats
        assert "security" in stats
        assert "validation" in stats
        assert "summary" in stats
        
        # Проверяем содержание
        summary = stats["summary"]
        assert summary["total_active_tokens"] > 0
        assert summary["total_active_sessions"] > 0
        assert summary["total_users"] > 0
    
    async def test_cleanup_all(self, cache_manager):
        """Тест принудительной очистки."""
        # Добавляем данные с коротким TTL
        await cache_manager.store_oauth_token("user10", "cleanup_token", expires_in=1)
        
        # Ждем истечения
        await asyncio.sleep(2)
        
        # Выполняем очистку
        cleanup_result = await cache_manager.cleanup_all()
        
        assert "tokens_cleaned" in cleanup_result
        assert "sessions_cleaned" in cleanup_result


class TestOAuthCacheFactory:
    """Тесты для OAuthCacheFactory."""
    
    def test_create_production_cache(self):
        """Тест создания production кэша."""
        cache = OAuthCacheFactory.create_production_cache()
        
        assert isinstance(cache, OAuthCacheManager)
        # Production кэш должен иметь большие лимиты
        assert cache.token_cache.max_size >= 5000
        assert cache.session_manager.max_sessions >= 50000
    
    def test_create_development_cache(self):
        """Тест создания development кэша."""
        cache = OAuthCacheFactory.create_development_cache()
        
        assert isinstance(cache, OAuthCacheManager)
        # Development кэш должен иметь средние лимиты
        assert cache.token_cache.max_size <= 1000
        assert cache.session_manager.max_sessions <= 10000
    
    def test_create_test_cache(self):
        """Тест создания test кэша."""
        cache = OAuthCacheFactory.create_test_cache()
        
        assert isinstance(cache, OAuthCacheManager)
        # Test кэш должен иметь маленькие лимиты
        assert cache.token_cache.max_size <= 100
        assert cache.session_manager.max_sessions <= 1000
    
    def test_create_cache_with_custom_params(self):
        """Тест создания кэша с кастомными параметрами."""
        cache = OAuthCacheFactory.create_production_cache(
            max_tokens=10000,
            max_sessions=100000
        )
        
        assert isinstance(cache, OAuthCacheManager)
        assert cache.token_cache.max_size == 10000
        assert cache.session_manager.max_sessions == 100000


# Интеграционные тесты
class TestIntegration:
    """Интеграционные тесты."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Тест полного рабочего процесса."""
        # Создаем кэш-менеджер
        cache_manager = OAuthCacheManager(auto_start_tasks=False)
        await cache_manager.initialize()
        
        try:
            # 1. Создаем пользовательскую сессию
            session_id = await cache_manager.create_user_session(
                user_identifier="integration_user",
                login="integration_test",
                metadata={"test": True}
            )
            assert session_id is not None
            
            # 2. Сохраняем OAuth токены
            token_result = await cache_manager.store_oauth_token(
                user_id="integration_user",
                access_token="integration_access_token",
                refresh_token="integration_refresh_token",
                expires_in=3600,
                user_data={"client_id": "test_client"}
            )
            assert token_result == True
            
            # 3. Валидируем access токен
            validation = await cache_manager.validate_access_token(
                "integration_access_token",
                session_id
            )
            assert validation is not None
            assert validation["valid"] == True
            
            # 4. Получаем токен по пользователю
            user_token = await cache_manager.get_token_by_user("integration_user")
            assert user_token is not None
            assert user_token.access_token == "integration_access_token"
            
            # 5. Валидируем сессию
            session_validation = await cache_manager.validate_session(session_id)
            assert session_validation is not None
            assert session_validation["valid"] == True
            
            # 6. Получаем статистику
            stats = await cache_manager.get_comprehensive_stats()
            assert stats["summary"]["total_active_tokens"] == 1
            assert stats["summary"]["total_active_sessions"] == 1
            
            # 7. Отзываем доступ пользователя
            revoke_result = await cache_manager.revoke_user_access("integration_user")
            assert revoke_result == True
            
            # 8. Проверяем что данные удалены
            final_token = await cache_manager.get_token("integration_access_token")
            assert final_token is None
            
            final_session = await cache_manager.get_session(session_id)
            assert final_session is None
            
        finally:
            await cache_manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Тест параллельных операций."""
        cache_manager = OAuthCacheManager(auto_start_tasks=False)
        await cache_manager.initialize()
        
        try:
            # Создаем множество токенов параллельно
            tasks = []
            for i in range(10):
                task = cache_manager.store_oauth_token(
                    user_id=f"concurrent_user_{i}",
                    access_token=f"concurrent_token_{i}",
                    expires_in=3600
                )
                tasks.append(task)
            
            # Ждем завершения всех операций
            results = await asyncio.gather(*tasks)
            assert all(results)  # Все операции должны быть успешными
            
            # Проверяем что все токены сохранены
            for i in range(10):
                token = await cache_manager.get_token(f"concurrent_token_{i}")
                assert token is not None
                assert token.access_token == f"concurrent_token_{i}"
            
            # Получаем статистику
            stats = await cache_manager.get_comprehensive_stats()
            assert stats["summary"]["total_active_tokens"] == 10
            
        finally:
            await cache_manager.shutdown()


# Запуск тестов
if __name__ == "__main__":
    # Настройка pytest
    pytest_args = [
        __file__,
        "-v",  # Подробный вывод
        "--tb=short",  # Краткий traceback
        "--asyncio-mode=auto"  # Автоматический режим для asyncio
    ]
    
    # Запуск тестов
    exit_code = pytest.main(pytest_args)
    exit(exit_code)