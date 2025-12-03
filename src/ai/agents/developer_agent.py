"""
Developer Agent Implementation

This agent is responsible for code generation, refactoring, and code review tasks.
It acts as the primary interface for "writing code" within the 1C AI Stack.
It wraps the secure implementation (DeveloperAISecure) to ensure all changes
adhere to the Rule of Two and security standards.
"""

from typing import Any, Dict, List, Optional

from src.ai.agents.base_agent import AgentCapability, BaseAgent
from src.ai.agents.developer_agent_secure import DeveloperAISecure


class DeveloperAgent(BaseAgent):
    """
    Developer Agent - AI программист 1С.
    
    Capabilities:
    - CODE_GENERATION: Написание нового кода по требованиям
    - CODE_REVIEW: Проверка существующего кода
    - REFACTORING: Улучшение качества кода
    
    Security:
    - Uses DeveloperAISecure for all code operations
    - Enforces Rule of Two (Human Approval)
    """

    def __init__(self):
        super().__init__(
            agent_name="developer_agent",
            capabilities=[
                AgentCapability.CODE_GENERATION,
                AgentCapability.CODE_REVIEW,
                AgentCapability.PERFORMANCE_OPTIMIZATION
            ]
        )
        # Initialize the secure core
        self.secure_core = DeveloperAISecure()

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process developer tasks.
        
        Input Schema:
        {
            "action": "generate" | "review" | "refactor",
            "prompt": "Description of the task",
            "context": { ... },
            "code": "Optional code for review/refactor"
        }
        """
        action = input_data.get("action", "generate")
        prompt = input_data.get("prompt", "")
        context = input_data.get("context", {})
        
        if action == "generate":
            return self._handle_generation(prompt, context)
        elif action == "review":
            # For review, we might use a different logic or delegate to a specialized reviewer
            # For now, let's use the secure core's safety analysis as a review mechanism
            code_to_review = input_data.get("code", "")
            return self._handle_review(code_to_review)
        else:
            return {"error": f"Unknown action: {action}", "success": False}

    def _handle_generation(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle code generation request via Secure Core"""
        result = self.secure_core.generate_code(prompt, context)
        
        # Adapt result to standard agent format
        if result.get("blocked"):
            return {
                "success": False,
                "error": result.get("error"),
                "details": result
            }
            
        return {
            "success": True,
            "data": {
                "suggestion": result.get("suggestion"),
                "token": result.get("token"),
                "safety_report": result.get("safety"),
                "requires_approval": True
            }
        }

    def _handle_review(self, code: str) -> Dict[str, Any]:
        """Handle code review request"""
        safety_analysis = self.secure_core._analyze_code_safety(code)
        
        return {
            "success": True,
            "data": {
                "review_result": "Approved" if safety_analysis["safe"] else "Issues Found",
                "issues": safety_analysis["concerns"],
                "score": safety_analysis["score"]
            }
        }
