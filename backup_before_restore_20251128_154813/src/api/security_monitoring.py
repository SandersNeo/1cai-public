# [NEXUS IDENTITY] ID: -1870656699795604280 | DATE: 2025-11-19

"""
Security Monitoring API (Legacy)

DEPRECATED: This module has been refactored into Clean Architecture.
Use src.modules.security_monitoring instead.
"""
from src.modules.security_monitoring.api.routes import router

__all__ = ["router"]
