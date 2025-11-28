# [NEXUS IDENTITY] ID: 3979493474409353629 | DATE: 2025-11-19


class LLMNotConfiguredError(RuntimeError):
    """Raised when an LLM client is not configured with credentials."""


class LLMCallError(RuntimeError):
    """Raised when an LLM call fails."""
