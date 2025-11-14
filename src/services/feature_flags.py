"""
Feature Flags Service
Версия: 2.1.0

Улучшения:
- Structured logging
- Улучшена обработка ошибок
- Input validation
"""

from typing import Dict, Any, Optional
from enum import Enum
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class FeatureState(Enum):
    DISABLED = "disabled"
    ENABLED = "enabled"
    BETA = "beta"  # Enabled for beta users only
    PERCENTAGE = "percentage"  # Rollout percentage


class FeatureFlag:
    """Single feature flag"""
    
    def __init__(
        self,
        key: str,
        name: str,
        description: str,
        state: FeatureState = FeatureState.DISABLED,
        percentage: int = 0,
        beta_users: list = None
    ):
        self.key = key
        self.name = name
        self.description = description
        self.state = state
        self.percentage = percentage
        self.beta_users = beta_users or []


class FeatureFlagService:
    """
    Feature flag management
    
    Usage:
        flags = FeatureFlagService()
        
        if flags.is_enabled('new_ai_model', user_id='user-123'):
            # Use new model
        else:
            # Use old model
    """
    
    def __init__(self):
        self.flags: Dict[str, FeatureFlag] = {}
        self._init_flags()
    
    def _init_flags(self):
        """Initialize default flags"""
        
        # AI Features
        self.register(FeatureFlag(
            key='ai_response_caching',
            name='AI Response Caching',
            description='Cache AI responses for similar queries',
            state=FeatureState.ENABLED
        ))
        
        self.register(FeatureFlag(
            key='advanced_code_review',
            name='Advanced Code Review',
            description='Enhanced code review with auto-fix',
            state=FeatureState.BETA
        ))
        
        self.register(FeatureFlag(
            key='copilot_v2',
            name='Copilot V2',
            description='Next generation Copilot with better suggestions',
            state=FeatureState.PERCENTAGE,
            percentage=20  # 20% rollout
        ))
        
        # UI Features
        self.register(FeatureFlag(
            key='realtime_updates',
            name='Real-Time Updates',
            description='WebSocket-based real-time notifications',
            state=FeatureState.ENABLED
        ))
        
        self.register(FeatureFlag(
            key='dark_mode_v2',
            name='Dark Mode V2',
            description='Improved dark mode with more themes',
            state=FeatureState.DISABLED
        ))
        
        # Infrastructure
        self.register(FeatureFlag(
            key='distributed_tracing',
            name='Distributed Tracing',
            description='OpenTelemetry tracing',
            state=FeatureState.ENABLED
        ))
    
    def register(self, flag: FeatureFlag):
        """Register a feature flag с input validation"""
        # Input validation
        if not isinstance(flag, FeatureFlag):
            logger.warning(
                "Invalid flag type in register",
                extra={"flag_type": type(flag).__name__}
            )
            raise ValueError("flag must be a FeatureFlag instance")
        
        if not isinstance(flag.key, str) or not flag.key.strip():
            logger.warning(
                "Invalid flag key in register",
                extra={"key_type": type(flag.key).__name__ if flag.key else None}
            )
            raise ValueError("flag.key must be a non-empty string")
        
        # Limit key length (prevent DoS)
        max_key_length = 200
        if len(flag.key) > max_key_length:
            logger.warning(
                "Flag key too long in register",
                extra={"key_length": len(flag.key), "max_length": max_key_length}
            )
            raise ValueError(f"flag.key too long (max {max_key_length} characters)")
        
        self.flags[flag.key] = flag
        logger.info(
            "Feature flag registered",
            extra={
                "flag_key": flag.key,
                "state": flag.state.value,
                "name": flag.name
            }
        )
    
    def is_enabled(
        self,
        flag_key: str,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> bool:
        """
        Check if feature is enabled с input validation
        
        Args:
            flag_key: Feature flag key
            user_id: User ID (for beta/percentage checks)
            tenant_id: Tenant ID (for tenant-specific flags)
        
        Returns:
            True if feature is enabled for this user
        """
        # Input validation
        if not isinstance(flag_key, str) or not flag_key.strip():
            logger.warning(
                "Invalid flag_key in is_enabled",
                extra={"flag_key_type": type(flag_key).__name__ if flag_key else None}
            )
            return False
        
        # Limit key length (prevent DoS)
        max_key_length = 200
        if len(flag_key) > max_key_length:
            logger.warning(
                "Flag key too long in is_enabled",
                extra={"key_length": len(flag_key), "max_length": max_key_length}
            )
            return False
        
        if user_id is not None and not isinstance(user_id, str):
            logger.warning(
                "Invalid user_id type in is_enabled",
                extra={"user_id_type": type(user_id).__name__}
            )
            user_id = None
        
        if user_id and len(user_id) > 200:
            user_id = user_id[:200]
        
        if tenant_id is not None and not isinstance(tenant_id, str):
            logger.warning(
                "Invalid tenant_id type in is_enabled",
                extra={"tenant_id_type": type(tenant_id).__name__}
            )
            tenant_id = None
        
        if tenant_id and len(tenant_id) > 200:
            tenant_id = tenant_id[:200]
        
        if flag_key not in self.flags:
            logger.warning(
                "Unknown feature flag",
                extra={"flag_key": flag_key}
            )
            return False
        
        flag = self.flags[flag_key]
        
        # Simple enabled/disabled
        if flag.state == FeatureState.ENABLED:
            return True
        
        if flag.state == FeatureState.DISABLED:
            return False
        
        # Beta users only
        if flag.state == FeatureState.BETA:
            if user_id and user_id in flag.beta_users:
                return True
            return False
        
        # Percentage rollout
        if flag.state == FeatureState.PERCENTAGE:
            if not user_id:
                return False
            
            # Consistent hashing (same user always gets same result)
            hash_val = hash(f"{flag_key}:{user_id}") % 100
            return hash_val < flag.percentage
        
        return False
    
    def get_all_flags(self, user_id: Optional[str] = None) -> Dict[str, bool]:
        """Get all flags and their status for user с input validation"""
        # Input validation
        if user_id is not None:
            if not isinstance(user_id, str):
                logger.warning(
                    "Invalid user_id type in get_all_flags",
                    extra={"user_id_type": type(user_id).__name__}
                )
                user_id = None
            elif len(user_id) > 200:
                user_id = user_id[:200]
        
        logger.debug(
            "Getting all flags",
            extra={"user_id": user_id, "flags_count": len(self.flags)}
        )
        
        return {
            key: self.is_enabled(key, user_id=user_id)
            for key in self.flags.keys()
        }
    
    def update_flag(
        self,
        flag_key: str,
        state: FeatureState = None,
        percentage: int = None,
        beta_users: list = None
    ):
        """Update feature flag at runtime с input validation"""
        # Input validation
        if not isinstance(flag_key, str) or not flag_key.strip():
            logger.warning(
                "Invalid flag_key in update_flag",
                extra={"flag_key_type": type(flag_key).__name__ if flag_key else None}
            )
            raise ValueError("flag_key must be a non-empty string")
        
        # Limit key length (prevent DoS)
        max_key_length = 200
        if len(flag_key) > max_key_length:
            logger.warning(
                "Flag key too long in update_flag",
                extra={"key_length": len(flag_key), "max_length": max_key_length}
            )
            raise ValueError(f"flag_key too long (max {max_key_length} characters)")
        
        if flag_key not in self.flags:
            logger.warning(
                "Unknown flag in update_flag",
                extra={"flag_key": flag_key}
            )
            raise ValueError(f"Unknown flag: {flag_key}")
        
        flag = self.flags[flag_key]
        
        if state is not None:
            if not isinstance(state, FeatureState):
                logger.warning(
                    "Invalid state type in update_flag",
                    extra={"state_type": type(state).__name__}
                )
                raise ValueError("state must be a FeatureState enum")
            flag.state = state
        
        if percentage is not None:
            if not isinstance(percentage, int) or percentage < 0 or percentage > 100:
                logger.warning(
                    "Invalid percentage in update_flag",
                    extra={"percentage": percentage, "percentage_type": type(percentage).__name__}
                )
                raise ValueError("percentage must be an integer between 0 and 100")
            flag.percentage = percentage
        
        if beta_users is not None:
            if not isinstance(beta_users, list):
                logger.warning(
                    "Invalid beta_users type in update_flag",
                    extra={"beta_users_type": type(beta_users).__name__}
                )
                raise ValueError("beta_users must be a list")
            
            # Validate and sanitize beta_users
            validated_beta_users = []
            for user_id in beta_users:
                if isinstance(user_id, str) and user_id.strip() and len(user_id) <= 200:
                    validated_beta_users.append(user_id.strip())
            
            flag.beta_users = validated_beta_users
        
        logger.info(
            "Feature flag updated",
            extra={
                "flag_key": flag_key,
                "state": flag.state.value,
                "percentage": flag.percentage,
                "beta_users_count": len(flag.beta_users)
            }
        )


# Global instance
_feature_flags = None


def get_feature_flags() -> FeatureFlagService:
    """Get singleton feature flags service"""
    global _feature_flags
    if _feature_flags is None:
        _feature_flags = FeatureFlagService()
    return _feature_flags


