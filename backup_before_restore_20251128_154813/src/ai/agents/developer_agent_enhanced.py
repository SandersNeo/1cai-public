"""
Enhanced Developer AI Agent with Real LLM Integration

Extends DeveloperAISecure with:
- Real BSL code generation using Adaptive LLM Selector
- Self-Healing integration
- Code DNA integration
- Predictive code generation
"""

from typing import Any, Dict, List, Optional

from src.ai.agents.base_agent import AgentCapability, BaseAgent
from src.ai.agents.developer_agent_secure import DeveloperAISecure
from src.ai.llm import TaskType


class DeveloperAgentEnhanced(BaseAgent):
    """
    Enhanced Developer Agent with real LLM integration.

    Inherits from BaseAgent for unified interface and metrics.
    Uses DeveloperAISecure for security checks.
    """

    def __init__(self):
        super().__init__(
            agent_name="developer_agent_enhanced",
            capabilities=[
                AgentCapability.CODE_GENERATION,
                AgentCapability.CODE_REVIEW,
                AgentCapability.PERFORMANCE_OPTIMIZATION
            ]
        )

        # Security layer
        self.secure_agent = DeveloperAISecure()

        # BSL-specific patterns
        self.bsl_patterns = {
            "function": "Функция {name}({params}) Экспорт\n{body}\nКонецФункции",
            "procedure": "Процедура {name}({params}) Экспорт\n{body}\nКонецПроцедуры",
            "module": "// Модуль: {name}\n// Описание: {description}\n\n{content}",
        }
        # Revolutionary Components (stubs for future integration)
        # Will be initialized when Code DNA is available
        self.code_dna = None
        # Will be initialized when Predictive Gen is available
        self.predictive_gen = None

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process code generation request.

        Args:
            input_data: {
                "action": "generate_code" | "review_code" | "fix_code",
                "prompt": str,
                "language": "bsl" | "python" | etc,
                "context": optional dict
            }
        """
        action = input_data.get("action", "generate_code")

        if action == "generate_code":
            return await self.generate_bsl_code(
                prompt=input_data.get("prompt", ""),
                context=input_data.get("context", {})
            )
        elif action == "review_code":
            return await self.review_code(
                code=input_data.get("code", ""),
                context=input_data.get("context", {})
            )
        elif action == "fix_code":
            return await self.fix_code(
                code=input_data.get("code", ""),
                issues=input_data.get("issues", []),
                context=input_data.get("context", {})
            )
        else:
            return {"error": f"Unknown action: {action}"}

    async def generate_bsl_code(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate BSL code using LLM.

        Args:
            prompt: Code generation prompt
            context: Additional context

        Returns:
            Generated code with safety analysis
        """
        context = context or {}
        context["language"] = "bsl"
        context["framework"] = "1C:Enterprise 8.3"

        # Build BSL-specific prompt
        bsl_prompt = self._build_bsl_prompt(prompt, context)

        # Generate with LLM
        if self.llm_selector:
            try:
