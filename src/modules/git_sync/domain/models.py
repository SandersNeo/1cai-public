from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class GitCommit(BaseModel):
    """Model representing a Git commit."""
    hash: str
    author: str
    message: str
    timestamp: datetime
    files: List[str]

class SyncStatus(BaseModel):
    """Model representing the synchronization status."""
    last_sync_time: datetime
    status: str  # 'success', 'failed', 'in_progress'
    details: Optional[str] = None
