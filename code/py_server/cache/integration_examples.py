# [NEXUS IDENTITY] ID: 6832659371708019264 | DATE: 2025-11-19

"""
Интеграция MCP Tools Cache с mcp_server.py и onec_client.py

Содержит практические примеры использования кэширования в контексте
MCP сервера и клиента 1С.

Основные сценарии:
1. Кэширование результатов вызовов 1С
2. Кэширование метаданных конфигурации
3. Кэширование агрегированных данных
4. Инвалидация кэша при изменениях
5. Мониторинг и метрики

Версия: 1.0.0
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .mcp_cache import (cached, get_cache, get_cache_stats,
                        init_cache)

logger = logging.getLogger(__name__)


class OneCCacheIntegration:
    """
    Класс для интеграции кэша с клиентом 1С
    """
    
    def __init__(self):
        self.cache = get_cache()
        
    async def cache_1c_query_result(self, 
                                   query_text: str,
                                   params: Dict[str, Any],
                                   result: Any) -> bool:
        """
        Кэширует результат запроса к 1С
        
        Args:
            query_text: Текст запроса
            params: Параметры запроса
            result: Результат
            
        Returns:
            True если кэширование успешно
        """
        # Генерируем ключ на основе запроса и параметров
        key_data = f"1c_query:{hashlib.sha256(query_text.encode()).hexdigest()}:{json.dumps(params, sort_keys=True)}"
        cache_key = hashlib.sha256(key_data.encode()).hexdigest()
        
        # Определяем TTL в зависимости от типа запроса
        ttl = self._determine_query_ttl(query_text)
        
        return await self.cache.set_async(
            cache_key, 
            {
                'result': result,
                'query': query_text,
                'params': params,
                'cached_at': datetime.now().isoformat()
            },
            ttl=ttl,
            data_type='api_response',
            metadata={'source': '1c_query', 'query_hash': hashlib.sha256(query_text.encode()).hexdigest()}
        )
    
    async def get_cached_1c_query(self,
                                 query_text: str,
                                 params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Получает закэшированный результат запроса к 1С
        
        Args:
            query_text: Текст запроса
            params: Параметры запроса
            
        Returns:
            Закэшированный результат или None
        """
        key_data = f"1c_query:{hashlib.sha256(query_text.encode()).hexdigest()}:{json.dumps(params, sort_keys=True)}"
        cache_key = hashlib.sha256(key_data.encode()).hexdigest()
        
        cached_data = await self.cache.get_async(cache_key, 'api_response')
        
        if cached_data and 'result' in cached_data:
            logger.debug(f"Найден закэшированный результат запроса: {query_text[:100]}...")
            return cached_data
        
        return None
    
    def _determine_query_ttl(self, query_text: str) -> float:
        """Определяет TTL на основе типа запроса"""
        query_lower = query_text.lower()
        
        # Справочники - более длительный TTL
        if any(keyword in query_lower for keyword in ['справочник', 'catalog', 'выбрать']):
            return 30 * 60  # 30 минут
        
        # Документы - средний TTL
        elif any(keyword in query_lower for keyword in ['документ', 'document']):
            return 10 * 60  # 10 минут
        
        # Регистры - короткий TTL
        elif any(keyword in query_lower for keyword in ['регистр', 'register']):
            return 5 * 60  # 5 минут
        
        # Отчёты - зависит от сложности
        elif any(keyword in query_lower for keyword in ['отчёт', 'report']):
            return 15 * 60  # 15 минут
        
        # По умолчанию
        return 10 * 60  # 10 минут


