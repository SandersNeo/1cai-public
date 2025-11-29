class ProjectManagerError(Exception):
    """Base exception for Project Manager module."""
    pass

class TaskNotFound(ProjectManagerError):
    """Raised when a task cannot be found."""
    def __init__(self, task_id: str):
        self.message = f"Task with ID {task_id} not found."
        super().__init__(self.message)

class SprintPlanningError(ProjectManagerError):
    """Raised when sprint planning fails (e.g. capacity exceeded)."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class InvalidEstimationError(ProjectManagerError):
    """Raised when estimation input is invalid."""
    pass
