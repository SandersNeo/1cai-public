# [NEXUS IDENTITY] ID: 1914586492552961708 | DATE: 2025-11-19

"""
Network Resilience Layer - Интеграция всех сетевых компонентов
Версия: 1.0.0

Объединяет все компоненты сетевой отказоустойчивости:
- DNS Manager
- TCP Optimizer
- Multi-Path Router
- Traffic Shaper
- VPN Manager
- Protocol Obfuscator

⚠️ ЮРИДИЧЕСКОЕ УВЕДОМЛЕНИЕ:
Данный модуль предоставляется исключительно в образовательных, исследовательских
и ознакомительных целях. Пользователь несёт полную ответственность за соблюдение
всех применимых законов и нормативных актов. Использование модуля для нарушения
законодательства строго запрещено.

Подробнее: docs/06-features/NETWORK_RESILIENCE_LEGAL_DISCLAIMER.md
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Dict, Optional, Awaitable

from .dns_manager import DNSManager, get_dns_manager
from .tcp_optimizer import TCPOptimizer, get_tcp_optimizer
from .multipath_router import MultiPathRouter, NetworkPath
from .traffic_shaper import TrafficShaper
from .vpn_manager import VPNManager, VPNTunnel
from .protocol_obfuscator import ProtocolObfuscator

logger = logging.getLogger(__name__)


class NetworkResilienceLayer:
    """
    Слой сетевой отказоустойчивости.

    Объединяет все компоненты для обеспечения максимальной отказоустойчивости:
    - DNS резолв с DoH/DoT
    - TCP оптимизация
    - Multi-path маршрутизация
    - Traffic shaping
    - VPN туннели
    - Protocol obfuscation
    """

    def __init__(
        self,
        enable_dns: bool = True,
        enable_tcp_optimization: bool = True,
        enable_multipath: bool = True,
        enable_traffic_shaping: bool = False,  # По умолчанию выключено
        enable_vpn: bool = False,  # По умолчанию выключено
        enable_obfuscation: bool = False,  # По умолчанию выключено
    ):
        """
        Args:
            enable_dns: Включить DNS Manager
            enable_tcp_optimization: Включить TCP оптимизацию
            enable_multipath: Включить multi-path маршрутизацию
            enable_traffic_shaping: Включить traffic shaping
            enable_vpn: Включить VPN Manager
            enable_obfuscation: Включить protocol obfuscation
        """
        # DNS Manager
        self.dns_manager: Optional[DNSManager] = None
        if enable_dns:
            try:
                self.dns_manager = get_dns_manager()
                logger.info("DNS Manager initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize DNS Manager: {e}")

        # TCP Optimizer
        self.tcp_optimizer: Optional[TCPOptimizer] = None
        if enable_tcp_optimization:
            try:
                self.tcp_optimizer = get_tcp_optimizer()
                # Применяем оптимизации (требует root на Linux)
                try:
                    self.tcp_optimizer.apply_optimizations()
                except Exception as e:
                    logger.debug(f"TCP optimizations require root: {e}")
                logger.info("TCP Optimizer initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize TCP Optimizer: {e}")

        # Multi-Path Router
        self.multipath_router: Optional[MultiPathRouter] = None
        if enable_multipath:
            try:
                self.multipath_router = MultiPathRouter()
                asyncio.create_task(self.multipath_router.start_health_monitoring())
                logger.info("Multi-Path Router initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Multi-Path Router: {e}")

        # Traffic Shaper
        self.traffic_shaper: Optional[TrafficShaper] = None
        if enable_traffic_shaping:
            try:
                self.traffic_shaper = TrafficShaper()
                logger.info("Traffic Shaper initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Traffic Shaper: {e}")

        # VPN Manager
        self.vpn_manager: Optional[VPNManager] = None
        if enable_vpn:
            try:
                self.vpn_manager = VPNManager()
                asyncio.create_task(self.vpn_manager.start_health_monitoring())
                logger.info("VPN Manager initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize VPN Manager: {e}")

        # Protocol Obfuscator
        self.protocol_obfuscator: Optional[ProtocolObfuscator] = None
        if enable_obfuscation:
            try:
                self.protocol_obfuscator = ProtocolObfuscator()
                logger.info("Protocol Obfuscator initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Protocol Obfuscator: {e}")

    async def resolve_domain(self, domain: str, record_type: str = "A") -> list[str]:
        """
        Резолвить домен с использованием DNS Manager.

        Args:
            domain: Домен для резолва
            record_type: Тип записи

        Returns:
            Список IP-адресов
        """
        if self.dns_manager:
            return await self.dns_manager.resolve(domain, record_type)
        else:
            # Fallback на стандартный DNS
            import socket

            return [socket.gethostbyname(domain)]

    async def send_request(
        self,
        request_func: Callable[..., Awaitable[Any]],
        *args,
        use_multipath: bool = True,
        use_traffic_shaping: bool = False,
        use_obfuscation: bool = False,
        **kwargs,
    ) -> Any:
        """
        Отправить запрос с использованием всех доступных механизмов.

        Args:
            request_func: Функция для выполнения запроса
            *args: Аргументы функции
            use_multipath: Использовать multi-path маршрутизацию
            use_traffic_shaping: Использовать traffic shaping
            use_obfuscation: Использовать protocol obfuscation
            **kwargs: Ключевые аргументы функции

        Returns:
            Результат запроса
        """
        # Применяем обфускацию если нужно
        if use_obfuscation and self.protocol_obfuscator:
            # Обфускация применяется на уровне данных
            # Здесь упрощённая версия
            pass

        # Используем multi-path если доступен
        if use_multipath and self.multipath_router:
            return await self.multipath_router.send_request(
                request_func, *args, **kwargs
            )
        else:
            # Прямой вызов
            return await request_func(*args, **kwargs)

    def add_network_path(self, path: NetworkPath):
        """Добавить сетевой путь"""
        if self.multipath_router:
            self.multipath_router.paths.append(path)
            from .multipath_router import PathMetrics, PathStatus

            self.multipath_router.path_metrics[path.path_id] = PathMetrics(
                path_id=path.path_id, status=PathStatus.UNKNOWN
            )

    def add_vpn_tunnel(self, tunnel: VPNTunnel):
        """Добавить VPN туннель"""
        if self.vpn_manager:
            self.vpn_manager.tunnels.append(tunnel)
            asyncio.create_task(self.vpn_manager.start_tunnel(tunnel))

    def get_status(self) -> Dict[str, Any]:
        """Получить статус всех компонентов"""
        status = {
            "dns_manager": {
                "enabled": self.dns_manager is not None,
                "stats": self.dns_manager.get_resolver_stats()
                if self.dns_manager
                else {},
            },
            "tcp_optimizer": {
                "enabled": self.tcp_optimizer is not None,
                "config": self.tcp_optimizer.get_current_config()
                if self.tcp_optimizer
                else {},
            },
            "multipath_router": {
                "enabled": self.multipath_router is not None,
                "healthy_paths": len(self.multipath_router.get_healthy_paths())
                if self.multipath_router
                else 0,
                "metrics": self.multipath_router.get_path_metrics()
                if self.multipath_router
                else {},
            },
            "traffic_shaper": {"enabled": self.traffic_shaper is not None},
            "vpn_manager": {
                "enabled": self.vpn_manager is not None,
                "healthy_tunnels": len(self.vpn_manager.get_healthy_tunnels())
                if self.vpn_manager
                else 0,
                "metrics": self.vpn_manager.get_tunnel_metrics()
                if self.vpn_manager
                else {},
            },
            "protocol_obfuscator": {"enabled": self.protocol_obfuscator is not None},
        }

        return status


# Глобальный экземпляр
_network_resilience_layer: Optional[NetworkResilienceLayer] = None


def get_network_resilience_layer() -> NetworkResilienceLayer:
    """Получить глобальный экземпляр Network Resilience Layer"""
    global _network_resilience_layer
    if _network_resilience_layer is None:
        _network_resilience_layer = NetworkResilienceLayer()
    return _network_resilience_layer
