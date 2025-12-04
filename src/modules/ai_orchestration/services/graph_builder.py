from langgraph.graph import StateGraph, END
from src.modules.ai_orchestration.domain.models import AgentState, GraphConfig
from src.modules.ai_orchestration.services.nodes import GraphNodes


class GraphBuilder:
    """
    Constructs the LangGraph StateGraph.
    """

    def __init__(self, nodes: GraphNodes, checkpointer=None):
        self.nodes = nodes
        self.checkpointer = checkpointer

    def build(self):
        """
        Builds and compiles the state graph.
        """
        workflow = StateGraph(AgentState)

        # Add Nodes
        workflow.add_node("reason", self.nodes.reason_node)
        workflow.add_node("action", self.nodes.action_node)
        workflow.add_node("reflect", self.nodes.reflect_node)

        # Set Entry Point
        workflow.set_entry_point("reason")

        # Add Edges (Conditional Logic)
        workflow.add_conditional_edges("reason", self._decide_next_step, {"action": "action", "end": END})

        workflow.add_edge("action", "reflect")
        workflow.add_edge("reflect", "reason")  # Loop back

        # Compile with Checkpointer
        # Note: In a real app, checkpointer should be passed in or resolved via DI
        # For now, we return the graph, and the runner (API) will attach the checkpointer
        return workflow.compile(checkpointer=self.checkpointer) if self.checkpointer else workflow.compile()

    def _decide_next_step(self, state: AgentState) -> str:
        """Conditional logic to determine the next node."""
        return state.get("next_step", "end")
