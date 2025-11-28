# [NEXUS IDENTITY] ID: 7823286099455197134 | DATE: 2025-11-19

"""
API Schemas for Authentication module.
"""

from typing import Optional

from pydantic import BaseModel


class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class OAuthCallbackRequest(BaseModel):
    """Request model для OAuth callback"""

    code: str
    state: str


class OAuthAuthorizeResponse(BaseModel):
    """Response model для authorize endpoint"""

    authorization_url: str
    provider: str


class OAuthCallbackResponse(BaseModel):
    """Response model для callback endpoint"""

    status: str
    provider: str
    user_id: int
    expires_in: int


class OAuthStatusResponse(BaseModel):
    """Response model для status endpoint"""

    connected: bool
    provider: str
    expires_at: Optional[str] = None


class OAuthDisconnectResponse(BaseModel):
    """Response model для disconnect endpoint"""

    status: str
    provider: str
