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
from typing import Any, Awaitable, Callable, Dict, Optional

from .dns_manager import DNSManager, get_dns_manager
from .multipath_router import MultiPathRouter, NetworkPath
from .protocol_obfuscator import ProtocolObfuscator
from .tcp_optimizer import TCPOptimizer, get_tcp_optimizer
from .traffic_shaper import TrafficShaper
from .vpn_manager import VPNManager, VPNTunnel

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