class MCPServerCacheIntegration:
    """
    Класс для интеграции кэша с MCP сервером
    """
    
    def __init__(self):
        self.cache = get_cache()
        self.onec_integration = OneCCacheIntegration()
    
    async def cache_tool_execution(self,
                                  tool_name: str,
                                  arguments: Dict[str, Any],
                                  result: Any) -> bool:
        """
        Кэширует результат выполнения MCP инструмента
        
        Args:
            tool_name: Имя инструмента
            arguments: Аргументы
            result: Результат
            
        Returns:
            True если кэширование успешно
        """
        cache_key = self._generate_tool_cache_key(tool_name, arguments)
        
        # Определяем TTL и тип данных на основе инструмента
        ttl, data_type = self._get_tool_cache_config(tool_name)
        
        return await self.cache.set_async(
            cache_key,
            {
                'result': result,
                'tool_name': tool_name,
                'arguments': arguments,
                'executed_at': datetime.now().isoformat()
            },
            ttl=ttl,
            data_type=data_type,
            metadata={
                'source': 'mcp_tool',
                'tool_name': tool_name,
                'arg_types': {k: type(v).__name__ for k, v in arguments.items()}
            }
        )
    
    async def get_cached_tool_execution(self,
                                       tool_name: str,
                                       arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Получает закэшированный результат выполнения инструмента
        
        Args:
            tool_name: Имя инструмента
            arguments: Аргументы
            
        Returns:
            Закэшированный результат или None
        """
        cache_key = self._generate_tool_cache_key(tool_name, arguments)
        
        cached_data = await self.cache.get_async(cache_key, self._get_tool_cache_config(tool_name)[1])
        
        if cached_data and 'result' in cached_data:
            logger.debug(f"Найден закэшированный результат инструмента: {tool_name}")
            return cached_data
        
        return None
    
    def _generate_tool_cache_key(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Генерирует ключ кэша для инструмента"""
        import hashlib

        # Сортируем аргументы для консистентности
        sorted_args = json.dumps(arguments, sort_keys=True)
        key_data = f"tool:{tool_name}:{sorted_args}"
        
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    def _get_tool_cache_config(self, tool_name: str) -> tuple[float, str]:
        """Возвращает конфигурацию кэша для инструмента"""
        
        # Инструменты для чтения метаданных - длительный TTL
        if tool_name in ['get_catalog_info', 'get_document_structure', 'get_register_info']:
            return 30 * 60, 'metadata'
        
        # Инструменты для получения данных - средний TTL
        elif tool_name in ['get_catalog_list', 'get_document_list', 'get_register_data']:
            return 10 * 60, 'api_response'
        
        # Инструменты для отчётов - зависит от периода
        elif 'report' in tool_name or 'aggregate' in tool_name:
            return 15 * 60, 'aggregates'
        
        # Инструменты для операций - короткий TTL
        elif tool_name in ['create_document', 'update_record', 'delete_item']:
            return 2 * 60, 'dynamic'
        
        # По умолчанию
        return 10 * 60, 'stable'
    
    @cached(ttl=300, data_type='metadata')
    def get_cached_catalog_structure(self, catalog_name: str) -> Dict[str, Any]:
        """Получает и кэширует структуру справочника"""
        # Здесь был бы реальный вызов к 1С
        return {
            'catalog_name': catalog_name,
            'fields': ['Код', 'Наименование', 'ДатаСоздания'],
            'hierarchical': True,
            'has_owners': False
        }
    
    @cached(ttl=600, data_type='aggregates')
    def get_cached_aggregate_data(self, 
                                 aggregate_type: str,
                                 period_start: str,
                                 period_end: str,
                                 filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Получает и кэширует агрегированные данные"""
        # Здесь был бы реальный расчёт агрегатов
        return [
            {'period': '2024-01', 'value': 1000, 'count': 100},
            {'period': '2024-02', 'value': 1200, 'count': 120}
        ]


class CacheManager:
    """
    Менеджер кэша для администрирования и мониторинга
    """
    
    def __init__(self):
        self.cache = get_cache()
        self.mcp_integration = MCPServerCacheIntegration()
        self.onec_integration = OneCCacheIntegration()
    
    def get_detailed_stats(self) -> Dict[str, Any]:
        """Возвращает детальную статистику кэша"""
        base_stats = get_cache_stats()
        
        # Добавляем специфичную информацию
        detailed_stats = {
            **base_stats,
            'cache_distribution': self._get_cache_distribution(),
            'top_cached_tools': self._get_top_cached_tools(),
            'expired_entries_count': self._count_expired_entries(),
            'memory_usage_by_type': self._get_memory_usage_by_type(),
            'invalidation_events': self._get_invalidation_events(),
            'performance_metrics': self._get_performance_metrics()
        }
        
        return detailed_stats
    
    def _get_cache_distribution(self) -> Dict[str, int]:
        """Возвращает распределение кэша по типам"""
        distribution = {
            'metadata': 0,
            'aggregates': 0,
            'tool_config': 0,
            'api_response': 0,
            'stable': 0,
            'dynamic': 0
        }
        
        # Анализируем ключи в кэше
        for key in self.cache._cache.keys():
            if key.startswith('metadata:'):
                distribution['metadata'] += 1
            elif key.startswith('aggregates:'):
                distribution['aggregates'] += 1
            elif key.startswith('tool_config:'):
                distribution['tool_config'] += 1
            elif key.startswith('tool:'):
                distribution['tool_config'] += 1
            elif key.startswith('1c_query:'):
                distribution['api_response'] += 1
            else:
                distribution['stable'] += 1
        
        return distribution
    
    def _get_top_cached_tools(self) -> List[Dict[str, Any]]:
        """Возвращает топ закэшированных инструментов"""
        tool_stats = {}
        
        for key, entry in self.cache._cache.items():
            if key.startswith('tool:'):
                # Извлекаем имя инструмента (упрощённо)
                parts = key.split(':')
                if len(parts) >= 2:
                    tool_name = parts[1]
                    if tool_name not in tool_stats:
                        tool_stats[tool_name] = {
                            'tool_name': tool_name,
                            'access_count': 0,
                            'total_age': 0,
                            'last_access': 0
                        }
                    
                    tool_stats[tool_name]['access_count'] += entry.access_count
                    tool_stats[tool_name]['total_age'] += entry.age
                    tool_stats[tool_name]['last_access'] = max(
                        tool_stats[tool_name]['last_access'], entry.last_access
                    )
        
        # Сортируем по количеству доступов
        sorted_tools = sorted(
            tool_stats.values(),
            key=lambda x: x['access_count'],
            reverse=True
        )
        
        return sorted_tools[:10]  # Топ 10
    
    def _count_expired_entries(self) -> int:
        """Возвращает количество истёкших записей"""
        count = 0
        for entry in self.cache._cache.values():
            if entry.is_expired:
                count += 1
        return count
    
    def _get_memory_usage_by_type(self) -> Dict[str, float]:
        """Возвращает использование памяти по типам (в MB)"""
        usage = {
            'metadata': 0.0,
            'aggregates': 0.0,
            'tool_config': 0.0,
            'api_response': 0.0,
            'stable': 0.0,
            'dynamic': 0.0
        }
        
        for key, entry in self.cache._cache.items():
            size_mb = entry.size_bytes / (1024 * 1024)
            
            if key.startswith('metadata:'):
                usage['metadata'] += size_mb
            elif key.startswith('aggregates:'):
                usage['aggregates'] += size_mb
            elif key.startswith('tool_config:') or key.startswith('tool:'):
                usage['tool_config'] += size_mb
            elif key.startswith('1c_query:'):
                usage['api_response'] += size_mb
            else:
                usage['stable'] += size_mb
        
        return usage
    
    def _get_invalidation_events(self) -> List[Dict[str, Any]]:
        """Возвращает события инвалидации (заглушка)"""
        # В реальной реализации здесь были бы логи инвалидации
        return []
    
    def _get_performance_metrics(self) -> Dict[str, float]:
        """Возвращает метрики производительности кэша"""
        metrics = self.cache.get_metrics()
        
        return {
            'hit_ratio': metrics.hit_ratio,
            'avg_response_time': metrics.avg_response_time,
            'error_rate': metrics.errors / max(1, metrics.total_requests),
            'eviction_rate': metrics.evictions / max(1, metrics.total_requests)
        }
    
    async def cleanup_expired_entries(self) -> Dict[str, int]:
        """
        Очищает истёкшие записи и возвращает статистику
        
        Returns:
            Словарь с количеством очищенных записей по типам
        """
        expired_by_type = {
            'metadata': 0,
            'aggregates': 0,
            'tool_config': 0,
            'api_response': 0,
            'stable': 0,
            'dynamic': 0
        }
        
        keys_to_remove = []
        
        for key, entry in self.cache._cache.items():
            if entry.is_expired:
                keys_to_remove.append(key)
                
                # Определяем тип для статистики
                if key.startswith('metadata:'):
                    expired_by_type['metadata'] += 1
                elif key.startswith('aggregates:'):
                    expired_by_type['aggregates'] += 1
                elif key.startswith('tool_config:') or key.startswith('tool:'):
                    expired_by_type['tool_config'] += 1
                elif key.startswith('1c_query:'):
                    expired_by_type['api_response'] += 1
                else:
                    expired_by_type['stable'] += 1
        
        # Удаляем записи
        for key in keys_to_remove:
            self.cache.delete(key)
        
        logger.info(f"Очищено {len(keys_to_remove)} истёкших записей из кэша")
        
        return expired_by_type
    
    async def warm_up_cache(self) -> Dict[str, int]:
        """
        Прогревает кэш популярными данными
        
        Returns:
            Словарь с количеством загруженных записей по типам
        """
        loaded_by_type = {
            'metadata': 0,
            'aggregates': 0,
            'tool_config': 0,
            'api_response': 0,
            'stable': 0,
            'dynamic': 0
        }
        
        # Здесь можно добавить логику предзагрузки популярных данных
        # Например, часто используемые справочники, общие настройки и т.д.
        
        popular_catalogs = ['Пользователи', 'Организации', 'Валюты']
        for catalog in popular_catalogs:
            try:
                # Имитация загрузки структуры справочника
                structure = self.mcp_integration.get_cached_catalog_structure(catalog)
                if structure:
                    loaded_by_type['metadata'] += 1
            except Exception as e:
                logger.warning(f"Не удалось прогреть кэш для справочника {catalog}: {e}")
        
        logger.info(f"Прогрев кэша завершён: {loaded_by_type}")
        return loaded_by_type


# Пример интеграции с mcp_server.py
def setup_cache_integration():
    """
    Настройка интеграции кэша с MCP сервером
    Вызывается при инициализации сервера
    """
    # Инициализируем кэш
    init_cache(
        max_size_mb=100,
        default_ttl_stable=30 * 60,  # 30 минут для стабильных данных
        default_ttl_dynamic=5 * 60,   # 5 минут для динамических данных
        persistent_cache_dir="./cache_data",
        strategy=None  # TTLCacheStrategy по умолчанию
    )
    
    # Создаём экземпляры интеграции
    cache_manager = CacheManager()
    mcp_integration = MCPServerCacheIntegration()
    
    logger.info("Интеграция кэша с MCP сервером настроена")
    
    return {
        'cache_manager': cache_manager,
        'mcp_integration': mcp_integration
    }


# Пример использования в mcp_server.py
async def handle_mcp_tool_with_cache(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Пример обработки MCP инструмента с кэшированием
    """
    mcp_integration = MCPServerCacheIntegration()
    
    # Проверяем кэш
    cached_result = await mcp_integration.get_cached_tool_execution(tool_name, arguments)
    if cached_result:
        logger.info(f"Возвращён закэшированный результат для инструмента {tool_name}")
        return {
            'content': [{
                'type': 'text',
                'text': f"Результат получен из кэша: {cached_result['result']}"
            }]
        }
    
    # Выполняем инструмент
    # result = await execute_1c_tool(tool_name, arguments)
    
    # Для примера используем заглушку
    result = {"tool": tool_name, "args": arguments, "status": "executed"}
    
    # Кэшируем результат
    await mcp_integration.cache_tool_execution(tool_name, arguments, result)
    
    return {
        'content': [{
            'type': 'text',
            'text': f"Результат: {result}"
        }]
    }


# Пример использования в onec_client.py
async def execute_1c_query_with_cache(query_text: str, params: Dict[str, Any]) -> Any:
    """
    Пример выполнения запроса к 1С с кэшированием
    """
    onec_integration = OneCCacheIntegration()
    
    # Проверяем кэш
    cached_result = await onec_integration.get_cached_1c_query(query_text, params)
    if cached_result:
        logger.debug(f"Возвращён закэшированный результат запроса")
        return cached_result['result']
    
    # Выполняем запрос
    # result = await execute_1c_query(query_text, params)
    
    # Для примера используем заглушку
    result = [{"id": 1, "name": "Тест", "value": 100}]
    
    # Кэшируем результат
    await onec_integration.cache_1c_query_result(query_text, params, result)
    
    return result


# Функции для периодического обслуживания кэша
async def periodic_cache_maintenance():
    """
    Периодическое обслуживание кэша
    Запускается в фоне (например, каждый час)
    """
    cache_manager = CacheManager()
    
    logger.info("Начинается периодическое обслуживание кэша")
    
    # Очищаем истёкшие записи
    await cache_manager.cleanup_expired_entries()
    
    # Получаем статистику
    stats = cache_manager.get_detailed_stats()
    
    # Логируем состояние
    logger.info(f"Состояние кэша: {stats['total_entries']} записей, "
               f"использование памяти: {stats['memory_usage_mb']:.2f}MB, "
               f"hit ratio: {stats['hit_ratio']:.2%}")
    
    # Проверяем использование памяти
    if stats['memory_usage_mb'] > 90:  # Если используется > 90% памяти
        logger.warning("Высокое использование памяти кэша, выполняется очистка")
        # Здесь можно добавить дополнительную логику очистки
    
    # Прогреваем кэш если нужно
    if stats['total_entries'] < 10:  # Если кэш почти пустой
        logger.info("Кэш почти пустой, выполняется прогрев")
        await cache_manager.warm_up_cache()


if __name__ == "__main__":
    # Пример инициализации и использования
    import hashlib

    # Настройка логирования
    logging.basicConfig(level=logging.INFO)
    
    # Инициализация
    integrations = setup_cache_integration()
    
    # Пример использования
    async def example_usage():
        # Тест кэширования инструмента
        result = await handle_mcp_tool_with_cache("get_catalog_info", {"catalog": "Пользователи"})
        print("Результат инструмента:", result)
        
        # Тест кэширования запроса к 1С
        query_result = await execute_1c_query_with_cache(
            "SELECT * FROM Справочник.Пользователи WHERE Активен = &Активен",
            {"Активен": True}
        )
        print("Результат запроса:", query_result)
        
        # Получение статистики
        cache_manager = CacheManager()
        stats = cache_manager.get_detailed_stats()
        print("Статистика кэша:", stats)
    
    # Запуск примера
    # asyncio.run(example_usage())
