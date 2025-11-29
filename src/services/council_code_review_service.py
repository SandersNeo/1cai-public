"""
Council Service for Code Review

Integrates LLM Council with code review process.
"""

from typing import Dict, List, Optional





class CouncilCodeReviewService:
    """
    Code review service using LLM Council.

    Multiple agents review code independently, then synthesize findings.
    """

    def __init__(self):
        """Initialize council code review service"""
        from src.ai.orchestrator import get_orchestrator
        self.orchestrator = get_orchestrator()

    async def review_with_council(self, code: str, context: Optional[Dict] = None) -> Dict:
        """
        Review code using council of agents.

        Args:
            code: Code to review
            context: Optional context (language, framework, etc.)

        Returns:
            Council review result
        """
        if not self.orchestrator.council:
            raise ValueError("Council not available")

        context = context or {}

        # Create review query
        query = self._create_review_query(code, context)

        # Use council for review
        result = await self.orchestrator.process_query_with_council(
            query=query, context=context, council_config={
                "models": ["kimi", "qwen", "gigachat"], "chairman": "kimi"}
        )

        # Parse review results
        review = self._parse_review_result(result)

        return review

    def _create_review_query(self, code: str, context: Dict) -> str:
        """
        Create review query for council.

        Args:
            code: Code to review
            context: Context

        Returns:
            Review query
        """
        language = context.get("language", "BSL")

        query = f"""Review the following {language} code for:
1. **Correctness** — Are there any bugs or errors?
2. **Best Practices** — Does it follow {language} best practices?
3. **Performance** — Are there any performance issues?
4. **Security** — Are there any security vulnerabilities?
5. **Maintainability** — Is the code readable and maintainable?

Code to review:
```{language.lower()}
{code}
```

Provide a detailed review with specific issues and recommendations."""

        return query

    def _parse_review_result(self, result: Dict) -> Dict:
        """
        Parse council review result.

        Args:
            result: Council result

        Returns:
            Parsed review
        """
        return {
            "final_review": result.get("final_answer", ""),
            "individual_reviews": result.get("individual_opinions", []),
            "consensus": result.get("chairman_synthesis", ""),
            "metadata": result.get("metadata", {}),
            "issues": self._extract_issues(result.get("final_answer", "")),
        }

    def _extract_issues(self, review_text: str) -> List[Dict]:
        """
        Extract issues from review text.

        Args:
            review_text: Review text

        Returns:
            List of issues
        """
        # Simple extraction (can be improved with NLP)
        issues = []

        # Look for numbered issues
        import re

        pattern = r"\d+\.\s*\*\*([^*]+)\*\*[:\s]*([^\n]+)"
        matches = re.findall(pattern, review_text)

        for category, description in matches:
            issues.append(
                {
                    "category": category.strip(),
                    "description": description.strip(),
                    "severity": "medium",  # TODO: Determine severity
                }
            )

        return issues


# Global instance
council_code_review_service = CouncilCodeReviewService()
