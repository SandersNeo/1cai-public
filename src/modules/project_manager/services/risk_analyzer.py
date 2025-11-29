from typing import List
from src.modules.project_manager.domain.models import Risk, RiskLevel, RiskStrategy


class RiskAnalyzer:
    """
    Сервис для анализа и категоризации проектных рисков (модель ROAM).
    """

    def analyze_risk(self, description: str, probability: int, impact: int) -> Risk:
        """
        Анализирует риск и определяет стратегию смягчения.
        """
        risk_id = f"risk-{hash(description) % 10000}"

        # Расчет оценки
        score = probability * impact

        # Определение стратегии на основе оценки (ROAM)
        if score >= 20:  # Critical
            strategy = RiskStrategy.MITIGATE
            plan = "Требуются немедленные действия. Эскалировать заинтересованным сторонам."
        elif score >= 12:  # High
            strategy = RiskStrategy.OWN
            plan = "Назначить ответственного для мониторинга и управления."
        elif score >= 6:  # Medium
            strategy = RiskStrategy.RESOLVE
            plan = "Предпринять шаги для снижения вероятности или воздействия."
        else:  # Low
            strategy = RiskStrategy.ACCEPT
            plan = "Периодический мониторинг, немедленных действий не требуется."

        return Risk(
            id=risk_id,
            description=description,
            probability=probability,
            impact=impact,
            strategy=strategy,
            mitigation_plan=plan,
        )

    def analyze_bulk(self, risks_data: List[dict]) -> List[Risk]:
        """
        Анализирует несколько рисков массово.
        """
        return [self.analyze_risk(r["description"], r["probability"], r["impact"]) for r in risks_data]
