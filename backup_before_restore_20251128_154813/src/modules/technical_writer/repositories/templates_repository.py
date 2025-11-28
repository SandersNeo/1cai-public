"""
Templates Repository

Repository для хранения documentation templates.
"""

from typing import Any, Dict


class TemplatesRepository:
    """
    Repository для базы знаний templates

    Хранит:
    - API documentation templates
    - User guide templates
    - Release notes templates
    - Code documentation templates
    """

    def __init__(self):
        """Initialize repository with default templates"""
        self._api_templates = self._load_api_templates()
        self._guide_templates = self._load_guide_templates()
        self._release_templates = self._load_release_templates()

    def get_api_template(self, template_type: str) -> Dict[str, Any]:
        """Получить API template"""
        return self._api_templates.get(template_type, {})

    def get_guide_template(self, audience: str) -> Dict[str, Any]:
        """Получить guide template"""
        return self._guide_templates.get(audience, {})

    def get_release_template(self) -> str:
        """Получить release notes template"""
        return self._release_templates.get("default", "")

    def _load_api_templates(self) -> Dict[str, Any]:
        """Load API templates"""
        return {
            "openapi": {
                "version": "3.0.0",
                "info_template": {"title": "API", "version": "1.0.0"},
            },
            "markdown": {
                "header": "# API Documentation\n\n",
                "endpoint_template": "### `{method} {path}`\n\n",
            },
        }

    def _load_guide_templates(self) -> Dict[str, Any]:
        """Load guide templates"""
        return {
            "end_user": {"sections": ["Обзор", "Начало работы", "Основные операции"]},
            "developer": {"sections": ["Обзор", "API Reference", "Code Examples"]},
            "admin": {"sections": ["Обзор", "Конфигурация", "Мониторинг"]},
        }

    def _load_release_templates(self) -> Dict[str, str]:
        """Load release notes templates"""
        return {"default": "# Release Notes - {version}\n\n"}


__all__ = ["TemplatesRepository"]
