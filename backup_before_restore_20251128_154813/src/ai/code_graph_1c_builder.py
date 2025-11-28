# [NEXUS IDENTITY] ID: -4931967186796764150 | DATE: 2025-11-19

"""
Unified Change Graph Builder for 1C Code
-----------------------------------------

Интегратор для построения Unified Change Graph из реального кода 1С (BSL модули).

Использует существующие BSL парсеры для извлечения структуры и автоматически
строит граф узлов (модули, функции, процедуры, переменные) и рёбер (зависимости,
вызовы, использование).

Это ключевая фича для "де-факто" стандарта: автоматическое построение графа
изменений из кода 1С без ручной настройки.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional, Set

from src.ai.code_graph import CodeGraphBackend, Edge, EdgeKind, Node, NodeKind

logger = logging.getLogger(__name__)


class OneCCodeGraphBuilder:
    """
    Построитель Unified Change Graph из кода 1С.

    Использует BSL парсеры для извлечения структуры и автоматически создаёт
    узлы и рёбра в Unified Change Graph.
    """

    def __init__(
        self,
        backend: CodeGraphBackend,
        *,
        use_ast_parser: bool = True,
    ) -> None:
        """
        Args:
            backend: Backend для хранения графа (InMemoryCodeGraphBackend, Neo4j и др.)
            use_ast_parser: Использовать продвинутый AST парсер (если доступен)
        """
        self.backend = backend
        self.use_ast_parser = use_ast_parser
        self._parser = None
        self._module_cache: Dict[str, Dict[str, Any]] = {}

    def _get_parser(self):
        """Ленивая инициализация парсера."""
        if self._parser is None:
            if self.use_ast_parser:
                try:
