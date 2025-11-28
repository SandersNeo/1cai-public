# [NEXUS IDENTITY] ID: -7018803628093744818 | DATE: 2025-11-19

"""
Role-Based AI Router
Маршрутизация запросов в зависимости от роли пользователя
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class UserRole(Enum):
    """Роли пользователей в системе"""

    DEVELOPER = "developer"
    BUSINESS_ANALYST = "business_analyst"
    QA_ENGINEER = "qa_engineer"
    ARCHITECT = "architect"
    DEVOPS = "devops"
    TECHNICAL_WRITER = "technical_writer"


@dataclass
class RoleConfig:
    """Конфигурация для роли"""

    role: UserRole
    primary_agent: str
    fallback_agents: List[str]
    specializations: List[str]
    temperature: float = 0.3
    max_tokens: int = 2000
    language: str = "ru"


class RoleDetector:
    """Определение роли по запросу"""

    # Keywords для каждой роли
    ROLE_KEYWORDS = {
        UserRole.DEVELOPER: [
            "сгенерируй код",
            "напиши функцию",
            "создай процедуру",
            "оптимизируй",
            "рефактор",
            "исправь код",
            "code",
            "function",
            "генерируй bsl",
            "реализуй",
            "доработай",
        ],
        UserRole.BUSINESS_ANALYST: [
            "требования",
            "ТЗ",
            "техническое задание",
            "бизнес-процесс",
            "user story",
            "use case",
            "сценарий",
            "анализ требований",
            "specification",
            "requirements",
            "процесс",
        ],
        UserRole.QA_ENGINEER: [
            "тест",
            "тестирование",
            "покрытие",
            "баг",
            "bug",
            "vanessa",
            "bdd",
            "smoke",
            "regression",
            "дефект",
            "проверка",
            "quality",
            "qa",
        ],
        UserRole.ARCHITECT: [
            "архитектура",
            "паттерн",
            "зависимости",
            "структура",
            "anti-pattern",
            "best practice",
            "design",
            "модульность",
            "coupling",
            "cohesion",
            "технический долг",
        ],
        UserRole.DEVOPS: [
            "ci/cd",
            "deployment",
            "производительность",
            "мониторинг",
            "docker",
            "kubernetes",
            "pipeline",
            "логи",
            "performance",
            "optimize",
            "infrastructure",
            "capacity",
        ],
        UserRole.TECHNICAL_WRITER: [
            "документация",
            "описание",
            "справка",
            "api docs",
            "user guide",
            "readme",
            "release notes",
            "мануал",
            "инструкция",
            "help",
            "documentation",
        ],
    }

    def detect_role(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> UserRole:
        """
        Определяет роль пользователя по запросу и контексту

        Args:
            query: Текст запроса
            context: Контекст (открытый файл, текущая задача и т.д.)

        Returns:
            Определенная роль
        """
        query_lower = query.lower()

        # Подсчет совпадений для каждой роли
        role_scores = {role: 0 for role in UserRole}

        for role, keywords in self.ROLE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query_lower:
                    role_scores[role] += 1

        # Если есть контекст, учитываем его
        if context:
            # Открытый файл
            current_file = context.get("current_file", "")
            if current_file.endswith(".bsl"):
                role_scores[UserRole.DEVELOPER] += 2
            elif current_file.endswith(".feature"):
                role_scores[UserRole.QA_ENGINEER] += 2
            elif current_file.endswith(".md"):
                role_scores[UserRole.TECHNICAL_WRITER] += 2

            # Явное указание роли в контексте
            if "role" in context:
                try:
                    logger = logging.getLogger(__name__)
                    logger.error("Error in try block", exc_info=True)

        # Находим роль с максимальным score
        max_score = max(role_scores.values())

        if max_score > 0:
            for role, score in role_scores.items():
                if score == max_score:
                    return role

        # По умолчанию - разработчик
        return UserRole.DEVELOPER


class RoleBasedRouter:
    """
    Маршрутизатор запросов на основе ролей
    """

    def __init__(self):
        self.detector = RoleDetector()
        self.role_configs = self._load_role_configs()

        # Импорты AI клиентов
        try:
