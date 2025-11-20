# [NEXUS IDENTITY] ID: 1548699014200172116 | DATE: 2025-11-19

"""
Revolutionary Security Layer - Безопасность для всех компонентов
================================================================

Система безопасности для:
- Аутентификация и авторизация
- Шифрование данных
- Аудит действий
- Защита от атак
- Compliance проверки

Научное обоснование:
- "Zero Trust Architecture" (2024): Без доверия по умолчанию
- "Security by Design" (2024): Безопасность с самого начала
"""

import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from cryptography.fernet import Fernet
import base64

logger = logging.getLogger(__name__)


class SecurityLevel(str, Enum):
    """Уровни безопасности"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(str, Enum):
    """Типы угроз"""

    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_BREACH = "data_breach"
    CODE_INJECTION = "code_injection"
    DOS_ATTACK = "dos_attack"
    MAN_IN_THE_MIDDLE = "man_in_the_middle"


@dataclass
class SecurityEvent:
    """Событие безопасности"""

    id: str = field(default_factory=lambda: str(uuid4()))
    threat_type: ThreatType = ThreatType.UNAUTHORIZED_ACCESS
    severity: SecurityLevel = SecurityLevel.MEDIUM
    source: str = ""
    target: str = ""
    action: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    blocked: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Сериализация события"""
        return {
            "id": self.id,
            "threat_type": self.threat_type.value,
            "severity": self.severity.value,
            "source": self.source,
            "target": self.target,
            "action": self.action,
            "timestamp": self.timestamp.isoformat(),
            "blocked": self.blocked,
            "metadata": self.metadata,
        }


@dataclass
class AccessToken:
    """Токен доступа"""

    token: str
    user_id: str
    permissions: Set[str] = field(default_factory=set)
    expires_at: datetime = field(
        default_factory=lambda: datetime.utcnow() + timedelta(hours=1)
    )
    created_at: datetime = field(default_factory=datetime.utcnow)

    def is_valid(self) -> bool:
        """Проверка валидности токена"""
        return datetime.utcnow() < self.expires_at


class EncryptionService:
    """Сервис шифрования"""

    def __init__(self, key: Optional[bytes] = None):
        if key is None:
            key = Fernet.generate_key()
        self.cipher = Fernet(key)

    def encrypt(self, data: str) -> str:
        """Шифрование данных"""
        encrypted = self.cipher.encrypt(data.encode())
        return base64.b64encode(encrypted).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Расшифровка данных"""
        encrypted_bytes = base64.b64decode(encrypted_data.encode())
        decrypted = self.cipher.decrypt(encrypted_bytes)
        return decrypted.decode()


class SecurityManager:
    """
    Менеджер безопасности для всех революционных компонентов

    Обеспечивает:
    - Аутентификацию и авторизацию
    - Шифрование данных
    - Аудит действий
    - Защиту от атак
    """

    def __init__(self):
        self.encryption = EncryptionService()
        self._tokens: Dict[str, AccessToken] = {}
        self._security_events: List[SecurityEvent] = []
        self._blocked_sources: Set[str] = set()
        self._rate_limits: Dict[str, List[datetime]] = {}

        logger.info("SecurityManager initialized")

    def generate_token(
        self, user_id: str, permissions: Set[str], expires_hours: int = 1
    ) -> AccessToken:
        """Генерация токена доступа"""
        token = secrets.token_urlsafe(32)
        access_token = AccessToken(
            token=token,
            user_id=user_id,
            permissions=permissions,
            expires_at=datetime.utcnow() + timedelta(hours=expires_hours),
        )

        self._tokens[token] = access_token

        logger.info(f"Token generated for user: {user_id}")

        return access_token

    def validate_token(self, token: str) -> Optional[AccessToken]:
        """Валидация токена"""
        access_token = self._tokens.get(token)

        if access_token and access_token.is_valid():
            return access_token

        # Невалидный токен - событие безопасности
        self._record_security_event(
            ThreatType.UNAUTHORIZED_ACCESS,
            SecurityLevel.MEDIUM,
            source="unknown",
            action="invalid_token_attempt",
        )

        return None

    def check_permission(self, token: str, permission: str) -> bool:
        """Проверка разрешения"""
        access_token = self.validate_token(token)

        if not access_token:
            return False

        return (
            permission in access_token.permissions
            or "admin" in access_token.permissions
        )

    def encrypt_data(self, data: str) -> str:
        """Шифрование данных"""
        return self.encryption.encrypt(data)

    def decrypt_data(self, encrypted_data: str) -> str:
        """Расшифровка данных"""
        return self.encryption.decrypt(encrypted_data)

    def check_rate_limit(
        self, source: str, max_requests: int = 100, window_seconds: int = 60
    ) -> bool:
        """Проверка rate limit"""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)

        if source not in self._rate_limits:
            self._rate_limits[source] = []

        # Очистка старых запросов
        self._rate_limits[source] = [
            req_time
            for req_time in self._rate_limits[source]
            if req_time > window_start
        ]

        # Проверка лимита
        if len(self._rate_limits[source]) >= max_requests:
            # Превышен лимит - событие безопасности
            self._record_security_event(
                ThreatType.DOS_ATTACK,
                SecurityLevel.HIGH,
                source=source,
                action="rate_limit_exceeded",
            )
            return False

        # Добавление текущего запроса
        self._rate_limits[source].append(now)
        return True

    def _record_security_event(
        self,
        threat_type: ThreatType,
        severity: SecurityLevel,
        source: str,
        action: str,
        blocked: bool = False,
    ) -> SecurityEvent:
        """Запись события безопасности"""
        event = SecurityEvent(
            threat_type=threat_type,
            severity=severity,
            source=source,
            action=action,
            blocked=blocked,
        )

        self._security_events.append(event)

        if blocked or severity == SecurityLevel.CRITICAL:
            self._blocked_sources.add(source)

        logger.warning(
            f"Security event: {threat_type.value}",
            extra={
                "event_id": event.id,
                "severity": severity.value,
                "source": source,
                "blocked": blocked,
            },
        )

        return event

    def is_blocked(self, source: str) -> bool:
        """Проверка, заблокирован ли источник"""
        return source in self._blocked_sources

    def get_security_stats(self) -> Dict[str, Any]:
        """Получение статистики безопасности"""
        return {
            "total_events": len(self._security_events),
            "blocked_sources": len(self._blocked_sources),
            "active_tokens": len([t for t in self._tokens.values() if t.is_valid()]),
            "events_by_type": {
                threat.value: len(
                    [e for e in self._security_events if e.threat_type == threat]
                )
                for threat in ThreatType
            },
            "events_by_severity": {
                level.value: len(
                    [e for e in self._security_events if e.severity == level]
                )
                for level in SecurityLevel
            },
        }
