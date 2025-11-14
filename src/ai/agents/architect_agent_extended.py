"""
Extended Architect AI Agent - Full Implementation
Расширенный AI ассистент для архитекторов с граф-анализом, ADR и детекцией anti-patterns
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


@dataclass
class ArchitectureMetrics:
    """Метрики архитектуры"""
    modules_count: int
    coupling_score: float  # 0-1 (чем ниже, тем лучше)
    cohesion_score: float  # 0-1 (чем выше, тем лучше)
    cyclic_dependencies_count: int
    god_objects_count: int
    orphan_modules_count: int
    overall_score: float  # 1-10


@dataclass
class AntiPattern:
    """Anti-pattern в архитектуре"""
    type: str
    severity: str  # critical, high, medium, low
    location: str
    metrics: Dict[str, Any]
    recommendation: str
    refactoring_effort: str  # Low, Medium, High
    estimated_days: int


class ArchitectAgentExtended:
    """
    Расширенный AI Архитектор с полным функционалом + интеграция ИТС
    """
    
    def __init__(self):
        # Подключение к Neo4j
        try:
            from src.db.neo4j_client import Neo4jClient
            self.neo4j = Neo4jClient()
            self.neo4j_available = True
        except (ImportError, Exception):
            self.neo4j = None
            self.neo4j_available = False
            logger.warning("Neo4j not available")
        
        # Интеграция знаний из ИТС
        try:
            from src.ai.agents.its_knowledge_integrator import ITSKnowledgeIntegrator
            self.its_knowledge = ITSKnowledgeIntegrator()
            self.its_integration = True
        except (ImportError, Exception):
            self.its_knowledge = None
            self.its_integration = False
            logger.warning("ITS Knowledge integration not available")
        
        # База знаний anti-patterns
        self.anti_patterns_catalog = self._load_anti_patterns_catalog()
        
        # База знаний технологий
        self.tech_knowledge_base = self._load_technology_knowledge()
    
    # ==========================================
    # 1. NEO4J ГРАФ-АНАЛИЗ
    # ==========================================
    
    async def analyze_architecture_graph(
        self, 
        config_name: str,
        deep_analysis: bool = True
    ) -> Dict[str, Any]:
        """
        Глубокий анализ архитектуры через Neo4j граф
        
        Args:
            config_name: Название конфигурации
            deep_analysis: Глубокий анализ (медленнее, но детальнее)
            
        Returns:
            Полный анализ архитектуры с метриками и рекомендациями
        """
        logger.info(
            "Starting graph analysis",
            extra={"config_name": config_name}
        )
        
        if not self.neo4j_available:
            return {
                "error": "Neo4j not available",
                "message": "Graph analysis requires Neo4j connection"
            }
        
        try:
            # 1. Базовые метрики
            modules = await self._get_modules_count(config_name)
            
            # 2. Анализ coupling (связанность)
            coupling_data = await self._analyze_coupling(config_name)
            
            # 3. Анализ cohesion (сплоченность)
            cohesion_data = await self._analyze_cohesion(config_name)
            
            # 4. Поиск циклических зависимостей
            cycles = await self._find_cyclic_dependencies(config_name)
            
            # 5. Поиск God Objects
            god_objects = await self._find_god_objects(config_name)
            
            # 6. Orphan modules (изолированные)
            orphans = await self._find_orphan_modules(config_name)
            
            # 7. Расчет общего score
            overall_score = self._calculate_architecture_score(
                coupling_data['score'],
                cohesion_data['score'],
                len(cycles),
                len(god_objects)
            )
            
            # 8. AI анализ и рекомендации
            recommendations = await self._generate_architecture_recommendations({
                'coupling': coupling_data,
                'cohesion': cohesion_data,
                'cycles': cycles,
                'god_objects': god_objects,
                'orphans': orphans
            })
            
            return {
                "config_name": config_name,
                "analysis_date": datetime.now().isoformat(),
                "metrics": {
                    "modules_count": modules,
                    "coupling_score": coupling_data['score'],
                    "cohesion_score": cohesion_data['score'],
                    "overall_score": overall_score
                },
                "issues": {
                    "cyclic_dependencies": cycles,
                    "god_objects": god_objects,
                    "orphan_modules": orphans
                },
                "detailed_coupling": coupling_data['details'],
                "detailed_cohesion": cohesion_data['details'],
                "recommendations": recommendations,
                "health_status": self._get_health_status(overall_score)
            }
            
        except Exception as e:
            logger.error(
                "Graph analysis error",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "config_name": config_name if 'config_name' in locals() else None
                },
                exc_info=True
            )
            return {"error": str(e)}
    
    async def _get_modules_count(self, config_name: str) -> int:
        """Подсчет модулей в конфигурации"""
        # Cypher query
        query = """
        MATCH (m:Module)-[:BELONGS_TO]->(c:Configuration {name: $config_name})
        RETURN count(m) as count
        """
        
        if self.neo4j:
            result = await self.neo4j.execute_query(query, {'config_name': config_name})
            return result[0]['count'] if result else 0
        return 0
    
    async def _analyze_coupling(self, config_name: str) -> Dict[str, Any]:
        """
        Анализ coupling (связанность модулей)
        
        Coupling score = количество зависимостей / максимально возможных связей
        Чем ниже, тем лучше (loose coupling)
        """
        query = """
        MATCH (m1:Module)-[:BELONGS_TO]->(c:Configuration {name: $config_name})
        OPTIONAL MATCH (m1)-[d:DEPENDS_ON]->(m2:Module)
        WITH m1, count(d) as dependencies_count
        RETURN 
            avg(dependencies_count) as avg_dependencies,
            max(dependencies_count) as max_dependencies,
            collect({module: m1.name, deps: dependencies_count}) as modules_data
        """
        
        if self.neo4j:
            result = await self.neo4j.execute_query(query, {'config_name': config_name})
            if result:
                data = result[0]
                avg_deps = data['avg_dependencies']
                max_deps = data['max_dependencies']
                
                # Score: 0-1 (ниже лучше)
                # Идеал: 0-3 зависимости = 0.0-0.3
                # Плохо: 10+ зависимостей = 1.0
                coupling_score = min(avg_deps / 10.0, 1.0)
                
                return {
                    'score': coupling_score,
                    'avg_dependencies': avg_deps,
                    'max_dependencies': max_deps,
                    'details': data['modules_data'][:10],  # Top 10
                    'status': self._get_coupling_status(coupling_score)
                }
        
        return {'score': 0.5, 'details': [], 'status': 'unknown'}
    
    async def _analyze_cohesion(self, config_name: str) -> Dict[str, Any]:
        """
        Анализ cohesion (сплоченность внутри модулей)
        
        Cohesion score = функции используют общие данные / общее количество функций
        Чем выше, тем лучше (high cohesion)
        """
        # Упрощенный анализ через количество внутренних вызовов
        query = """
        MATCH (m:Module)-[:BELONGS_TO]->(c:Configuration {name: $config_name})
        MATCH (f1:Function)-[:BELONGS_TO]->(m)
        OPTIONAL MATCH (f1)-[:CALLS]->(f2:Function)-[:BELONGS_TO]->(m)
        WITH m, count(DISTINCT f1) as functions_count, count(DISTINCT f2) as internal_calls
        RETURN 
            avg(CASE WHEN functions_count > 0 THEN toFloat(internal_calls) / functions_count ELSE 0 END) as avg_cohesion,
            collect({module: m.name, cohesion: internal_calls * 1.0 / functions_count}) as modules_data
        """
        
        if self.neo4j:
            result = await self.neo4j.execute_query(query, {'config_name': config_name})
            if result:
                data = result[0]
                avg_cohesion = data['avg_cohesion']
                
                # Score: 0-1 (выше лучше)
                cohesion_score = min(avg_cohesion, 1.0)
                
                return {
                    'score': cohesion_score,
                    'avg_cohesion': avg_cohesion,
                    'details': data['modules_data'][:10],
                    'status': self._get_cohesion_status(cohesion_score)
                }
        
        return {'score': 0.5, 'details': [], 'status': 'unknown'}
    
    async def _find_cyclic_dependencies(self, config_name: str) -> List[Dict[str, Any]]:
        """
        Поиск циклических зависимостей
        
        Returns:
            Список циклов с путями
        """
        query = """
        MATCH path = (m1:Module)-[:DEPENDS_ON*2..5]->(m2:Module)
        WHERE m1 = m2 
          AND all(r in relationships(path) WHERE 
            startNode(r)-[:BELONGS_TO]->(:Configuration {name: $config_name}))
        RETURN 
            m1.name as module,
            length(path) as cycle_length,
            [n in nodes(path) | n.name] as cycle_path
        ORDER BY cycle_length DESC
        LIMIT 20
        """
        
        if self.neo4j:
            result = await self.neo4j.execute_query(query, {'config_name': config_name})
            return [
                {
                    'module': row['module'],
                    'cycle_length': row['cycle_length'],
                    'path': row['cycle_path'],
                    'severity': 'critical' if row['cycle_length'] > 3 else 'high'
                }
                for row in result
            ]
        
        return []
    
    async def _find_god_objects(self, config_name: str) -> List[Dict[str, Any]]:
        """
        Поиск God Objects (модули с слишком многими ответственностями)
        
        Критерии:
        - Большое количество функций (> 50)
        - Много зависимостей (> 20)
        - Много входящих связей (> 15)
        """
        query = """
        MATCH (m:Module)-[:BELONGS_TO]->(c:Configuration {name: $config_name})
        OPTIONAL MATCH (f:Function)-[:BELONGS_TO]->(m)
        OPTIONAL MATCH (m)-[out:DEPENDS_ON]->()
        OPTIONAL MATCH ()-[in:DEPENDS_ON]->(m)
        WITH m, 
             count(DISTINCT f) as functions_count,
             count(DISTINCT out) as outgoing_deps,
             count(DISTINCT in) as incoming_deps
        WHERE functions_count > 50 OR outgoing_deps > 20 OR incoming_deps > 15
        RETURN 
            m.name as module,
            functions_count,
            outgoing_deps,
            incoming_deps,
            (functions_count + outgoing_deps + incoming_deps) as complexity_score
        ORDER BY complexity_score DESC
        LIMIT 10
        """
        
        if self.neo4j:
            result = await self.neo4j.execute_query(query, {'config_name': config_name})
            return [
                {
                    'name': row['module'],
                    'functions_count': row['functions_count'],
                    'outgoing_dependencies': row['outgoing_deps'],
                    'incoming_dependencies': row['incoming_deps'],
                    'complexity_score': row['complexity_score'],
                    'severity': 'critical' if row['complexity_score'] > 100 else 'high'
                }
                for row in result
            ]
        
        return []
    
    async def _find_orphan_modules(self, config_name: str) -> List[str]:
        """Поиск изолированных модулей (нет связей)"""
        query = """
        MATCH (m:Module)-[:BELONGS_TO]->(c:Configuration {name: $config_name})
        WHERE NOT (m)-[:DEPENDS_ON]-() AND NOT ()-[:DEPENDS_ON]->(m)
        RETURN m.name as module
        LIMIT 20
        """
        
        if self.neo4j:
            result = await self.neo4j.execute_query(query, {'config_name': config_name})
            return [row['module'] for row in result]
        
        return []
    
    def _calculate_architecture_score(
        self, 
        coupling: float, 
        cohesion: float, 
        cycles_count: int, 
        god_objects_count: int
    ) -> float:
        """
        Расчет общего score архитектуры (1-10)
        
        10 - идеальная архитектура
        1 - катастрофа
        """
        # Базовый score
        score = 10.0
        
        # Штрафы
        score -= coupling * 3.0  # Coupling: до -3 баллов
        score -= (1.0 - cohesion) * 2.0  # Cohesion: до -2 баллов
        score -= min(cycles_count * 0.5, 3.0)  # Cycles: до -3 баллов
        score -= min(god_objects_count * 0.3, 2.0)  # God Objects: до -2 баллов
        
        return max(1.0, min(10.0, score))
    
    def _get_coupling_status(self, score: float) -> str:
        """Статус coupling"""
        if score < 0.3:
            return "excellent"  # Loose coupling
        elif score < 0.5:
            return "good"
        elif score < 0.7:
            return "moderate"
        else:
            return "poor"  # Tight coupling
    
    def _get_cohesion_status(self, score: float) -> str:
        """Статус cohesion"""
        if score > 0.7:
            return "excellent"  # High cohesion
        elif score > 0.5:
            return "good"
        elif score > 0.3:
            return "moderate"
        else:
            return "poor"  # Low cohesion
    
    def _get_health_status(self, overall_score: float) -> str:
        """Общий статус здоровья архитектуры"""
        if overall_score >= 8.0:
            return "healthy"
        elif overall_score >= 6.0:
            return "moderate"
        elif overall_score >= 4.0:
            return "needs_attention"
        else:
            return "critical"
    
    async def _generate_architecture_recommendations(
        self, 
        analysis_data: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        AI генерация рекомендаций по улучшению архитектуры
        С интеграцией знаний из ИТС!
        """
        recommendations = []
        
        # Получаем рекомендации из ИТС (если доступны)
        its_recommendations = []
        if self.its_integration and self.its_knowledge:
            # Для каждой проблемы ищем best practices в ИТС
            if len(analysis_data.get('cycles', [])) > 0:
                its_practices = await self.its_knowledge.get_best_practices_for_issue(
                    'circular_dependency'
                )
                for practice in its_practices[:2]:
                    its_recommendations.append({
                        'category': 'dependencies',
                        'priority': 'critical',
                        'issue': 'Circular dependencies',
                        'recommendation': practice.get('title', ''),
                        'its_reference': practice.get('source', 'ITS'),
                        'effort': 'high'
                    })
            
            if len(analysis_data.get('god_objects', [])) > 0:
                its_practices = await self.its_knowledge.get_best_practices_for_issue(
                    'god_object'
                )
                for practice in its_practices[:2]:
                    its_recommendations.append({
                        'category': 'complexity',
                        'priority': 'critical',
                        'issue': 'God Objects',
                        'recommendation': practice.get('title', ''),
                        'its_reference': practice.get('source', 'ITS'),
                        'effort': 'high'
                    })
        
        # Coupling
        if analysis_data['coupling']['score'] > 0.7:
            recommendations.append({
                'category': 'coupling',
                'priority': 'high',
                'issue': f"Tight coupling detected (score: {analysis_data['coupling']['score']:.2f})",
                'recommendation': "Применить Dependency Inversion Principle, использовать интерфейсы",
                'effort': 'medium'
            })
        
        # Cohesion
        if analysis_data['cohesion']['score'] < 0.3:
            recommendations.append({
                'category': 'cohesion',
                'priority': 'high',
                'issue': f"Low cohesion detected (score: {analysis_data['cohesion']['score']:.2f})",
                'recommendation': "Пересмотреть разбиение на модули, группировать связанные функции",
                'effort': 'high'
            })
        
        # Cycles
        if len(analysis_data['cycles']) > 0:
            recommendations.append({
                'category': 'dependencies',
                'priority': 'critical',
                'issue': f"Found {len(analysis_data['cycles'])} cyclic dependencies",
                'recommendation': "Разорвать циклы через события или промежуточные модули",
                'effort': 'high'
            })
        
        # God Objects
        if len(analysis_data['god_objects']) > 0:
            recommendations.append({
                'category': 'complexity',
                'priority': 'critical',
                'issue': f"Found {len(analysis_data['god_objects'])} God Objects",
                'recommendation': "Разбить на специализированные модули по Single Responsibility Principle",
                'effort': 'high'
            })
        
        # Orphans
        if len(analysis_data['orphans']) > 3:
            recommendations.append({
                'category': 'maintenance',
                'priority': 'low',
                'issue': f"Found {len(analysis_data['orphans'])} orphan modules",
                'recommendation': "Проверить использование и удалить неиспользуемые модули",
                'effort': 'low'
            })
        
        return recommendations
    
    # ==========================================
    # 2. ADR GENERATOR
    # ==========================================
    
    async def generate_adr(
        self,
        title: str,
        context: str,
        problem: str,
        alternatives: List[Dict[str, Any]],
        decision: str,
        rationale: str,
        consequences: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """
        Генерация Architecture Decision Record
        
        Args:
            title: Название решения
            context: Контекст принятия решения
            problem: Проблема/вызов
            alternatives: Список альтернатив с оценками
            decision: Принятое решение
            rationale: Обоснование выбора
            consequences: Последствия (pros/cons)
            
        Returns:
            ADR документ
        """
        adr_id = await self._generate_adr_id()
        
        adr = {
            "adr_id": adr_id,
            "title": title,
            "date": datetime.now().isoformat(),
            "status": "accepted",
            "context": context,
            "problem": problem,
            "alternatives": self._score_alternatives(alternatives),
            "decision": decision,
            "rationale": rationale,
            "consequences": consequences,
            "review_date": (datetime.now() + timedelta(days=180)).isoformat(),
            "tags": self._extract_tags(title, context, problem),
            "stakeholders": []
        }
        
        # Сохранить в БД
        await self._save_adr(adr)
        
        # Генерация markdown
        markdown = self._adr_to_markdown(adr)
        
        return {
            "adr": adr,
            "markdown": markdown,
            "file_path": f"docs/adr/{adr_id}-{self._slugify(title)}.md"
        }
    
    async def _generate_adr_id(self) -> str:
        """Генерация ID для ADR"""
        # TODO: Query PostgreSQL для получения последнего ID
        # Пока просто timestamp
        return f"ADR-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    def _score_alternatives(self, alternatives: List[Dict]) -> List[Dict]:
        """
        Scoring альтернатив
        
        Критерии: feasibility, cost, complexity, performance, maintainability
        """
        for alt in alternatives:
            scores = alt.get('scores', {})
            total_score = sum(scores.values()) / len(scores) if scores else 0
            alt['total_score'] = round(total_score, 2)
        
        # Сортировка по score
        return sorted(alternatives, key=lambda x: x.get('total_score', 0), reverse=True)
    
    def _extract_tags(self, title: str, context: str, problem: str) -> List[str]:
        """Извлечение тегов из текста"""
        text = f"{title} {context} {problem}".lower()
        
        tags = []
        keywords = {
            'integration': ['интеграция', 'integration', 'api', 'rest', 'kafka'],
            'performance': ['производительность', 'performance', 'optimization'],
            'database': ['база', 'database', 'sql', 'postgresql', 'neo4j'],
            'architecture': ['архитектура', 'architecture', 'pattern', 'design'],
            'security': ['безопасность', 'security', 'auth', 'authorization']
        }
        
        for tag, kws in keywords.items():
            if any(kw in text for kw in kws):
                tags.append(tag)
        
        return tags
    
    def _slugify(self, text: str) -> str:
        """Преобразование текста в slug"""
        import re
        text = text.lower()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '-', text)
        return text[:50]
    
    def _adr_to_markdown(self, adr: Dict) -> str:
        """Конвертация ADR в Markdown"""
        md = f"""# {adr['adr_id']}: {adr['title']}

**Date:** {adr['date'][:10]}  
**Status:** {adr['status']}  
**Tags:** {', '.join(adr['tags'])}

---

## Context

{adr['context']}

## Problem

{adr['problem']}

## Considered Alternatives

"""
        
        for i, alt in enumerate(adr['alternatives'], 1):
            md += f"\n### {i}. {alt['option']}\n\n"
            md += f"**Score:** {alt.get('total_score', 'N/A')}/10\n\n"
            
            if 'pros' in alt:
                md += "**Pros:**\n"
                for pro in alt['pros']:
                    md += f"- ✅ {pro}\n"
                md += "\n"
            
            if 'cons' in alt:
                md += "**Cons:**\n"
                for con in alt['cons']:
                    md += f"- ❌ {con}\n"
                md += "\n"
        
        md += f"""
## Decision

{adr['decision']}

## Rationale

{adr['rationale']}

## Consequences

### Positive

"""
        
        for pro in adr['consequences'].get('pros', []):
            md += f"- ✅ {pro}\n"
        
        md += "\n### Negative\n\n"
        
        for con in adr['consequences'].get('cons', []):
            md += f"- ❌ {con}\n"
        
        md += f"\n\n**Review Date:** {adr['review_date'][:10]}\n"
        
        return md
    
    async def _save_adr(self, adr: Dict):
        """Сохранение ADR в БД"""
        # TODO: Save to PostgreSQL
        logger.info(
            "ADR saved",
            extra={"adr_id": adr['adr_id']}
        )
    
    # ==========================================
    # 3. ANTI-PATTERN DETECTION
    # ==========================================
    
    async def detect_anti_patterns(
        self,
        config_name: str,
        include_code_analysis: bool = True
    ) -> Dict[str, Any]:
        """
        Детекция anti-patterns в конфигурации
        
        Returns:
            {
                "anti_patterns": [...],
                "overall_score": 3.2,  # 1-10
                "priority_fixes": [...],
                "refactoring_roadmap": [...]
            }
        """
        logger.info(
            "Detecting anti-patterns",
            extra={"config_name": config_name}
        )
        
        anti_patterns = []
        
        # 1. God Object
        god_objects = await self._detect_god_object(config_name)
        anti_patterns.extend(god_objects)
        
        # 2. Spaghetti Code
        spaghetti = await self._detect_spaghetti_code(config_name)
        anti_patterns.extend(spaghetti)
        
        # 3. Circular Dependencies
        circular = await self._detect_circular_dependencies(config_name)
        anti_patterns.extend(circular)
        
        # 4. Long Method
        if include_code_analysis:
            long_methods = await self._detect_long_methods(config_name)
            anti_patterns.extend(long_methods)
        
        # 5. Code Duplication
        if include_code_analysis:
            duplicates = await self._detect_code_duplication(config_name)
            anti_patterns.extend(duplicates)
        
        # Расчет overall score
        overall_score = self._calculate_quality_score(anti_patterns)
        
        # Приоритизация исправлений
        priority_fixes = self._prioritize_fixes(anti_patterns)
        
        # Roadmap рефакторинга
        roadmap = self._generate_refactoring_roadmap(priority_fixes)
        
        return {
            "config_name": config_name,
            "analysis_date": datetime.now().isoformat(),
            "anti_patterns": anti_patterns,
            "anti_patterns_count": len(anti_patterns),
            "by_severity": self._group_by_severity(anti_patterns),
            "overall_score": overall_score,
            "quality_grade": self._get_quality_grade(overall_score),
            "priority_fixes": priority_fixes[:10],
            "refactoring_roadmap": roadmap
        }
    
    async def _detect_god_object(self, config_name: str) -> List[AntiPattern]:
        """Детекция God Objects"""
        god_objects = await self._find_god_objects(config_name)
        
        return [
            {
                'type': 'God Object',
                'severity': obj['severity'],
                'location': obj['name'],
                'metrics': {
                    'functions_count': obj['functions_count'],
                    'outgoing_dependencies': obj['outgoing_dependencies'],
                    'incoming_dependencies': obj['incoming_dependencies'],
                    'complexity_score': obj['complexity_score']
                },
                'recommendation': f"Разбить модуль '{obj['name']}' на специализированные модули по Single Responsibility Principle",
                'refactoring_effort': 'High',
                'estimated_days': self._estimate_refactoring_days(obj['complexity_score'])
            }
            for obj in god_objects
        ]
    
    async def _detect_spaghetti_code(self, config_name: str) -> List[Dict]:
        """Детекция Spaghetti Code (высокая цикломатическая сложность)"""
        # TODO: Интеграция с SonarQube или анализ кода
        return []
    
    async def _detect_circular_dependencies(self, config_name: str) -> List[Dict]:
        """Детекция циклических зависимостей"""
        cycles = await self._find_cyclic_dependencies(config_name)
        
        return [
            {
                'type': 'Circular Dependency',
                'severity': cycle['severity'],
                'location': ' → '.join(cycle['path']),
                'metrics': {
                    'cycle_length': cycle['cycle_length'],
                    'modules_involved': len(cycle['path'])
                },
                'recommendation': f"Разорвать цикл через события, интерфейсы или промежуточный модуль",
                'refactoring_effort': 'Medium' if cycle['cycle_length'] <= 3 else 'High',
                'estimated_days': cycle['cycle_length']
            }
            for cycle in cycles
        ]
    
    async def _detect_long_methods(self, config_name: str) -> List[Dict]:
        """Детекция длинных методов (> 100 строк)"""
        # TODO: Анализ кода из PostgreSQL
        return []
    
    async def _detect_code_duplication(self, config_name: str) -> List[Dict]:
        """Детекция дублирования кода"""
        # TODO: Использовать алгоритм поиска похожих блоков
        return []
    
    def _estimate_refactoring_days(self, complexity_score: int) -> int:
        """Оценка дней на рефакторинг"""
        if complexity_score < 50:
            return 1
        elif complexity_score < 100:
            return 3
        elif complexity_score < 200:
            return 5
        else:
            return 10
    
    def _calculate_quality_score(self, anti_patterns: List[Dict]) -> float:
        """Расчет общего score качества (1-10)"""
        if not anti_patterns:
            return 10.0
        
        score = 10.0
        
        severity_penalties = {
            'critical': 2.0,
            'high': 1.0,
            'medium': 0.5,
            'low': 0.2
        }
        
        for pattern in anti_patterns:
            penalty = severity_penalties.get(pattern.get('severity', 'medium'), 0.5)
            score -= penalty
        
        return max(1.0, min(10.0, score))
    
    def _get_quality_grade(self, score: float) -> str:
        """Оценка качества A-F"""
        if score >= 9.0:
            return "A (Excellent)"
        elif score >= 7.5:
            return "B (Good)"
        elif score >= 6.0:
            return "C (Acceptable)"
        elif score >= 4.0:
            return "D (Needs Improvement)"
        else:
            return "F (Critical Issues)"
    
    def _group_by_severity(self, anti_patterns: List[Dict]) -> Dict[str, int]:
        """Группировка по severity"""
        from collections import Counter
        severities = [p.get('severity', 'medium') for p in anti_patterns]
        return dict(Counter(severities))
    
    def _prioritize_fixes(self, anti_patterns: List[Dict]) -> List[Dict]:
        """Приоритизация исправлений по ROI"""
        severity_priority = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        effort_score = {'Low': 3, 'Medium': 2, 'High': 1}
        
        for pattern in anti_patterns:
            sev = severity_priority.get(pattern.get('severity', 'medium'), 2)
            eff = effort_score.get(pattern.get('refactoring_effort', 'Medium'), 2)
            pattern['priority_score'] = sev * eff
        
        return sorted(anti_patterns, key=lambda x: x.get('priority_score', 0), reverse=True)
    
    def _generate_refactoring_roadmap(self, priority_fixes: List[Dict]) -> List[Dict]:
        """Генерация roadmap рефакторинга"""
        roadmap = []
        current_week = 1
        
        for fix in priority_fixes[:10]:  # Top 10
            days = fix.get('estimated_days', 3)
            roadmap.append({
                'phase': f"Week {current_week}",
                'task': f"Fix {fix['type']}: {fix['location']}",
                'effort': f"{days} days",
                'impact': fix['severity'],
                'deliverable': fix['recommendation']
            })
            
            if days > 3:
                current_week += 1
        
        return roadmap
    
    def _load_anti_patterns_catalog(self) -> Dict:
        """Загрузка каталога anti-patterns"""
        return {
            'God Object': {
                'description': 'Модуль с слишком многими ответственностями',
                'threshold': {'functions': 50, 'dependencies': 20}
            },
            'Spaghetti Code': {
                'description': 'Высокая цикломатическая сложность',
                'threshold': {'complexity': 15}
            },
            'Circular Dependency': {
                'description': 'Циклические зависимости между модулями',
                'threshold': {}
            }
        }
    
    def _load_technology_knowledge(self) -> Dict:
        """База знаний технологий"""
        return {
            'Apache Kafka': {
                'type': 'Message Broker',
                'best_for': ['high-throughput', 'event-driven', 'streaming'],
                'complexity': 'high',
                'cost': 'medium'
            },
            'RabbitMQ': {
                'type': 'Message Broker',
                'best_for': ['reliable-messaging', 'microservices', 'task-queues'],
                'complexity': 'medium',
                'cost': 'low'
            },
            '1С:Шина': {
                'type': 'ESB',
                'best_for': ['1c-native', 'enterprise-integration', 'transformation'],
                'complexity': 'medium',
                'cost': 'medium'
            }
        }


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test():
        agent = ArchitectAgentExtended()
        
        # Test 1: Graph analysis
        print("=== Test 1: Graph Analysis ===")
        result = await agent.analyze_architecture_graph("ERP")
        print(f"Overall score: {result.get('metrics', {}).get('overall_score', 'N/A')}")
        
        # Test 2: ADR generation
        print("\n=== Test 2: ADR Generation ===")
        adr = await agent.generate_adr(
            title="Выбор шины данных для интеграций",
            context="B2B-портал требует устойчивых интеграций при пиковых нагрузках",
            problem="Синхронные REST вызовы приводят к таймаутам",
            alternatives=[
                {
                    "option": "Apache Kafka",
                    "pros": ["Высокая пропускная способность", "Событийная модель"],
                    "cons": ["Операционная сложность"],
                    "scores": {"performance": 9, "complexity": 6, "cost": 7}
                }
            ],
            decision="Использовать Apache Kafka для событий, REST для запросов",
            rationale="Баланс между производительностью и сложностью",
            consequences={
                "pros": ["Устойчивость повышена", "Масштабируемость"],
                "cons": ["Требуется обучение команды"]
            }
        )
        print(f"ADR created: {adr['adr']['adr_id']}")
        
        # Test 3: Anti-pattern detection
        print("\n=== Test 3: Anti-Pattern Detection ===")
        patterns = await agent.detect_anti_patterns("ERP", include_code_analysis=False)
        print(f"Found {patterns['anti_patterns_count']} anti-patterns")
        print(f"Quality grade: {patterns['quality_grade']}")
    
    asyncio.run(test())

