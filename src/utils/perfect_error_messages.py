# [NEXUS IDENTITY] ID: -45541752430501671 | DATE: 2025-11-19

"""
Perfect Error Messages
User-friendly, contextual, actionable error messages in multiple languages
"""

from typing import Dict, Any, Optional
from enum import Enum


class Language(Enum):
    """Supported languages"""

    EN = "en"
    RU = "ru"


class ErrorCode(Enum):
    """Standardized error codes"""

    # Authentication
    AUTH_REQUIRED = "AUTH_001"
    AUTH_INVALID_TOKEN = "AUTH_002"
    AUTH_EXPIRED = "AUTH_003"
    AUTH_INSUFFICIENT_PERMISSIONS = "AUTH_004"

    # Database
    DB_CONNECTION_FAILED = "DB_001"
    DB_QUERY_TIMEOUT = "DB_002"
    DB_NOT_FOUND = "DB_003"

    # Validation
    VALIDATION_REQUIRED_FIELD = "VAL_001"
    VALIDATION_INVALID_FORMAT = "VAL_002"
    VALIDATION_OUT_OF_RANGE = "VAL_003"

    # Business Logic
    BUSINESS_INSUFFICIENT_FUNDS = "BIZ_001"
    BUSINESS_DUPLICATE_ENTRY = "BIZ_002"
    BUSINESS_QUOTA_EXCEEDED = "BIZ_003"

    # External Services
    EXT_SERVICE_UNAVAILABLE = "EXT_001"
    EXT_API_RATE_LIMIT = "EXT_002"


ERROR_MESSAGES: Dict[ErrorCode, Dict[Language, Dict[str, str]]] = {
    # Authentication errors
    ErrorCode.AUTH_REQUIRED: {
        Language.EN: {
            "title": "Authentication Required",
            "message": "Please log in to access this resource",
            "action": "Click 'Login' button to sign in",
            "technical": "Missing or invalid Authorization header",
        },
        Language.RU: {
            "title": "Требуется аутентификация",
            "message": "Пожалуйста, войдите в систему для доступа к ресурсу",
            "action": "Нажмите кнопку 'Войти' для входа в систему",
            "technical": "Отсутствует или неверный заголовок Authorization",
        },
    },
    ErrorCode.AUTH_INVALID_TOKEN: {
        Language.EN: {
            "title": "Invalid Token",
            "message": "Your session token is invalid",
            "action": "Please log in again",
            "technical": "JWT token validation failed",
        },
        Language.RU: {
            "title": "Неверный токен",
            "message": "Ваш токен сессии недействителен",
            "action": "Пожалуйста, войдите снова",
            "technical": "Ошибка валидации JWT токена",
        },
    },
    ErrorCode.AUTH_EXPIRED: {
        Language.EN: {
            "title": "Session Expired",
            "message": "Your session has expired for security",
            "action": "Please log in again to continue",
            "technical": "JWT token expired (exp claim)",
        },
        Language.RU: {
            "title": "Сессия истекла",
            "message": "Ваша сессия истекла из соображений безопасности",
            "action": "Пожалуйста, войдите снова для продолжения",
            "technical": "JWT токен истёк (exp claim)",
        },
    },
    # Database errors
    ErrorCode.DB_CONNECTION_FAILED: {
        Language.EN: {
            "title": "Database Connection Error",
            "message": "We're having trouble connecting to our database",
            "action": "Please try again in a moment. If problem persists, contact support",
            "technical": "PostgreSQL connection failed",
        },
        Language.RU: {
            "title": "Ошибка подключения к базе данных",
            "message": "У нас проблемы с подключением к базе данных",
            "action": "Попробуйте снова через минуту. Если проблема сохраняется, свяжитесь с поддержкой",
            "technical": "Не удалось подключиться к PostgreSQL",
        },
    },
    ErrorCode.DB_NOT_FOUND: {
        Language.EN: {
            "title": "Not Found",
            "message": "The item you're looking for doesn't exist",
            "action": "Check the ID and try again, or go back to list view",
            "technical": "Record not found in database",
        },
        Language.RU: {
            "title": "Не найдено",
            "message": "Запрашиваемый элемент не существует",
            "action": "Проверьте ID и попробуйте снова, или вернитесь к списку",
            "technical": "Запись не найдена в базе данных",
        },
    },
    # Validation errors
    ErrorCode.VALIDATION_REQUIRED_FIELD: {
        Language.EN: {
            "title": "Required Field Missing",
            "message": "Please fill in all required fields",
            "action": "Look for fields marked with * and fill them in",
            "technical": "Required field validation failed",
        },
        Language.RU: {
            "title": "Пропущено обязательное поле",
            "message": "Пожалуйста, заполните все обязательные поля",
            "action": "Найдите поля отмеченные * и заполните их",
            "technical": "Валидация обязательного поля провалилась",
        },
    },
    # Business errors
    ErrorCode.BUSINESS_QUOTA_EXCEEDED: {
        Language.EN: {
            "title": "Quota Exceeded",
            "message": "You've reached your plan limit",
            "action": "Upgrade your plan or wait until next billing cycle",
            "technical": "Usage quota exceeded for current plan",
        },
        Language.RU: {
            "title": "Превышен лимит",
            "message": "Вы достигли лимита вашего тарифа",
            "action": "Обновите тариф или дождитесь следующего расчётного периода",
            "technical": "Превышена квота использования для текущего тарифа",
        },
    },
}


def get_error_message(
    error_code: ErrorCode,
    language: Language = Language.EN,
    context: Optional[Dict[str, Any]] = None,
    include_technical: bool = False,
) -> Dict[str, str]:
    """
    Get formatted error message

    Args:
        error_code: Error code enum
        language: Preferred language
        context: Additional context (field names, values, etc.)
        include_technical: Include technical details (for developers)

    Returns:
        Dict with title, message, action, and optionally technical details
    """

    if error_code not in ERROR_MESSAGES:
        # Fallback for unknown errors
        return {
            "title": "Error" if language == Language.EN else "Ошибка",
            "message": (
                "An unexpected error occurred"
                if language == Language.EN
                else "Произошла неожиданная ошибка"
            ),
            "action": (
                "Please try again or contact support"
                if language == Language.EN
                else "Попробуйте снова или свяжитесь с поддержкой"
            ),
            "code": (
                error_code.value if isinstance(error_code, ErrorCode) else "UNKNOWN"
            ),
        }

    error_data = ERROR_MESSAGES[error_code][language].copy()
    error_data["code"] = error_code.value

    # Add context if provided
    if context:
        for key, value in context.items():
            error_data["message"] = error_data["message"].replace(
                f"{{{key}}}", str(value)
            )
            error_data["action"] = error_data["action"].replace(
                f"{{{key}}}", str(value)
            )

    # Include technical details only if requested
    if not include_technical:
        error_data.pop("technical", None)

    return error_data


# Helper function
def format_validation_error(
    field_name: str, issue: str, language: Language = Language.EN
) -> Dict[str, str]:
    """Format validation error for specific field"""

    if language == Language.EN:
        return {
            "field": field_name,
            "message": f"{field_name}: {issue}",
            "suggestion": f"Please provide a valid {field_name}",
        }
    else:  # RU
        return {
            "field": field_name,
            "message": f"{field_name}: {issue}",
            "suggestion": f"Пожалуйста, укажите корректное значение для {field_name}",
        }
