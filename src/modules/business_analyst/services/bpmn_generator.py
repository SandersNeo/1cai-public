"""
BPMN Generator Service

Сервис для генерации BPMN 2.0 диаграмм из текстового описания процессов.
"""

import html
import re
from typing import List

from src.modules.business_analyst.domain.exceptions import BPMNGenerationError
from src.modules.business_analyst.domain.models import BPMNDiagram, DecisionPoint
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class BPMNGenerator:
    """
    Сервис генерации BPMN диаграмм

    Features:
    - BPMN 2.0 XML generation
    - Mermaid diagram generation
    - Actor/activity extraction
    - Decision points extraction
    """

    def __init__(self):
        """Initialize BPMN generator"""
        self.default_lane = "System"
        self._max_label_length = 120
        self._mermaid_translation = str.maketrans({
            "[": "(",
            "]": ")",
            "{": "(",
            "}": ")",
            "<": " ",
            ">": " ",
            "`": " ",
            '"': " ",
            "'": " ",
        })

    async def generate_bpmn(
        self,
        process_description: str
    ) -> BPMNDiagram:
        """
        Генерация BPMN диаграммы из описания процесса

        Args:
            process_description: Текстовое описание процесса

        Returns:
            BPMNDiagram с XML, Mermaid и метаданными
        """
        try:
            logger.info("Generating BPMN diagram")

            # Extract components
            actors = self._extract_actors(process_description)
            activities = self._extract_activities(process_description)
            decisions = self._extract_decision_points(process_description)

            # Generate diagrams
            bpmn_xml = self._generate_bpmn_xml(actors, activities, decisions)
            mermaid = self._generate_mermaid(actors, activities, decisions)

            return BPMNDiagram(
                bpmn_xml=bpmn_xml,
                diagram_svg=None,  # SVG generation optional
                mermaid=mermaid,
                actors=actors,
                activities=activities,
                decision_points=decisions,
            )

        except Exception as e:
            logger.error(f"Failed to generate BPMN: {e}")
            raise BPMNGenerationError(
                f"Failed to generate BPMN: {e}",
                details={"description_length": len(process_description)}
            )

    def _extract_actors(self, description: str) -> List[str]:
        """Извлечение участников процесса"""
        actors = set()

        patterns = [
            r"(\w+(?:щик|лог|тель|ант|ер))",
            r"(менеджер|директор|бухгалтер|кладовщик|продавец|клиент)",
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, description, re.IGNORECASE)
            for match in matches:
                actors.add(match.group(1).capitalize())

        return list(actors)[:10]

    def _extract_activities(self, description: str) -> List[str]:
        """Извлечение активностей"""
        activities = []
        verb_patterns = [
            r"(создать|создание)\s+(\w+)",
            r"(проверить|проверка)\s+(\w+)",
            r"(утвердить|утверждение)\s+(\w+)",
            r"(отправить|отправка)\s+(\w+)",
            r"(получить|получение)\s+(\w+)",
        ]

        for pattern in verb_patterns:
            matches = re.finditer(pattern, description, re.IGNORECASE)
            for match in matches:
                activity = f"{match.group(1)} {match.group(2)}"
                activities.append(activity)

        return activities[:15]

    def _extract_decision_points(
        self,
        description: str
    ) -> List[DecisionPoint]:
        """Извлечение точек принятия решений"""
        decisions: List[DecisionPoint] = []
        patterns = [
            r"если\s+(.+?)\s+,?\s+то\s+(.+?)(?:,\s*иначе\s+(.+))?",
            r"в случае\s+(.+?)\s+,?\s+(?:выполняется|происходит)\s+(.+)",
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, description, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                decisions.append(
                    DecisionPoint(
                        condition=groups[0].strip(),
                        true_path=groups[1].strip() if len(groups) > 1 else "Да",
                        false_path=groups[2].strip() if len(
                            groups) > 2 and groups[2] else "Нет",
                    )
                )

        return decisions[:10]

    def _generate_mermaid(
        self,
        actors: List[str],
        activities: List[str],
        decisions: List[DecisionPoint],
    ) -> str:
        """Генерация Mermaid диаграммы"""
        mermaid = "graph TD\n"
        mermaid += "    Start[Начало] --> Activity1\n"

        limited_activities = activities[:5]
        for i, activity in enumerate(limited_activities, 1):
            label = self._sanitize_step(activity, for_mermaid=True)
            mermaid += f"    Activity{i}[{label}] --> "
            if i < len(limited_activities):
                mermaid += f"Activity{i+1}\n"
            else:
                mermaid += "End[Конец]\n"

        return mermaid

    def _generate_bpmn_xml(
        self,
        actors: List[str],
        activities: List[str],
        decisions: List[DecisionPoint],
    ) -> str:
        """Генерация BPMN 2.0 XML"""
        bpmn = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
                  id="Definitions_1">
  <bpmn:process id="Process_1" isExecutable="false">
    <bpmn:startEvent id="StartEvent_1" name="Начало"/>
"""

        for i, activity in enumerate(activities[:5], 1):
            label = self._sanitize_step(activity, for_mermaid=False)
            bpmn += f'    <bpmn:task id="Activity_{i}" name="{label}"/>\n'

        bpmn += """    <bpmn:endEvent id="EndEvent_1" name="Конец"/>
  </bpmn:process>
</bpmn:definitions>
"""

        return bpmn

    def _sanitize_step(self, text: str, *, for_mermaid: bool) -> str:
        """Санитизация текста для диаграмм"""
        cleaned = re.sub(r"\s+", " ", text or "").strip()
        if not cleaned:
            cleaned = "Step"
        if len(cleaned) > self._max_label_length:
            cleaned = cleaned[:self._max_label_length].rstrip()

        if for_mermaid:
            cleaned = cleaned.translate(self._mermaid_translation)
            cleaned = cleaned.replace("--", "—")
        else:
            cleaned = html.escape(cleaned, quote=True)

        return cleaned


__all__ = ["BPMNGenerator"]
