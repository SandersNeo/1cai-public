"""
Configuration Knowledge Base Service
База знаний по типовым конфигурациям 1С
Версия: 1.0.0
"""

import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class ConfigurationKnowledgeBase:
    """База знаний по типовым конфигурациям 1С"""
    
    # Поддерживаемые конфигурации
    SUPPORTED_CONFIGURATIONS = [
        "erp",
        "ut",
        "zup",
        "buh",
        "holding"
    ]
    
    # Маппинг названий
    CONFIG_NAME_MAP = {
        "erp": "ERP Управление предприятием 2",
        "ut": "Управление торговлей",
        "zup": "Зарплата и управление персоналом",
        "buh": "Бухгалтерия предприятия",
        "holding": "Управление холдингом"
    }
    
    def __init__(self, knowledge_base_path: Optional[str] = None):
        """
        Инициализация базы знаний
        
        Args:
            knowledge_base_path: Путь к директории с базой знаний
        """
        if knowledge_base_path:
            self.kb_path = Path(knowledge_base_path)
        else:
            # По умолчанию: ./knowledge_base или из env
            default_path = os.getenv("KNOWLEDGE_BASE_PATH", "./knowledge_base")
            self.kb_path = Path(default_path)
        
        self.kb_path.mkdir(parents=True, exist_ok=True)
        
        # Кэш загруженных знаний
        self._cache: Dict[str, Dict[str, Any]] = {}
        
        # Загрузка существующих знаний
        self._load_knowledge_base()
    
    def _load_knowledge_base(self):
        """Загрузка базы знаний из файлов"""
        for config in self.SUPPORTED_CONFIGURATIONS:
            config_file = self.kb_path / f"{config}.json"
            
            if config_file.exists():
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        self._cache[config] = json.load(f)
                    logger.info(
                        "Загружена база знаний",
                        extra={"config": config}
                    )
                except Exception as e:
                    logger.error(
                        "Ошибка загрузки базы знаний",
                        extra={
                            "config": config,
                            "error": str(e),
                            "error_type": type(e).__name__
                        },
                        exc_info=True
                    )
    
    def get_configuration_info(self, config_name: str) -> Optional[Dict[str, Any]]:
        """
        Получение информации о конфигурации
        
        Args:
            config_name: Название конфигурации (erp, ut, zup, buh, holding)
            
        Returns:
            Словарь с информацией о конфигурации или None
        """
        config_key = config_name.lower()
        
        if config_key not in self.SUPPORTED_CONFIGURATIONS:
            logger.warning(
                "Неподдерживаемая конфигурация",
                extra={"config_name": config_name}
            )
            return None
        
        return self._cache.get(config_key, {
            "name": self.CONFIG_NAME_MAP.get(config_key, config_name),
            "modules": [],
            "best_practices": [],
            "common_patterns": [],
            "api_usage": [],
            "performance_tips": [],
            "known_issues": []
        })
    
    def add_module_documentation(
        self,
        config_name: str,
        module_name: str,
        documentation: Dict[str, Any]
    ) -> bool:
        """
        Добавление документации модуля
        
        Args:
            config_name: Название конфигурации
            config_name: Имя модуля
            documentation: Документация модуля
            
        Returns:
            True если успешно добавлено
        """
        config_key = config_name.lower()
        
        if config_key not in self.SUPPORTED_CONFIGURATIONS:
            logger.error(
                "Неподдерживаемая конфигурация",
                extra={"config_name": config_name}
            )
            return False
        
        # Получаем или создаем конфигурацию
        if config_key not in self._cache:
            self._cache[config_key] = {
                "name": self.CONFIG_NAME_MAP.get(config_key, config_name),
                "modules": [],
                "best_practices": [],
                "common_patterns": [],
                "api_usage": [],
                "performance_tips": [],
                "known_issues": []
            }
        
        config_data = self._cache[config_key]
        
        # Добавляем или обновляем модуль
        module_exists = False
        for i, module in enumerate(config_data["modules"]):
            if module.get("name") == module_name:
                config_data["modules"][i] = {
                    "name": module_name,
                    "documentation": documentation,
                    "updated_at": datetime.now().isoformat()
                }
                module_exists = True
                break
        
        if not module_exists:
            config_data["modules"].append({
                "name": module_name,
                "documentation": documentation,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            })
        
        # Сохранение в файл
        return self._save_configuration(config_key)
    
    def add_best_practice(
        self,
        config_name: str,
        category: str,
        practice: Dict[str, Any]
    ) -> bool:
        """
        Добавление best practice
        
        Args:
            config_name: Название конфигурации
            category: Категория практики (performance, security, design, etc.)
            practice: Описание практики
            
        Returns:
            True если успешно добавлено
        """
        config_key = config_name.lower()
        
        if config_key not in self.SUPPORTED_CONFIGURATIONS:
            return False
        
        if config_key not in self._cache:
            self._cache[config_key] = self._get_default_config()
        
        practice_entry = {
            "category": category,
            **practice,
            "added_at": datetime.now().isoformat()
        }
        
        self._cache[config_key]["best_practices"].append(practice_entry)
        
        return self._save_configuration(config_key)
    
    def search_patterns(
        self,
        config_name: Optional[str] = None,
        pattern_type: Optional[str] = None,
        query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Поиск паттернов в базе знаний
        
        Args:
            config_name: Название конфигурации (опционально)
            pattern_type: Тип паттерна (опционально)
            query: Поисковый запрос (опционально)
            
        Returns:
            Список найденных паттернов
        """
        results = []
        
        configs_to_search = [config_name.lower()] if config_name else self.SUPPORTED_CONFIGURATIONS
        
        for config_key in configs_to_search:
            if config_key not in self._cache:
                continue
            
            config_data = self._cache[config_key]
            patterns = config_data.get("common_patterns", [])
            
            for pattern in patterns:
                # Фильтрация по типу
                if pattern_type and pattern.get("type") != pattern_type:
                    continue
                
                # Поиск по запросу
                if query:
                    search_text = json.dumps(pattern, ensure_ascii=False).lower()
                    if query.lower() not in search_text:
                        continue
                
                pattern_result = {
                    **pattern,
                    "configuration": config_key,
                    "configuration_name": config_data.get("name", config_key)
                }
                results.append(pattern_result)
        
        return results
    
    def get_recommendations(
        self,
        code: str,
        config_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Получение рекомендаций на основе базы знаний
        
        Args:
            code: Код для анализа
            config_name: Название конфигурации (опционально)
            
        Returns:
            Список рекомендаций
        """
        recommendations = []
        
        configs_to_search = [config_name.lower()] if config_name else self.SUPPORTED_CONFIGURATIONS
        
        for config_key in configs_to_search:
            if config_key not in self._cache:
                continue
            
            config_data = self._cache[config_key]
            
            # Поиск паттернов в коде
            patterns = config_data.get("common_patterns", [])
            for pattern in patterns:
                pattern_code = pattern.get("code_example", "")
                if pattern_code and pattern_code.lower() in code.lower():
                    recommendations.append({
                        "type": "pattern_match",
                        "severity": "info",
                        "message": f"Обнаружен паттерн: {pattern.get('name', 'Unknown')}",
                        "pattern": pattern,
                        "configuration": config_key,
                        "suggestion": pattern.get("recommendation", "")
                    })
            
            # Проверка best practices
            best_practices = config_data.get("best_practices", [])
            for practice in best_practices:
                if practice.get("code_pattern") and practice["code_pattern"].lower() in code.lower():
                    recommendations.append({
                        "type": "best_practice",
                        "severity": practice.get("severity", "info"),
                        "message": practice.get("title", "Best practice"),
                        "description": practice.get("description", ""),
                        "configuration": config_key,
                        "suggestion": practice.get("recommendation", "")
                    })
        
        return recommendations
    
    def _save_configuration(self, config_key: str) -> bool:
        """Сохранение конфигурации в файл"""
        try:
            config_file = self.kb_path / f"{config_key}.json"
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache[config_key], f, indent=2, ensure_ascii=False)
            
            logger.debug(
                "Сохранена база знаний",
                extra={"config_key": config_key}
            )
            return True
            
        except Exception as e:
            logger.error(
                "Ошибка сохранения базы знаний",
                extra={
                    "config_key": config_key,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            return False
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Получение дефолтной структуры конфигурации"""
        return {
            "name": "",
            "modules": [],
            "best_practices": [],
            "common_patterns": [],
            "api_usage": [],
            "performance_tips": [],
            "known_issues": []
        }
    
    def load_from_directory(self, directory_path: str) -> int:
        """
        Загрузка конфигураций из директории
        
        Args:
            directory_path: Путь к директории с конфигурациями
            
        Returns:
            Количество загруженных конфигураций
        """
        dir_path = Path(directory_path)
        
        if not dir_path.exists() or not dir_path.is_dir():
            logger.error(
                "Директория не найдена",
                extra={"directory_path": str(directory_path)}
            )
            return 0
        
        loaded_count = 0
        
        # Поиск всех .xml файлов (типичный формат 1С конфигураций)
        for xml_file in dir_path.rglob("*.xml"):
            try:
                # TODO: Парсинг XML файлов 1С конфигурации
                # Это требует специального парсера для формата 1С
                logger.info(
                    "Найден файл конфигурации",
                    extra={"xml_file": str(xml_file)}
                )
                # Пока пропускаем
                continue
                
            except Exception as e:
                logger.error(
                    "Ошибка обработки файла конфигурации",
                    extra={
                        "xml_file": str(xml_file),
                        "error": str(e),
                        "error_type": type(e).__name__
                    },
                    exc_info=True
                )
        
        # Поиск JSON файлов с документацией
        for json_file in dir_path.rglob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Определение типа конфигурации по имени файла или содержимому
                config_name = json_file.stem.lower()
                
                if config_name in self.SUPPORTED_CONFIGURATIONS:
                    self._cache[config_name] = data
                    loaded_count += 1
                    logger.info(
                        "Загружена конфигурация",
                        extra={"config_name": config_name}
                    )
                    
            except Exception as e:
                logger.error(
                    "Ошибка загрузки JSON файла",
                    extra={
                        "json_file": str(json_file),
                        "error": str(e),
                        "error_type": type(e).__name__
                    },
                    exc_info=True
                )
        
        return loaded_count


# Глобальный экземпляр
_kb_instance: Optional[ConfigurationKnowledgeBase] = None


def get_knowledge_base() -> ConfigurationKnowledgeBase:
    """Получение экземпляра базы знаний"""
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = ConfigurationKnowledgeBase()
    return _kb_instance







