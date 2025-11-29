# [NEXUS IDENTITY] ID: -3103403458551142353 | DATE: 2025-11-19

#!/usr/bin/env python3
"""
Демонстрация работы MCP Tools Cache

Полный пример использования всех возможностей модуля кэширования.
Показывает интеграцию с mcp_server.py и onec_client.py.

Запуск:
    python cache/mcp_cache_demo.py

Версия: 1.0.0
"""

import asyncio
import random
import time
from datetime import datetime
from typing import Any, Dict, List

# Импорты модуля кэширования
from cache import (cache_aggregates, cache_metadata_1c, cache_tool_result, get_cache,
                   get_cache_stats, get_cached_aggregates, get_cached_metadata_1c, get_cached_tool_result,
                   init_cache)
from cache.integration_examples import (MCPServerCacheIntegration,
                                        OneCCacheIntegration)


class MockOneCClient:
    """Мок-клиент для имитации работы с 1С"""
    
    def __init__(self):
        self.call_count = 0
        self.call_log = []
    
    async def execute_query(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Имитирует выполнение запроса к 1С"""
        self.call_count += 1
        self.call_log.append({
            'query': query[:100] + '...' if len(query) > 100 else query,
            'params': params,
            'timestamp': datetime.now().isoformat(),
            'call_number': self.call_count
        })
        
        # Имитируем задержку выполнения
        await asyncio.sleep(random.uniform(0.1, 0.5))
        
        # Возвращаем тестовые данные
        return [
            {'id': i, 'name': f'Item {i}', 'value': random.randint(1, 100)}
            for i in range(1, 11)
        ]
    
    async def get_catalog_structure(self, catalog_name: str) -> Dict[str, Any]:
        """Имитирует получение структуры справочника"""
        self.call_count += 1
        
        await asyncio.sleep(random.uniform(0.2, 0.8))
        
        return {
            'catalog_name': catalog_name,
            'fields': ['Код', 'Наименование', 'ДатаСоздания', 'Активен'],
            'hierarchical': True,
            'has_owners': False,
            'total_records': random.randint(100, 10000)
        }
    
    async def get_report_data(self, report_type: str, period: str) -> List[Dict[str, Any]]:
        """Имитирует получение данных отчёта"""
        self.call_count += 1
        
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        return [
            {
                'period': f'2024-{month:02d}',
                'sales': random.randint(50000, 200000),
                'count': random.randint(500, 2000),
                'profit': random.randint(10000, 50000)
            }
            for month in range(1, 13)
        ]


class MockMCPServer:
    """Мок MCP сервер для демонстрации"""
    
    def __init__(self):
        self.onec_client = MockOneCClient()
        self.mcp_integration = MCPServerCacheIntegration()
        self.onec_integration = OneCCacheIntegration()
    
    async def handle_tool_request(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Обрабатывает запрос к MCP инструменту с кэшированием"""
        # Проверяем кэш
        cached_result = await self.mcp_integration.get_cached_tool_execution(tool_name, arguments)
        
        if cached_result:
            return {
                'tool': tool_name,
                'arguments': arguments,
                'result': cached_result['result'],
                'from_cache': True,
                'cached_at': cached_result['executed_at']
            }
        
        # Выполняем инструмент
        start_time = time.time()
        
        if tool_name == "get_catalog_structure":
            result = await self.onec_client.get_catalog_structure(arguments['catalog'])
        elif tool_name == "execute_query":
            result = await self.onec_client.execute_query(arguments['query'], arguments['params'])
        elif tool_name == "get_report_data":
            result = await self.onec_client.get_report_data(arguments['type'], arguments['period'])
        else:
            result = {"error": f"Unknown tool: {tool_name}"}
        
        execution_time = time.time() - start_time
        
        # Кэшируем результат
        await self.mcp_integration.cache_tool_execution(tool_name, arguments, result)
        
        return {
            'tool': tool_name,
            'arguments': arguments,
            'result': result,
            'from_cache': False,
            'execution_time': execution_time,
            'cached_at': datetime.now().isoformat()
        }
    
    async def execute_1c_query(self, query: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Выполняет запрос к 1С с кэшированием"""
        # Проверяем кэш
        cached_result = await self.onec_integration.get_cached_1c_query(query, params)
        
        if cached_result:
            return {
                'query': query,
                'params': params,
                'result': cached_result['result'],
                'from_cache': True,
                'cached_at': cached_result['cached_at']
            }
        
        # Выполняем запрос
        result = await self.onec_client.execute_query(query, params)
        
        # Кэшируем результат
        await self.onec_integration.cache_1c_query_result(query, params, result)
        
        return {
            'query': query,
            'params': params,
            'result': result,
            'from_cache': False,
            'executed_at': datetime.now().isoformat()
        }


async def demo_basic_operations():
    """Демонстрация базовых операций кэширования"""
    print("\n=== ДЕМОНСТРАЦИЯ БАЗОВЫХ ОПЕРАЦИЙ ===")
    
    # Инициализация кэша
    cache = init_cache(max_size_mb=50)
    
    # Базовые операции
    print("1. Сохранение данных в кэш...")
    cache.set("user:123", {"name": "Иван", "role": "admin"}, ttl=300)
    cache.set("config:main", {"theme": "dark", "lang": "ru"}, data_type='stable')
    cache.set("session:active", {"user_id": 123, "login_time": datetime.now().isoformat()}, data_type='dynamic')
    
    print("2. Получение данных из кэша...")
    user = cache.get("user:123")
    config = cache.get("config:main")
    session = cache.get("session:active")
    
    print(f"   Пользователь: {user}")
    print(f"   Конфигурация: {config}")
    print(f"   Сессия: {session}")
    
    print("3. Проверка наличия ключей...")
    print(f"   user:123 существует: {cache.has('user:123')}")
    print(f"   user:999 существует: {cache.has('user:999')}")
    
    print("4. Получение статистики...")
    stats = get_cache_stats()
    print(f"   Всего записей: {stats['total_entries']}")
    print(f"   Использование памяти: {stats['memory_usage_mb']:.2f} MB")
    print(f"   Hit ratio: {stats['hit_ratio']:.2%}")


async def demo_specialized_cache():
    """Демонстрация специализированных функций кэширования"""
    print("\n=== ДЕМОНСТРАЦИЯ СПЕЦИАЛИЗИРОВАННОГО КЭШИРОВАНИЯ ===")
    
    init_cache(max_size_mb=50)
    
    print("1. Кэширование результатов MCP tools...")
    
    # Инструмент получения структуры справочника
    tool_name = "get_catalog_structure"
    args = {"catalog": "Пользователи"}
    
    # Имитируем результат
    tool_result = {
        'fields': ['Код', 'Наименование', 'ДатаСоздания', 'Активен'],
        'hierarchical': True,
        'total_records': 1250
    }
    
    # Кэшируем результат
    cache_tool_result(tool_name, args, tool_result)
    print(f"   Закэширован результат инструмента {tool_name}")
    
    # Получаем из кэша
    cached_result = get_cached_tool_result(tool_name, args)
    print(f"   Получен из кэша: {cached_result}")
    
    print("\n2. Кэширование метаданных 1С...")
    
    # Метаданные справочника
    metadata = {
        'type': 'справочник',
        'hierarchical': True,
        'has_owners': False,
        'max_length_name': 150,
        'default_picture': None
    }
    
    cache_metadata_1c("catalog", "Пользователи", metadata)
    print("   Закэшированы метаданные справочника 'Пользователи'")
    
    # Получаем метаданные
    cached_metadata = get_cached_metadata_1c("catalog", "Пользователи")
    print(f"   Метаданные: {cached_metadata}")
    
    print("\n3. Кэширование агрегированных данных...")
    
    # Данные продаж
    sales_data = [
        {'period': '2024-01', 'sales': 150000, 'count': 150},
        {'period': '2024-02', 'sales': 180000, 'count': 180},
        {'period': '2024-03', 'sales': 210000, 'count': 210}
    ]
    
    cache_aggregates("monthly_sales", "2024-Q1", {'region': 'Moscow'}, sales_data)
    print("   Закэшированы данные продаж за Q1 2024")
    
    # Получаем агрегаты
    cached_aggregates = get_cached_aggregates("monthly_sales", "2024-Q1", {'region': 'Moscow'})
    print(f"   Агрегаты: {cached_aggregates}")


async def demo_mcp_server_integration():
    """Демонстрация интеграции с MCP сервером"""
    print("\n=== ДЕМОНСТРАЦИЯ ИНТЕГРАЦИИ С MCP СЕРВЕРОМ ===")
    
    init_cache(max_size_mb=50)
    mcp_server = MockMCPServer()
    
    print("1. Выполнение MCP инструментов с кэшированием...")
    
    # Первый вызов инструмента (выполняется функция)
    print("   Первый вызов get_catalog_structure:")
    result1 = await mcp_server.handle_tool_request(
        "get_catalog_structure", 
        {"catalog": "Пользователи"}
    )
    print(f"   Результат получен из кэша: {result1['from_cache']}")
    print(f"   Время выполнения: {result1.get('execution_time', 0):.3f}s")
    
    # Второй вызов с теми же аргументами (из кэша)
    print("\n   Второй вызов get_catalog_structure:")
    result2 = await mcp_server.handle_tool_request(
        "get_catalog_structure", 
        {"catalog": "Пользователи"}
    )
    print(f"   Результат получен из кэша: {result2['from_cache']}")
    print(f"   Время выполнения: {result2.get('execution_time', 0):.3f}s")
    
    print("\n2. Выполнение запросов к 1С с кэшированием...")
    
    query = "SELECT * FROM Справочник.Пользователи WHERE Активен = &Активен"
    params = {"Активен": True}
    
    # Первый запрос
    print("   Первый запрос к 1С:")
    result3 = await mcp_server.execute_1c_query(query, params)
    print(f"   Из кэша: {result3['from_cache']}")
    
    # Второй запрос с теми же параметрами
    print("\n   Второй запрос к 1С:")
    result4 = await mcp_server.execute_1c_query(query, params)
    print(f"   Из кэша: {result4['from_cache']}")
    
    print(f"\n3. Статистика вызовов к 1С:")
    print(f"   Всего вызовов: {mcp_server.onec_client.call_count}")
    print(f"   Лог последних вызовов:")
    for call in mcp_server.onec_client.call_log[-3:]:
        print(f"     {call['call_number']}: {call['query']} с параметрами {call['params']}")


async def demo_performance_test():
    """Простой тест производительности"""
    print("\n=== ТЕСТ ПРОИЗВОДИТЕЛЬНОСТИ ===")
    
    init_cache(max_size_mb=50)
    
    # Тест 1: Последовательные операции
    print("1. Тест последовательных операций...")
    
    cache = get_cache()
    
    start_time = time.time()
    for i in range(1000):
        cache.set(f"perf_key_{i}", f"perf_value_{i}" * 10)
    write_time = time.time() - start_time
    
    start_time = time.time()
    for i in range(1000):
        cache.get(f"perf_key_{i}")
    read_time = time.time() - start_time
    
    print(f"   Запись 1000 записей: {write_time:.3f}s")
    print(f"   Чтение 1000 записей: {read_time:.3f}s")
    print(f"   Среднее время записи: {write_time*1000/1000:.3f}ms")
    print(f"   Среднее время чтения: {read_time*1000/1000:.3f}ms")
    
    # Тест 2: Проверка кэширования
    print("\n2. Тест эффективности кэширования...")
    
    # Первый доступ (промах)
    start_time = time.time()
    for i in range(500):
        cache.get(f"perf_key_{i}")
    first_access_time = time.time() - start_time
    
    # Второй доступ (попадание)
    start_time = time.time()
    for i in range(500):
        cache.get(f"perf_key_{i}")
    second_access_time = time.time() - start_time
    
    speedup = first_access_time / second_access_time if second_access_time > 0 else float('inf')
    
    print(f"   Первый доступ (промах): {first_access_time:.3f}s")
    print(f"   Второй доступ (попадание): {second_access_time:.3f}s")
    print(f"   Ускорение: {speedup:.1f}x")


async def main():
    """Главная функция демонстрации"""
    print("🚀 ДЕМОНСТРАЦИЯ MCP TOOLS CACHE")
    print("=" * 50)
    print(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Запускаем все демонстрации
        await demo_basic_operations()
        await demo_specialized_cache()
        await demo_mcp_server_integration()
        await demo_performance_test()
        
        print("\n" + "=" * 50)
        print("✅ ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА УСПЕШНО")
        print("=" * 50)
        
        # Финальная статистика
        final_stats = get_cache_stats()
        print(f"\nФинальная статистика кэша:")
        print(f"  Всего записей: {final_stats['total_entries']}")
        print(f"  Использование памяти: {final_stats['memory_usage_mb']:.2f} MB")
        print(f"  Hit ratio: {final_stats['hit_ratio']:.2%}")
        print(f"  Попадания: {final_stats['hits']}")
        print(f"  Промахи: {final_stats['misses']}")
        print(f"  Ошибки: {final_stats['errors']}")
        
    except Exception as e:
        print(f"\n❌ ОШИБКА В ДЕМОНСТРАЦИИ: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Настройка логирования
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Запуск демонстрации
    asyncio.run(main())
