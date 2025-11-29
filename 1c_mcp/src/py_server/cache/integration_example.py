# [NEXUS IDENTITY] ID: -6662657690313080087 | DATE: 2025-11-19

"""
Интеграционный пример использования OAuth Cache с существующим OAuth2 модулем

Демонстрирует:
1. Инициализацию OAuthCacheManager
2. Интеграцию с OAuth2Service и OAuth2Store
3. Безопасное кэширование токенов
4. Управление сессиями пользователей
5. Валидацию и обновление токенов
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from auth.oauth2 import OAuth2Service, OAuth2Store

# Импорты модулей
from cache import OAuthCacheFactory, OAuthCacheManager

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntegratedOAuthService:
    """
    Интегрированный OAuth сервис, объединяющий существующий OAuth2Service
    с новым модулем кэширования.
    """
    
    def __init__(self, 
                 cache_manager: Optional[OAuthCacheManager] = None,
                 environment: str = "development"):
        """
        Инициализация интегрированного сервиса.
        
        Args:
            cache_manager: Менеджер кэша (создается автоматически если не указан)
            environment: Окружение для настройки параметров
        """
        # Создаем кэш-менеджер если не предоставлен
        self.cache_manager = cache_manager or OAuthCacheFactory.create_development_cache()
        
        # Инициализируем базовый OAuth2 сервис
        self.oauth2_store = OAuth2Store()
        self.oauth2_service = OAuth2Service(
            store=self.oauth2_store,
            code_ttl=300,  # 5 минут
            access_ttl=3600,  # 1 час
            refresh_ttl=86400  # 24 часа
        )
        
        # Запускаем фоновые задачи кэша
        asyncio.create_task(self._start_background_tasks())
        
        logger.info(f"IntegratedOAuthService инициализирован для окружения: {environment}")
    
    async def _start_background_tasks(self):
        """Запуск фоновых задач."""
        await self.cache_manager.initialize()
    
    async def authorize_user(self, 
                           user_identifier: str,
                           login: str, 
                           password: str,
                           redirect_uri: str,
                           code_challenge: str,
                           metadata: Optional[dict] = None) -> str:
        """
        Авторизация пользователя с созданием сессии и кэшированием.
        
        Args:
            user_identifier: Уникальный идентификатор пользователя
            login: Логин пользователя
            password: Пароль пользователя  
            redirect_uri: URI для редиректа
            code_challenge: PKCE challenge
            metadata: Дополнительные метаданные
            
        Returns:
            Authorization code
        """
        try:
            # Создаем пользовательскую сессию
            session_id = await self.cache_manager.create_user_session(
                user_identifier=user_identifier,
                login=login,
                metadata=metadata or {}
            )
            
            if not session_id:
                raise RuntimeError("Не удалось создать сессию пользователя")
            
            # Генерируем authorization code через существующий сервис
            auth_code = self.oauth2_service.generate_authorization_code(
                login=login,
                password=password,
                redirect_uri=redirect_uri,
                code_challenge=code_challenge
            )
            
            logger.info(f"Пользователь {login} авторизован, session_id: {session_id}")
            return auth_code
            
        except Exception as e:
            logger.error(f"Ошибка авторизации пользователя {login}: {e}")
            raise
    
    async def exchange_authorization_code(self,
                                        authorization_code: str,
                                        redirect_uri: str,
                                        code_verifier: str) -> dict:
        """
        Обмен authorization code на токены с кэшированием.
        
        Args:
            authorization_code: Код авторизации
            redirect_uri: URI редиректа
            code_verifier: PKCE verifier
            
        Returns:
            Словарь с токенами и метаданными
        """
        try:
            # Обмениваем код на токены через существующий сервис
            tokens_data = self.oauth2_service.exchange_code_for_tokens(
                code=authorization_code,
                redirect_uri=redirect_uri,
                code_verifier=code_verifier
            )
            
            if not tokens_data:
                raise ValueError("Недействительный authorization code")
            
            access_token, token_type, expires_in, refresh_token = tokens_data
            
            # Извлекаем данные пользователя из OAuth2 store
            # В реальной реализации здесь была бы связь с OAuth2Service
            user_identifier = f"user_{hash(access_token) % 10000}"  # Пример
            
            # Кэшируем токены
            cache_success = await self.cache_manager.store_oauth_token(
                user_id=user_identifier,
                access_token=access_token,
                refresh_token=refresh_token,
                token_type=token_type,
                expires_in=expires_in,
                user_data={
                    "token_type": token_type,
                    "issued_at": datetime.now().isoformat(),
                    "authorization_method": "pkce"
                }
            )
            
            if not cache_success:
                logger.warning("Не удалось кэшировать токены")
            
            result = {
                "access_token": access_token,
                "token_type": token_type,
                "expires_in": expires_in,
                "refresh_token": refresh_token,
                "user_identifier": user_identifier,
                "cached": cache_success
            }
            
            logger.info(f"Токены выданы для пользователя {user_identifier}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка обмена кода на токены: {e}")
            raise
    
    async def validate_access_token(self, access_token: str, session_id: Optional[str] = None) -> dict:
        """
        Валидация access токена с проверкой кэша.
        
        Args:
            access_token: Access токен для проверки
            session_id: Опциональный ID сессии
            
        Returns:
            Словарь с данными валидации
        """
        try:
            # Проверяем токен через кэш-менеджер
            validation_result = await self.cache_manager.validate_access_token(
                access_token=access_token,
                session_id=session_id
            )
            
            if not validation_result:
                return {
                    "valid": False,
                    "reason": "token_invalid_or_expired",
                    "access_token": access_token[:16] + "..."
                }
            
            # Дополнительная проверка через базовый OAuth2 сервис
            credentials = self.oauth2_service.validate_access_token(access_token)
            
            return {
                "valid": True,
                "user_data": validation_result["user_data"],
                "expires_in": validation_result["expires_in"],
                "access_count": validation_result["access_count"],
                "oauth_credentials": bool(credentials),
                "access_token": access_token[:16] + "..."
            }
            
        except Exception as e:
            logger.error(f"Ошибка валидации токена: {e}")
            return {
                "valid": False,
                "reason": "validation_error",
                "error": str(e)
            }
    
    async def refresh_user_token(self, refresh_token: str) -> dict:
        """
        Обновление токенов пользователя.
        
        Args:
            refresh_token: Refresh токен
            
        Returns:
            Словарь с новыми токенами
        """
        try:
            # Обновляем токены через базовый OAuth2 сервис
            tokens_data = self.oauth2_service.refresh_tokens(refresh_token)
            
            if not tokens_data:
                raise ValueError("Недействительный refresh token")
            
            new_access_token, token_type, expires_in, new_refresh_token = tokens_data
            
            # Находим пользователя по refresh_token
            # В реальной реализации здесь был бы поиск в кэше
            user_identifier = f"user_{hash(refresh_token) % 10000}"
            
            # Кэшируем новые токены
            cache_success = await self.cache_manager.store_oauth_token(
                user_id=user_identifier,
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                token_type=token_type,
                expires_in=expires_in,
                user_data={
                    "token_type": token_type,
                    "issued_at": datetime.now().isoformat(),
                    "refresh_method": "refresh_token"
                }
            )
            
            result = {
                "access_token": new_access_token,
                "token_type": token_type,
                "expires_in": expires_in,
                "refresh_token": new_refresh_token,
                "user_identifier": user_identifier,
                "cached": cache_success
            }
            
            logger.info(f"Токены обновлены для пользователя {user_identifier}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка обновления токенов: {e}")
            raise
    
    async def revoke_user_access(self, 
                               user_identifier: str, 
                               reason: str = "user_logout") -> dict:
        """
        Полный отзыв доступа пользователя.
        
        Args:
            user_identifier: Идентификатор пользователя
            reason: Причина отзыва
            
        Returns:
            Словарь с результатом операции
        """
        try:
            # Отзываем токены через кэш-менеджер
            tokens_revoked = await self.cache_manager.revoke_user_access(user_identifier)
            
            # Отзываем сессии пользователя
            sessions_closed = await self.cache_manager.cache_manager.session_manager.close_user_sessions(user_identifier)
            
            result = {
                "user_identifier": user_identifier,
                "tokens_revoked": tokens_revoked,
                "sessions_closed": sessions_closed,
                "reason": reason,
                "revoked_at": datetime.now().isoformat()
            }
            
            logger.info(f"Доступ отозван для пользователя {user_identifier}: {reason}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка отзыва доступа для {user_identifier}: {e}")
            raise
    
    async def get_user_session_info(self, session_id: str) -> dict:
        """
        Получение информации о сессии пользователя.
        
        Args:
            session_id: ID сессии
            
        Returns:
            Словарь с информацией о сессии
        """
        try:
            session_data = await self.cache_manager.get_session(session_id)
            
            if not session_data:
                return {
                    "valid": False,
                    "reason": "session_not_found_or_expired"
                }
            
            # Валидируем связанный токен
            user_tokens = await self.cache_manager.get_token_by_user(session_data.user_identifier)
            token_valid = False
            if user_tokens:
                validation = await self.cache_manager.validate_access_token(
                    user_tokens.access_token,
                    session_id
                )
                token_valid = validation.get("valid", False)
            
            return {
                "valid": True,
                "session": {
                    "session_id": session_data.session_id,
                    "user_identifier": session_data.user_identifier,
                    "login": session_data.login,
                    "age": session_data.age,
                    "inactive_time": session_data.inactive_time,
                    "access_count": session_data.access_count,
                    "created_at": session_data.created_at.isoformat(),
                    "last_activity": session_data.last_activity.isoformat(),
                    "active": session_data.active
                },
                "token_valid": token_valid,
                "metadata": session_data.metadata
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения информации о сессии {session_id}: {e}")
            return {
                "valid": False,
                "reason": "error",
                "error": str(e)
            }
    
    async def get_comprehensive_status(self) -> dict:
        """
        Получение полного статуса системы.
        
        Returns:
            Словарь со всей статистикой
        """
        try:
            stats = await self.cache_manager.get_comprehensive_stats()
            
            # Добавляем статистику OAuth2 store
            oauth_stats = {
                "auth_codes_count": len(self.oauth2_store.auth_codes),
                "access_tokens_count": len(self.oauth2_store.access_tokens),
                "refresh_tokens_count": len(self.oauth2_store.refresh_tokens)
            }
            
            return {
                "timestamp": datetime.now().isoformat(),
                "cache_stats": stats,
                "oauth2_stats": oauth_stats,
                "integration_healthy": True
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статуса: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "integration_healthy": False
            }
    
    async def cleanup_expired_data(self) -> dict:
        """
        Принудительная очистка истекших данных.
        
        Returns:
            Словарь с результатами очистки
        """
        try:
            # Очищаем кэш-менеджер
            cache_cleanup = await self.cache_manager.cleanup_all()
            
            # Очищаем OAuth2 store (вручную)
            oauth_cleanup = {
                "auth_codes_cleaned": 0,
                "access_tokens_cleaned": 0,
                "refresh_tokens_cleaned": 0
            }
            
            # В реальной реализации здесь был бы вызов _cleanup_expired для OAuth2Store
            # self.oauth2_store._cleanup_expired()
            
            result = {
                "timestamp": datetime.now().isoformat(),
                "cache_cleanup": cache_cleanup,
                "oauth_cleanup": oauth_cleanup,
                "total_cleaned": sum(cache_cleanup.values()) + sum(oauth_cleanup.values())
            }
            
            logger.info(f"Очистка завершена: очищено {result['total_cleaned']} элементов")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка очистки данных: {e}")
            raise
    
    async def shutdown(self):
        """Корректное завершение работы сервиса."""
        logger.info("Завершение работы IntegratedOAuthService")
        await self.cache_manager.shutdown()


# Демонстрационные функции
async def demo_basic_usage():
    """Демонстрация базового использования."""
    logger.info("=== Демонстрация базового использования ===")
    
    # Создаем интегрированный сервис
    oauth_service = IntegratedOAuthService(environment="development")
    
    try:
        # 1. Авторизация пользователя
        auth_code = await oauth_service.authorize_user(
            user_identifier="user_123",
            login="test_user",
            password="test_password",
            redirect_uri="https://example.com/callback",
            code_challenge="challenge_example",
            metadata={"ip": "192.168.1.100", "user_agent": "Mozilla/5.0"}
        )
        print(f"Authorization Code: {auth_code[:16]}...")
        
        # 2. Обмен кода на токены
        tokens = await oauth_service.exchange_authorization_code(
            authorization_code=auth_code,
            redirect_uri="https://example.com/callback",
            code_verifier="verifier_example"
        )
        print(f"Access Token: {tokens['access_token'][:16]}...")
        print(f"Token Cached: {tokens['cached']}")
        
        # 3. Валидация токена
        validation = await oauth_service.validate_access_token(tokens['access_token'])
        print(f"Token Valid: {validation['valid']}")
        
        # 4. Получение статистики
        status = await oauth_service.get_comprehensive_status()
        print(f"Active Tokens: {status['cache_stats']['summary']['total_active_tokens']}")
        
    finally:
        await oauth_service.shutdown()


async def demo_session_management():
    """Демонстрация управления сессиями."""
    logger.info("=== Демонстрация управления сессиями ===")
    
    oauth_service = IntegratedOAuthService(environment="development")
    
    try:
        # Создаем сессию
        session_id = await oauth_service.cache_manager.create_user_session(
            user_identifier="user_456",
            login="demo_user",
            metadata={"role": "admin", "department": "IT"}
        )
        print(f"Session ID: {session_id}")
        
        # Получаем информацию о сессии
        session_info = await oauth_service.get_user_session_info(session_id)
        print(f"Session Valid: {session_info['valid']}")
        print(f"User Login: {session_info.get('session', {}).get('login')}")
        
        # Обновляем активность
        updated = await oauth_service.cache_manager.update_session_activity(session_id)
        print(f"Activity Updated: {updated}")
        
        # Отзываем доступ
        revoke_result = await oauth_service.revoke_user_access(
            user_identifier="user_456",
            reason="demo_completed"
        )
        print(f"Access Revoked: {revoke_result['tokens_revoked']}")
        
    finally:
        await oauth_service.shutdown()


async def demo_cache_performance():
    """Демонстрация производительности кэша."""
    logger.info("=== Демонстрация производительности кэша ===")
    
    # Создаем кэш для тестирования производительности
    cache_manager = OAuthCacheManager(
        max_token_cache_size=100,
        max_sessions=500,
        token_ttl=3600,
        auto_start_tasks=True
    )
    
    try:
        await cache_manager.initialize()
        
        # Сохраняем несколько токенов
        start_time = datetime.now()
        for i in range(50):
            await cache_manager.store_oauth_token(
                user_id=f"user_{i}",
                access_token=f"token_{i}_{secrets.token_hex(16)}",
                user_data={"test": True, "index": i}
            )
        
        # Тестируем получение токенов
        for i in range(50):
            token = await cache_manager.get_token_by_user(f"user_{i}")
            assert token is not None, f"Token not found for user_{i}"
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Получаем статистику
        stats = await cache_manager.get_comprehensive_stats()
        
        print(f"Performance Test Results:")
        print(f"  Duration: {duration:.3f}s")
        print(f"  Cache Hit Rate: {stats['cache_stats']['hit_rate']}%")
        print(f"  Memory Usage: {stats['cache_stats']['memory_usage_mb']} MB")
        print(f"  Total Tokens: {stats['summary']['total_active_tokens']}")
        
    finally:
        await cache_manager.shutdown()


async def main():
    """Главная демонстрационная функция."""
    try:
        await demo_basic_usage()
        print("\n" + "="*50 + "\n")
        
        await demo_session_management()
        print("\n" + "="*50 + "\n")
        
        await demo_cache_performance()
        print("\n" + "="*50 + "\n")
        
        logger.info("Все демонстрации завершены успешно")
        
    except Exception as e:
        logger.error(f"Ошибка в демонстрации: {e}")
        raise


if __name__ == "__main__":
    # Запуск демонстрации
    asyncio.run(main())