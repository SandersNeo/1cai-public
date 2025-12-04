# AI Orchestration Module

**Purpose**: This module implements the core reasoning engine for 1C AI Agents using **LangGraph**. It replaces the legacy `AgentExecutor` with a stateful, cyclic graph architecture.

## Architecture

This module follows **Clean Architecture** principles:

- **Domain**: Contains `AgentState` (TypedDict) and core entities. No external dependencies.
- **Services**: Contains the business logic for the Graph (`GraphBuilder`, `Nodes`). Depends on Domain.
- **API**: FastAPI routes to expose the orchestrator. Depends on Services.
- **Infrastructure**: Checkpointing and external integrations.

## Key Components

- **StateGraph**: The core graph definition.
- **Nodes**:
  - `Planner`: Decides the high-level plan.
  - `Executor`: Executes tools.
  - `Reflector`: Critiques the output.
- **Checkpointer**: Persists state to Postgres (via `pgvector` infrastructure).

## Usage

```python
from src.modules.ai_orchestration.services.workflow import Orchestrator

orchestrator = Orchestrator()
result = await orchestrator.run(input="Analyze this 1C code")
```
