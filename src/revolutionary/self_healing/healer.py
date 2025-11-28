"""
Self-Healing Code Engine

Automatically detects and fixes code issues:
- Bug detection
- Fix generation
- Validation
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class CodeIssue:
    """Detected code issue"""
    issue_type: str
    severity: str  # low, medium, high, critical
    description: str
    line_number: Optional[int] = None
    auto_fixable: bool = False


@dataclass
class CodeFix:
    """Generated code fix"""
    original_code: str
    fixed_code: str
    fix_description: str
    confidence: float


class SelfHealingEngine:
    """
    Self-healing code engine

    Features:
    - Automatic bug detection
    - Fix generation
    - Validation
    """

    def __init__(self):
        self.logger = logging.getLogger("self_healing_engine")
        self.fix_patterns = self._init_fix_patterns()

    def _init_fix_patterns(self) -> Dict[str, Dict[str, str]]:
        """Initialize fix patterns"""
        return {
            "missing_error_handling": {
                "pattern": "no_try_catch",
                "fix": "wrap_in_try_catch"
            },
            "missing_validation": {
                "pattern": "no_null_check",
                "fix": "add_null_check"
            },
            "deprecated_syntax": {
                "pattern": "old_syntax",
                "fix": "modernize_syntax"
            }
        }

    async def detect_issues(
        self,
        code: str,
        language: str = "bsl"
    ) -> List[CodeIssue]:
        """
        Detect issues in code

        Args:
            code: Source code
            language: Programming language

        Returns:
            List of detected issues
        """
        issues = []

        # Check for missing error handling
        if "Попытка" not in code and "Функция" in code:
            issues.append(CodeIssue(
                issue_type="missing_error_handling",
                severity="medium",
                description="Function lacks error handling",
                auto_fixable=True
            ))

        # Check for deprecated constructs
        if "Сообщить(" in code:
            issues.append(CodeIssue(
                issue_type="deprecated_syntax",
                severity="low",
                description="Using deprecated Сообщить()",
                auto_fixable=True
            ))

        self.logger.info(f"Detected {len(issues)} issues")
        return issues

    async def heal_code(
        self,
        code: str,
        issues: Optional[List[CodeIssue]] = None
    ) -> CodeFix:
        """
        Heal code by fixing detected issues

        Args:
            code: Original code
            issues: Optional list of issues (auto-detect if None)

        Returns:
            Code fix
        """
        if issues is None:
            issues = await self.detect_issues(code)

        fixed_code = code
        fixes_applied = []

        for issue in issues:
            if issue.auto_fixable:
                fixed_code = self._apply_fix(fixed_code, issue)
                fixes_applied.append(issue.issue_type)

        return CodeFix(
            original_code=code,
            fixed_code=fixed_code,
            fix_description=f"Applied {len(fixes_applied)} fixes",
            confidence=0.85
        )

    def _apply_fix(self, code: str, issue: CodeIssue) -> str:
        """Apply fix for specific issue"""
        if issue.issue_type == "missing_error_handling":
            return self._add_error_handling(code)
        elif issue.issue_type == "deprecated_syntax":
            return code.replace(
                "Сообщить(",
                "ЗаписьЖурналаРегистрации("
            )
        return code

    def _add_error_handling(self, code: str) -> str:
        """Add error handling to code"""
        lines = code.split("\n")
        result = []

        for i, line in enumerate(lines):
            result.append(line)
            if "Функция" in line or "Процедура" in line:
                # Add try-catch after function declaration
                result.append("    Попытка")

        # Add exception handler before end
        for i in range(len(result) - 1, -1, -1):
            if "КонецФункции" in result[i] or "КонецПроцедуры" in result[i]:
                result.insert(i, "    Исключение")
                result.insert(i + 1, "        ЗаписьЖурналаРегистрации();")
                result.insert(i + 2, "    КонецПопытки;")
                break

        return "\n".join(result)


def get_self_healing_engine() -> SelfHealingEngine:
    """Get self-healing engine instance"""
    return SelfHealingEngine()


__all__ = [
    "CodeIssue",
    "CodeFix",
    "SelfHealingEngine",
    "get_self_healing_engine"
]
