# [NEXUS IDENTITY] ID: 6060644966728006161 | DATE: 2025-11-19

#!/usr/bin/env python3
"""
Поиск реальных API эндпоинтов ИТС через анализ JavaScript кода
Версия: 1.0.0
"""

import re
import json
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.services.its_library_service import get_its_service


def extract_api_endpoints(html_content: str) -> list:
    """Извлечение API эндпоинтов из JavaScript кода"""
    endpoints = []
    
    # Паттерны для поиска API эндпоинтов
    patterns = [
        # XMLHttpRequest.open('GET', 'url')
        r"XMLHttpRequest\s*\.\s*open\s*\(\s*['\"](?:GET|POST|PUT|DELETE)['\"]\s*,\s*['\"]([^'\"]+)['\"]",
        # fetch('url')
        r"fetch\s*\(\s*['\"]([^'\"]+)['\"]",
        # $.ajax({ url: 'url' })
        r"\$\.ajax\s*\(\s*\{[^}]*url\s*:\s*['\"]([^'\"]+)['\"]",
        # http.get('url') или http.post('url')
        r"http\.(?:get|post|put|delete)\s*\(\s*['\"]([^'\"]+)['\"]",
        # '/db/metod8dev/content/...'
        r"['\"](/db/metod8dev/[^'\"]+)['\"]",
        # '/content/.../hdoc'
        r"['\"](/content/[^'\"]*hdoc[^'\"]*)['\"]",
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, html_content, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            endpoint = match.group(1) if match.lastindex else match.group(0)
            
            # Очищаем endpoint
            endpoint = endpoint.strip()
            
            # Фильтруем полезные
            if any(keyword in endpoint.lower() for keyword in ['content', 'hdoc', 'api', 'db/metod8dev']):
                if endpoint not in endpoints:
                    endpoints.append(endpoint)
    
    return endpoints


async def test_endpoints():
    """Тестирование найденных эндпоинтов"""
    its_service = get_its_service(username="its_rrpk", password="RRPK_2022")
    
    print("=" * 70)
    print("ПОИСК API ЭНДПОИНТОВ ИТС")
    print("=" * 70)
    
    print("\n[1] Авторизация...")
    auth_result = await its_service.authenticate()
    
    if not auth_result:
        print("[ERROR] Не удалось авторизоваться")
        return
    
    print("[OK] Авторизация успешна!\n")
    
    print("[2] Получение страницы ERP...")
    page_url = "https://its.1c.ru/db/metod8dev#content:78:1"
    response = its_service.session.get(page_url)
    
    if response.status_code != 200:
        print(f"[ERROR] Не удалось получить страницу: {response.status_code}")
        return
    
    print(f"[OK] Страница получена ({len(response.text)} байт)\n")
    
    print("[3] Извлечение API эндпоинтов из JavaScript...")
    endpoints = extract_api_endpoints(response.text)
    
    print(f"\n[INFO] Найдено потенциальных эндпоинтов: {len(endpoints)}\n")
    
    # Показываем найденные эндпоинты
    print("=" * 70)
    print("НАЙДЕННЫЕ ЭНДПОИНТЫ:")
    print("=" * 70)
    
    for i, endpoint in enumerate(endpoints[:20], 1):  # Ограничиваем вывод
        print(f"{i:2}. {endpoint}")
    
    print("\n" + "=" * 70)
    print("ТЕСТИРОВАНИЕ ЭНДПОИНТОВ:")
    print("=" * 70)
    
    # Тестируем самые перспективные эндпоинты
    test_endpoints = [
        "/db/metod8dev/content/78/1/hdoc",
        "/db/metod8dev/content/78/1",
        "/content/78/1/hdoc",
        "/db/metod8dev/content/78/1/hdoc?bus",
    ]
    
    # Добавляем найденные уникальные эндпоинты
    for endpoint in endpoints[:10]:
        if endpoint.startswith('/'):
            full_url = f"https://its.1c.ru{endpoint}"
            test_endpoints.append(endpoint)
    
    # Убираем дубликаты
    test_endpoints = list(dict.fromkeys(test_endpoints))
    
    for endpoint in test_endpoints:
        if not endpoint.startswith('/'):
            continue
        
        full_url = f"https://its.1c.ru{endpoint}"
        
        print(f"\n[TEST] {endpoint}")
        try:
            # Пробуем разные варианты запросов
            test_variants = [
                {"headers": {}},
                {"headers": {"X-Requested-With": "XMLHttpRequest"}},
                {"headers": {"Referer": "https://its.1c.ru/db/metod8dev"}},
                {"headers": {"Accept": "application/json"}},
                {"headers": {"Accept": "text/html"}},
            ]
            
            for i, variant in enumerate(test_variants):
                try:
                    resp = its_service.session.get(full_url, headers=variant["headers"], timeout=5)
                    
                    print(f"  Variant {i+1}: Status {resp.status_code}, "
                          f"Content-Type: {resp.headers.get('content-type', 'N/A')[:50]}, "
                          f"Size: {len(resp.text)} bytes")
                    
                    if resp.status_code == 200:
                        # Проверяем что это полезный контент
                        if len(resp.text) > 1000:
                            # Пробуем парсить JSON
                            try:
                                data = json.loads(resp.text)
                                print(f"  ✅ JSON ответ! Keys: {list(data.keys())[:5]}")
                            except:
                                # HTML ответ
                                if any(keyword in resp.text.lower() for keyword in ['модуль', 'функция', 'процедура']):
                                    print(f"  ✅ HTML с контентом! Найдены ключевые слова")
                        elif 'json' in resp.headers.get('content-type', '').lower():
                            print(f"  ✅ JSON ответ! Content: {resp.text[:200]}")
                    
                    if resp.status_code in [200, 302] and len(resp.text) > 1000:
                        # Сохраняем успешный ответ
                        filename = f"its_api_response_{endpoint.replace('/', '_')}.html"
                        with open(filename, "w", encoding="utf-8") as f:
                            f.write(resp.text)
                        print(f"  💾 Сохранено в {filename}")
                        
                except Exception as e:
                    print(f"  [ERROR] Variant {i+1}: {e}")
                    continue
                    
        except Exception as e:
            print(f"  [ERROR] {e}")
    
    print("\n" + "=" * 70)
    print("АНАЛИЗ ЗАВЕРШЕН")
    print("=" * 70)
    print("\n[INFO] Проверьте сохраненные файлы для анализа структуры ответов")


if __name__ == "__main__":
    asyncio.run(test_endpoints())





