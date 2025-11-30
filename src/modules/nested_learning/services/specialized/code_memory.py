"""
Code Memory - Specialized CMS for code patterns

Multi-level memory for code completion with different temporal scales.
"""

import hashlib
from typing import Any, Dict, Optional

import numpy as np

from src.modules.nested_learning.services.cms import ContinuumMemorySystem
from src.modules.nested_learning.services.memory_level import MemoryLevel, MemoryLevelConfig
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class CodePatternLevel(MemoryLevel):
    """Memory level for code patterns"""

    def __init__(self, config: MemoryLevelConfig, pattern_type: str):
        """
        Initialize code pattern level

        Args:
            config: Level configuration
            pattern_type: Type of patterns (char, token, function, etc.)
        """
        super().__init__(config)
        self.pattern_type = pattern_type

    def encode(self, data: Any, context: Dict) -> np.ndarray:
        """
        Encode code pattern

        Args:
            data: Code string or pattern
            context: Additional context

        Returns:
            Pattern embedding
        """
        self.stats.total_encodes += 1

        if isinstance(data, str):
            code = data
        elif isinstance(data, dict):
            code = data.get("code", str(data))
        else:
            code = str(data)

        # Extract pattern based on level type
        if self.pattern_type == "char":
            pattern = self._extract_char_pattern(code)
        elif self.pattern_type == "token":
            pattern = self._extract_token_pattern(code)
        elif self.pattern_type == "function":
            pattern = self._extract_function_pattern(code)
        elif self.pattern_type == "project":
            pattern = self._extract_project_pattern(code, context)
        elif self.pattern_type == "platform":
            pattern = self._extract_platform_pattern(code)
        else:
            pattern = code

        # Hash to embedding
        pattern_hash = hashlib.sha256(pattern.encode()).digest()
        embedding = np.array(
            [float(b) / 255.0 for b in pattern_hash[:64]], dtype="float32")

        return embedding

    def _extract_char_pattern(self, code: str) -> str:
        """Extract character-level pattern"""
        # Last 10 characters
        return code[-10:] if len(code) > 10 else code

    def _extract_token_pattern(self, code: str) -> str:
        """Extract token-level pattern"""
        # Last few tokens (words)
        tokens = code.split()
        return " ".join(tokens[-5:]) if len(tokens) > 5 else code

    def _extract_function_pattern(self, code: str) -> str:
        """Extract function-level pattern"""
        # Function signature or structure
        lines = code.split("\n")

        # Look for function declarations
        for line in reversed(lines):
            if "Функция" in line or "Процедура" in line:
                return line.strip()

        # Fallback: last line
        return lines[-1] if lines else code

    def _extract_project_pattern(self, code: str, context: Dict) -> str:
        """Extract project-level pattern"""
        # Project context + code structure
        project_name = context.get("project", "unknown")
        module_name = context.get("module", "unknown")

        return f"{project_name}:{module_name}:{code[:50]}"

    def _extract_platform_pattern(self, code: str) -> str:
        """Extract platform-level pattern"""
        # 1C platform keywords and structures
        platform_keywords = [
            "Функция",
            "Процедура",
            "КонецФункции",
            "КонецПроцедуры",
            "Если",
            "Тогда",
            "КонецЕсли",
            "Для",
            "КонецЦикла",
            "Возврат",
            "Новый",
            "Выборка",
        ]

        # Extract keywords present in code
        found_keywords = [kw for kw in platform_keywords if kw in code]

        return " ".join(found_keywords) if found_keywords else "generic"


class CodeMemory(ContinuumMemorySystem):
    """
    Specialized CMS for code patterns

    5 levels:
    - char (L0): Character-level patterns
    - token (L1): Token/word-level patterns
    - function (L2): Function-level structures
    - project (L3): Project-specific patterns
    - platform (L4): 1C platform knowledge

    Example:
        >>> memory = CodeMemory()
        >>> memory.store_code("char", "key1", "Функция Test()")
        >>> suggestions = memory.get_suggestions("Функция ", context={})
    """

    def __init__(self):
        """Initialize code memory with 5 levels"""
        levels = [
            ("char", 1, 0.01),  # Every keystroke
            ("token", 10, 0.001),  # Every 10 keystrokes
            ("function", 100, 0.0001),  # Every function
            ("project", 1000, 0.00001),  # Project patterns
            ("platform", int(1e9), 0.0),  # Static platform knowledge
        ]

        super().__init__(levels, embedding_dim=64)

        # Override with CodePatternLevel
        for name, level in self.levels.items():
            config = level.config

            # Mark platform as frozen
            if name == "platform":
                config.frozen = True

            self.levels[name] = CodePatternLevel(config, pattern_type=name)

        logger.info("Created CodeMemory with 5 levels")

    def store_code(self, level_name: str, key: str, code: str, context: Optional[Dict] = None):
        """
        Store code pattern at specific level

        Args:
            level_name: Level to store at
            key: Unique key
            code: Code string
            context: Optional context
        """
        context = context or {}
        self.store(level_name, key, {"code": code, **context})

    def get_suggestions(self, prefix: str, context: Optional[Dict] = None, k: int = 5) -> Dict[str, list]:
        """
        Get completion suggestions from all levels

        Args:
            prefix: Code prefix to complete
            context: Optional context
            k: Number of suggestions per level

        Returns:
            Dict mapping level -> suggestions
        """
        context = context or {}

        # Retrieve from all levels
        levels_to_search = ["char", "token", "function", "project"]

        suggestions = self.retrieve_similar(
            {"code": prefix, **context}, levels=levels_to_search, k=k)

        return suggestions

    def learn_from_acceptance(self, code: str, accepted: bool, context: Optional[Dict] = None):
        """
        Learn from user acceptance/rejection

        Args:
            code: Code that was suggested
            accepted: Whether user accepted it
            context: Optional context
        """
        context = context or {}

        # Compute surprise (unexpected rejection/acceptance)
        surprise = 0.8 if not accepted else 0.2

        # Generate key
        key = hashlib.sha256(code.encode()).hexdigest()

        # Update appropriate levels
        if not accepted:  # High surprise - rejected suggestion
            # Update fast levels to avoid this pattern
            self.update_level("char", key, {"code": code, **context}, surprise)
            self.update_level("token", key, {"code": code, **context}, surprise)
        else:  # Low surprise - accepted suggestion
            # Reinforce pattern
            self.update_level("char", key, {"code": code, **context}, 0.3)

        # Advance step
        self.step()
