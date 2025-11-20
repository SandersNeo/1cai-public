# [NEXUS IDENTITY] ID: -5127080697703299148 | DATE: 2025-11-19

"""
Scenario Hub & Execution Plans
------------------------------

Экспериментальный слой поверх AI Orchestrator, который оперирует не
отдельными инструментами, а сценариями (goals) и детерминированными
плейбуками для их выполнения.

Цели файла:
- Описать базовые модели для сценариев / планов / шагов.
- Задать каркас для двухконтурного режима:
  - online: планирование (LLM/агенты);
  - offline: выполнение (playbooks / execution env / HTTP API).
- Ввести явные уровни риска и автономности.

Интеграция:
- На данном этапе модуль не подключён к FastAPI/Orchestrator и
  используется как reference-слой типов, который можно постепенно
  встраивать в существующие сервисы.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class ScenarioRiskLevel(str, Enum):
    """Уровень риска сценария или шага."""

    READ_ONLY = "read_only"  # Без изменений состояния
    NON_PROD_CHANGE = "non_prod_change"  # Изменения только в test/staging
    PROD_LOW = "prod_low"  # Низкий риск в prod (ограниченные операции)
    PROD_HIGH = "prod_high"  # Высокий риск в prod (DR, миграции, крупные изменения)


class AutonomyLevel(str, Enum):
    """
    Уровень автономности системы (A0–A3).

    A0 - только предложения, без действий.
    A1 - автоматизация низкорисковых задач.
    A2 - изменения в non-prod.
    A3 - ограниченные действия в prod по строгим правилам.
    """

    A0_PROPOSE_ONLY = "A0_propose_only"
    A1_SAFE_AUTOMATION = "A1_safe_automation"
    A2_NON_PROD_CHANGES = "A2_non_prod_changes"
    A3_RESTRICTED_PROD = "A3_restricted_prod"


@dataclass
class ScenarioGoal:
    """
    Описание цели сценария на языке пользователя.

    Примеры:
    - "Провести DR rehearsal для сервиса vault на staging"
    - "Проверить BA→Dev→QA поток для фичи X"
    """

    id: str
    title: str
    description: str
    constraints: Dict[str, Any] = field(default_factory=dict)
    success_criteria: List[str] = field(default_factory=list)


@dataclass
class ScenarioStep:
    """
    Один шаг в сценарии.

    Важно: на этом уровне ещё нет привязки к конкретному протоколу
    (MCP/HTTP/CLI). Шаг описывает действие и его контракт.
    """

    id: str
    title: str
    description: str
    risk_level: ScenarioRiskLevel
    autonomy_required: AutonomyLevel
    # Формальные требования к успешному выполнению шага
    checks: List[str] = field(default_factory=list)
    # Тип исполнителя: "agent:BA", "agent:Dev", "playbook:dr", "script"
    executor: str = "agent:orchestrator"
    # Арбитрарный контекст для конкретных интеграций (HTTP endpoint, имя playbook и т.д.)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScenarioPlan:
    """
    Детерминированный план (плейбук) для достижения цели.

    Может быть сгенерирован онлайн-агентом и выполнен офлайн-исполнителем.
    """

    id: str
    goal: ScenarioGoal
    steps: List[ScenarioStep]
    # Глобальный уровень автономности, при котором план допускается к запуску
    required_autonomy: AutonomyLevel
    # Общий уровень риска сценария (на основе шагов)
    overall_risk: ScenarioRiskLevel
    # Произвольный контекст (например, ссылки на ADR/DR план)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TrustScore:
    """
    Оценка "доверия" к плану / шагу.

    Число и простые маркеры, которые можно показать пользователю.
    """

    score: float  # 0.0–1.0
    level: str  # "low" / "medium" / "high"
    reasons: List[str] = field(default_factory=list)


@dataclass
class ScenarioExecutionReport:
    """
    Краткий отчёт о выполнении сценария для пользователя.

    Задача: дать понятный нарратив и ссылки на артефакты,
    не перегружая деталями реализации.
    """

    scenario_id: str
    goal: ScenarioGoal
    trust_before: TrustScore
    trust_after: TrustScore
    summary: str
    # Список ключевых событий/решений в формате "нарратива"
    timeline: List[str] = field(default_factory=list)
    # Ссылки на артефакты: отчёты, логи, ADR, DR-постмортемы
    artifacts: Dict[str, str] = field(default_factory=dict)


def compute_trust_score(
    tests_passed: bool,
    coverage_ok: bool,
    recent_incidents: int,
    risk_level: ScenarioRiskLevel,
) -> TrustScore:
    """
    Простая евристика для расчёта trust-score.

    Это экспериментальная функция, её можно заменить
    более продвинутой моделью/политикой.
    """

    score = 0.0
    reasons: List[str] = []

    if tests_passed:
        score += 0.4
        reasons.append("Юнит/системные тесты сценария зелёные")
    else:
        reasons.append("Есть упавшие тесты по связанным компонентам")

    if coverage_ok:
        score += 0.2
        reasons.append("Покрытие тестами выше минимального порога")
    else:
        reasons.append("Покрытие тестами ниже желаемого уровня")

    if recent_incidents == 0:
        score += 0.2
        reasons.append("Нет недавних инцидентов по этому сценарию/сервису")
    elif recent_incidents == 1:
        score += 0.1
        reasons.append("Был один недавний инцидент, учтён в DR-плане")
    else:
        reasons.append("Несколько недавних инцидентов, повышенный риск")

    if risk_level == ScenarioRiskLevel.READ_ONLY:
        score += 0.2
        reasons.append("Сценарий read-only, изменения состояния отсутствуют")
    elif risk_level == ScenarioRiskLevel.NON_PROD_CHANGE:
        score += 0.1
        reasons.append("Изменения ограничены non-prod окружениями")
    else:
        reasons.append("Сценарий затрагивает prod, риск повышен")

    # Нормализуем и ограничим [0, 1]
    score = max(0.0, min(score, 1.0))

    if score >= 0.8:
        level = "high"
    elif score >= 0.5:
        level = "medium"
    else:
        level = "low"

    return TrustScore(score=score, level=level, reasons=reasons)
