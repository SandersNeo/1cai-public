# [NEXUS IDENTITY] ID: -6143009017350627893 | DATE: 2025-11-23

"""
1C XML Parser
Парсер XML файлов конфигураций 1С
Версия: 1.0.0

Поддерживает:
- Configuration.xml - основные файлы конфигураций
- Module.xml - модули (общие, объектные, форм)
- Object metadata - документы, справочники, отчеты и т.д.
"""

import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class OneCXMLParser:
    """Парсер XML файлов конфигураций 1C"""

    # Namespaces для 1C XML (разные версии платформы)
    NAMESPACES = {
        "v8": "http://v8.1c.ru/8.3/MDClasses",
        "v82": "http://v8.1c.ru/8.2/MDClasses",
        "v81": "http://v8.1c.ru/8.1/MDClasses",
        "core": "http://v8.1c.ru/8.1/data/core",
        "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    }

    # Типы объектов метаданных 1C
    OBJECT_TYPES = {
        "Subsystem": "Подсистема",
        "Document": "Документ",
        "Catalog": "Справочник",
        "DataProcessor": "Обработка",
        "Report": "Отчет",
        "CommonModule": "Общий модуль",
        "Role": "Роль",
        "Constant": "Константа",
        "InformationRegister": "Регистр сведений",
        "AccumulationRegister": "Регистр накопления",
        "ChartOfCharacteristicTypes": "План видов характеристик",
        "ChartOfAccounts": "План счетов",
        "ChartOfCalculationTypes": "План видов расчета",
        "BusinessProcess": "Бизнес-процесс",
        "Task": "Задача",
    }

    # Максимальный размер XML файла (защита от DoS)
    MAX_XML_SIZE = 50 * 1024 * 1024  # 50MB

    def __init__(self):
        """Инициализация парсера"""
        self.stats = {"parsed_files": 0, "errors": 0, "warnings": 0}

    def parse_configuration(self, xml_path: Path) -> Optional[Dict[str, Any]]:
        """
        Парсинг основного файла конфигурации

        Args:
            xml_path: Путь к Configuration.xml

        Returns:
            Словарь с метаданными конфигурации или None
        """
        try:
            # Проверка размера файла
            if not self._validate_file_size(xml_path):
                return None

            # Парсинг XML с защитой от XXE
            tree = ET.parse(xml_path, parser=ET.XMLParser(resolve_entities=False))
            root = tree.getroot()

            # Извлечение базовой информации
            config_data = {
                "name": self._get_text(root, ".//Name") or "Unknown",
                "synonym": self._get_text(root, ".//Synonym") or "",
                "version": self._get_text(root, ".//Version") or "0.0.0.0",
                "vendor": self._get_text(root, ".//Vendor") or "",
                "description": self._get_text(root, ".//Comment") or "",
                "objects": {},
                "subsystems": [],
                "modules": [],
            }

            # Извлечение дочерних объектов
            child_objects = root.find(".//ChildObjects")
            if child_objects is not None:
                for obj_type, obj_name in self.OBJECT_TYPES.items():
                    objects = child_objects.findall(f".//{obj_type}")
                    if objects:
                        config_data["objects"][obj_name] = [
                            obj.text for obj in objects if obj.text]

            # Извлечение подсистем
            subsystems = root.findall(".//Subsystem")
            config_data["subsystems"] = [sub.text for sub in subsystems if sub.text]

            self.stats["parsed_files"] += 1
            logger.info(
                f"Parsed configuration: {config_data['name']} v{config_data['version']}")

            return config_data

        except ET.ParseError as e:
            logger.error("XML parse error in %s: {e}", xml_path)
            self.stats["errors"] += 1
            return None
        except Exception as e:
            logger.error(f"Error parsing configuration {xml_path}: {e}", exc_info=True)
            self.stats["errors"] += 1
            return None

    def parse_module(self, xml_path: Path) -> Optional[Dict[str, Any]]:
        """
        Парсинг модуля (общий, объектный, формы)

        Args:
            xml_path: Путь к Module.xml

        Returns:
            Словарь с метаданными модуля или None
        """
        try:
            if not self._validate_file_size(xml_path):
                return None

            tree = ET.parse(xml_path, parser=ET.XMLParser(resolve_entities=False))
            root = tree.getroot()

            module_data = {
                "name": self._get_text(root, ".//Name") or xml_path.stem,
                "type": self._detect_module_type(root),
                "server": self._get_bool(root, ".//Server"),
                "client": self._get_bool(root, ".//Client"),
                "external_connection": self._get_bool(root, ".//ExternalConnection"),
                "global": self._get_bool(root, ".//Global"),
                "privileged": self._get_bool(root, ".//Privileged"),
                "procedures": [],
                "code": "",
            }

            # Извлечение кода модуля
            module_text = self._get_text(root, ".//Text") or ""
            module_data["code"] = module_text

            # Извлечение процедур и функций
            if module_text:
                module_data["procedures"] = self.extract_procedures(module_text)

            self.stats["parsed_files"] += 1
            logger.info(f"Parsed module: {module_data['name']} ({module_data['type']})")

            return module_data

        except Exception as e:
            logger.error(f"Error parsing module {xml_path}: {e}", exc_info=True)
            self.stats["errors"] += 1
            return None

    def extract_procedures(self, module_text: str) -> List[Dict[str, Any]]:
        """
        Извлечение процедур и функций из кода модуля 1C

        Args:
            module_text: Текст модуля на языке 1C

        Returns:
            Список процедур и функций с метаданными
        """
        procedures = []

        # Регулярные выражения для поиска процедур и функций
        # Поддержка русского и английского синтаксиса
        patterns = [
            # Функция/Function
            r"(?:Функция|Function)\s+(\w+)\s*\((.*?)\)(?:\s+Экспорт|\s+Export)?",
            # Процедура/Procedure
            r"(?:Процедура|Procedure)\s+(\w+)\s*\((.*?)\)(?:\s+Экспорт|\s+Export)?",
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, module_text, re.IGNORECASE | re.MULTILINE)

            for match in matches:
                proc_name = match.group(1)
                params_str = match.group(2).strip()
                is_export = "Экспорт" in match.group(0) or "Export" in match.group(0)

                # Определение типа (функция или процедура)
                proc_type = "function" if "Функция" in match.group(
                    0) or "Function" in match.group(0) else "procedure"

                # Парсинг параметров
                parameters = []
                if params_str:
                    param_parts = params_str.split(",")
                    for param in param_parts:
                        param = param.strip()
                        if param:
                            # Извлечение имени параметра (до знака =)
                            param_name = param.split("=")[0].strip()
                            parameters.append(param_name)

                # Извлечение комментария перед процедурой/функцией
                description = self._extract_procedure_description(
                    module_text, match.start())

                procedures.append(
                    {
                        "name": proc_name,
                        "type": proc_type,
                        "export": is_export,
                        "parameters": parameters,
                        "description": description,
                    }
                )

        logger.debug(f"Extracted {len(procedures)} procedures/functions")
        return procedures

    def parse_object_metadata(self, xml_path: Path) -> Optional[Dict[str, Any]]:
        """
        Парсинг метаданных объекта (документ, справочник, отчет и т.д.)

        Args:
            xml_path: Путь к XML файлу объекта

        Returns:
            Словарь с метаданными объекта или None
        """
        try:
            if not self._validate_file_size(xml_path):
                return None

            tree = ET.parse(xml_path, parser=ET.XMLParser(resolve_entities=False))
            root = tree.getroot()

            # Определение типа объекта по корневому элементу
            object_type = root.tag.split("}")[-1] if "}" in root.tag else root.tag

            metadata = {
                "name": self._get_text(root, ".//Name") or xml_path.stem,
                "type": self.OBJECT_TYPES.get(object_type, object_type),
                "synonym": self._get_text(root, ".//Synonym") or "",
                "comment": self._get_text(root, ".//Comment") or "",
                "attributes": [],
                "tabular_sections": [],
                "forms": [],
                "commands": [],
            }

            # Извлечение реквизитов (attributes)
            attributes = root.findall(".//Attribute")
            for attr in attributes:
                attr_name = self._get_text(attr, ".//Name")
                if attr_name:
                    metadata["attributes"].append(
                        {
                            "name": attr_name,
                            "synonym": self._get_text(attr, ".//Synonym") or "",
                            "type": self._get_text(attr, ".//Type") or "",
                        }
                    )

            # Извлечение табличных частей
            tab_sections = root.findall(".//TabularSection")
            for tab in tab_sections:
                tab_name = self._get_text(tab, ".//Name")
                if tab_name:
                    metadata["tabular_sections"].append(tab_name)

            # Извлечение форм
            forms = root.findall(".//Form")
            for form in forms:
                form_name = self._get_text(form, ".//Name")
                if form_name:
                    metadata["forms"].append(form_name)

            # Извлечение команд
            commands = root.findall(".//Command")
            for cmd in commands:
                cmd_name = self._get_text(cmd, ".//Name")
                if cmd_name:
                    metadata["commands"].append(cmd_name)

            self.stats["parsed_files"] += 1
            logger.info(f"Parsed object: {metadata['name']} ({metadata['type']})")

            return metadata

        except Exception as e:
            logger.error(
                f"Error parsing object metadata {xml_path}: {e}", exc_info=True)
            self.stats["errors"] += 1
            return None

    # Private helper methods

    def _validate_file_size(self, xml_path: Path) -> bool:
        """Проверка размера файла (защита от DoS)"""
        try:
            file_size = xml_path.stat().st_size
            if file_size > self.MAX_XML_SIZE:
                logger.warning(
                    f"File {xml_path} is too large: {file_size} bytes (max {self.MAX_XML_SIZE})")
                self.stats["warnings"] += 1
                return False
            return True
        except Exception as e:
            logger.error("Error checking file size for %s: {e}", xml_path)
            return False

    def _get_text(self, element: ET.Element, xpath: str) -> Optional[str]:
        """Безопасное извлечение текста из элемента"""
        try:
            found = element.find(xpath)
            return found.text.strip() if found is not None and found.text else None
        except Exception:
            return None

    def _get_bool(self, element: ET.Element, xpath: str) -> bool:
        """Извлечение boolean значения"""
        text = self._get_text(element, xpath)
        if text:
            return text.lower() in ("true", "1", "да", "yes")
        return False

    def _detect_module_type(self, root: ET.Element) -> str:
        """Определение типа модуля"""
        # Проверяем атрибуты модуля
        if self._get_bool(root, ".//Global"):
            return "CommonModule"

        # Проверяем по родительскому элементу
        parent_tag = root.tag.split("}")[-1] if "}" in root.tag else root.tag

        type_map = {
            "ObjectModule": "ObjectModule",
            "FormModule": "FormModule",
            "CommandModule": "CommandModule",
            "RecordSetModule": "RecordSetModule",
            "ValueManagerModule": "ValueManagerModule",
            "ManagerModule": "ManagerModule",
        }

        return type_map.get(parent_tag, "Module")

    def _extract_procedure_description(self, module_text: str, proc_start: int) -> str:
        """Извлечение комментария перед процедурой/функцией"""
        # Ищем комментарии перед процедурой (строки начинающиеся с //)
        lines_before = module_text[:proc_start].split("\n")
        description_lines = []

        # Идём с конца и собираем комментарии
        for line in reversed(lines_before[-10:]):  # Последние 10 строк
            stripped = line.strip()
            if stripped.startswith("//"):
                description_lines.insert(0, stripped[2:].strip())
            elif stripped:
                # Если встретили не комментарий - прерываем
                break

        return " ".join(description_lines) if description_lines else ""

    def get_stats(self) -> Dict[str, int]:
        """Получение статистики парсинга"""
        return self.stats.copy()

    def reset_stats(self):
        """Сброс статистики"""
        self.stats = {"parsed_files": 0, "errors": 0, "warnings": 0}
