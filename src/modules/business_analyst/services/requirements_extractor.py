"""
Requirements Extractor Service

Сервис для извлечения требований из документов с NLP и pattern matching.
"""

import re
from typing import List, Optional

from src.modules.business_analyst.domain.exceptions import RequirementExtractionError
from src.modules.business_analyst.domain.models import (
    Priority,
    Requirement,
    RequirementExtractionResult,
    RequirementType,
    UserStory,
)
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class RequirementsExtractor:
    """
    Сервис извлечения требований из документов

    Features:
    - Pattern matching для functional/non-functional/constraints
    - Stakeholder extraction
    - User stories extraction
    - Acceptance criteria extraction
    - Confidence scoring
    """

    def __init__(self, requirements_repository=None):
        """
        Args:
            requirements_repository: Repository для паттернов
                                    (опционально, для dependency injection)
        """
        if requirements_repository is None:
            from src.modules.business_analyst.repositories import RequirementsRepository
            requirements_repository = RequirementsRepository()

        self.requirements_repository = requirements_repository
        self.requirement_patterns = (
            self.requirements_repository.get_requirement_patterns()
        )
        self.user_story_patterns = (
            self.requirements_repository.get_user_story_patterns()
        )

    async def extract_requirements(
        self,
        document_text: str,
        document_type: str = "tz",
        source_path: Optional[str] = None,
    ) -> RequirementExtractionResult:
        """
        Извлечение требований из документа

        Args:
            document_text: Текст документа
            document_type: Тип документа (tz, srs, etc.)
            source_path: Путь к файлу (опционально)

        Returns:
            RequirementExtractionResult с извлеченными требованиями
        """
        try:
            logger.info(
                "Extracting requirements",
                extra={"document_type": document_type}
            )

            sentences = self._split_sentences(document_text)
            functional: List[Requirement] = []
            non_functional: List[Requirement] = []
            constraints: List[Requirement] = []

            # Pattern matching для каждого предложения
            for idx, sentence in enumerate(sentences):
                cleaned = sentence.strip()
                if not cleaned:
                    continue

                for pattern_info in self.requirement_patterns:
                    req_type = pattern_info["type"]
                    matched = False

                    for pattern in pattern_info["patterns"]:
                        match = re.search(pattern, cleaned, re.IGNORECASE)
                        if not match:
                            continue

                        body = match.groupdict().get("body") or match.group(0)
                        requirement = self._build_requirement(
                            req_type, body, cleaned, sentence_index=idx
                        )

                        if req_type == "functional":
                            functional.append(requirement)
                        elif req_type == "non_functional":
                            non_functional.append(requirement)
                        else:
                            constraints.append(requirement)

                        matched = True
                        break

                    if matched:
                        break

            # Извлечение дополнительных артефактов
            stakeholders = self._extract_stakeholders(document_text)
            user_stories = self._extract_user_stories(document_text)

            # Summary
            summary = {
                "total_requirements": (
                    len(functional) + len(non_functional) + len(constraints)
                ),
                "functional": len(functional),
                "non_functional": len(non_functional),
                "constraints": len(constraints),
                "stakeholders_count": len(stakeholders),
                "user_stories_count": len(user_stories),
            }

            return RequirementExtractionResult(
                functional_requirements=functional,
                non_functional_requirements=non_functional,
                constraints=constraints,
                stakeholders=stakeholders,
                user_stories=user_stories,
                summary=summary,
            )

        except Exception as e:
            logger.error("Failed to extract requirements: %s", e)
            raise RequirementExtractionError(
                f"Failed to extract requirements: {e}",
                details={"document_type": document_type}
            )

    def _build_requirement(
        self,
        req_type: str,
        body: str,
        sentence: str,
        sentence_index: int,
    ) -> Requirement:
        """
        Построение объекта Requirement

        Args:
            req_type: Тип требования
            body: Тело требования
            sentence: Полное предложение
            sentence_index: Индекс предложения

        Returns:
            Requirement object
        """
        body = self._normalize_whitespace(body)
        sentence = self._normalize_whitespace(sentence)

        # Generate ID
        prefix = {
            "functional": "FR",
            "non_functional": "NFR",
            "constraint": "CON"
        }[req_type]
        requirement_id = f"{prefix}-{sentence_index + 1:03d}"

        # Determine priority
        priority = self._determine_priority(sentence)

        # Calculate confidence
        confidence = self._calculate_confidence(sentence, priority)

        return Requirement(
            id=requirement_id,
            type=RequirementType(req_type),
            title=body[:120],
            description=sentence,
            priority=priority,
            source=f"sentence:{sentence_index + 1}",
            confidence=confidence,
            stakeholders=[],
            acceptance_criteria=[],
        )

    def _determine_priority(self, sentence: str) -> Priority:
        """Определение приоритета требования"""
        lowered = sentence.lower()

        if any(
            keyword in lowered
            for keyword in ("обязательно", "критично", "срочно", "must")
        ):
            return Priority.HIGH
        elif any(
            keyword in lowered
            for keyword in ("желательно", "может", "опционально", "nice")
        ):
            return Priority.LOW
        else:
            return Priority.MEDIUM

    def _calculate_confidence(
        self,
        sentence: str,
        priority: Priority
    ) -> float:
        """Расчет уверенности в извлечении"""
        confidence = 0.65

        if priority == Priority.HIGH:
            confidence += 0.1
        if len(sentence) > 120:
            confidence += 0.05

        return min(round(confidence, 2), 0.95)

    def _split_sentences(self, document_text: str) -> List[str]:
        """Разбиение текста на предложения"""
        return re.split(r"(?<=[.!?])\s+", document_text)

    def _normalize_whitespace(self, text: str) -> str:
        """Нормализация пробелов"""
        return re.sub(r"\s+", " ", text).strip()

    def _extract_stakeholders(self, text: str) -> List[str]:
        """Извлечение заинтересованных сторон"""
        titles = [
            "менеджер",
            "руководитель",
            "директор",
            "администратор",
            "пользователь",
            "бухгалтер",
            "кладовщик",
            "продавец",
            "клиент",
            "оператор",
        ]

        found = {
            title.capitalize()
            for title in titles
            if title in text.lower()
        }

        return sorted(found)

    def _extract_user_stories(self, text: str) -> List[UserStory]:
        """Извлечение user stories"""
        stories: List[UserStory] = []
        lines = [line.strip() for line in text.splitlines()]
        counter = 1

        for line in lines:
            normalized = line.lower()

            for pattern in self.user_story_patterns:
                match = re.search(pattern, normalized, re.IGNORECASE)
                if not match:
                    continue

                groups = match.groupdict()
                role = groups.get("role", "").strip().strip(",.")
                goal = groups.get("goal", "").strip().strip(",.")
                benefit = groups.get("benefit", "").strip().strip(",.")

                stories.append(
                    UserStory(
                        id=f"US-{counter:03d}",
                        role=role.capitalize(),
                        goal=goal,
                        benefit=benefit or "",
                        acceptance_criteria=[],
                    )
                )
                counter += 1
                break

        return stories


__all__ = ["RequirementsExtractor"]
