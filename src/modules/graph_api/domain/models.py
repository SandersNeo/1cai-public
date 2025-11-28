import re
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator

MAX_SEMANTIC_QUERY_LENGTH = 5000


class SemanticSearchRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        max_length=MAX_SEMANTIC_QUERY_LENGTH,
        description="Search query",
    )
    configuration: Optional[str] = Field(
        None, max_length=200, description="Configuration filter")
    limit: int = Field(10, ge=1, le=100, description="Maximum results")

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Sanitize query to prevent injection"""
        v = re.sub(r'[<>"\'"]', "", v)
        sanitized = v.strip()
        if len(sanitized) > MAX_SEMANTIC_QUERY_LENGTH:
            raise ValueError(
                f"Query too long. Maximum length: {MAX_SEMANTIC_QUERY_LENGTH} characters")
        return sanitized

    @field_validator("configuration")
    @classmethod
    def validate_configuration(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize configuration name"""
        if v:
            v = v.replace("..", "").replace("/", "").replace("\\", "")
            return v.strip()
        return v


class GraphQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=5000, description="Cypher query")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Query parameters")

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Basic validation for Cypher query (prevent dangerous operations)"""
        v = v.strip()

        dangerous_patterns = [
            r"\bDROP\b",
            r"\bDELETE\b",
            r"\bDETACH\b",
            r"\bREMOVE\b",
            r"\bCREATE\s+INDEX\b",
            r"\bCREATE\s+CONSTRAINT\b",
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError(f"Dangerous operation detected in query: {pattern}")

        return v


class FunctionDependenciesRequest(BaseModel):
    module_name: str = Field(..., min_length=1, max_length=200,
                             description="Module name")
    function_name: str = Field(..., min_length=1, max_length=200,
                               description="Function name")

    @field_validator("module_name", "function_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Sanitize name to prevent injection"""
        if not re.match(r"^[a-zA-Z0-9_.-]+$", v):
            raise ValueError("Invalid characters in name")
        return v.strip()
