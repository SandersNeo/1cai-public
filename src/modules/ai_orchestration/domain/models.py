from typing import TypedDict, Annotated, List, Union, Dict, Any
import operator
from pydantic import BaseModel, Field

# --- Domain Models (Pydantic) ---

class GraphConfig(BaseModel):
    """Configuration for the graph execution."""
    thread_id: str = Field(..., description="Unique identifier for the conversation thread.")
    recursion_limit: int = Field(default=25, description="Maximum number of graph steps.")
    model_name: str = Field(default="gpt-4-turbo", description="LLM model to use.")

# --- State Definitions (TypedDict) ---

class AgentState(TypedDict):
    """
    The state of the agent graph.
    
    Attributes:
        messages: List of messages in the conversation history.
                  Annotated with operator.add to append messages instead of overwriting.
        context: Shared context dictionary (e.g., file contents, user info).
        next_step: The next step decided by the planner.
        scratchpad: Temporary storage for intermediate reasoning.
    """
    messages: Annotated[List[Dict[str, Any]], operator.add]
    context: Dict[str, Any]
    next_step: str
    scratchpad: Dict[str, Any]

class Plan(BaseModel):
    """Structured plan output from the Planner node."""
    steps: List[str]
    reasoning: str
