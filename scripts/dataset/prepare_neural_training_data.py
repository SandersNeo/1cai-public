# [NEXUS IDENTITY] ID: 6256332134941883513 | DATE: 2025-11-19

#!/usr/bin/env python3
"""
Подготовка training dataset для Neural BSL Parser
Извлечение и обогащение данных из PostgreSQL

Создает:
- train.json (40,000+ примеров)
- val.json (5,000+)
- test.json (5,000+)

С метаданными:
- Intent labels
- Quality scores
- Complexity metrics
- Best practices tags

Версия: 1.0.0
"""

import argparse
import asyncio
import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

try:
    import asyncpg
except ImportError:
    print("[ERROR] asyncpg not installed: pip install asyncpg")
    exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NeuralDatasetPreparer:
    """
    Подготовка dataset для Neural Parser
    
    Процесс:
    1. Извлечение из PostgreSQL (50k+ функций)
    2. Auto-labeling (intent, quality)
    3. Data augmentation
    4. Train/val/test split
    """
    
    def __init__(self, output_dir: str | Path = "./data/neural_training"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.examples = []
        self.stats = defaultdict(int)
    
    async def prepare_from_postgres(
        self,
        db_url: str = "postgresql://parser_user:parser_pass_2024@localhost:5433/1c_ai_db"
    ):
        """
        Извлечение и обогащение данных из PostgreSQL
        """
        logger.info("🔄 Подключение к PostgreSQL...")
        
        try:
            conn = await asyncpg.connect(db_url)
            
            # Запрос всех функций с кодом
            query = """
                SELECT 
                    function_name,
                    code,
                    description,
                    parameters,
                    is_exported,
                    config_name,
                    module_type
                FROM knowledge_base.module_details
                WHERE code IS NOT NULL
                AND LENGTH(code) > 50
                AND LENGTH(code) < 5000
                LIMIT 50000
            """
            
            logger.info("📊 Извлечение функций...")
            rows = await conn.fetch(query)
            
            logger.info(f"✅ Извлечено {len(rows)} функций")
            
            # Обрабатываем каждую функцию
            for row in rows:
                example = self._prepare_example(row)
                if example:
                    self.examples.append(example)
                    self.stats['total'] += 1
                    self.stats[f"intent_{example['intent']}"] += 1
            
            await conn.close()
            
            logger.info(f"✅ Подготовлено {len(self.examples)} примеров")
            
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к PostgreSQL: {e}")
            logger.warning("⚠️  Создаем sample dataset...")
            self._create_sample_dataset()
    
    def _prepare_example(self, row: asyncpg.Record) -> Dict[str, Any]:
        """
        Подготовка одного обучающего примера
        
        Auto-labeling:
        - Intent detection (на основе имени и кода)
        - Quality score (эвристики)
        - Complexity (подсчет циклов, условий)
        """
        code = row['code']
        function_name = row['function_name'] or ''
        
        # 1. Auto-label intent
        intent = self._detect_intent(function_name, code)
        
        # 2. Calculate quality score
        quality = self._calculate_quality(code, row)
        
        # 3. Calculate complexity
        complexity = self._calculate_complexity(code)
        
        # 4. Calculate maintainability
        maintainability = self._calculate_maintainability(code)
        
        return {
            'code': code,
            'function_name': function_name,
            'intent': intent,
            'quality': quality,
            'complexity': complexity,
            'maintainability': maintainability,
            'is_exported': row.get('is_exported', False),
            'config_name': row.get('config_name', ''),
            'module_type': row.get('module_type', '')
        }
    
    def _detect_intent(self, function_name: str, code: str) -> str:
        """
        Auto-labeling намерений функции
        
        На основе:
        - Имени функции
        - Ключевых слов в коде
        - Паттернов использования
        """
        fname_lower = function_name.lower()
        code_lower = code.lower()
        
        # Data Retrieval
        if any(kw in fname_lower for kw in ['получить', 'найти', 'выбрать', 'get', 'find', 'select']):
            if 'запрос' in code_lower or 'query' in code_lower:
                return 'data_retrieval'
        
        # Data Creation
        if any(kw in fname_lower for kw in ['создать', 'добавить', 'новый', 'create', 'add', 'new']):
            return 'data_creation'
        
        # Data Update
        if any(kw in fname_lower for kw in ['обновить', 'изменить', 'update', 'modify']):
            return 'data_update'
        
        # Data Deletion
        if any(kw in fname_lower for kw in ['удалить', 'delete', 'remove']):
            return 'data_deletion'
        
        # Calculation
        if any(kw in fname_lower for kw in ['рассчитать', 'вычислить', 'calc', 'calculate', 'compute']):
            return 'calculation'
        
        # Validation
        if any(kw in fname_lower for kw in ['проверить', 'валидировать', 'validate', 'check']):
            return 'validation'
        
        # Transformation
        if any(kw in fname_lower for kw in ['преобразовать', 'конвертировать', 'transform', 'convert']):
            return 'transformation'
        
        # Integration
        if 'http' in code_lower or 'rest' in code_lower or 'soap' in code_lower:
            return 'integration'
        
        # UI Interaction
        if 'форма' in code_lower or 'form' in code_lower or 'элемент' in code_lower:
            return 'ui_interaction'
        
        # Default
        return 'utility'
    
    def _calculate_quality(self, code: str, row: asyncpg.Record) -> float:
        """
        Расчет quality score (0-1)
        
        Критерии:
        - Наличие комментариев
        - Обработка ошибок
        - Длина функции
        - Экспортируемость
        """
        score = 0.5  # Base score
        
        # Комментарии (+0.15)
        if '//' in code or '/*' in code:
            score += 0.15
        
        # Обработка ошибок (+0.15)
        if 'Попытка' in code or 'Try' in code:
            score += 0.15
        
        # Оптимальная длина (+0.1)
        lines = len(code.split('\n'))
        if 10 <= lines <= 100:
            score += 0.1
        
        # Экспортируемая функция (+0.05)
        if row.get('is_exported'):
            score += 0.05
        
        # Описание (+0.05)
        if row.get('description'):
            score += 0.05
        
        return min(score, 1.0)
    
    def _calculate_complexity(self, code: str) -> float:
        """
        Цикломатическая сложность (нормализованная 0-1)
        
        Подсчет:
        - Условия (Если, Иначе)
        - Циклы (Для, Пока)
        - Try-Catch блоки
        """
        complexity = 1  # Base complexity
        
        # Условия
        complexity += code.count('Если')
        complexity += code.count('Иначе')
        
        # Циклы
        complexity += code.count('Для')
        complexity += code.count('Пока')
        complexity += code.count('Цикл')
        
        # Exception handling
        complexity += code.count('Попытка')
        
        # Нормализация (max expected = 20)
        normalized = min(complexity / 20.0, 1.0)
        
        return normalized
    
    def _calculate_maintainability(self, code: str) -> float:
        """
        Maintainability index (упрощенный, 0-1)
        
        Факторы:
        - Длина функции
        - Вложенность
        - Комментарии
        """
        score = 1.0
        
        lines = len(code.split('\n'))
        
        # Штраф за длину
        if lines > 100:
            score -= 0.3
        elif lines > 50:
            score -= 0.15
        
        # Штраф за отсутствие комментариев
        if '//' not in code and '/*' not in code:
            score -= 0.2
        
        # Штраф за высокую вложенность
        max_indent = max(
            (len(line) - len(line.lstrip())) // 4 
            for line in code.split('\n') 
            if line.strip()
        )
        if max_indent > 4:
            score -= 0.2
        
        return max(score, 0.0)
    
    def _create_sample_dataset(self):
        """Создание sample dataset для тестирования"""
        samples = [
            {
                'code': 'Функция ПолучитьДанные() Запрос = Новый Запрос; Возврат Запрос.Выполнить(); КонецФункции',
                'function_name': 'ПолучитьДанные',
                'intent': 'data_retrieval',
                'quality': 0.6,
                'complexity': 0.1,
                'maintainability': 0.7
            },
            {
                'code': 'Функция РассчитатьСумму(А, Б) Возврат А + Б; КонецФункции',
                'function_name': 'РассчитатьСумму',
                'intent': 'calculation',
                'quality': 0.7,
                'complexity': 0.05,
                'maintainability': 0.9
            },
            # Добавим еще примеры для разнообразия
        ] * 100  # Дублируем для минимального dataset
        
        self.examples = samples
        logger.info(f"✅ Создано {len(self.examples)} sample примеров")
    
    def save_dataset(self, train_ratio: float = 0.8, val_ratio: float = 0.1):
        """
        Сохранение dataset с разбиением
        
        Args:
            train_ratio: Доля train (default 0.8)
            val_ratio: Доля validation (default 0.1)
            test_ratio: Остальное для test
        """
        logger.info("💾 Сохранение dataset...")
        
        # Shuffle
        import random
        random.shuffle(self.examples)
        
        # Split
        n = len(self.examples)
        train_size = int(n * train_ratio)
        val_size = int(n * val_ratio)
        
        train_examples = self.examples[:train_size]
        val_examples = self.examples[train_size:train_size + val_size]
        test_examples = self.examples[train_size + val_size:]
        
        # Save
        self._save_json(train_examples, 'train.json')
        self._save_json(val_examples, 'val.json')
        self._save_json(test_examples, 'test.json')
        
        # Stats
        self._save_stats()
        
        logger.info(f"✅ Train: {len(train_examples)}")
        logger.info(f"✅ Val: {len(val_examples)}")
        logger.info(f"✅ Test: {len(test_examples)}")
    
    def _save_json(self, examples: List[Dict], filename: str):
        """Сохранение в JSON"""
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(examples, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 {filename}: {len(examples)} примеров")
    
    def _save_stats(self):
        """Сохранение статистики"""
        stats_file = self.output_dir / 'stats.json'
        payload = {
            'schema_version': '1.0.0',
            'summary': dict(self.stats),
        }
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2)
        logger.info(f"📊 Статистика: {stats_file}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Подготовка dataset для Neural BSL Parser")
    parser.add_argument(
        "--db-url",
        default="postgresql://parser_user:parser_pass_2024@localhost:5433/1c_ai_db",
        help="Строка подключения к PostgreSQL",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("./data/neural_training"),
        help="Каталог для сохранения train/val/test",
    )
    parser.add_argument(
        "--train-ratio",
        type=float,
        default=0.8,
        help="Доля обучающей выборки",
    )
    parser.add_argument(
        "--val-ratio",
        type=float,
        default=0.1,
        help="Доля валидационной выборки",
    )
    return parser.parse_args()


async def run(args: argparse.Namespace) -> None:
    logger.info("=" * 70)
    logger.info("ПОДГОТОВКА TRAINING DATASET ДЛЯ NEURAL PARSER")
    logger.info("=" * 70)

    preparer = NeuralDatasetPreparer(args.output_dir)
    await preparer.prepare_from_postgres(db_url=args.db_url)
    preparer.save_dataset(train_ratio=args.train_ratio, val_ratio=args.val_ratio)

    logger.info("=" * 70)
    logger.info("✅ Dataset готов!")
    logger.info("=" * 70)
    logger.info("Файлы:")
    logger.info("  - %s", preparer.output_dir / "train.json")
    logger.info("  - %s", preparer.output_dir / "val.json")
    logger.info("  - %s", preparer.output_dir / "test.json")


def main() -> int:
    args = parse_args()
    try:
        asyncio.run(run(args))
    except Exception as err:  # noqa: BLE001
        logger.error("❌ Ошибка подготовки dataset: %s", err)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())





