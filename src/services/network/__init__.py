# [NEXUS IDENTITY] ID: 3323633353630428890 | DATE: 2025-11-19

"""
Network Resilience Components
Версия: 1.0.0

Компоненты сетевой отказоустойчивости:
- DNS Manager (DoH/DoT)
- TCP Optimizer
- Multi-Path Router
- Traffic Shaper
- VPN Manager
- Protocol Obfuscator
- HTTP/3 Client
- Network Resilience Layer

⚠️ ЮРИДИЧЕСКОЕ УВЕДОМЛЕНИЕ:
Данный модуль предоставляется исключительно в образовательных, исследовательских
и ознакомительных целях. Пользователь несёт полную ответственность за соблюдение
всех применимых законов и нормативных актов. Использование модуля для нарушения
законодательства строго запрещено.

Подробнее: docs/06-features/NETWORK_RESILIENCE_LEGAL_DISCLAIMER.md
"""

from .dns_manager import DNSManager, DNSResolver, DNSResolverType, get_dns_manager
from .tcp_optimizer import TCPOptimizer, TCPConfig, get_tcp_optimizer
from .multipath_router import MultiPathRouter, NetworkPath, PathStatus
from .traffic_shaper import TrafficShaper, TrafficShapeConfig
from .vpn_manager import VPNManager, VPNTunnel, TunnelStatus
from .protocol_obfuscator import ProtocolObfuscator
from .http3_client import HTTP3Client
from .network_resilience_layer import (
    NetworkResilienceLayer,
    get_network_resilience_layer,
)

__all__ = [
    "DNSManager",
    "DNSResolver",
    "DNSResolverType",
    "get_dns_manager",
    "TCPOptimizer",
    "TCPConfig",
    "get_tcp_optimizer",
    "MultiPathRouter",
    "NetworkPath",
    "PathStatus",
    "TrafficShaper",
    "TrafficShapeConfig",
    "VPNManager",
    "VPNTunnel",
    "TunnelStatus",
    "ProtocolObfuscator",
    "HTTP3Client",
    "NetworkResilienceLayer",
    "get_network_resilience_layer",
]
