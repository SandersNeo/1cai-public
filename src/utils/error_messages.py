"""
Standardized Error Messages
Версия: 2.0.0

Улучшения:
- Полный набор сообщений об ошибках
- Поддержка форматирования
- Мультиязычность (готовность)
"""

from typing import Dict, Optional

class ErrorMessages:
    """
    Centralized error messages (English)
    
    Best practices:
    - User-friendly messages
    - Consistent formatting
    - Support for parameter substitution
    """
    
    # Authentication
    AUTH_INVALID_CREDENTIALS = "Invalid email or password. Please check your credentials and try again."
    AUTH_TOKEN_EXPIRED = "Your session has expired. Please log in again."
    AUTH_TOKEN_INVALID = "Invalid authentication token. Please log in again."
    AUTH_REQUIRED = "Authentication required. Please log in to access this resource."
    AUTH_INSUFFICIENT_PERMISSIONS = "You don't have permission to perform this action."
    
    # Rate Limiting
    RATE_LIMIT_EXCEEDED = "Too many requests. Please wait {seconds} seconds before trying again."
    
    # Database
    DB_CONNECTION_ERROR = "We're experiencing technical difficulties. Please try again in a few minutes."
    DB_QUERY_ERROR = "Unable to process your request. Please try again or contact support."
    DB_NOT_FOUND = "The requested resource was not found."
    
    # Validation
    VALIDATION_ERROR = "Invalid input. Please check your data and try again."
    VALIDATION_EMAIL_INVALID = "Please enter a valid email address."
    VALIDATION_REQUIRED_FIELD = "{field} is required."
    VALIDATION_MIN_LENGTH = "{field} must be at least {min} characters."
    VALIDATION_MAX_LENGTH = "{field} must not exceed {max} characters."
    VALIDATION_CODE_TOO_LONG = "Code is too long. Maximum length: {max_length} characters."
    VALIDATION_CODE_EMPTY = "Code cannot be empty."
    VALIDATION_INVALID_LANGUAGE = "Unsupported language: {language}. Supported: {supported}."
    VALIDATION_INVALID_CONFIG_NAME = "Invalid configuration name."
    VALIDATION_PATH_TRAVERSAL = "Invalid path detected. Path traversal is not allowed."
    
    # External Services
    EXTERNAL_API_ERROR = "External service temporarily unavailable. Please try again later."
    OPENAI_API_ERROR = "AI service is temporarily unavailable. Please try again in a few moments."
    STRIPE_API_ERROR = "Payment processing is temporarily unavailable. Please try again later."
    
    # Business Logic
    TENANT_NOT_FOUND = "Organization not found."
    PROJECT_NOT_FOUND = "Project not found."
    USER_NOT_FOUND = "User not found."
    INSUFFICIENT_QUOTA = "Insufficient quota. Please upgrade your plan."
    
    # ML/AI
    ML_MODEL_NOT_LOADED = "ML model is not loaded. Please try again later."
    AI_SERVICE_UNAVAILABLE = "AI service is temporarily unavailable. Please try again later."
    
    # Generic
    INTERNAL_ERROR = "An unexpected error occurred. We've been notified and are working on it."
    NOT_IMPLEMENTED = "This feature is not yet available. Coming soon!"
    
    @staticmethod
    def format(message: str, **kwargs) -> str:
        """
        Format error message with parameters с input validation
        
        Best practice: Safe string formatting with validation
        """
        # Input validation
        if not isinstance(message, str):
            return str(message) if message else ""
        
        # Limit message length (prevent DoS)
        max_message_length = 10000
        if len(message) > max_message_length:
            message = message[:max_message_length]
        
        # Validate kwargs (prevent injection)
        safe_kwargs = {}
        for key, value in kwargs.items():
            if isinstance(key, str) and len(key) <= 100:
                # Convert value to string and limit length
                str_value = str(value)
                if len(str_value) > 1000:
                    str_value = str_value[:1000]
                safe_kwargs[key] = str_value
        
        try:
            return message.format(**safe_kwargs)
        except (KeyError, ValueError) as e:
            # If formatting fails, return original message
            return message
    
    @staticmethod
    def with_suggestion(error: str, suggestion: str, action_url: Optional[str] = None) -> Dict:
        """Create error response with helpful suggestion"""
        response = {
            "error": error,
            "suggestion": suggestion,
        }
        
        if action_url:
            response["action"] = {
                "label": "Learn more",
                "url": action_url
            }
        
        return response
    
    @staticmethod
    def with_support(error: str, error_id: str) -> Dict:
        """Create error response with support info"""
        return {
            "error": error,
            "error_id": error_id,
            "support": {
                "message": "If the problem persists, contact support with this error ID.",
                "email": "support@1c-ai.com",
                "docs": "https://docs.1c-ai.com/troubleshooting"
            }
        }


# Convenience functions
def auth_error(message: str = None) -> Dict:
    """Standard authentication error"""
    return {
        "error": message or ErrorMessages.AUTH_INVALID_CREDENTIALS,
        "suggestion": "Check your credentials or reset your password.",
        "action": {
            "label": "Reset password",
            "url": "/reset-password"
        }
    }


def rate_limit_error(retry_after: int) -> Dict:
    """Standard rate limit error"""
    return {
        "error": ErrorMessages.format(ErrorMessages.RATE_LIMIT_EXCEEDED, seconds=retry_after),
        "retry_after": retry_after,
        "suggestion": f"Please wait {retry_after} seconds before making more requests."
    }


def quota_exceeded_error(current: int, limit: int) -> Dict:
    """Quota exceeded error"""
    return {
        "error": ErrorMessages.INSUFFICIENT_QUOTA,
        "current_usage": current,
        "plan_limit": limit,
        "suggestion": "Upgrade your plan to increase limits.",
        "action": {
            "label": "View plans",
            "url": "/pricing"
        }
    }


def internal_error(error_id: str, details: str = None) -> Dict:
    """Internal server error"""
    response = {
        "error": ErrorMessages.INTERNAL_ERROR,
        "error_id": error_id,
        "support": {
            "message": "Please contact support with this error ID if the issue persists.",
            "email": "support@1c-ai.com"
        }
    }
    
    # Only include details in development
    import os
    if os.getenv("ENVIRONMENT") == "development" and details:
        response["details"] = details
    
    return response


