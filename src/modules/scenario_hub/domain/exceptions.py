class ScenarioHubError(Exception):
    """Base exception for Scenario Hub module."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class ScenarioNotFound(ScenarioHubError):
    """Raised when a scenario is not found."""
    pass

class ExecutionError(ScenarioHubError):
    """Raised when scenario execution fails."""
    pass

class InvalidScenarioError(ScenarioHubError):
    """Raised when scenario definition is invalid."""
    pass
