# [NEXUS IDENTITY] ID: 2068138963340429857 | DATE: 2025-11-19

"""
Configuration for Authentication module.
"""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    """Authentication configuration (loaded from environment variables)."""

    jwt_secret: str = Field(default="CHANGE_ME")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=60)
    demo_users: Optional[str] = Field(default=None)
    service_tokens: Optional[str] = Field(default=None)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
