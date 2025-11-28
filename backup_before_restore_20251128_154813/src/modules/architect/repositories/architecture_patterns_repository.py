"""
Architecture Patterns Repository

Repository для хранения паттернов и best practices.
"""

from typing import Any, Dict


class ArchitecturePatternsRepository:
    """
    Repository для базы знаний архитектурных паттернов

    Хранит:
    - Anti-pattern definitions
    - Refactoring patterns
    - Best practices
    - Thresholds
    """

    def __init__(self):
        """Initialize repository with default data"""
        self._thresholds = self._load_thresholds()
        self._best_practices = self._load_best_practices()

    def get_thresholds(self) -> Dict[str, float]:
        """
        Получить пороговые значения для метрик

        Returns:
            Словарь thresholds
        """
        return self._thresholds

    def get_best_practices(self) -> Dict[str, Any]:
        """
        Получить best practices

        Returns:
            Словарь best practices
        """
        return self._best_practices

    def _load_thresholds(self) -> Dict[str, float]:
        """Load thresholds database"""
        return {
            "coupling": 0.3,  # Coupling score > 0.3 = tight coupling
            "cohesion": 0.7,  # Cohesion score < 0.7 = low cohesion
            "god_object_functions": 50,  # > 50 functions = god object
            "god_object_dependencies": 20,  # > 20 dependencies = god object
            "max_cyclic_dependencies": 0,  # 0 = no cycles allowed
        }

    def _load_best_practices(self) -> Dict[str, Any]:
        """Load best practices database"""
        return {
            "coupling": {
                "target": 0.2,
                "description": "Стремитесь к loose coupling (< 0.3)",
                "techniques": [
                    "Dependency Injection",
                    "Interface Segregation",
                    "Facade Pattern",
                ],
            },
            "cohesion": {
                "target": 0.8,
                "description": "Стремитесь к high cohesion (> 0.7)",
                "techniques": [
                    "Single Responsibility Principle",
                    "Feature Envy Detection",
                    "Extract Class Refactoring",
                ],
            },
            "cyclic_dependencies": {
                "target": 0,
                "description": "Избегайте циклических зависимостей",
                "techniques": [
                    "Dependency Inversion",
                    "Extract Interface",
                    "Introduce Mediator",
                ],
            },
        }


__all__ = ["ArchitecturePatternsRepository"]
