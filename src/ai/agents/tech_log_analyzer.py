"""
Tech Log Analyzer - Анализ технологического журнала 1С
Основан на: https://github.com/Polyplastic/1c-parsing-tech-log

Анализирует:
- DBMSSQL - медленные SQL запросы
- CALL - медленные вызовы методов
- EXCP - исключения
- TLOCK - блокировки транзакций
- SDBL - медленные обращения к БД
"""

import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


@dataclass
class TechLogEvent:
    """Событие технологического журнала"""
    timestamp: datetime
    duration_ms: int
    event_type: str  # DBMSSQL, CALL, EXCP, TLOCK, SDBL
    process: str
    user: str
    application: str
    event: str
    context: str
    sql: Optional[str] = None
    method: Optional[str] = None
    error: Optional[str] = None
    severity: str = "info"


@dataclass
class PerformanceIssue:
    """Проблема производительности"""
    issue_type: str
    severity: str  # critical, high, medium, low
    description: str
    location: str
    metric_value: float
    threshold: float
    occurrences: int
    recommendation: str
    auto_fix_available: bool


class TechLogAnalyzer:
    """
    Анализатор технологического журнала 1С
    
    Features:
    - Парсинг tech log (формат 1С)
    - Анализ производительности
    - Детекция паттернов проблем
    - Интеграция с SQL Optimizer
    - AI рекомендации
    """
    
    def __init__(self):
        # Пороги для детекции проблем (из 1c-parsing-tech-log best practices)
        self.thresholds = {
            'slow_query_ms': 3000,  # 3 sec
            'slow_call_ms': 2000,  # 2 sec
            'slow_sdbl_ms': 1000,  # 1 sec
            'lock_wait_ms': 500,  # 0.5 sec
        }
        
        # Статистика событий
        self.events_stats = {
            'DBMSSQL': [],
            'CALL': [],
            'EXCP': [],
            'TLOCK': [],
            'SDBL': []
        }
    
    # ==========================================
    # ПАРСИНГ TECH LOG
    # ==========================================
    
    async def parse_tech_log(
        self,
        log_path: str,
        time_period: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """
        Парсинг технологического журнала
        
        Args:
            log_path: Путь к файлу(ам) tech log
            time_period: Период анализа (начало, конец)
            
        Returns:
            Структурированные данные из журнала
        """
        logger.info(
            "Parsing tech log",
            extra={"log_path": str(log_path)}
        )
        
        events = []
        log_files = self._find_log_files(log_path, time_period)
        
        for log_file in log_files:
            file_events = await self._parse_log_file(log_file)
            events.extend(file_events)
        
        # Фильтрация по времени если указано
        if time_period:
            events = [
                e for e in events
                if time_period[0] <= e.timestamp <= time_period[1]
            ]
        
        logger.info(
            "Parsed events",
            extra={"events_count": len(events)}
        )
        
        return {
            "events": events,
            "events_count": len(events),
            "period": time_period,
            "by_type": self._group_by_type(events),
            "by_severity": self._group_by_severity(events)
        }
    
    def _find_log_files(
        self,
        log_path: str,
        time_period: Optional[Tuple[datetime, datetime]]
    ) -> List[Path]:
        """Поиск файлов tech log"""
        path = Path(log_path)
        
        if path.is_file():
            return [path]
        elif path.is_dir():
            # Ищем все .log файлы
            return list(path.glob('*.log'))
        else:
            logger.warning(
                "Path not found",
                extra={"log_path": str(log_path)}
            )
            return []
    
    async def _parse_log_file(self, log_file: Path) -> List[TechLogEvent]:
        """
        Парсинг одного файла tech log
        
        Формат tech log (пример):
        59:49.123456-1234,DBMSSQL,5,process=rphost,p:processName=...,Sql=SELECT...
        """
        events = []
        
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                current_event = {}
                
                for line in f:
                    line = line.strip()
                    
                    if not line:
                        continue
                    
                    # Новое событие начинается с timestamp
                    if re.match(r'\d+:\d+\.\d+', line):
                        # Сохраняем предыдущее событие
                        if current_event:
                            event = self._parse_event_data(current_event)
                            if event:
                                events.append(event)
                        
                        # Начинаем новое событие
                        current_event = {'lines': [line]}
                    else:
                        # Продолжение текущего события
                        if current_event:
                            current_event['lines'].append(line)
                
                # Сохраняем последнее событие
                if current_event:
                    event = self._parse_event_data(current_event)
                    if event:
                        events.append(event)
        
        except Exception as e:
            logger.error(
                "Error parsing log file",
                extra={
                    "log_file": str(log_file),
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
        
        return events
    
    def _parse_event_data(self, event_data: Dict) -> Optional[TechLogEvent]:
        """Парсинг данных события"""
        try:
            lines = event_data['lines']
            first_line = lines[0]
            
            # Парсинг первой строки
            # Format: MM:SS.mmmmmm-duration,EVENT_TYPE,level,process=...,p:processName=...
            parts = first_line.split(',')
            
            if len(parts) < 3:
                return None
            
            # Timestamp и duration
            time_duration = parts[0].split('-')
            timestamp_str = time_duration[0]  # MM:SS.mmmmmm
            duration_ms = int(time_duration[1]) if len(time_duration) > 1 else 0
            
            # Event type
            event_type = parts[1]
            
            # Парсинг атрибутов
            attributes = self._parse_attributes(parts[2:])
            
            # SQL из следующих строк (для DBMSSQL)
            sql = None
            if event_type == 'DBMSSQL' and len(lines) > 1:
                sql_lines = [l for l in lines[1:] if l.startswith('Sql=')]
                if sql_lines:
                    sql = sql_lines[0].replace('Sql=', '').strip()
            
            # Метод (для CALL)
            method = attributes.get('Method') or attributes.get('Func')
            
            # Ошибка (для EXCP)
            error = attributes.get('Descr') if event_type == 'EXCP' else None
            
            # Определение severity
            severity = self._determine_severity(event_type, duration_ms, error)
            
            # Создаем простой timestamp (без даты, используем текущую дату)
            try:
                time_obj = datetime.strptime(timestamp_str.split('.')[0], '%M:%S')
                timestamp = datetime.now().replace(
                    hour=0,
                    minute=time_obj.minute,
                    second=time_obj.second,
                    microsecond=0
                )
            except (ValueError, TypeError):
                timestamp = datetime.now()
            
            return TechLogEvent(
                timestamp=timestamp,
                duration_ms=duration_ms,
                event_type=event_type,
                process=attributes.get('process', ''),
                user=attributes.get('Usr', ''),
                application=attributes.get('AppID', ''),
                event=attributes.get('Event', ''),
                context=attributes.get('Context', ''),
                sql=sql,
                method=method,
                error=error,
                severity=severity
            )
            
        except Exception as e:
            logger.debug(
                "Error parsing event",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            return None
    
    def _parse_attributes(self, parts: List[str]) -> Dict[str, str]:
        """Парсинг атрибутов события"""
        attributes = {}
        
        for part in parts:
            if '=' in part:
                key_value = part.split('=', 1)
                key = key_value[0].strip()
                value = key_value[1].strip() if len(key_value) > 1 else ''
                
                # Убираем префикс p:
                if key.startswith('p:'):
                    key = key[2:]
                
                attributes[key] = value
        
        return attributes
    
    def _determine_severity(
        self,
        event_type: str,
        duration_ms: int,
        error: Optional[str]
    ) -> str:
        """Определение severity события"""
        
        # EXCP всегда важно
        if event_type == 'EXCP':
            if error and any(kw in error.lower() for kw in ['deadlock', 'timeout', 'connection']):
                return 'critical'
            return 'high'
        
        # По длительности
        if event_type == 'DBMSSQL':
            threshold = self.thresholds['slow_query_ms']
        elif event_type == 'CALL':
            threshold = self.thresholds['slow_call_ms']
        elif event_type == 'SDBL':
            threshold = self.thresholds['slow_sdbl_ms']
        elif event_type == 'TLOCK':
            threshold = self.thresholds['lock_wait_ms']
        else:
            threshold = 1000
        
        if duration_ms > threshold * 5:
            return 'critical'
        elif duration_ms > threshold * 2:
            return 'high'
        elif duration_ms > threshold:
            return 'medium'
        else:
            return 'low'
    
    def _group_by_type(self, events: List[TechLogEvent]) -> Dict[str, int]:
        """Группировка по типу события"""
        from collections import Counter
        return dict(Counter(e.event_type for e in events))
    
    def _group_by_severity(self, events: List[TechLogEvent]) -> Dict[str, int]:
        """Группировка по severity"""
        from collections import Counter
        return dict(Counter(e.severity for e in events))
    
    # ==========================================
    # АНАЛИЗ ПРОИЗВОДИТЕЛЬНОСТИ
    # ==========================================
    
    async def analyze_performance(
        self,
        log_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Анализ производительности на основе tech log
        
        Returns:
            {
                "performance_issues": [...],
                "top_slow_queries": [...],
                "top_slow_methods": [...],
                "errors_by_type": {...},
                "locks_analysis": {...},
                "ai_recommendations": [...]
            }
        """
        events = log_data['events']
        
        # 1. Медленные SQL запросы
        slow_queries = self._find_slow_queries(events)
        
        # 2. Медленные методы
        slow_methods = self._find_slow_methods(events)
        
        # 3. Исключения
        exceptions = self._analyze_exceptions(events)
        
        # 4. Блокировки
        locks = self._analyze_locks(events)
        
        # 5. Performance issues
        issues = await self._detect_performance_issues(
            slow_queries,
            slow_methods,
            exceptions,
            locks
        )
        
        # 6. AI рекомендации
        recommendations = await self._generate_ai_recommendations(issues)
        
        return {
            "analysis_date": datetime.now().isoformat(),
            "events_analyzed": len(events),
            "performance_issues": issues,
            "top_slow_queries": slow_queries[:10],
            "top_slow_methods": slow_methods[:10],
            "exceptions": exceptions,
            "locks_analysis": locks,
            "ai_recommendations": recommendations,
            "summary": {
                "critical_issues": len([i for i in issues if i.severity == 'critical']),
                "high_issues": len([i for i in issues if i.severity == 'high']),
                "total_issues": len(issues)
            }
        }
    
    def _find_slow_queries(self, events: List[TechLogEvent]) -> List[Dict]:
        """Поиск медленных SQL запросов"""
        slow_queries = []
        
        dbmssql_events = [e for e in events if e.event_type == 'DBMSSQL']
        
        # Группируем по SQL
        sql_stats = {}
        for event in dbmssql_events:
            if event.sql:
                sql_key = event.sql[:200]  # First 200 chars as key
                
                if sql_key not in sql_stats:
                    sql_stats[sql_key] = {
                        'sql': event.sql,
                        'durations': [],
                        'count': 0
                    }
                
                sql_stats[sql_key]['durations'].append(event.duration_ms)
                sql_stats[sql_key]['count'] += 1
        
        # Находим самые медленные
        for sql_key, stats in sql_stats.items():
            avg_duration = sum(stats['durations']) / len(stats['durations'])
            max_duration = max(stats['durations'])
            
            if avg_duration > self.thresholds['slow_query_ms']:
                slow_queries.append({
                    'sql': stats['sql'][:500],
                    'avg_duration_ms': int(avg_duration),
                    'max_duration_ms': max_duration,
                    'executions': stats['count'],
                    'total_time_ms': sum(stats['durations']),
                    'severity': 'critical' if avg_duration > 10000 else 'high'
                })
        
        # Сортировка по total_time (больше всего времени тратится)
        slow_queries.sort(key=lambda x: x['total_time_ms'], reverse=True)
        
        return slow_queries
    
    def _find_slow_methods(self, events: List[TechLogEvent]) -> List[Dict]:
        """Поиск медленных методов/процедур"""
        slow_methods = []
        
        call_events = [e for e in events if e.event_type == 'CALL']
        
        # Группируем по методу
        method_stats = {}
        for event in call_events:
            if event.method:
                if event.method not in method_stats:
                    method_stats[event.method] = {
                        'durations': [],
                        'count': 0,
                        'context': event.context
                    }
                
                method_stats[event.method]['durations'].append(event.duration_ms)
                method_stats[event.method]['count'] += 1
        
        # Находим самые медленные
        for method, stats in method_stats.items():
            avg_duration = sum(stats['durations']) / len(stats['durations'])
            
            if avg_duration > self.thresholds['slow_call_ms']:
                slow_methods.append({
                    'method': method,
                    'avg_duration_ms': int(avg_duration),
                    'max_duration_ms': max(stats['durations']),
                    'calls_count': stats['count'],
                    'total_time_ms': sum(stats['durations']),
                    'context': stats['context']
                })
        
        slow_methods.sort(key=lambda x: x['total_time_ms'], reverse=True)
        
        return slow_methods
    
    def _analyze_exceptions(self, events: List[TechLogEvent]) -> Dict[str, Any]:
        """Анализ исключений"""
        exceptions = [e for e in events if e.event_type == 'EXCP']
        
        # Группируем по типу ошибки
        error_types = {}
        for event in exceptions:
            error_key = event.error[:100] if event.error else 'Unknown'
            
            if error_key not in error_types:
                error_types[error_key] = {
                    'error': event.error,
                    'count': 0,
                    'contexts': []
                }
            
            error_types[error_key]['count'] += 1
            if event.context and event.context not in error_types[error_key]['contexts']:
                error_types[error_key]['contexts'].append(event.context)
        
        # Топ ошибки
        top_errors = sorted(
            [
                {
                    'error': v['error'][:200],
                    'count': v['count'],
                    'contexts': v['contexts'][:5]
                }
                for v in error_types.values()
            ],
            key=lambda x: x['count'],
            reverse=True
        )
        
        return {
            'total_exceptions': len(exceptions),
            'unique_errors': len(error_types),
            'top_errors': top_errors[:20]
        }
    
    def _analyze_locks(self, events: List[TechLogEvent]) -> Dict[str, Any]:
        """Анализ блокировок"""
        lock_events = [e for e in events if e.event_type == 'TLOCK']
        
        long_locks = [
            {
                'duration_ms': e.duration_ms,
                'user': e.user,
                'context': e.context,
                'severity': e.severity
            }
            for e in lock_events
            if e.duration_ms > self.thresholds['lock_wait_ms']
        ]
        
        return {
            'total_locks': len(lock_events),
            'long_locks': len(long_locks),
            'max_wait_ms': max([e.duration_ms for e in lock_events]) if lock_events else 0,
            'details': long_locks[:10]
        }
    
    # ==========================================
    # ДЕТЕКЦИЯ ПРОБЛЕМ
    # ==========================================
    
    async def _detect_performance_issues(
        self,
        slow_queries: List[Dict],
        slow_methods: List[Dict],
        exceptions: Dict,
        locks: Dict
    ) -> List[PerformanceIssue]:
        """Детекция проблем производительности"""
        issues = []
        
        # Slow queries
        for query in slow_queries[:5]:  # Top 5
            issues.append(PerformanceIssue(
                issue_type='slow_query',
                severity=query['severity'],
                description=f"Медленный SQL запрос (avg: {query['avg_duration_ms']}ms)",
                location=query['sql'][:100] + '...',
                metric_value=query['avg_duration_ms'],
                threshold=self.thresholds['slow_query_ms'],
                occurrences=query['executions'],
                recommendation="Оптимизировать запрос (см. SQL Optimizer)",
                auto_fix_available=True
            ))
        
        # Slow methods
        for method in slow_methods[:5]:
            issues.append(PerformanceIssue(
                issue_type='slow_method',
                severity='high',
                description=f"Медленный метод (avg: {method['avg_duration_ms']}ms)",
                location=method['method'],
                metric_value=method['avg_duration_ms'],
                threshold=self.thresholds['slow_call_ms'],
                occurrences=method['calls_count'],
                recommendation="Профилировать и оптимизировать код",
                auto_fix_available=False
            ))
        
        # Frequent exceptions
        if exceptions['total_exceptions'] > 100:
            issues.append(PerformanceIssue(
                issue_type='frequent_exceptions',
                severity='high',
                description=f"Частые исключения ({exceptions['total_exceptions']} шт)",
                location='Multiple locations',
                metric_value=exceptions['total_exceptions'],
                threshold=100,
                occurrences=exceptions['total_exceptions'],
                recommendation="Исправить источники ошибок",
                auto_fix_available=False
            ))
        
        # Long locks
        if locks['long_locks'] > 10:
            issues.append(PerformanceIssue(
                issue_type='lock_contention',
                severity='critical',
                description=f"Проблемы с блокировками ({locks['long_locks']} длинных ожиданий)",
                location='Transaction locks',
                metric_value=locks['max_wait_ms'],
                threshold=self.thresholds['lock_wait_ms'],
                occurrences=locks['long_locks'],
                recommendation="Использовать управляемые блокировки, сократить транзакции",
                auto_fix_available=False
            ))
        
        return issues
    
    # ==========================================
    # AI РЕКОМЕНДАЦИИ
    # ==========================================
    
    async def _generate_ai_recommendations(
        self,
        issues: List[PerformanceIssue]
    ) -> List[Dict[str, str]]:
        """
        AI генерация рекомендаций
        
        Based on:
        - 1c-parsing-tech-log AI analysis
        - SQL Optimizer integration
        - Pattern recognition
        """
        recommendations = []
        
        # Группируем по типу
        by_type = {}
        for issue in issues:
            if issue.issue_type not in by_type:
                by_type[issue.issue_type] = []
            by_type[issue.issue_type].append(issue)
        
        # Рекомендации по типам
        if 'slow_query' in by_type:
            count = len(by_type['slow_query'])
            total_time = sum(i.metric_value * i.occurrences for i in by_type['slow_query'])
            
            recommendations.append({
                'category': 'SQL Performance',
                'priority': 'critical',
                'issue': f"{count} медленных запросов (total: {total_time/1000:.1f} sec)",
                'recommendation': "Оптимизировать топ-5 запросов с помощью SQL Optimizer",
                'expected_improvement': '50-200% ускорение',
                'action': 'use_sql_optimizer'
            })
        
        if 'slow_method' in by_type:
            count = len(by_type['slow_method'])
            
            recommendations.append({
                'category': 'Code Performance',
                'priority': 'high',
                'issue': f"{count} медленных методов",
                'recommendation': "Профилировать и оптимизировать бизнес-логику",
                'expected_improvement': '30-100% ускорение',
                'action': 'code_profiling'
            })
        
        if 'lock_contention' in by_type:
            recommendations.append({
                'category': 'Concurrency',
                'priority': 'critical',
                'issue': "Проблемы с блокировками",
                'recommendation': "Использовать управляемые блокировки, сократить транзакции",
                'expected_improvement': 'Устранение deadlocks',
                'action': 'optimize_transactions'
            })
        
        return recommendations
    
    # ==========================================
    # ИНТЕГРАЦИЯ С SQL OPTIMIZER
    # ==========================================
    
    async def optimize_slow_queries(
        self,
        slow_queries: List[Dict],
        sql_optimizer
    ) -> List[Dict]:
        """
        Оптимизация медленных запросов через SQL Optimizer
        
        Integration with: SQLOptimizer
        """
        optimizations = []
        
        for query_info in slow_queries[:10]:  # Top 10
            # Используем SQL Optimizer
            result = await sql_optimizer.optimize_query(
                query_info['sql'],
                context={'database': 'postgresql'}
            )
            
            optimizations.append({
                'original_sql': query_info['sql'][:200],
                'avg_duration_ms': query_info['avg_duration_ms'],
                'executions': query_info['executions'],
                'optimization': result,
                'expected_improvement': result['expected_improvement']
            })
        
        return optimizations


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test():
        analyzer = TechLogAnalyzer()
        
        print("=== Tech Log Analyzer Test ===")
        print(f"Thresholds configured:")
        for key, value in analyzer.thresholds.items():
            print(f"  {key}: {value}ms")
        
        # Mock event
        mock_event = TechLogEvent(
            timestamp=datetime.now(),
            duration_ms=5300,
            event_type='DBMSSQL',
            process='rphost',
            user='Manager1',
            application='1CV8C',
            event='Query',
            context='Report generation',
            sql='SELECT * FROM Sales WHERE...',
            severity='high'
        )
        
        print(f"\nMock event created:")
        print(f"  Type: {mock_event.event_type}")
        print(f"  Duration: {mock_event.duration_ms}ms")
        print(f"  Severity: {mock_event.severity}")
        
        # Simulate analysis
        issues = [
            PerformanceIssue(
                issue_type='slow_query',
                severity='critical',
                description='Slow SQL query',
                location='SELECT * FROM...',
                metric_value=15300,
                threshold=3000,
                occurrences=45,
                recommendation='Add index',
                auto_fix_available=True
            )
        ]
        
        recommendations = await analyzer._generate_ai_recommendations(issues)
        
        print(f"\nAI Recommendations generated: {len(recommendations)}")
        for rec in recommendations:
            print(f"  [{rec['priority'].upper()}] {rec['category']}: {rec['recommendation']}")
        
        print("\n[OK] Tech Log Analyzer ready!")
    
    asyncio.run(test())


