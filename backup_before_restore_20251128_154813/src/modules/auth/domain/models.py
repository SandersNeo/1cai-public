# [NEXUS IDENTITY] ID: 2068138963340429857 | DATE: 2025-11-19

"""
Domain models for Authentication module.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class UserCredentials(BaseModel):
    """User credentials model."""

    username: str
    password: str
    user_id: str
    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    full_name: Optional[str] = None
    email: Optional[str] = None


class CurrentUser(BaseModel):
    """Current authenticated user model."""

    user_id: str
    username: str
    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    full_name: Optional[str] = None
    email: Optional[str] = None

    def has_role(self, *required_roles: str) -> bool:
        return any(role in self.roles for role in required_roles)

    def has_permission(self, *required_permissions: str) -> bool:
        return any(
            permission in self.permissions for permission in required_permissions
        )
