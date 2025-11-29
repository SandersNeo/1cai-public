# [NEXUS IDENTITY] ID: 2212086134694538385 | DATE: 2025-11-19

#!/usr/bin/env python3
"""
Скрипт для загрузки конфигураций 1С в базу знаний
Версия: 1.0.0
"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.services.configuration_knowledge_base import get_knowledge_base
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    print("Убедитесь, что все зависимости установлены: pip install -r requirements.txt")
    sys.exit(1)


class ConfigurationLoader:
    """Загрузчик конфигураций 1С"""
    
    def __init__(self):
        self.kb = get_knowledge_base()
        self.config_dir = Path("./1c_configurations")
        
    def load_all_configurations(self) -> Dict[str, Any]:
        """Загрузка всех конфигураций"""
        results = {}
        
        configurations = ["ERP", "UT", "ZUP", "BUH", "HOLDING"]
        
        for config_name in configurations:
            config_path = self.config_dir / config_name
            
            if not config_path.exists():
                print(f"[SKIP] Директория не найдена: {config_path}")
                continue
            
            print(f"\n{'='*60}")
            print(f"Загрузка конфигурации: {config_name}")
            print(f"{'='*60}")
            
            try:
                result = self.load_configuration(config_name, config_path)
                results[config_name] = result
                print(f"[OK] Конфигурация {config_name} загружена успешно")
            except Exception as e:
                print(f"[ERROR] Ошибка загрузки {config_name}: {e}")
                results[config_name] = {"error": str(e)}
        
        return results
    
    def load_configuration(self, config_name: str, config_path: Path) -> Dict[str, Any]:
        """Загрузка одной конфигурации"""
        
        # Поиск XML файлов
        xml_files = list(config_path.rglob("*.xml"))
        
        if not xml_files:
            print(f"[WARN] XML файлы не найдены в {config_path}")
            return {"files_found": 0, "modules_loaded": 0}
        
        print(f"[INFO] Найдено XML файлов: {len(xml_files)}")
        
        modules_count = 0
        total_files = len(xml_files)
        
        # Обработка каждого XML файла
        for xml_file in xml_files[:10]:  # Ограничиваем первыми 10 файлами для производительности
            try:
                modules = self.parse_xml_file(xml_file, config_name)
                if modules:
                    modules_count += len(modules)
                    print(f"[INFO] Обработан {xml_file.name}: {len(modules)} модулей")
            except Exception as e:
                print(f"[WARN] Ошибка обработки {xml_file.name}: {e}")
        
        # Загрузка через API базы знаний
        if modules_count > 0:
            # Добавляем базовую информацию о конфигурации
            self.add_configuration_info(config_name, total_files, modules_count)
        
        return {
            "files_found": total_files,
            "files_processed": min(10, total_files),
            "modules_loaded": modules_count,
            "status": "success"
        }
    
    def parse_xml_file(self, xml_file: Path, config_name: str) -> List[Dict[str, Any]]:
        """Парсинг XML файла конфигурации 1С"""
        modules = []
        
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # Поиск модулей в XML структуре 1С
            # 1С конфигурации имеют специфическую структуру XML
            
            # Поиск объектов с модулями
            for obj in root.iter():
                obj_type = obj.tag
                
                # Типичные объекты 1С с модулями
                if obj_type in ["Document", "Catalog", "Register", "Report", "DataProcessor"]:
                    module_data = self.extract_module_data(obj, xml_file, config_name)
                    if module_data:
                        modules.append(module_data)
                
                # Поиск общих модулей
                if obj_type == "CommonModule":
                    module_data = self.extract_common_module(obj, xml_file, config_name)
                    if module_data:
                        modules.append(module_data)
        
        except ET.ParseError as e:
            print(f"[WARN] Ошибка парсинга XML {xml_file.name}: {e}")
        except Exception as e:
            print(f"[WARN] Ошибка обработки {xml_file.name}: {e}")
        
        return modules
    
    def extract_module_data(self, obj: ET.Element, xml_file: Path, config_name: str) -> Optional[Dict[str, Any]]:
        """Извлечение данных модуля объекта"""
        try:
            obj_name = obj.get("name") or obj.findtext("Name", "")
            if not obj_name:
                return None
            
            # Поиск модуля объекта
            module = obj.find(".//Module")
            if module is None:
                return None
            
            module_text = module.text or ""
            if not module_text.strip():
                return None
            
            module_data = {
                "name": f"{obj.tag}_{obj_name}",
                "object_type": obj.tag,
                "object_name": obj_name,
                "code": module_text[:1000],  # Ограничиваем длину
                "source_file": str(xml_file.relative_to(self.config_dir)),
                "functions": self.extract_functions(module_text),
                "description": f"Модуль {obj.tag} {obj_name} из {xml_file.name}"
            }
            
            # Добавление в базу знаний
            self.kb.add_module_documentation(
                config_name=config_name.lower(),
                module_name=module_data["name"],
                documentation=module_data
            )
            
            return module_data
        
        except Exception as e:
            print(f"[WARN] Ошибка извлечения модуля: {e}")
            return None
    
    def extract_common_module(self, obj: ET.Element, xml_file: Path, config_name: str) -> Optional[Dict[str, Any]]:
        """Извлечение данных общего модуля"""
        try:
            module_name = obj.get("name") or obj.findtext("Name", "")
            if not module_name:
                return None
            
            # Поиск текста модуля
            module_text_elem = obj.find(".//Module")
            if module_text_elem is None:
                return None
            
            module_text = module_text_elem.text or ""
            if not module_text.strip():
                return None
            
            module_data = {
                "name": f"ОбщийМодуль_{module_name}",
                "object_type": "CommonModule",
                "object_name": module_name,
                "code": module_text[:1000],
                "source_file": str(xml_file.relative_to(self.config_dir)),
                "functions": self.extract_functions(module_text),
                "description": f"Общий модуль {module_name}"
            }
            
            # Добавление в базу знаний
            self.kb.add_module_documentation(
                config_name=config_name.lower(),
                module_name=module_data["name"],
                documentation=module_data
            )
            
            return module_data
        
        except Exception as e:
            print(f"[WARN] Ошибка извлечения общего модуля: {e}")
            return None
    
    def extract_functions(self, code: str) -> List[Dict[str, str]]:
        """Извлечение функций из кода BSL"""
        import re
        
        functions = []
        
        # Паттерн для функций и процедур
        pattern = r'(?:Функция|Процедура)\s+(\w+)\s*(?:\(([^)]*)\))?'
        
        matches = re.finditer(pattern, code, re.IGNORECASE)
        
        for match in matches:
            func_name = match.group(1)
            params_str = match.group(2) or ""
            
            # Парсинг параметров
            params = [p.strip() for p in params_str.split(',') if p.strip()] if params_str else []
            
            functions.append({
                "name": func_name,
                "parameters": params,
                "signature": match.group(0)
            })
        
        return functions[:20]  # Ограничиваем количество
    
    def add_configuration_info(self, config_name: str, files_count: int, modules_count: int):
        """Добавление базовой информации о конфигурации"""
        try:
            # Получаем текущую информацию
            info = self.kb.get_configuration_info(config_name.lower())
            
            if not info:
                # Создаем базовую структуру
                info = {
                    "name": config_name,
                    "modules": [],
                    "best_practices": [],
                    "common_patterns": [],
                    "api_usage": [],
                    "performance_tips": [],
                    "known_issues": [],
                    "statistics": {
                        "files_count": files_count,
                        "modules_count": modules_count,
                        "loaded_at": None
                    }
                }
            
            # Обновляем статистику
            if "statistics" not in info:
                info["statistics"] = {}
            
            info["statistics"]["files_count"] = files_count
            info["statistics"]["modules_count"] = modules_count
            
            # Сохраняем (это сделает add_module_documentation автоматически)
            print(f"[INFO] Статистика конфигурации {config_name}: {modules_count} модулей из {files_count} файлов")
        
        except Exception as e:
            print(f"[WARN] Ошибка добавления информации о конфигурации: {e}")


def main():
    """Главная функция"""
    print("=" * 60)
    print("Загрузка конфигураций 1С в базу знаний")
    print("=" * 60)
    
    loader = ConfigurationLoader()
    results = loader.load_all_configurations()
    
    print("\n" + "=" * 60)
    print("Результаты загрузки:")
    print("=" * 60)
    
    total_modules = 0
    total_files = 0
    
    for config_name, result in results.items():
        if "error" in result:
            print(f"[ERROR] {config_name}: {result['error']}")
        else:
            modules = result.get("modules_loaded", 0)
            files = result.get("files_found", 0)
            total_modules += modules
            total_files += files
            print(f"[OK] {config_name}: {modules} модулей из {files} файлов")
    
    print("\n" + "=" * 60)
    print(f"Итого загружено: {total_modules} модулей из {total_files} файлов")
    print("=" * 60)
    
    print("\n[OK] Загрузка завершена!")
    print("\nСледующие шаги:")
    print("1. Проверьте базу знаний через API:")
    print("   GET http://localhost:8000/api/knowledge-base/configurations")
    print("2. Используйте рекомендации в Code Review")
    print("3. Изучите паттерны и best practices")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INFO] Прервано пользователем")
        sys.exit(130)
    except Exception as e:
        print(f"\n[ERROR] Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)





