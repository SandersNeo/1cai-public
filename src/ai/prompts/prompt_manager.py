# [NEXUS IDENTITY] ID: -3123437763713397881 | DATE: 2025-11-19

"""
Менеджер промптов для AI-ассистентов.
Обеспечивает загрузку, шаблонизацию и управление версиями промптов.
"""

from typing import Any, Dict


class PromptManager:
    """Менеджер промптов."""

    def __init__(self) -> None:
        """Инициализация менеджера промптов."""
        self._prompts: Dict[str, str] = {}

    def get_prompt(self, prompt_name: str, **kwargs: Any) -> str:
        """Получить отформатированный промпт по имени.
        
        Args:
            prompt_name: Имя промпта
            **kwargs: Параметры для форматирования
            
        Returns:
            str: Отформатированный текст промпта
        """
        template = self._prompts.get(prompt_name, "")
        if not template:
            return f"Prompt {prompt_name} not found"
        
        try:
            return template.format(**kwargs)
        except KeyError as e:
            return template  # Возвращаем как есть в случае ошибки

    def register_prompt(self, name: str, template: str) -> None:
        """Зарегистрировать новый промпт.
        
        Args:
            name: Имя промпта
            template: Шаблон промпта
        """
        self._prompts[name] = template


# Глобальный экземпляр
prompt_manager = PromptManager()
