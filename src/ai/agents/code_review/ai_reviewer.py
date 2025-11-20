# [NEXUS IDENTITY] ID: 7560449087030259305 | DATE: 2025-11-19

"""
AI Code Reviewer - главный orchestrator
Координирует все проверки и генерирует review
"""

import os
from typing import List, Dict, Any
from datetime import datetime
from src.utils.structured_logging import StructuredLogger

from src.ai.agents.code_review.bsl_parser import BSLParser
from src.ai.agents.code_review.security_scanner import SecurityScanner
from src.ai.agents.code_review.performance_analyzer import PerformanceAnalyzer
from src.ai.agents.code_review.best_practices_checker import BestPracticesChecker

logger = StructuredLogger(__name__).logger


class AICodeReviewer:
    """
    AI Code Reviewer

    Автоматический review BSL кода с:
    - Security scanning
    - Performance analysis
    - Best practices checking
    - AI-powered suggestions
    """

    def __init__(self):
        self.parser = BSLParser()
        self.security_scanner = SecurityScanner()
        self.performance_analyzer = PerformanceAnalyzer()
        self.best_practices_checker = BestPracticesChecker()

        # LLM для глубокого анализа (опционально)
        self.llm_available = False
        try:
            # TODO: Integration with OpenAI or local LLM
            self.llm_api_key = os.getenv("OPENAI_API_KEY", "")
            if self.llm_api_key:
                self.llm_available = True
        except (OSError, Exception):
            pass

        logger.info("AI Code Reviewer initialized")

    async def review_code(
        self, code: str, filename: str = "unknown.bsl"
    ) -> Dict[str, Any]:
        """
        Review одного файла

        Args:
            code: BSL код
            filename: Имя файла

        Returns:
            Детальный review с issues и метриками
        """
        logger.info("Reviewing file", extra={"file_name": filename})

        # 1. Parse code
        try:
            ast = self.parser.parse_file(code)
        except Exception as e:
            logger.error(
                "Parsing error",
                extra={
                    "file_name": filename,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            return {"error": "Failed to parse code", "details": str(e)}

        # 2. Run all scanners
        security_issues = self.security_scanner.scan(code, ast)
        performance_issues = self.performance_analyzer.analyze(code, ast)
        bp_issues = self.best_practices_checker.check(code, ast)

        # 3. AI suggestions (if available)
        ai_suggestions = []
        if self.llm_available:
            ai_suggestions = await self._ai_deep_review(code, ast)

        # 4. Aggregate results
        all_issues = security_issues + performance_issues + bp_issues + ai_suggestions

        # 5. Calculate metrics
        metrics = self._calculate_metrics(all_issues, ast)

        # 6. Determine overall status
        overall_status = self._determine_status(all_issues)

        # 7. Generate summary
        summary = self._generate_summary(all_issues, metrics, overall_status)

        return {
            "filename": filename,
            "overall_status": overall_status,
            "summary": summary,
            "metrics": metrics,
            "issues": {
                "security": security_issues,
                "performance": performance_issues,
                "best_practices": bp_issues,
                "ai_suggestions": ai_suggestions,
            },
            "total_issues": len(all_issues),
            "reviewed_at": datetime.now().isoformat(),
        }

    async def review_pull_request(
        self, files_changed: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Review целого Pull Request

        Args:
            files_changed: [
                {'filename': 'Module.bsl', 'content': '...'}
            ]

        Returns:
            Aggregated review для всего PR
        """
        logger.info("Reviewing PR", extra={"files_count": len(files_changed)})

        file_reviews = []
        all_issues = []

        # Review каждого файла
        for file_data in files_changed:
            if not file_data["filename"].endswith(".bsl"):
                continue

            review = await self.review_code(
                code=file_data["content"], filename=file_data["filename"]
            )

            if "error" not in review:
                file_reviews.append(review)
                all_issues.extend(review.get("issues", {}).get("security", []))
                all_issues.extend(review.get("issues", {}).get("performance", []))
                all_issues.extend(review.get("issues", {}).get("best_practices", []))

        # Overall metrics
        overall_metrics = {
            "files_reviewed": len(file_reviews),
            "total_issues": len(all_issues),
            "critical": sum(1 for i in all_issues if i.get("severity") == "CRITICAL"),
            "high": sum(1 for i in all_issues if i.get("severity") == "HIGH"),
            "medium": sum(1 for i in all_issues if i.get("severity") == "MEDIUM"),
            "low": sum(1 for i in all_issues if i.get("severity") == "LOW"),
        }

        # Overall status
        if overall_metrics["critical"] > 0:
            overall_status = "CHANGES_REQUESTED"
        elif overall_metrics["high"] > 3:
            overall_status = "CHANGES_REQUESTED"
        elif overall_metrics["total_issues"] > 0:
            overall_status = "COMMENTED"
        else:
            overall_status = "APPROVED"

        # Generate PR summary
        pr_summary = self._generate_pr_summary(
            file_reviews, overall_metrics, overall_status
        )

        return {
            "overall_status": overall_status,
            "summary": pr_summary,
            "file_reviews": file_reviews,
            "metrics": overall_metrics,
            "reviewed_at": datetime.now().isoformat(),
        }

    async def _ai_deep_review(self, code: str, ast: Dict) -> List[Dict]:
        """AI глубокий анализ (опционально, требует LLM)"""
        # Placeholder для LLM integration
        # TODO: Integrate with OpenAI GPT-4 or local LLM
        return []

    def _calculate_metrics(self, issues: List[Dict], ast: Dict) -> Dict:
        """Расчет метрик качества кода"""
        return {
            "total_issues": len(issues),
            "critical": sum(1 for i in issues if i.get("severity") == "CRITICAL"),
            "high": sum(1 for i in issues if i.get("severity") == "HIGH"),
            "medium": sum(1 for i in issues if i.get("severity") == "MEDIUM"),
            "low": sum(1 for i in issues if i.get("severity") == "LOW"),
            "complexity": ast.get("total_complexity", 0),
            "loc": ast.get("loc", 0),
            "functions_count": ast.get("functions_count", 0),
        }

    def _determine_status(self, issues: List[Dict]) -> str:
        """Определение общего статуса"""
        critical_count = sum(1 for i in issues if i.get("severity") == "CRITICAL")
        high_count = sum(1 for i in issues if i.get("severity") == "HIGH")

        if critical_count > 0:
            return "CHANGES_REQUESTED"
        elif high_count > 3:
            return "CHANGES_REQUESTED"
        elif len(issues) > 0:
            return "COMMENTED"
        else:
            return "APPROVED"

    def _generate_summary(self, issues: List[Dict], metrics: Dict, status: str) -> str:
        """Генерация summary"""

        status_emoji = {"APPROVED": "✅", "COMMENTED": "💬", "CHANGES_REQUESTED": "⚠️"}

        summary = f"""
## {status_emoji.get(status, '🔍')} AI Code Review

**Status:** {status}

### 📊 Metrics
- **Total Issues:** {metrics['total_issues']}
  - 🔴 Critical: {metrics['critical']}
  - 🟠 High: {metrics['high']}
  - 🟡 Medium: {metrics['medium']}
  - 🟢 Low: {metrics['low']}

- **Code Complexity:** {metrics['complexity']}
- **Lines of Code:** {metrics['loc']}
- **Functions:** {metrics['functions_count']}
"""

        if metrics["critical"] > 0:
            summary += """
### ⚠️ CRITICAL Issues Found!

Обнаружены критичные проблемы безопасности!
Пожалуйста, исправьте перед merge.
"""

        if metrics["total_issues"] == 0:
            summary += """
### ✨ Excellent Code Quality!

Код соответствует всем best practices! 🎉
Нет критичных замечаний.
"""

        return summary

    def _generate_pr_summary(
        self, file_reviews: List[Dict], metrics: Dict, status: str
    ) -> str:
        """Генерация summary для PR"""

        status_emoji = {"APPROVED": "✅", "COMMENTED": "💬", "CHANGES_REQUESTED": "⚠️"}

        summary = f"""
## {status_emoji.get(status, '🔍')} AI Code Review Summary

**Overall Status:** {status}

### 📊 Review Metrics
- **Files Reviewed:** {metrics['files_reviewed']}
- **Total Issues Found:** {metrics['total_issues']}

**By Severity:**
- 🔴 Critical: {metrics['critical']}
- 🟠 High: {metrics['high']}  
- 🟡 Medium: {metrics['medium']}
- 🟢 Low: {metrics['low']}
"""

        if metrics["critical"] > 0:
            summary += "\n### ⚠️ Action Required\n\n"
            summary += "Найдены критичные проблемы безопасности. Merge заблокирован до исправления.\n"

        elif metrics["total_issues"] == 0:
            summary += "\n### ✨ Great Job!\n\n"
            summary += "Код отличного качества! Все проверки пройдены. 🎉\n"

        return summary
