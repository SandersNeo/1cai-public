# [NEXUS IDENTITY] ID: -1233742692372497687 | DATE: 2025-11-19

"""
Migration Script: Celery → Event-Driven Architecture
====================================================

Скрипт для миграции существующих Celery задач на Event-Driven Architecture

Использование:
    python src/migration/celery_to_event_driven.py --dry-run
    python src/migration/celery_to_event_driven.py --migrate
"""

import asyncio
import ast
import logging
import sys
from pathlib import Path
from typing import Dict, List
import argparse

from src.infrastructure.event_bus import EventBus, EventType
from src.infrastructure.event_store import InMemoryEventStore

logger = logging.getLogger(__name__)


class CeleryTaskAnalyzer:
    """Анализатор Celery задач"""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.tasks: List[Dict] = []

    def analyze(self) -> List[Dict]:
        """Анализ файла с Celery задачами"""
        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Проверка декоратора @celery_app.task
                if self._is_celery_task(node):
                    task_info = self._extract_task_info(node)
                    self.tasks.append(task_info)

        return self.tasks

    def _is_celery_task(self, node: ast.FunctionDef) -> bool:
        """Проверка, является ли функция Celery задачей"""
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Attribute):
                if decorator.attr == "task":
                    return True
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Attribute):
                    if decorator.func.attr == "task":
                        return True
        return False

    def _extract_task_info(self, node: ast.FunctionDef) -> Dict:
        """Извлечение информации о задаче"""
        return {
            "name": node.name,
            "args": [arg.arg for arg in node.args.args],
            "docstring": ast.get_docstring(node),
            "line_number": node.lineno,
        }


class EventDrivenMigrator:
    """Мигратор Celery → Event-Driven"""

    def __init__(self):
        self.event_bus = EventBus()
        self.event_store = InMemoryEventStore()
        self.migration_map: Dict[str, EventType] = {}

    async def migrate_task(self, task_info: Dict, source_file: Path) -> str:
        """
        Миграция одной задачи

        Returns:
            Сгенерированный код для Event-Driven версии
        """
        task_name = task_info["name"]

        # Определение типа события
        event_type = self._map_task_to_event_type(task_name)

        # Генерация кода
        code = self._generate_event_handler_code(task_info, event_type)

        return code

    def _map_task_to_event_type(self, task_name: str) -> EventType:
        """Маппинг имени задачи на тип события"""
        # Простая эвристика
        if "ml" in task_name.lower() or "train" in task_name.lower():
            return EventType.ML_TRAINING_STARTED
        elif "test" in task_name.lower():
            return EventType.CODE_TESTED
        elif "deploy" in task_name.lower():
            return EventType.CODE_DEPLOYED
        else:
            return EventType.AI_AGENT_STARTED

    def _generate_event_handler_code(
        self, task_info: Dict, event_type: EventType
    ) -> str:
        """Генерация кода обработчика событий"""
        args = ", ".join(task_info["args"])
        docstring = task_info.get("docstring", "")

        code = f'''
"""
Event Handler: {task_info["name"]}
Migrated from Celery task
{docstring}
"""

from src.infrastructure.event_bus import Event, EventHandler, EventType

class {task_info["name"].title()}Handler(EventHandler):
    """Обработчик события {event_type.value}"""
    
    @property
    def event_types(self):
        return {{EventType.{event_type.name}}}
    
    async def handle(self, event: Event) -> None:
        """
        Обработка события
        
        Args:
            event: Событие с payload
        """
        # Извлечение параметров из payload
        payload = event.payload
        {args} = payload.get("{args.split(',')[0] if args else 'data'}", None)
        
        # TODO: Реализовать логику из оригинальной Celery задачи
        # Оригинальная функция: {task_info["name"]}
        
        # Ваша логика здесь
        pass
'''
        return code


async def migrate_file(
    source_file: Path, output_dir: Path, dry_run: bool = False
) -> None:
    """Миграция файла с Celery задачами"""
    logger.info(f"Analyzing file: {source_file}")

    analyzer = CeleryTaskAnalyzer(source_file)
    tasks = analyzer.analyze()

    logger.info(f"Found {len(tasks)} Celery tasks")

    if dry_run:
        logger.info("DRY RUN - No files will be modified")
        for task in tasks:
            print(f"  - {task['name']} (line {task['line_number']})")
        return

    migrator = EventDrivenMigrator()
    output_dir.mkdir(parents=True, exist_ok=True)

    for task in tasks:
        logger.info(f"Migrating task: {task['name']}")

        code = await migrator.migrate_task(task, source_file)

        # Сохранение в файл
        output_file = output_dir / f"{task['name']}_handler.py"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(code)

        logger.info(f"Generated: {output_file}")


async def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description="Migrate Celery tasks to Event-Driven Architecture"
    )
    parser.add_argument(
        "--source",
        type=str,
        default="src/workers",
        help="Source directory with Celery tasks",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="src/workers/event_driven",
        help="Output directory for migrated handlers",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Dry run mode (no files modified)"
    )

    args = parser.parse_args()

    source_dir = Path(args.source)
    output_dir = Path(args.output)

    if not source_dir.exists():
        logger.error(f"Source directory not found: {source_dir}")
        sys.exit(1)

    # Поиск всех Python файлов с Celery задачами
    celery_files = list(source_dir.glob("**/*ml_tasks*.py"))

    if not celery_files:
        logger.warning("No Celery task files found")
        return

    logger.info(f"Found {len(celery_files)} files to migrate")

    for file_path in celery_files:
        await migrate_file(file_path, output_dir, args.dry_run)

    logger.info("Migration completed!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
