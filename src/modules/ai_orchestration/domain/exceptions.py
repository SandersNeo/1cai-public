class GraphExecutionError(Exception):
    """Base exception for graph execution errors."""

    pass


class NodeExecutionError(GraphExecutionError):
    """Raised when a specific node fails to execute."""

    def __init__(self, node_name: str, original_error: Exception):
        self.node_name = node_name
        self.original_error = original_error
        super().__init__(f"Node '{node_name}' failed: {str(original_error)}")


class StateValidationError(GraphExecutionError):
    """Raised when the graph state is invalid."""

    pass
