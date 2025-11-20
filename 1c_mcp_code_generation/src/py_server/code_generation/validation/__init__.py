# [NEXUS IDENTITY] ID: 3122040539614511485 | DATE: 2025-11-19

#!/usr/bin/env python3
"""
Validation Package для 1C AI MCP Code Generation

Пакет для валидации кода 1С.

Версия: 1.0
Дата: 30.10.2025
"""

from .validator import CodeValidator, ValidationResult, SyntaxValidationResult, StandardComplianceResult, SecurityAnalysisResult

__version__ = "1.0.0"
__all__ = [
    'CodeValidator', 
    'ValidationResult', 
    'SyntaxValidationResult', 
    'StandardComplianceResult', 
    'SecurityAnalysisResult'
]