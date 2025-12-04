from fastapi import APIRouter, HTTPException
from src.modules.ai_orchestration.domain.models import GraphConfig, AgentState
from src.modules.ai_orchestration.services.nodes import GraphNodes
from src.modules.ai_orchestration.services.graph_builder import GraphBuilder

router = APIRouter(prefix="/orchestrate", tags=["AI Orchestration"])

# Initialize Graph (Singleton for now, in real app use Dependency Injection)
nodes = GraphNodes()
builder = GraphBuilder(nodes)
graph = builder.build()

@router.post("/run")
async def run_workflow(config: GraphConfig, initial_message: str):
    """
    Triggers the execution of the LangGraph workflow.
    """
    try:
        initial_state: AgentState = {
            "messages": [{"role": "user", "content": initial_message}],
            "context": {"thread_id": config.thread_id},
            "next_step": "reason",
            "scratchpad": {}
        }
        
        # Run the graph
        # Note: In a real async environment, we might want to run this in background
        # or use astream events. For MVP, we await the result.
        result = await graph.ainvoke(initial_state)
        
        return {
            "status": "success",
            "thread_id": config.thread_id,
            "final_state": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/state/{thread_id}")
async def get_state(thread_id: str):
    """
    Retrieves the current state of a thread (for Time Travel/Debugging).
    Placeholder for persistence integration.
    """
    return {"status": "not_implemented_yet", "thread_id": thread_id}
