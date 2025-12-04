from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from src.modules.ai_orchestration.domain.models import AgentState, Plan
from src.modules.ai_orchestration.domain.exceptions import NodeExecutionError

from src.modules.ai_orchestration.infrastructure.llm import LLMFactory


class GraphNodes:
    """
    Encapsulates the logic for each node in the graph.
    Follows Clean Architecture: depends on Domain, but not on API/Infrastructure.
    """

    def __init__(self, llm=None):
        self.llm = llm or LLMFactory.create()

    async def reason_node(self, state: AgentState) -> Dict[str, Any]:
        """
        The 'Brain' node. Decides the next step based on context and history.
        """
        try:
            messages = state["messages"]
            # Call Real LLM
            response = await self.llm.ainvoke(messages)

            return {
                "messages": [response],
                "next_step": "action" if response.tool_calls else "end",
                "scratchpad": {"last_reasoning": response.content},
            }
        except Exception as e:
            raise NodeExecutionError("reason_node", e)

    async def action_node(self, state: AgentState) -> Dict[str, Any]:
        """
        The 'Hands' node. Executes tools requested by the reason_node.
        """
        try:
            # Logic to execute tools
            # For now, mock execution
            result = "Tool executed successfully"
            return {"messages": [AIMessage(content=f"Action result: {result}")], "next_step": "reflect"}
        except Exception as e:
            raise NodeExecutionError("action_node", e)

    async def reflect_node(self, state: AgentState) -> Dict[str, Any]:
        """
        The 'Critic' node. Reviews the action result and decides if it's satisfactory.
        """
        try:
            # Logic to critique result
            return {
                "messages": [AIMessage(content="Reflection: Result looks good.")],
                "next_step": "reason",  # Loop back to reason
            }
        except Exception as e:
            raise NodeExecutionError("reflect_node", e)
