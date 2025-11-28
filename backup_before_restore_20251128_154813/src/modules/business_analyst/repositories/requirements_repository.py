"""
Requirements Repository

Repository для хранения паттернов требований и user stories.
"""

from typing import Any, Dict, List


class RequirementsRepository:
    """
    Repository для базы знаний требований

    Хранит:
    - Requirement patterns (functional, non-functional, constraints)
    - User story patterns
    - Acceptance criteria templates
    - Stakeholder roles
    """

    def __init__(self):
        """Initialize repository with default patterns"""
        self._requirement_patterns = self._load_requirement_patterns()
        self._user_story_patterns = self._load_user_story_patterns()

    def get_requirement_patterns(self) -> List[Dict[str, Any]]:
        """
        Получить паттерны для извлечения требований

        Returns:
            Список паттернов с типами и regex
        """
        return self._requirement_patterns

    def get_user_story_patterns(self) -> List[str]:
        """
        Получить паттерны для user stories

        Returns:
            Список regex паттернов
        """
        return self._user_story_patterns

    def _load_requirement_patterns(self) -> List[Dict[str, Any]]:
        """Load requirement patterns database"""
        return [
            {
                "type": "functional",
                "patterns": [
                    r"система должна\s+(?P<body>.+)",
                    r"необходимо\s+(?P<body>.+)",
                    r"должен(?:а|о|ы)?\s+обеспечивать\s+(?P<body>.+)",
                    r"требуется\s+(?P<body>.+)",
                    r"пользователь\s+(?:может|должен)\s+(?P<body>.+)",
                ],
            },
            {
                "type": "non_functional",
                "patterns": [
                    r"производительность[:\s]+(?P<body>.+)",
                    r"(?:время|скорость)\s+(?:отклика|выполнения)[:\s]+(?P<body>.+)",
                    r"(?:количество|число)\s+пользователей[:\s]+(?P<body>.+)",
                    r"(?:доступность|uptime)[:\s]+(?P<body>.+)",
                    r"безопасность[:\s]+(?P<body>.+)",
                ],
            },
            {
                "type": "constraint",
                "patterns": [
                    r"ограничение[:\s]+(?P<body>.+)",
                    r"не допускается\s+(?P<body>.+)",
                    r"запрещено\s+(?P<body>.+)",
                    r"в рамках\s+(?:бюджета|срока)\s+(?P<body>.+)",
                ],
            },
        ]

    def _load_user_story_patterns(self) -> List[str]:
        """Load user story patterns"""
        return [
            r"как\s+(?P<role>[^,]+?),?\s+я\s+(?:хочу|должен|могу)\s+(?P<goal>[^,]+?)(?:,\s*чтобы\s+(?P<benefit>.+))?$",
            r"как\s+(?P<role>[^,]+?)\s+мне\s+нужно\s+(?P<goal>[^,]+)",
        ]


__all__ = ["RequirementsRepository"]
