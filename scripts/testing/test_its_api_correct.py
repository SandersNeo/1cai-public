# [NEXUS IDENTITY] ID: 40022579626944058 | DATE: 2025-11-19

#!/usr/bin/env python3
"""
Правильное тестирование API ИТС на основе JavaScript кода
Версия: 1.0.0
"""

import asyncio
import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.services.its_library_service import get_its_service


def extract_js_url_logic(html_content: str):
    """Извлечение логики формирования URL из JavaScript"""
    # Ищем строку с формированием URL
    pattern = r"var\s+url\s*=\s*location\.protocol\s*\+\s*['\"]//['\"]\s*\+\s*location\.hostname\s*\+\s*location\.pathname\s*\+\s*['\"]/['\"]\s*\+\s*attrs"
    match = re.search(pattern, html_content)
    
    if match:
        # Ищем следующую строку с параметрами
        next_pattern = r"url\s*\+=\s*\(attrs\.indexOf\s*\(['\"][?]['\"]\s*\)\s*!==\s*-1\s*['\"][&]['\"]\s*:\s*['\"][?]['\"]\s*\)\s*\+\s*['\"]([^'\"]+)['\"]"
        param_match = re.search(next_pattern, html_content)
        
        if param_match:
            return param_match.group(1)
    
    # Альтернативный поиск
    pattern2 = r"['\"]bus[&'][^'\"]*event\[name\]"
    match2 = re.search(pattern2, html_content)
    if match2:
        return "bus"
    
    return None


async def test_correct_api():
    """Тестирование правильного формата API запросов"""
    its_service = get_its_service(username="its_rrpk", password="RRPK_2022")
    
    print("=" * 70)
    print("ПРАВИЛЬНОЕ ТЕСТИРОВАНИЕ API ИТС")
    print("=" * 70)
    
    print("\n[1] Авторизация...")
    auth_result = await its_service.authenticate()
    
    if not auth_result:
        print("[ERROR] Не удалось авторизоваться")
        return
    
    print("[OK] Авторизация успешна!\n")
    
    print("[2] Анализ JavaScript кода для определения формата запроса...")
    page_url = "https://its.1c.ru/db/metod8dev#content:78:1"
    response = its_service.session.get(page_url)
    
    # Извлекаем логику из JavaScript
    js_url_logic = extract_js_url_logic(response.text)
    
    if js_url_logic:
        print(f"[OK] Найдена логика формирования URL: {js_url_logic}")
    else:
        print("[INFO] Логика не найдена, используем стандартный формат")
    
    print("\n[3] Тестирование различных форматов запросов...")
    print("=" * 70)
    
    # Варианты запросов на основе анализа JavaScript
    # Из JS: attrs = decodeURIComponent(location.hash.replace('#', '').replace(/:/g, '/'))
    # attrs = "content:78:1" -> "content/78/1"
    # URL = location.pathname + '/' + attrs + (attrs.indexOf('?')!==-1?'&':'?') + 'bus&timestamp&event[name]=mode'
    
    base_path = "/db/metod8dev"
    
    # Варианты для тестирования
    test_configs = [
        {"id": "78:1", "hash": "content:78:1", "path": "content/78/1", "name": "ERP"},
        {"id": "78:2", "hash": "content:78:2", "path": "content/78/2", "name": "UT"},
        {"id": "100010", "hash": "content:100010", "path": "content/100010", "name": "Test (working)"},
    ]
    
    # Варианты параметров
    param_variants = [
        "?bus",
        "?bus&event[name]=mode",
        "?bus&1234567890=&event[name]=mode",  # С timestamp
        "",  # Без параметров
    ]
    
    # Варианты заголовков
    header_variants = [
        {},  # Без заголовков
        {"X-Requested-With": "XMLHttpRequest"},
        {"Referer": "https://its.1c.ru/db/metod8dev"},
        {"Referer": "https://its.1c.ru/db/metod8dev", "X-Requested-With": "XMLHttpRequest"},
        {"X-Referer": "https://its.1c.ru/db/metod8dev"},  # Из JS кода
    ]
    
    found_working = []
    
    for config in test_configs:
        print(f"\n[TEST] Конфигурация: {config['name']} (ID: {config['id']})")
        print("-" * 70)
        
        for param_variant in param_variants:
            for header_variant in header_variants:
                # Формируем URL как в JavaScript
                # pathname = "/db/metod8dev"
                # attrs = "content/78/1" (из hash "content:78:1")
                url = f"{base_path}/{config['path']}/hdoc{param_variant}"
                
                try:
                    resp = its_service.session.get(
                        f"https://its.1c.ru{url}",
                        headers=header_variant,
                        timeout=5
                    )
                    
                    status_icon = "[OK]" if resp.status_code == 200 else "[FAIL]"
                    print(f"  {status_icon} {url}")
                    print(f"    Params: {param_variant or 'none'}")
                    print(f"    Headers: {header_variant or 'none'}")
                    print(f"    Status: {resp.status_code}, Size: {len(resp.text)} bytes")
                    
                    if resp.status_code == 200 and len(resp.text) > 1000:
                        # Проверяем наличие полезного контента
                        content_lower = resp.text.lower()
                        has_content = any(keyword in content_lower for keyword in [
                            'модуль', 'module', 'функция', 'процедура', 
                            'function', 'procedure', 'erp', 'конфигурация'
                        ])
                        
                        if has_content:
                            print(f"    [SUCCESS] СОДЕРЖИТ ПОЛЕЗНЫЙ КОНТЕНТ!")
                            found_working.append({
                                "url": url,
                                "params": param_variant,
                                "headers": header_variant,
                                "config": config['name'],
                                "size": len(resp.text)
                            })
                            
                            # Сохраняем успешный ответ
                            filename = f"its_success_{config['name'].lower()}_{len(found_working)}.html"
                            with open(filename, "w", encoding="utf-8", errors="ignore") as f:
                                f.write(resp.text)
                            print(f"    💾 Сохранено в {filename}")
                    
                except Exception as e:
                    print(f"    [ERROR] {str(e)[:50]}")
                    continue
    
    print("\n" + "=" * 70)
    print("РЕЗУЛЬТАТЫ:")
    print("=" * 70)
    
    if found_working:
        print(f"\n✅ Найдено {len(found_working)} рабочих эндпоинтов:\n")
        for i, endpoint in enumerate(found_working, 1):
            print(f"{i}. Конфигурация: {endpoint['config']}")
            print(f"   URL: {endpoint['url']}")
            print(f"   Параметры: {endpoint['params'] or 'none'}")
            print(f"   Заголовки: {endpoint['headers'] or 'none'}")
            print(f"   Размер: {endpoint['size']} bytes")
            print()
        
        print("\n[OK] Найден рабочий API эндпоинт!")
        print("[INFO] Используйте этот формат для загрузки документации")
    else:
        print("\n[WARN] Рабочие эндпоинты не найдены")
        print("[INFO] Возможно:")
        print("  1. ID конфигураций неверны")
        print("  2. Нужен другой формат запроса")
        print("  3. Требуется JavaScript выполнение (Selenium/Playwright)")
        print("\n[RECOMMEND] Рассмотрите вариант 3 (ручное наполнение)")


if __name__ == "__main__":
    asyncio.run(test_correct_api())

