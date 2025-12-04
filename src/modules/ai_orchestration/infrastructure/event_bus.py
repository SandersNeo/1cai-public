import logging
from typing import Set
from src.infrastructure.event_bus import EventHandler, Event, EventType
from src.modules.ai_orchestration.services.nodes import GraphNodes
from src.modules.ai_orchestration.services.graph_builder import GraphBuilder
from src.modules.ai_orchestration.domain.models import AgentState

logger = logging.getLogger(__name__)

class AIOrchestratorConsumer(EventHandler):
    """
    Consumes events from NATS and triggers AI workflows.
    """
    def __init__(self):
        self.nodes = GraphNodes() # Uses LLMFactory internally
        self.builder = GraphBuilder(self.nodes)
        self.graph = self.builder.build()

    @property
    def event_types(self) -> Set[EventType]:
        return {EventType.AI_AGENT_STARTED}

    async def handle(self, event: Event) -> None:
        """
        Handles incoming events.
        """
        logger.info(f"AIOrchestrator received event: {event.type.value} | ID: {event.id}")
        
        if event.type == EventType.AI_AGENT_STARTED:
            await self._handle_agent_start(event)

    async def _handle_agent_start(self, event: Event):
        """
        Triggers the agent workflow based on the event payload.
        """
        try:
            initial_message = event.payload.get("message", "Hello from Event Bus")
            thread_id = event.payload.get("thread_id", "event-bus-thread")
            
            logger.info(f"Starting workflow for thread: {thread_id}")
            
            initial_state: AgentState = {
                "messages": [{"role": "user", "content": initial_message}],
                "context": {"thread_id": thread_id, "source": "nats"},
                "next_step": "reason",
                "scratchpad": {}
            }
            
            # Execute Graph
            # Note: In production, this should be a background task or separate service
            result = await self.graph.ainvoke(initial_state)
            
            logger.info(f"Workflow completed. Final message: {result['messages'][-1].content}")
            
        except Exception as e:
            logger.error(f"Error executing workflow: {e}", exc_info=True)
