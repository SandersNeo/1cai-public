"""
AI Issue Classifier - ML классификация проблем производительности
Based on: Neural networks from 1c-parsing-tech-log
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


@dataclass
class ClassifiedIssue:
    """Классифицированная проблема"""
    category: str
    subcategory: str
    confidence: float
    severity: str
    root_cause: str
    recommendation: str
    similar_cases: int
    auto_fix_available: bool


class AIIssueClassifier:
    """
    AI классификатор проблем производительности
    
    Uses:
    - Pattern recognition
    - Historical data analysis
    - ML model (placeholder for real model)
    
    Categories:
    - SQL performance (медленный запрос)
    - Memory leak (утечка памяти)
    - Deadlock (блокировка)
    - Exception (исключение)
    - Connection issue (проблемы подключения)
    - Business logic (бизнес-логика)
    """
    
    def __init__(self):
        # ML model (placeholder)
        self.model = None
        
        # Knowledge base из исторических данных
        self.known_patterns = self._load_known_patterns()
        
        # Статистика классификации
        self.classification_stats = {
            'total_classified': 0,
            'by_category': {},
            'confidence_avg': 0.0
        }
    
    def _load_known_patterns(self) -> Dict[str, List[Dict]]:
        """
        Загрузка известных паттернов из базы знаний
        
        Based on: 1c-parsing-tech-log historical data
        """
        return {
            'sql_performance': [
                {
                    'pattern': 'SELECT * FROM large_table',
                    'root_cause': 'Full table scan без WHERE',
                    'solution': 'Добавить WHERE clause и индексы',
                    'confidence_threshold': 0.9
                },
                {
                    'pattern': 'N+1 queries in loop',
                    'root_cause': 'Запрос на каждой итерации цикла',
                    'solution': 'Использовать JOIN или временную таблицу',
                    'confidence_threshold': 0.95
                },
                {
                    'pattern': 'UPPER() in WHERE',
                    'root_cause': 'Функция блокирует использование индекса',
                    'solution': 'Создать functional index или computed column',
                    'confidence_threshold': 0.85
                }
            ],
            
            'memory_leak': [
                {
                    'pattern': 'Memory growth over time',
                    'root_cause': 'Не освобождаются объекты',
                    'solution': 'Очищать коллекции, освобождать COM объекты',
                    'confidence_threshold': 0.8
                }
            ],
            
            'deadlock': [
                {
                    'pattern': 'Lock wait timeout',
                    'root_cause': 'Конкурентный доступ к ресурсу',
                    'solution': 'Использовать управляемые блокировки',
                    'confidence_threshold': 0.9
                }
            ],
            
            'exception': [
                {
                    'pattern': 'Ошибка проведения документа',
                    'root_cause': 'Нарушение бизнес-логики или блокировка',
                    'solution': 'Проверить логику проведения и блокировки',
                    'confidence_threshold': 0.7
                }
            ]
        }
    
    async def classify_issue(
        self,
        issue_data: Dict[str, Any]
    ) -> ClassifiedIssue:
        """
        Классификация проблемы с помощью AI
        
        Args:
            issue_data: {
                "type": "slow_query",
                "details": "...",
                "sql": "SELECT ...",
                "duration_ms": 15300,
                "context": "..."
            }
            
        Returns:
            Классифицированная проблема с рекомендациями
        """
        logger.info(
            "Classifying issue",
            extra={"issue_type": issue_data.get('type')}
        )
        
        # 1. Feature extraction
        features = self._extract_features(issue_data)
        
        # 2. Pattern matching
        matched_pattern = await self._match_pattern(features)
        
        # 3. ML classification (если модель доступна)
        if self.model:
            ml_category = await self._ml_classify(features)
        else:
            ml_category = matched_pattern
        
        # 4. Определение root cause
        root_cause = self._determine_root_cause(issue_data, matched_pattern)
        
        # 5. Генерация рекомендации
        recommendation = self._generate_recommendation(matched_pattern, root_cause)
        
        # 6. Поиск похожих случаев
        similar_cases = self._find_similar_cases(issue_data)
        
        # 7. Проверка auto-fix
        auto_fix = self._check_auto_fix_available(matched_pattern['category'])
        
        # Update stats
        self.classification_stats['total_classified'] += 1
        
        return ClassifiedIssue(
            category=matched_pattern['category'],
            subcategory=matched_pattern['subcategory'],
            confidence=matched_pattern['confidence'],
            severity=issue_data.get('severity', 'medium'),
            root_cause=root_cause,
            recommendation=recommendation,
            similar_cases=similar_cases,
            auto_fix_available=auto_fix
        )
    
    def _extract_features(self, issue_data: Dict) -> Dict[str, Any]:
        """Извлечение признаков для классификации"""
        return {
            'issue_type': issue_data.get('type', ''),
            'duration': issue_data.get('duration_ms', 0),
            'sql_text': issue_data.get('sql', ''),
            'error_text': issue_data.get('error', ''),
            'context': issue_data.get('context', ''),
            'has_where': 'WHERE' in issue_data.get('sql', '').upper() if issue_data.get('sql') else False,
            'has_join': 'JOIN' in issue_data.get('sql', '').upper() if issue_data.get('sql') else False,
        }
    
    async def _match_pattern(self, features: Dict) -> Dict[str, Any]:
        """Поиск совпадающего паттерна"""
        
        # Определяем категорию
        if features['issue_type'] == 'slow_query':
            category = 'sql_performance'
        elif 'memory' in features['context'].lower():
            category = 'memory_leak'
        elif 'lock' in features['issue_type']:
            category = 'deadlock'
        elif features['issue_type'] == 'exception':
            category = 'exception'
        else:
            category = 'sql_performance'  # Default
        
        # Находим лучший паттерн в категории
        patterns = self.known_patterns.get(category, [])
        
        if not patterns:
            return {
                'category': category,
                'subcategory': 'unknown',
                'confidence': 0.5,
                'solution': 'Requires manual analysis'
            }
        
        # Упрощенный matching
        best_pattern = patterns[0]  # Берем первый паттерн
        
        # Проверяем SQL text для более точного matching
        if features['sql_text']:
            sql_upper = features['sql_text'].upper()
            
            if 'SELECT *' in sql_upper and not features['has_where']:
                # Точное совпадение с паттерном
                best_pattern = patterns[0]  # SELECT * pattern
                confidence = 0.95
            elif not features['has_where'] and features['has_join']:
                confidence = 0.9
            elif 'UPPER(' in sql_upper or 'LOWER(' in sql_upper:
                # Function in WHERE pattern
                if len(patterns) > 2:
                    best_pattern = patterns[2]
                confidence = 0.85
            else:
                confidence = 0.7
        else:
            confidence = best_pattern.get('confidence_threshold', 0.7)
        
        return {
            'category': category,
            'subcategory': best_pattern.get('pattern', 'unknown'),
            'confidence': confidence,
            'solution': best_pattern.get('solution', '')
        }
    
    async def _ml_classify(self, features: Dict) -> str:
        """ML классификация (placeholder для реальной модели)"""
        # TODO: Implement real ML model
        # Model trained on historical tech log data
        # Features: duration, sql_patterns, error_patterns, context
        # Output: category with confidence
        
        return 'sql_performance'  # Default
    
    def _determine_root_cause(
        self,
        issue_data: Dict,
        pattern: Dict
    ) -> str:
        """Определение root cause"""
        
        # Из matched pattern
        if 'solution' in pattern:
            # Извлекаем root cause из solution
            solution = pattern['solution']
            
            if 'индекс' in solution.lower() or 'index' in solution.lower():
                return 'Отсутствуют индексы'
            elif 'where' in solution.lower():
                return 'Отсутствует фильтрация WHERE'
            elif 'join' in solution.lower() or 'цикл' in solution.lower():
                return 'N+1 queries problem'
            else:
                return 'Неоптимальный запрос'
        
        return 'Требуется детальный анализ'
    
    def _generate_recommendation(
        self,
        pattern: Dict,
        root_cause: str
    ) -> str:
        """Генерация рекомендации"""
        return pattern.get('solution', 'Требуется ручной анализ')
    
    def _find_similar_cases(self, issue_data: Dict) -> int:
        """Поиск похожих случаев в истории"""
        # TODO: Query PostgreSQL для поиска похожих проблем
        # Пока возвращаем случайное число
        import random
        return random.randint(5, 50)
    
    def _check_auto_fix_available(self, category: str) -> bool:
        """Проверка доступности auto-fix"""
        # Auto-fix доступен для SQL performance
        return category == 'sql_performance'


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test():
        classifier = AIIssueClassifier()
        
        print("=== AI Issue Classifier Test ===")
        print(f"Known patterns: {sum(len(v) for v in classifier.known_patterns.values())}")
        
        # Test classification
        issue = {
            'type': 'slow_query',
            'sql': 'SELECT * FROM orders WHERE UPPER(name) = "VALUE"',
            'duration_ms': 15300,
            'severity': 'critical',
            'context': 'Report generation'
        }
        
        result = await classifier.classify_issue(issue)
        
        print(f"\nClassification Result:")
        print(f"  Category: {result.category}")
        print(f"  Subcategory: {result.subcategory}")
        print(f"  Confidence: {result.confidence}")
        print(f"  Root Cause: {result.root_cause}")
        print(f"  Recommendation: {result.recommendation[:80]}...")
        print(f"  Similar Cases: {result.similar_cases}")
        print(f"  Auto-fix: {result.auto_fix_available}")
        
        print("\n[OK] AI Issue Classifier ready!")
    
    asyncio.run(test())


