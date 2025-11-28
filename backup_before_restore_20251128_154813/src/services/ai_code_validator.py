# [NEXUS IDENTITY] ID: -8173202557794530176 | DATE: 2025-11-19

"""
Сервис автоматической валидации AI-сгенерированного кода через YAxUnit тесты.

Этот сервис:
1. Генерирует YAxUnit тесты для AI-сгенерированного кода
2. Запускает тесты автоматически
3. Анализирует результаты
4. Предоставляет отчет о качестве кода
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.ai.agents.qa_engineer_agent_extended import QAEngineerAgentExtended
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


@dataclass
class ValidationResult:
    """Результат валидации AI-кода"""

    success: bool
    test_count: int
    passed_tests: int
    failed_tests: int
    errors: List[str]
    warnings: List[str]
    test_file_path: Optional[str] = None
    report_path: Optional[str] = None
    execution_time: float = 0.0
    coverage_estimate: float = 0.0


class AICodeValidator:
    """
    Валидатор AI-сгенерированного кода через YAxUnit тесты.
    """

    def __init__(
        self,
        test_output_dir: Path = Path("output/bsl-tests"),
        ib_path: Optional[str] = None,
        ib_name: Optional[str] = None,
        ib_user: str = "Admin",
        ib_password: Optional[str] = None,
    ):
        """
        Инициализация валидатора.

        Args:
            test_output_dir: Директория для сохранения тестов и отчетов
            ib_path: Путь к файловой информационной базе
            ib_name: Имя информационной базы на сервере
            ib_user: Имя пользователя
            ib_password: Пароль пользователя
        """
        self.test_output_dir = Path(test_output_dir)
        self.test_output_dir.mkdir(parents=True, exist_ok=True)

        self.ib_path = ib_path
        self.ib_name = ib_name
        self.ib_user = ib_user
        self.ib_password = ib_password

        self.qa_agent = QAEngineerAgentExtended()

        logger.info(
            "AICodeValidator initialized",
            extra={
                "test_output_dir": str(self.test_output_dir),
                "ib_path": ib_path,
                "ib_name": ib_name,
            },
        )

    async def validate_generated_code(
        self,
        generated_code: str,
        function_name: str,
        module_name: Optional[str] = None,
        test_scenarios: Optional[List[str]] = None,
        auto_run: bool = True,
    ) -> ValidationResult:
        """
        Валидирует AI-сгенерированный код через YAxUnit тесты.

        Args:
            generated_code: AI-сгенерированный BSL код
            function_name: Имя функции
            module_name: Имя модуля (опционально)
            test_scenarios: Сценарии тестирования (опционально)
            auto_run: Автоматически запускать тесты после генерации

        Returns:
            ValidationResult с результатами валидации
        """
        start_time = datetime.now()

        logger.info(
            "Starting code validation",
            extra={
                "function_name": function_name,
                "module_name": module_name,
                "auto_run": auto_run,
            },
        )

        try:
