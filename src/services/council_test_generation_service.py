"""
Council Test Generation Service

Integrates LLM Council with test generation.
"""

from typing import Dict, Optional





class CouncilTestGenerationService:
    """
    Test generation service using LLM Council.

    Multiple agents generate tests independently, then synthesize.
    """

    def __init__(self):
        """Initialize council test generation service"""
        from src.ai.orchestrator import get_orchestrator
        self.orchestrator = get_orchestrator()

    async def generate_tests_with_council(self, code: str, context: Optional[Dict] = None) -> Dict:
        """
        Generate tests using council of agents.

        Args:
            code: Code to generate tests for
            context: Optional context

        Returns:
            Council test generation result
        """
        if not self.orchestrator.council:
            raise ValueError("Council not available")

        context = context or {}

        # Create test generation query
        query = self._create_test_query(code, context)

        # Use council for test generation
        result = await self.orchestrator.process_query_with_council(
            query=query, context=context, council_config={
                "models": ["kimi", "qwen", "gigachat"], "chairman": "kimi"}
        )

        # Parse test results
        tests = self._parse_test_result(result)

        return tests

    def _create_test_query(self, code: str, context: Dict) -> str:
        """
        Create test generation query for council.

        Args:
            code: Code to test
            context: Context

        Returns:
            Test generation query
        """
        language = context.get("language", "BSL")
        test_framework = context.get("test_framework", "xUnit")

        query = f"""Generate comprehensive unit tests for the following {language} code using {test_framework}.

Requirements:
1. **Coverage** — Test all functions and edge cases
2. **Assertions** — Include meaningful assertions
3. **Setup/Teardown** — Include necessary setup and cleanup
4. **Naming** — Use descriptive test names
5. **Documentation** — Add comments explaining test purpose

Code to test:
```{language.lower()}
{code}
```

Generate complete test suite with multiple test cases."""

        return query

    def _parse_test_result(self, result: Dict) -> Dict:
        """
        Parse council test generation result.

        Args:
            result: Council result

        Returns:
            Parsed tests
        """
        return {
            "test_code": result.get("final_answer", ""),
            "individual_tests": result.get("individual_opinions", []),
            "consensus": result.get("chairman_synthesis", ""),
            "metadata": result.get("metadata", {}),
            "test_cases": self._extract_test_cases(result.get("final_answer", "")),
        }

    def _extract_test_cases(self, test_code: str) -> list:
        """
        Extract test cases from generated code.

        Args:
            test_code: Generated test code

        Returns:
            List of test cases
        """
        # Simple extraction (can be improved)
        test_cases = []

        # Look for test functions
        import re

        pattern = r"(?:Процедура|Procedure|Function)\s+(\w+Test\w*)\s*\("
        matches = re.findall(pattern, test_code, re.IGNORECASE)

        for test_name in matches:
            test_cases.append({"name": test_name, "type": "unit_test"})

        return test_cases


# Global instance
council_test_generation_service = CouncilTestGenerationService()
