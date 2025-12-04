from typing import AsyncIterator, Optional, Sequence, Tuple
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint, CheckpointMetadata, CheckpointTuple
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
import os


class PostgresCheckpointer:
    """
    Wrapper around LangGraph's AsyncPostgresSaver.
    Ensures the checkpointer is initialized and connected.
    """

    def __init__(self):
        # Resolve DB_URL at runtime to respect os.environ changes (e.g. in tests)
        self.connection_string = os.getenv(
            "DATABASE_URL", "postgresql://admin:change_me_in_prod@postgres:5432/enterprise_os"
        )
        self.saver = None
        self.saver_cm = None

    async def setup(self):
        """
        Initializes the connection pool and creates tables if needed.
        """
        # AsyncPostgresSaver.from_conn_string returns an async context manager
        self.saver_cm = AsyncPostgresSaver.from_conn_string(self.connection_string)
        self.saver = await self.saver_cm.__aenter__()
        await self.saver.setup()
        return self.saver

    async def close(self):
        if self.saver_cm:
            await self.saver_cm.__aexit__(None, None, None)

    async def get_saver(self) -> AsyncPostgresSaver:
        if not self.saver:
            await self.setup()
        return self.saver
