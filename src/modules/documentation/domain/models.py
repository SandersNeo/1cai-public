from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class DocumentationRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=100000, description="Source code")
    language: str = Field(...,
                          description="Programming language (bsl, typescript, python)")
    functionName: Optional[str] = Field(
        None, max_length=200, description="Specific function name")
    format: Literal["markdown", "html", "plain"] = Field(
        "markdown", description="Output format")


class DocumentationResponse(BaseModel):
    title: str
    language: str
    format: str
    content: str
    sections: List[dict]
    generationId: str
