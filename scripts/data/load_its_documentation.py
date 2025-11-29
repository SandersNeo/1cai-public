# [NEXUS IDENTITY] ID: -7676650226360476520 | DATE: 2025-11-19

#!/usr/bin/env python3
"""
Скрипт для загрузки документации из библиотеки 1С ИТС
Версия: 1.0.0
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.services.configuration_knowledge_base import get_knowledge_base
    from src.services.its_library_service import get_its_service
except ImportError as e:
    print(f"[ERROR] Ошибка импорта: {e}")
    print("Установите зависимости: pip install httpx beautifulsoup4")
    sys.exit(1)


async def load_documentation_from_its():
    """Загрузка документации из ИТС"""
    print("=" * 70)
    print("ЗАГРУЗКА ДОКУМЕНТАЦИИ ИЗ БИБЛИОТЕКИ 1С ИТС")
    print("=" * 70)
    
    # Инициализация сервисов
    its_service = get_its_service(
        username="its_rrpk",
        password="RRPK_2022"
    )
    
    kb = get_knowledge_base()
    
    configurations = ["erp", "ut", "zup", "buh", "holding", "buhbit", "do", "ka"]
    config_names_map = {
        "erp": "ERP Управление предприятием 2",
        "ut": "Управление торговлей",
        "zup": "Зарплата и управление персоналом",
        "buh": "Бухгалтерия предприятия",
        "holding": "Управление холдингом",
        "buhbit": "Бухгалтерия БИТ",
        "do": "Документооборот",
        "ka": "Комплексная автоматизация"
    }
    
    results = {}
    
    print("\n[INFO] Авторизация в ИТС...")
    auth_result = await its_service.authenticate()
    
    if not auth_result:
        print("[ERROR] Не удалось авторизоваться в ИТС")
        print("[INFO] Проверьте учётные данные и доступ к интернету")
        return {}
    
    print("[OK] Авторизация успешна\n")
    
    for config_name in configurations:
        config_full_name = config_names_map.get(config_name, config_name)
        
        print(f"{'='*70}")
        print(f"Загрузка документации: {config_full_name} ({config_name})")
        print(f"{'='*70}")
        
        try:
            # Получаем документацию из ИТС
            documentation = await its_service.get_configuration_documentation(config_name)
            
            if "error" in documentation:
                print(f"[ERROR] Ошибка загрузки: {documentation['error']}")
                results[config_name] = {"status": "error", "error": documentation["error"]}
                continue
            
            # Сохраняем в базу знаний
            print(f"[INFO] Обработка документации...")
            
            # Добавляем модули
            modules_count = 0
            for module in documentation.get("modules", []):
                try:
                    kb.add_module_documentation(
                        config_name=config_name,
                        module_name=module.get("name", "Unknown"),
                        documentation={
                            "description": module.get("description", ""),
                            "code_examples": module.get("code_examples", []),
                            "source": "ИТС библиотека",
                            "extracted_at": documentation.get("extracted_at")
                        }
                    )
                    modules_count += 1
                except Exception as e:
                    print(f"[WARN] Ошибка добавления модуля: {e}")
            
            # Добавляем best practices
            practices_count = 0
            for practice in documentation.get("best_practices", []):
                try:
                    kb.add_best_practice(
                        config_name=config_name,
                        category=practice.get("category", "general"),
                        practice={
                            "title": practice.get("title", ""),
                            "description": practice.get("description", ""),
                            "source": "ИТС библиотека",
                            "extracted_at": documentation.get("extracted_at")
                        }
                    )
                    practices_count += 1
                except Exception as e:
                    print(f"[WARN] Ошибка добавления practice: {e}")
            
            # Сохраняем примеры кода
            examples_count = len(documentation.get("code_examples", []))
            
            print(f"[OK] Загружено: {modules_count} модулей, {practices_count} best practices, {examples_count} примеров кода")
            
            results[config_name] = {
                "status": "success",
                "modules": modules_count,
                "practices": practices_count,
                "examples": examples_count
            }
            
        except Exception as e:
            print(f"[ERROR] Критическая ошибка: {e}")
            import traceback
            traceback.print_exc()
            results[config_name] = {"status": "error", "error": str(e)}
    
    print(f"\n{'='*70}")
    print("ИТОГИ ЗАГРУЗКИ:")
    print(f"{'='*70}")
    
    total_modules = 0
    total_practices = 0
    total_examples = 0
    
    for config_name, result in results.items():
        if result.get("status") == "success":
            modules = result.get("modules", 0)
            practices = result.get("practices", 0)
            examples = result.get("examples", 0)
            total_modules += modules
            total_practices += practices
            total_examples += examples
            
            print(f"[OK] {config_name:10} | Модулей: {modules:3} | Practices: {practices:3} | Примеров: {examples:3}")
        else:
            print(f"[ERROR] {config_name:10} | {result.get('error', 'Unknown error')}")
    
    print(f"{'='*70}")
    print(f"ВСЕГО: {total_modules} модулей, {total_practices} practices, {total_examples} примеров")
    print(f"{'='*70}")
    
    print("\n[OK] Загрузка завершена!")
    print("\nСледующие шаги:")
    print("1. Проверьте базу знаний: GET /api/knowledge-base/configurations")
    print("2. Используйте рекомендации в Code Review")
    print("3. Изучите загруженные best practices и примеры")
    
    return results


if __name__ == "__main__":
    try:
        results = asyncio.run(load_documentation_from_its())
    except KeyboardInterrupt:
        print("\n[INFO] Прервано пользователем")
        sys.exit(130)
    except Exception as e:
        print(f"\n[ERROR] Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)





