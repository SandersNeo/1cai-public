# [NEXUS IDENTITY] ID: 8303937428841422536 | DATE: 2025-11-19

"""
Пакет системы промптов для генерации кода 1С.

Предоставляет инструменты для создания, управления и оптимизации промптов
для генерации кода 1С с помощью LLM.
"""

from .manager import PromptManager, PromptTemplate
from .optimizer import PromptOptimizer
from .context import ContextualPromptBuilder

__all__ = [
    'PromptManager',
    'PromptTemplate', 
    'PromptOptimizer',
    'ContextualPromptBuilder'
]

__version__ = '1.0.0'