import asyncio
from datetime import datetime
from typing import Any, Dict

from src.services.documentation_generation_service import get_documentation_generator
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class DocumentationService:
    """Service for generating documentation from code."""

    def __init__(self) -> None:
        self.generator = get_documentation_generator()

    async def generate(
        self,
        code: str,
        language: str,
        function_name: str | None = None,
        format: str = "markdown",
        timeout: float = 60.0,
    ) -> Dict[str, Any]:
        """Generate documentation with timeout handling."""
        # Validate timeout
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            logger.warning(
                "Invalid timeout in generate_documentation",
                extra={"timeout": timeout, "timeout_type": type(timeout).__name__},
            )
            timeout = 60.0

        if timeout > 300:  # Max 5 minutes
            logger.warning("Timeout too large in generate_documentation",
                           extra={"timeout": timeout})
            timeout = 300.0

        # Validate inputs
        code = code.strip()
        if not code:
            raise ValueError("Code cannot be empty")

        max_code_length = 100000
        if len(code) > max_code_length:
            logger.warning(
                "Code too long in generate_documentation",
                extra={"code_length": len(code), "max_length": max_code_length},
            )
            raise ValueError(
                f"Code too long. Maximum length: {max_code_length} characters")

        supported_languages = ["bsl", "typescript", "javascript", "python"]
        if language not in supported_languages:
            logger.warning(
                "Unsupported language in generate_documentation",
                extra={
                    "language": language,
                    "supported": supported_languages,
                },
            )
            raise ValueError(
                f"Unsupported language: {language}. Supported: {', '.join(supported_languages)}")

        # Sanitize function name
        if function_name:
            if not isinstance(function_name, str):
                logger.warning(
                    "Invalid functionName type in generate_documentation",
                    extra={"functionName_type": type(function_name).__name__},
                )
                function_name = None
            else:
                function_name = function_name.strip()[:200]

        # Execute with timeout
        try:
            doc = await asyncio.wait_for(
                asyncio.to_thread(
                    self.generator.generate_documentation,
                    code=code,
                    language=language,
                    function_name=function_name,
                    format=format,
                ),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            logger.error(
                "Timeout generating documentation",
                extra={
                    "language": language,
                    "format": format,
                    "code_length": len(code),
                    "timeout": timeout,
                },
            )
            raise TimeoutError(
                f"Documentation generation timed out after {timeout} seconds")

        generation_id = f"doc-{datetime.now().timestamp()}"

        return {
            "title": doc.get("title", "Documentation"),
            "language": doc.get("language", language),
            "format": format,
            "content": doc.get("content", ""),
            "sections": doc.get("sections", []),
            "generationId": generation_id,
        }
