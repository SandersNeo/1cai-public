"""Issue Classifier Service."""

import re
from typing import Dict, List

from ..domain import Issue, IssueClassification, IssueType


class IssueClassifier:
    """Service for classifying issues using pattern matching and keywords."""

    def __init__(self):
        """Initialize classifier with keyword patterns."""
        self.type_keywords = {
            IssueType.ERROR: [
                "error",
                "exception",
                "failed",
                "crash",
                "fault",
                "ошибка",
                "исключение",
                "сбой",
                "отказ",
            ],
            IssueType.WARNING: [
                "warning",
                "deprecated",
                "obsolete",
                "предупреждение",
                "устарел",
            ],
            IssueType.PERFORMANCE: [
                "slow",
                "timeout",
                "performance",
                "lag",
                "delay",
                "медленно",
                "тормозит",
                "производительность",
            ],
            IssueType.SECURITY: [
                "security",
                "vulnerability",
                "breach",
                "unauthorized",
                "безопасность",
                "уязвимость",
                "несанкционированный",
            ],
            IssueType.CONFIGURATION: [
                "config",
                "setting",
                "parameter",
                "misconfigured",
                "конфигурация",
                "настройка",
                "параметр",
            ],
            IssueType.DATABASE: [
                "database",
                "sql",
                "query",
                "table",
                "index",
                "база данных",
                "запрос",
                "таблица",
                "индекс",
            ],
            IssueType.NETWORK: [
                "network",
                "connection",
                "socket",
                "timeout",
                "dns",
                "сеть",
                "соединение",
                "подключение",
            ],
        }

    def classify(self, issue: Issue) -> IssueClassification:
        """
        Classify issue by type.

        Args:
            issue: Issue to classify

        Returns:
            Issue classification with confidence score
        """
        # Combine title and description for analysis
        text = f"{issue.title} {issue.description}".lower()

        # Extract keywords
        keywords = self._extract_keywords(text)

        # Extract entities (simplified)
        entities = self._extract_entities(text)

        # Calculate scores for each type
        type_scores = {}
        for issue_type, type_keywords in self.type_keywords.items():
            score = sum(1 for keyword in type_keywords if keyword in text)
            type_scores[issue_type] = score

        # Get best match
        if max(type_scores.values()) == 0:
            classified_type = IssueType.UNKNOWN
            confidence = 0.0
            reasoning = ["No matching keywords found"]
        else:
            classified_type = max(type_scores, key=type_scores.get)
            total_keywords = sum(type_scores.values())
            confidence = type_scores[classified_type] / max(1, total_keywords)
            reasoning = [
                f"Found {type_scores[classified_type]} {classified_type.value} keywords",
                f"Confidence: {confidence:.2f}",
            ]

        return IssueClassification(
            issue=issue,
            classified_type=classified_type,
            confidence=confidence,
            keywords=keywords,
            entities=entities,
            reasoning=reasoning,
        )

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text."""
        # Simple keyword extraction (words > 4 chars)
        words = re.findall(r"\b\w{5,}\b", text.lower())
        # Get unique words
        return list(set(words))[:20]  # Limit to 20

    def _extract_entities(self, text: str) -> Dict[str, str]:
        """Extract entities like error codes, file paths, etc."""
        entities = {}

        # Extract error codes (e.g., ERR-1234, ERROR_CODE)
        error_codes = re.findall(r"\b[A-Z]{3,}_?\d+\b", text.upper())
        if error_codes:
            entities["error_codes"] = ", ".join(error_codes[:3])

        # Extract file paths
        file_paths = re.findall(r"[/\\][\w/\\.-]+", text)
        if file_paths:
            entities["file_paths"] = ", ".join(file_paths[:2])

        # Extract IP addresses
        ips = re.findall(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", text)
        if ips:
            entities["ip_addresses"] = ", ".join(ips[:2])

        return entities

    def batch_classify(self, issues: List[Issue]) -> List[IssueClassification]:
        """
        Classify multiple issues.

        Args:
            issues: List of issues

        Returns:
            List of classifications
        """
        return [self.classify(issue) for issue in issues]
