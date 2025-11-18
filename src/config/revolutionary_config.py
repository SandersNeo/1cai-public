"""
Revolutionary Configuration Management
======================================

Управление конфигурацией для всех революционных компонентов:
- Централизованная конфигурация
- Environment-based config
- Hot reload
- Validation
- Secrets management
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigSource(str, Enum):
    """Источники конфигурации"""
    
    ENV = "environment"
    FILE = "file"
    VAULT = "vault"
    DATABASE = "database"


@dataclass
class ComponentConfig:
    """Конфигурация компонента"""
    
    component_name: str
    enabled: bool = True
    settings: Dict[str, Any] = field(default_factory=dict)
    source: ConfigSource = ConfigSource.ENV
    
    def get(self, key: str, default: Any = None) -> Any:
        """Получение значения настройки"""
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Установка значения настройки"""
        self.settings[key] = value


class RevolutionaryConfigManager:
    """
    Менеджер конфигурации для всех революционных компонентов
    
    Управляет конфигурацией:
    - Event-Driven Architecture
    - Self-Evolving AI
    - Self-Healing Code
    - Distributed Network
    - Code DNA
    - Predictive Generation
    """
    
    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = config_file
        self._components: Dict[str, ComponentConfig] = {}
        self._watchers: List[callable] = []
        
        # Загрузка конфигурации
        if config_file and config_file.exists():
            self._load_from_file(config_file)
        else:
            self._load_from_env()
        
        logger.info("RevolutionaryConfigManager initialized")
    
    def _load_from_file(self, config_file: Path) -> None:
        """Загрузка конфигурации из файла"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            for component_name, settings in config_data.get("components", {}).items():
                self._components[component_name] = ComponentConfig(
                    component_name=component_name,
                    enabled=settings.get("enabled", True),
                    settings=settings.get("settings", {}),
                    source=ConfigSource.FILE
                )
            
            logger.info(f"Configuration loaded from {config_file}")
        except Exception as e:
            logger.error(f"Failed to load config from file: {e}")
            self._load_from_env()
    
    def _load_from_env(self) -> None:
        """Загрузка конфигурации из переменных окружения"""
        # Event-Driven
        self._components["event_driven"] = ComponentConfig(
            component_name="event_driven",
            enabled=os.getenv("EVENT_DRIVEN_ENABLED", "true").lower() == "true",
            settings={
                "backend": os.getenv("EVENT_BACKEND", "memory"),
                "num_workers": int(os.getenv("EVENT_WORKERS", "4")),
                "nats_url": os.getenv("NATS_URL", "nats://localhost:4222")
            },
            source=ConfigSource.ENV
        )
        
        # Self-Evolving AI
        self._components["self_evolving"] = ComponentConfig(
            component_name="self_evolving",
            enabled=os.getenv("SELF_EVOLVING_ENABLED", "true").lower() == "true",
            settings={
                "use_rl": os.getenv("SELF_EVOLVING_RL", "true").lower() == "true",
                "multi_objective": os.getenv("SELF_EVOLVING_MULTI_OBJ", "true").lower() == "true"
            },
            source=ConfigSource.ENV
        )
        
        # Self-Healing Code
        self._components["self_healing"] = ComponentConfig(
            component_name="self_healing",
            enabled=os.getenv("SELF_HEALING_ENABLED", "true").lower() == "true",
            settings={
                "use_patterns": os.getenv("SELF_HEALING_PATTERNS", "true").lower() == "true",
                "learn_from_history": os.getenv("SELF_HEALING_LEARN", "true").lower() == "true"
            },
            source=ConfigSource.ENV
        )
        
        # Distributed Network
        self._components["distributed_network"] = ComponentConfig(
            component_name="distributed_network",
            enabled=os.getenv("DISTRIBUTED_NETWORK_ENABLED", "true").lower() == "true",
            settings={
                "consensus_protocol": os.getenv("CONSENSUS_PROTOCOL", "raft"),
                "fault_tolerance": int(os.getenv("FAULT_TOLERANCE", "1"))
            },
            source=ConfigSource.ENV
        )
        
        logger.info("Configuration loaded from environment")
    
    def get_component_config(self, component_name: str) -> Optional[ComponentConfig]:
        """Получение конфигурации компонента"""
        return self._components.get(component_name)
    
    def is_enabled(self, component_name: str) -> bool:
        """Проверка, включен ли компонент"""
        config = self._components.get(component_name)
        return config.enabled if config else False
    
    def update_config(
        self,
        component_name: str,
        settings: Dict[str, Any]
    ) -> None:
        """Обновление конфигурации"""
        if component_name not in self._components:
            self._components[component_name] = ComponentConfig(component_name=component_name)
        
        self._components[component_name].settings.update(settings)
        
        # Уведомление watchers
        for watcher in self._watchers:
            try:
                watcher(component_name, settings)
            except Exception as e:
                logger.error(f"Error in config watcher: {e}")
    
    def register_watcher(self, watcher: callable) -> None:
        """Регистрация watcher для изменений конфигурации"""
        self._watchers.append(watcher)
    
    def save_to_file(self, config_file: Path) -> None:
        """Сохранение конфигурации в файл"""
        config_data = {
            "components": {
                name: {
                    "enabled": config.enabled,
                    "settings": config.settings
                }
                for name, config in self._components.items()
            }
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, default_flow_style=False)
        
        logger.info(f"Configuration saved to {config_file}")

