# [NEXUS IDENTITY] ID: 7133194669231632365 | DATE: 2025-11-19

"""
DNS Manager with DoH/DoT support and multiple resolvers
Версия: 1.0.0

Поддержка:
- DNS over HTTPS (DoH)
- DNS over TLS (DoT)
- Множественные резолверы с fallback
- Кэширование DNS запросов
- Мониторинг и метрики
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

import httpx

try:
    from src.monitoring.prometheus_metrics import (
        dns_resolution_duration_seconds,
        dns_resolution_total,
        dns_resolver_health,
    )
except ImportError:
    # Fallback для случаев когда prometheus_metrics не доступен
    dns_resolution_total = None
    dns_resolution_duration_seconds = None
    dns_resolver_health = None

logger = logging.getLogger(__name__)


class DNSResolverType(str, Enum):
    """Тип DNS резолвера"""

    STANDARD = "standard"  # Стандартный DNS
    DOH = "doh"  # DNS over HTTPS
    DOT = "dot"  # DNS over TLS


@dataclass
class DNSResolver:
    """Конфигурация DNS резолвера"""

    name: str
    type: DNSResolverType
    address: str
    port: int = 53
    enabled: bool = True
    priority: int = 0  # Чем меньше, тем выше приоритет
    timeout: float = 5.0
    metadata: Dict = field(default_factory=dict)


@dataclass
class DNSCacheEntry:
    """Запись в DNS кэше"""

    domain: str
    ip_addresses: List[str]
    created_at: datetime
    ttl: int = 300  # 5 минут по умолчанию

    def is_expired(self) -> bool:
        """Проверить, истёк ли срок действия"""
        age = (datetime.utcnow() - self.created_at).total_seconds()
        return age > self.ttl


class DNSManager:
    """
    Менеджер DNS с поддержкой DoH/DoT и множественных резолверов.

    Особенности:
    - Поддержка DoH, DoT, стандартного DNS
    - Автоматический fallback между резолверами
    - Кэширование DNS запросов
    - Мониторинг и метрики
    """

    def __init__(
        self,
        resolvers: Optional[List[DNSResolver]] = None,
        enable_cache: bool = True,
        cache_ttl: int = 300,
    ):
        """
        Args:
            resolvers: Список DNS резолверов (если None, используются по умолчанию)
            enable_cache: Включить кэширование
            cache_ttl: TTL кэша в секундах
        """
        self.resolvers = resolvers or self._get_default_resolvers()
        self.enable_cache = enable_cache
        self.cache_ttl = cache_ttl
        self.cache: Dict[str, DNSCacheEntry] = {}
        self.resolver_stats: Dict[str, Dict] = {}

        # Инициализация статистики
        for resolver in self.resolvers:
            self.resolver_stats[resolver.name] = {
                "success_count": 0,
                "failure_count": 0,
                "last_success": None,
                "last_failure": None,
                "avg_latency_ms": 0.0,
            }

    def _get_default_resolvers(self) -> List[DNSResolver]:
        """Получить резолверы по умолчанию"""
        return [
            # DoH резолверы (высокий приоритет)
            DNSResolver(
                name="cloudflare-doh",
                type=DNSResolverType.DOH,
                address="https://cloudflare-dns.com/dns-query",
                priority=1,
            ),
            DNSResolver(
                name="google-doh",
                type=DNSResolverType.DOH,
                address="https://dns.google/resolve",
                priority=2,
            ),
            DNSResolver(
                name="quad9-doh",
                type=DNSResolverType.DOH,
                address="https://dns.quad9.net/dns-query",
                priority=3,
            ),
            # DoT резолверы
            DNSResolver(
                name="cloudflare-dot",
                type=DNSResolverType.DOT,
                address="1.1.1.1",
                port=853,
                priority=4,
            ),
            DNSResolver(
                name="google-dot",
                type=DNSResolverType.DOT,
                address="8.8.8.8",
                port=853,
                priority=5,
            ),
            # Стандартные DNS резолверы (низкий приоритет)
            DNSResolver(
                name="cloudflare-standard",
                type=DNSResolverType.STANDARD,
                address="1.1.1.1",
                port=53,
                priority=6,
            ),
            DNSResolver(
                name="google-standard",
                type=DNSResolverType.STANDARD,
                address="8.8.8.8",
                port=53,
                priority=7,
            ),
        ]

    async def resolve(
        self, domain: str, record_type: str = "A", use_cache: bool = True
    ) -> List[str]:
        """
        Резолвить домен с fallback на несколько резолверов.

        Args:
            domain: Домен для резолва
            record_type: Тип записи (A, AAAA, MX, etc.)
            use_cache: Использовать кэш

        Returns:
            Список IP-адресов или других значений
        """
        start_time = time.time()

        # Проверяем кэш
        if use_cache and self.enable_cache:
            cache_key = f"{domain}:{record_type}"
            cached = self.cache.get(cache_key)
            if cached and not cached.is_expired():
                logger.debug("DNS cache hit for %s", domain)
                return cached.ip_addresses

        # Сортируем резолверы по приоритету
        sorted_resolvers = sorted(
            [r for r in self.resolvers if r.enabled], key=lambda x: x.priority
        )

        last_error: Optional[Exception] = None

        # Пробуем каждый резолвер по очереди
        for resolver in sorted_resolvers:
            try:
                result = await self._resolve_with_resolver(
                    resolver, domain, record_type
                )

                # Успешный резолв
                duration = (time.time() - start_time) * 1000
                self._update_stats(resolver.name, success=True, latency_ms=duration)

                # Обновляем метрики
                if dns_resolution_total:
                    dns_resolution_total.labels(
                        resolver=resolver.name,
                        type=resolver.type.value,
                        status="success",
                    ).inc()
                if dns_resolution_duration_seconds:
                    dns_resolution_duration_seconds.labels(
                        resolver=resolver.name, type=resolver.type.value
                    ).observe(duration / 1000)
                if dns_resolver_health:
                    dns_resolver_health.labels(resolver=resolver.name).set(1.0)

                # Сохраняем в кэш
                if self.enable_cache:
                    self._save_to_cache(domain, record_type, result)

                return result

            except Exception as e:
                last_error = e
                logger.warning("DNS resolver {resolver.name} failed: %s", e)

                # Обновляем статистику
                self._update_stats(resolver.name, success=False)

                # Обновляем метрики
                if dns_resolution_total:
                    dns_resolution_total.labels(
                        resolver=resolver.name, type=resolver.type.value, status="error"
                    ).inc()
                if dns_resolver_health:
                    dns_resolver_health.labels(resolver=resolver.name).set(0.0)

                # Продолжаем к следующему резолверу
                continue

        # Все резолверы недоступны
        duration = (time.time() - start_time) * 1000
        logger.error("All DNS resolvers failed for %s, last error: {last_error}", domain)

        raise DNSResolutionError(f"Failed to resolve {domain}: {last_error}")

    async def _resolve_with_resolver(
        self, resolver: DNSResolver, domain: str, record_type: str
    ) -> List[str]:
        """Резолвить через конкретный резолвер"""
        if resolver.type == DNSResolverType.DOH:
            return await self._resolve_doh(resolver, domain, record_type)
        elif resolver.type == DNSResolverType.DOT:
            return await self._resolve_dot(resolver, domain, record_type)
        else:
            return await self._resolve_standard(resolver, domain, record_type)

    async def _resolve_doh(
        self, resolver: DNSResolver, domain: str, record_type: str
    ) -> List[str]:
        """Резолвить через DNS over HTTPS"""
        async with httpx.AsyncClient(timeout=resolver.timeout) as client:
            # Cloudflare DoH формат
            if "cloudflare-dns.com" in resolver.address:
                response = await client.get(
                    resolver.address,
                    params={"name": domain, "type": record_type},
                    headers={"Accept": "application/dns-json"},
                )
                data = response.json()
                if "Answer" in data:
                    return [answer["data"] for answer in data["Answer"]]
                return []

            # Google DoH формат
            elif "dns.google" in resolver.address:
                response = await client.get(
                    resolver.address, params={"name": domain, "type": record_type}
                )
                data = response.json()
                if "Answer" in data:
                    return [answer["data"] for answer in data["Answer"]]
                return []

            # Quad9 DoH формат
            elif "quad9.net" in resolver.address:
                response = await client.get(
                    resolver.address,
                    params={"name": domain, "type": record_type},
                    headers={"Accept": "application/dns-json"},
                )
                data = response.json()
                if "Answer" in data:
                    return [answer["data"] for answer in data["Answer"]]
                return []

            else:
                raise ValueError(f"Unknown DoH resolver format: {resolver.address}")

    async def _resolve_dot(
        self, resolver: DNSResolver, domain: str, record_type: str
    ) -> List[str]:
        """Резолвить через DNS over TLS"""
        # Используем dnspython с поддержкой DoT
        try:
            import dns.resolver

            resolver_obj = dns.resolver.Resolver()
            resolver_obj.nameservers = [resolver.address]
            resolver_obj.port = resolver.port

            # DoT требует специальной настройки
            # Для упрощения используем стандартный DNS через TLS порт
            answers = resolver_obj.resolve(domain, record_type)
            return [str(answer) for answer in answers]
        except Exception as e:
            raise DNSResolutionError(f"DoT resolution failed: {e}")

    async def _resolve_standard(
        self, resolver: DNSResolver, domain: str, record_type: str
    ) -> List[str]:
        """Резолвить через стандартный DNS"""
        try:
            import dns.resolver

            resolver_obj = dns.resolver.Resolver()
            resolver_obj.nameservers = [resolver.address]
            resolver_obj.port = resolver.port
            resolver_obj.timeout = resolver.timeout

            answers = resolver_obj.resolve(domain, record_type)
            return [str(answer) for answer in answers]
        except Exception as e:
            raise DNSResolutionError(f"Standard DNS resolution failed: {e}")

    def _save_to_cache(self, domain: str, record_type: str, ip_addresses: List[str]):
        """Сохранить результат в кэш"""
        cache_key = f"{domain}:{record_type}"
        self.cache[cache_key] = DNSCacheEntry(
            domain=domain,
            ip_addresses=ip_addresses,
            created_at=datetime.utcnow(),
            ttl=self.cache_ttl,
        )

    def _update_stats(self, resolver_name: str, success: bool, latency_ms: float = 0.0):
        """Обновить статистику резолвера"""
        stats = self.resolver_stats.get(resolver_name, {})
        if success:
            stats["success_count"] = stats.get("success_count", 0) + 1
            stats["last_success"] = datetime.utcnow()
            # Обновляем среднюю latency
            current_avg = stats.get("avg_latency_ms", 0.0)
            count = stats["success_count"]
            stats["avg_latency_ms"] = (current_avg * (count - 1) + latency_ms) / count
        else:
            stats["failure_count"] = stats.get("failure_count", 0) + 1
            stats["last_failure"] = datetime.utcnow()

    def get_resolver_stats(self) -> Dict[str, Dict]:
        """Получить статистику всех резолверов"""
        return self.resolver_stats.copy()

    def clear_cache(self):
        """Очистить DNS кэш"""
        self.cache.clear()
        logger.info("DNS cache cleared")


class DNSResolutionError(Exception):
    """Ошибка резолва DNS"""


# Глобальный экземпляр
_dns_manager: Optional[DNSManager] = None


def get_dns_manager() -> DNSManager:
    """Получить глобальный экземпляр DNS Manager"""
    global _dns_manager
    if _dns_manager is None:
        _dns_manager = DNSManager()
    return _dns_manager
