"""
ADR Generator Service

Сервис для генерации Architecture Decision Records.
"""

from typing import Dict, List

from src.modules.architect.domain.exceptions import ADRGenerationError
from src.modules.architect.domain.models import (
    ADR,
    ADRStatus,
    Alternative,
    Consequences,
)
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class ADRGenerator:
    """
    Сервис генерации Architecture Decision Records

    Features:
    - ADR generation
    - Template rendering
    - Alternatives comparison
    - Consequences analysis
    """

    def __init__(self):
        """Initialize ADR generator"""
        self.adr_counter = 1

    async def generate_adr(
        self,
        title: str,
        context: str,
        problem: str,
        decision: str,
        alternatives: List[Dict[str, List[str]]],
        consequences: Dict[str, List[str]],
        status: ADRStatus = ADRStatus.PROPOSED
    ) -> ADR:
        """
        Генерация Architecture Decision Record

        Args:
            title: Название решения
            context: Контекст принятия решения
            problem: Проблема/вызов
            decision: Принятое решение
            alternatives: Рассмотренные альтернативы
            consequences: Последствия решения
            status: Статус ADR

        Returns:
            ADR object
        """
        try:
            logger.info(
                "Generating ADR",
                extra={"title": title}
            )

            # Generate ID
            adr_id = f"ADR-{self.adr_counter:03d}"
            self.adr_counter += 1

            # Parse alternatives
            alternatives_list = [
                Alternative(
                    name=alt.get("name", ""),
                    pros=alt.get("pros", []),
                    cons=alt.get("cons", [])
                )
                for alt in alternatives
            ]

            # Parse consequences
            consequences_obj = Consequences(
                positive=consequences.get("positive", []),
                negative=consequences.get("negative", []),
                risks=consequences.get("risks", [])
            )

            return ADR(
                id=adr_id,
                title=title,
                status=status,
                context=context,
                problem=problem,
                decision=decision,
                alternatives=alternatives_list,
                consequences=consequences_obj
            )

        except Exception as e:
            logger.error("Failed to generate ADR: %s", e)
            raise ADRGenerationError(
                f"Failed to generate ADR: {e}",
                details={"title": title}
            )

    def render_adr_markdown(self, adr: ADR) -> str:
        """
        Рендеринг ADR в Markdown формат

        Args:
            adr: ADR object

        Returns:
            Markdown текст
        """
        markdown = f"""# {adr.id}: {adr.title}

**Статус:** {adr.status.value}
**Дата:** {adr.created_at}

## Контекст

{adr.context}

## Проблема

{adr.problem}

## Решение

{adr.decision}

## Альтернативы

"""

        for alt in adr.alternatives:
            markdown += f"""### {alt.name}

**Преимущества:**
"""
            for pro in alt.pros:
                markdown += f"- {pro}\n"

            markdown += "\n**Недостатки:**\n"
            for con in alt.cons:
                markdown += f"- {con}\n"

            markdown += "\n"

        markdown += """## Последствия

### Позитивные
"""
        for pos in adr.consequences.positive:
            markdown += f"- {pos}\n"

        markdown += "\n### Негативные\n"
        for neg in adr.consequences.negative:
            markdown += f"- {neg}\n"

        markdown += "\n### Риски\n"
        for risk in adr.consequences.risks:
            markdown += f"- {risk}\n"

        return markdown


__all__ = ["ADRGenerator"]
