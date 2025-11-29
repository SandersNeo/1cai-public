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

        self.ib_user = ib_user
        self.ib_password = ib_password

        from src.ai.agents.qa_engineer_agent_extended import QAEngineerAgentExtended
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
            # 1. Генерация YAxUnit тестов
            test_code = await self.qa_agent.generate_yaxunit_tests_for_ai_code(
                generated_code=generated_code,
                function_name=function_name,
                test_scenarios=test_scenarios,
            )

            # 2. Сохранение тестов в файл
            test_file_path = self._save_test_file(
                test_code=test_code,
                function_name=function_name,
                module_name=module_name,
            )

            # 3. Запуск тестов (если auto_run=True)
            if auto_run:
                validation_result = await self._run_tests(
                    test_file_path=test_file_path,
                    function_name=function_name,
                )
            else:
                # Только генерация, без запуска
                validation_result = ValidationResult(
                    success=True,
                    test_count=test_code.count("Процедура"),
                    passed_tests=0,
                    failed_tests=0,
                    errors=[],
                    warnings=["Тесты сгенерированы, но не запущены (auto_run=False)"],
                    test_file_path=str(test_file_path),
                )

            # 4. Расчет времени выполнения
            execution_time = (datetime.now() - start_time).total_seconds()
            validation_result.execution_time = execution_time
            validation_result.test_file_path = str(test_file_path)

            logger.info(
                "Code validation completed",
                extra={
                    "function_name": function_name,
                    "success": validation_result.success,
                    "test_count": validation_result.test_count,
                    "passed_tests": validation_result.passed_tests,
                    "failed_tests": validation_result.failed_tests,
                    "execution_time": execution_time,
                },
            )

            return validation_result

        except Exception as e:
            logger.error(
                "Code validation failed",
                extra={
                    "function_name": function_name,
                    "error": str(e),
                },
                exc_info=True,
            )

            execution_time = (datetime.now() - start_time).total_seconds()
            return ValidationResult(
                success=False,
                test_count=0,
                passed_tests=0,
                failed_tests=0,
                errors=[f"Ошибка валидации: {str(e)}"],
                warnings=[],
                execution_time=execution_time,
            )

    def _save_test_file(
        self,
        test_code: str,
        function_name: str,
        module_name: Optional[str] = None,
    ) -> Path:
        """
        Сохраняет сгенерированные тесты в файл.

        Args:
            test_code: Код тестов
            function_name: Имя функции
            module_name: Имя модуля

        Returns:
            Путь к сохраненному файлу
        """
        # Определяем имя файла
        if module_name:
            file_name = f"test_{module_name}_{function_name}.bsl"
        else:
            file_name = f"test_ai_{function_name}.bsl"

        # Создаем директорию для тестов
        test_dir = self.test_output_dir / "generated_tests"
        test_dir.mkdir(parents=True, exist_ok=True)

        # Сохраняем файл
        test_file_path = test_dir / file_name
        test_file_path.write_text(test_code, encoding="utf-8")

        logger.info(
            "Test file saved",
            extra={
                "test_file_path": str(test_file_path),
                "function_name": function_name,
            },
        )

        return test_file_path

    async def _run_tests(
        self,
        test_file_path: Path,
        function_name: str,
    ) -> ValidationResult:
        """
        Запускает YAxUnit тесты.

        Args:
            test_file_path: Путь к файлу с тестами
            function_name: Имя функции

        Returns:
            ValidationResult с результатами выполнения тестов
        """
        if not self.ib_path and not self.ib_name:
            logger.warning(
                "Cannot run tests: IB not configured",
                extra={"function_name": function_name},
            )
            return ValidationResult(
                success=False,
                test_count=0,
                passed_tests=0,
                failed_tests=0,
                errors=["Информационная база не настроена (ib_path или ib_name)"],
                warnings=[],
            )

        # Запускаем тесты через run_yaxunit_tests.py
        script_path = Path("scripts/tests/run_yaxunit_tests.py")

        if not script_path.exists():
            logger.error(
                "Test runner script not found", extra={"script_path": str(script_path)}
            )
            return ValidationResult(
                success=False,
                test_count=0,
                passed_tests=0,
                failed_tests=0,
                errors=[f"Скрипт запуска тестов не найден: {script_path}"],
                warnings=[],
            )

        # Формируем команду
        cmd = [
            "python",
            str(script_path),
            "--test-files",
            test_file_path.name,
            "--report-format",
            "jUnit",
            "--log-level",
            "info",
            "--output-dir",
            str(self.test_output_dir),
        ]

        if self.ib_path:
            cmd.extend(["--ib-path", self.ib_path])
        elif self.ib_name:
            cmd.extend(["--ib-name", self.ib_name])

        if self.ib_user:
            cmd.extend(["--ib-user", self.ib_user])

        if self.ib_password:
            cmd.extend(["--ib-password", self.ib_password])

        logger.info(
            "Running tests",
            extra={
                "command": " ".join(cmd),
                "test_file": str(test_file_path),
            },
        )

        try:
            # Запускаем тесты
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=test_file_path.parent.parent.parent,  # Корень проекта
            )

            stdout, stderr = await process.communicate()

            # Парсим результаты
            report_path = self.test_output_dir / "reports" / "report.xml"

            if process.returncode == 0:
                # Успешное выполнение
                # Парсим XML отчет для получения детальной информации
                test_count, passed, failed = self._parse_junit_report(report_path)

                return ValidationResult(
                    success=True,
                    test_count=test_count,
                    passed_tests=passed,
                    failed_tests=failed,
                    errors=[],
                    warnings=[],
                    report_path=str(report_path) if report_path.exists() else None,
                )
            else:
                # Ошибка выполнения
                error_msg = (
                    stderr.decode("utf-8", errors="ignore")
                    if stderr
                    else "Unknown error"
                )

                return ValidationResult(
                    success=False,
                    test_count=0,
                    passed_tests=0,
                    failed_tests=0,
                    errors=[f"Ошибка запуска тестов: {error_msg}"],
                    warnings=[],
                    report_path=str(report_path) if report_path.exists() else None,
                )

        except Exception as e:
            logger.error(
                "Test execution failed",
                extra={
                    "function_name": function_name,
                    "error": str(e),
                },
                exc_info=True,
            )

            return ValidationResult(
                success=False,
                test_count=0,
                passed_tests=0,
                failed_tests=0,
                errors=[f"Исключение при выполнении тестов: {str(e)}"],
                warnings=[],
            )

    def _parse_junit_report(self, report_path: Path) -> tuple[int, int, int]:
        """
        Парсит JUnit XML отчет для получения статистики.

        Args:
            report_path: Путь к XML отчету

        Returns:
            Кортеж (test_count, passed, failed)
        """
        if not report_path.exists():
            return 0, 0, 0

        try:
            import xml.etree.ElementTree as ET

            tree = ET.parse(report_path)
            root = tree.getroot()

            # Парсим JUnit формат
            tests = 0
            failures = 0
            errors = 0

            for testsuite in root.findall(".//testsuite"):
                tests += int(testsuite.get("tests", 0))
                failures += int(testsuite.get("failures", 0))
                errors += int(testsuite.get("errors", 0))

            passed = tests - failures - errors

            return tests, passed, failures + errors

        except Exception as e:
            logger.warning(
                "Failed to parse JUnit report",
                extra={"report_path": str(report_path), "error": str(e)},
            )
            return 0, 0, 0

    def get_validation_summary(self, result: ValidationResult) -> Dict[str, Any]:
        """
        Возвращает краткую сводку результатов валидации.

        Args:
            result: Результат валидации

        Returns:
            Словарь с сводкой
        """
        return {
            "success": result.success,
            "test_count": result.test_count,
            "passed": result.passed_tests,
            "failed": result.failed_tests,
            "pass_rate": (
                result.passed_tests / result.test_count * 100
                if result.test_count > 0
                else 0
            ),
            "execution_time": result.execution_time,
            "has_errors": len(result.errors) > 0,
            "has_warnings": len(result.warnings) > 0,
            "test_file": result.test_file_path,
            "report_file": result.report_path,
        }
