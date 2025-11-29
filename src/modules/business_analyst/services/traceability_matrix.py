"""
Traceability Matrix Service

Сервис для генерации матрицы прослеживаемости требований.
"""

from typing import Any, Dict, List

from src.modules.business_analyst.domain.exceptions import TraceabilityError
from src.modules.business_analyst.domain.models import (
    CoverageSummary,
    Requirement,
    TraceabilityItem,
    TraceabilityMatrix,
)
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class TraceabilityMatrixGenerator:
    """
    Сервис генерации матрицы прослеживаемости

    Features:
    - Requirement → Test case mapping
    - Coverage calculation
    - Gap identification
    """

    def __init__(self) -> None:
        """Initialize traceability matrix generator"""

    async def generate_matrix(
        self,
        requirements: List[Requirement],
        test_cases: List[Dict[str, Any]]
    ) -> TraceabilityMatrix:
        """
        Генерация матрицы прослеживаемости

        Args:
            requirements: Список требований
            test_cases: Список тест-кейсов [{id, requirement_ids, ...}]

        Returns:
            TraceabilityMatrix с coverage analysis
        """
        try:
            logger.info(
                "Generating traceability matrix",
                extra={"requirements_count": len(requirements)}
            )

            matrix: List[TraceabilityItem] = []

            for req in requirements:
                req_id = req.id

                # Find test cases covering this requirement
                covering_tests = [
                    tc
                    for tc in test_cases
                    if req_id in tc.get("requirement_ids", [])
                ]

                coverage = "100%" if covering_tests else "0%"

                matrix.append(
                    TraceabilityItem(
                        requirement_id=req_id,
                        test_cases=[tc.get("id") for tc in covering_tests],
                        coverage=coverage,
                    )
                )

            # Coverage summary
            total_reqs = len(requirements)
            covered_reqs = sum(
                1 for item in matrix if len(item.test_cases) > 0
            )
            coverage_percent = (
                (covered_reqs / total_reqs) * 100 if total_reqs > 0 else 0.0
            )

            coverage_summary = CoverageSummary(
                total_requirements=total_reqs,
                covered=covered_reqs,
                coverage_percent=round(coverage_percent, 2),
            )

            return TraceabilityMatrix(
                matrix=matrix,
                coverage_summary=coverage_summary,
            )

        except Exception as e:
            logger.error("Failed to generate traceability matrix: %s", e)
            raise TraceabilityError(
                f"Failed to generate traceability matrix: {e}",
                details={"requirements_count": len(requirements)}
            )


__all__ = ["TraceabilityMatrixGenerator"]
