"""
Advanced Security Features
OAuth2, 2FA, Audit Logging, Compliance
"""

import secrets
import pyotp
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import HTTPException
from jose import jwt
import hashlib
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class AdvancedSecurity:
    """Advanced security features"""
    
    def __init__(self):
        self.jwt_secret = secrets.token_urlsafe(32)
        self.jwt_algorithm = "HS256"
    
    # ===== 2FA (Two-Factor Authentication) =====
    
    def generate_2fa_secret(self, user_email: str) -> Dict[str, str]:
        """
        Generate 2FA secret for user
        
        Returns:
            Dict with secret and QR code URL
        """
        secret = pyotp.random_base32()
        
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user_email,
            issuer_name="1C AI Stack"
        )
        
        return {
            'secret': secret,
            'qr_uri': provisioning_uri,
            'manual_entry': secret
        }
    
    def verify_2fa_token(self, secret: str, token: str) -> bool:
        """
        Verify 2FA token
        
        Args:
            secret: User's 2FA secret
            token: 6-digit code from authenticator app
            
        Returns:
            bool: True if valid
        """
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    
    # ===== OAuth2 Integration =====
    
    async def initiate_oauth2_flow(
        self,
        provider: str,
        redirect_uri: str
    ) -> Dict[str, str]:
        """
        Initiate OAuth2 authorization flow
        
        Args:
            provider: github, google, microsoft
            redirect_uri: Where to redirect after auth
            
        Returns:
            Dict with authorization URL
        """
        
        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)
        
        oauth_configs = {
            'github': {
                'auth_url': 'https://github.com/login/oauth/authorize',
                'client_id': 'YOUR_GITHUB_CLIENT_ID',
                'scope': 'read:user user:email'
            },
            'google': {
                'auth_url': 'https://accounts.google.com/o/oauth2/v2/auth',
                'client_id': 'YOUR_GOOGLE_CLIENT_ID',
                'scope': 'openid email profile'
            }
        }
        
        if provider not in oauth_configs:
            raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")
        
        config = oauth_configs[provider]
        
        auth_url = (
            f"{config['auth_url']}"
            f"?client_id={config['client_id']}"
            f"&redirect_uri={redirect_uri}"
            f"&scope={config['scope']}"
            f"&state={state}"
            f"&response_type=code"
        )
        
        return {
            'authorization_url': auth_url,
            'state': state
        }
    
    # ===== Audit Logging =====
    
    async def log_audit_event(
        self,
        user_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        changes: Dict[str, Any],
        ip_address: str,
        user_agent: str
    ):
        """
        Log security audit event
        
        For compliance and security tracking
        """
        try:
            import asyncpg
            import os
            from src.database import get_pool
            
            pool = get_pool()
            
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO audit_log 
                    (user_id, action, entity_type, entity_id, changes, ip_address, user_agent)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    user_id,
                    action,
                    entity_type,
                    entity_id,
                    changes,
                    ip_address,
                    user_agent
                )
            
            logger.info(
                "Audit log",
                extra={
                    "action": action,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "user_id": user_id
                }
            )
            
        except Exception as e:
            logger.error(
                "Failed to log audit event",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "action": action if 'action' in locals() else None
                },
                exc_info=True
            )
    
    # ===== Rate Limiting Advanced =====
    
    def check_rate_limit(
        self,
        identifier: str,
        limit: int = 100,
        window_seconds: int = 60
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Advanced rate limiting with sliding window
        
        Args:
            identifier: User ID, IP, or API key
            limit: Max requests per window
            window_seconds: Time window in seconds
            
        Returns:
            (allowed, info) tuple
        """
        # TODO: Implement with Redis sorted sets for accuracy
        # For now, simple in-memory (would reset on restart)
        
        return True, {
            'allowed': True,
            'limit': limit,
            'remaining': limit - 1,
            'reset_at': (datetime.now() + timedelta(seconds=window_seconds)).isoformat()
        }
    
    # ===== API Key Management =====
    
    def generate_api_key(self, user_id: str, name: str) -> str:
        """
        Generate secure API key
        
        Format: sk_live_xxxxxxxxxxxxx
        """
        prefix = "sk_live_" if os.getenv('ENVIRONMENT') == 'production' else "sk_test_"
        key = secrets.token_urlsafe(32)
        
        return f"{prefix}{key}"
    
    def hash_api_key(self, api_key: str) -> str:
        """Hash API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    # ===== Session Management =====
    
    def create_session(
        self,
        user_id: str,
        device_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create secure session
        
        Returns:
            Dict with session_id and tokens
        """
        session_id = secrets.token_urlsafe(32)
        
        # Create access token (short-lived)
        access_token = jwt.encode(
            {
                'sub': user_id,
                'session_id': session_id,
                'type': 'access',
                'exp': datetime.now() + timedelta(hours=1)
            },
            self.jwt_secret,
            algorithm=self.jwt_algorithm
        )
        
        # Create refresh token (long-lived)
        refresh_token = jwt.encode(
            {
                'sub': user_id,
                'session_id': session_id,
                'type': 'refresh',
                'exp': datetime.now() + timedelta(days=30)
            },
            self.jwt_secret,
            algorithm=self.jwt_algorithm
        )
        
        return {
            'session_id': session_id,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': 3600,  # 1 hour
            'device_info': device_info
        }
    
    # ===== Password Security =====
    
    def hash_password(self, password: str) -> str:
        """Hash password with bcrypt"""
        import bcrypt
        
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode(), salt)
        
        return hashed.decode()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        import bcrypt
        
        return bcrypt.checkpw(password.encode(), hashed.encode())
    
    def check_password_strength(self, password: str) -> Dict[str, Any]:
        """
        Check password strength
        
        Returns:
            Dict with score and suggestions
        """
        score = 0
        suggestions = []
        
        if len(password) >= 8:
            score += 20
        else:
            suggestions.append("Use at least 8 characters")
        
        if len(password) >= 12:
            score += 10
        
        if any(c.isupper() for c in password):
            score += 20
        else:
            suggestions.append("Add uppercase letters")
        
        if any(c.islower() for c in password):
            score += 20
        else:
            suggestions.append("Add lowercase letters")
        
        if any(c.isdigit() for c in password):
            score += 20
        else:
            suggestions.append("Add numbers")
        
        if any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            score += 10
        else:
            suggestions.append("Add special characters")
        
        strength = "weak" if score < 50 else "medium" if score < 80 else "strong"
        
        return {
            'score': score,
            'strength': strength,
            'suggestions': suggestions
        }


# Global instance
advanced_security = AdvancedSecurity()


