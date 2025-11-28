"""
Gap Analyzer Service

Сервис для анализа разрывов между текущим и желаемым состоянием.
"""

from typing import Any, Dict, List

from src.modules.business_analyst.domain.exceptions import GapAnalysisError
from src.modules.business_analyst.domain.models import (
    Effort,
    Gap,
    GapAnalysisResult,
    Impact,
    RoadmapItem,
)
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class GapAnalyzer:
    """
    Сервис gap analysis

    Features:
    - Process/system/capability comparison
    - Gap identification
    - Roadmap generation
    - Priority calculation
    """

    def __init__(self):
        """Initialize gap analyzer"""

    async def perform_gap_analysis(
        self,
        current_state: Dict[str, Any],
        desired_state: Dict[str, Any]
    ) -> GapAnalysisResult:
        """
        Gap анализ между текущим и желаемым состоянием

        Args:
            current_state: {
                "processes": [...],
                "systems": [...],
                "capabilities": [...]
            }
            desired_state: {
                "processes": [...],
                "systems": [...],
                "capabilities": [...]
            }

        Returns:
            GapAnalysisResult с gaps и roadmap
        """
        try:
            logger.info("Performing gap analysis")

            gaps: List[Gap] = []

            # Analyze processes
            gaps.extend(
                self._analyze_processes(current_state, desired_state)
            )

            # Analyze systems
            gaps.extend(
                self._analyze_systems(current_state, desired_state)
            )

            # Analyze capabilities
            gaps.extend(
                self._analyze_capabilities(current_state, desired_state)
            )

            # Sort by priority
            gaps.sort(key=lambda x: x.priority, reverse=True)

            # Generate roadmap
            roadmap = self._generate_roadmap(gaps)

            # Estimate timeline
            total_effort_days = sum(
                {"low": 10, "medium": 30, "high": 90}.get(
                    gap.effort.value, 30
                )
                for gap in gaps
            )
            estimated_timeline = f"{total_effort_days // 20} months"

            return GapAnalysisResult(
                gaps=gaps,
                roadmap=roadmap,
                estimated_timeline=estimated_timeline,
            )

        except Exception as e:
            logger.error("Failed to perform gap analysis: %s", e)
            raise GapAnalysisError(
                f"Failed to perform gap analysis: {e}",
                details={}
            )

    def _analyze_processes(
        self,
        current_state: Dict,
        desired_state: Dict
    ) -> List[Gap]:
        """Анализ процессов"""
        gaps: List[Gap] = []

        current_processes = set(current_state.get("processes", []))
        desired_processes = set(desired_state.get("processes", []))
        missing_processes = desired_processes - current_processes

        for process in missing_processes:
            gaps.append(
                Gap(
                    area="Processes",
                    current="Not implemented",
                    desired=f"Automated process: {process}",
                    impact=Impact.HIGH,
                    effort=Effort.MEDIUM,
                    priority=8.0,
                )
            )

        return gaps

    def _analyze_systems(
        self,
        current_state: Dict,
        desired_state: Dict
    ) -> List[Gap]:
        """Анализ систем"""
        gaps: List[Gap] = []

        current_systems = set(current_state.get("systems", []))
        desired_systems = set(desired_state.get("systems", []))
        missing_systems = desired_systems - current_systems

        for system in missing_systems:
            gaps.append(
                Gap(
                    area="Systems",
                    current="Not available",
                    desired=f"Integrated system: {system}",
                    impact=Impact.HIGH,
                    effort=Effort.HIGH,
                    priority=7.0,
                )
            )

        return gaps

    def _analyze_capabilities(
        self,
        current_state: Dict,
        desired_state: Dict
    ) -> List[Gap]:
        """Анализ возможностей"""
        gaps: List[Gap] = []

        current_capabilities = set(current_state.get("capabilities", []))
        desired_capabilities = set(desired_state.get("capabilities", []))
        missing_capabilities = desired_capabilities - current_capabilities

        for capability in missing_capabilities:
            gaps.append(
                Gap(
                    area="Capabilities",
                    current="Manual/Limited",
                    desired=f"Full capability: {capability}",
                    impact=Impact.MEDIUM,
                    effort=Effort.MEDIUM,
                    priority=6.0,
                )
            )

        return gaps

    def _generate_roadmap(self, gaps: List[Gap]) -> List[RoadmapItem]:
        """Генерация дорожной карты"""
        roadmap: List[RoadmapItem] = []

        # Phase 1: High priority, low/medium effort
        phase1_gaps = [
            g for g in gaps
            if g.priority >= 7.0 and g.effort in [Effort.LOW, Effort.MEDIUM]
        ]
        if phase1_gaps:
            roadmap.append(
                RoadmapItem(
                    phase="Phase 1: Quick Wins",
                    gaps=[f"{g.area}: {g.desired}" for g in phase1_gaps],
                    duration="1-2 months",
                    dependencies=[],
                )
            )

        # Phase 2: High priority, high effort
        phase2_gaps = [
            g for g in gaps
            if g.priority >= 7.0 and g.effort == Effort.HIGH
        ]
        if phase2_gaps:
            roadmap.append(
                RoadmapItem(
                    phase="Phase 2: Strategic Initiatives",
                    gaps=[f"{g.area}: {g.desired}" for g in phase2_gaps],
                    duration="3-6 months",
                    dependencies=["Phase 1"] if phase1_gaps else [],
                )
            )

        # Phase 3: Medium priority
        phase3_gaps = [g for g in gaps if g.priority < 7.0]
        if phase3_gaps:
            roadmap.append(
                RoadmapItem(
                    phase="Phase 3: Improvements",
                    gaps=[f"{g.area}: {g.desired}" for g in phase3_gaps],
                    duration="2-4 months",
                    dependencies=["Phase 2"] if phase2_gaps else [],
                )
            )

        return roadmap


__all__ = ["GapAnalyzer"]
