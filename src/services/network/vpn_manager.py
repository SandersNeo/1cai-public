# [NEXUS IDENTITY] ID: -3659210567390117114 | DATE: 2025-11-19

"""
VPN Manager - Управление VPN туннелями (WireGuard)
Версия: 1.0.0

Поддержка:
- WireGuard туннели
- Автоматическое переключение
- Мониторинг состояния
- Метрики производительности
"""

from __future__ import annotations

import asyncio
import logging
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

try:
    from src.monitoring.prometheus_metrics import (
        vpn_tunnel_health,
        vpn_tunnel_latency_ms,
        vpn_tunnel_throughput_bytes,
    )
except ImportError:
    vpn_tunnel_health = None
    vpn_tunnel_latency_ms = None
    vpn_tunnel_throughput_bytes = None

logger = logging.getLogger(__name__)


class TunnelStatus(str, Enum):
    """Статус VPN туннеля"""

    UP = "up"
    DOWN = "down"
    UNKNOWN = "unknown"


@dataclass
class VPNTunnel:
    """Конфигурация VPN туннеля"""

    name: str
    config_path: Path
    tunnel_type: str = "wireguard"
    enabled: bool = True
    priority: int = 0
    metadata: Dict = field(default_factory=dict)


@dataclass
class TunnelMetrics:
    """Метрики VPN туннеля"""

    name: str
    status: TunnelStatus
    latency_ms: float = 0.0
    throughput_bytes_per_sec: float = 0.0
    last_check: Optional[datetime] = None
    uptime_seconds: float = 0.0


class VPNManager:
    """
    Менеджер VPN туннелей.

    Особенности:
    - Управление WireGuard туннелями
    - Автоматическое переключение
    - Мониторинг состояния
    - Метрики производительности
    """

    def __init__(
        self,
        tunnels: Optional[List[VPNTunnel]] = None,
        health_check_interval: float = 60.0,
    ):
        """
        Args:
            tunnels: Список VPN туннелей
            health_check_interval: Интервал проверки здоровья в секундах
        """
        self.tunnels = tunnels or []
        self.health_check_interval = health_check_interval

        self.tunnel_metrics: Dict[str, TunnelMetrics] = {}
        self._health_check_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

        # Инициализация метрик
        for tunnel in self.tunnels:
            self.tunnel_metrics[tunnel.name] = TunnelMetrics(
                name=tunnel.name, status=TunnelStatus.UNKNOWN
            )

    async def start_tunnel(self, tunnel: VPNTunnel) -> bool:
        """
        Запустить VPN туннель.

        Args:
            tunnel: Конфигурация туннеля

        Returns:
            True если успешно, False если ошибка
        """
        if tunnel.tunnel_type == "wireguard":
            return await self._start_wireguard(tunnel)
        else:
            logger.warning(f"Unknown tunnel type: {tunnel.tunnel_type}")
            return False

    async def _start_wireguard(self, tunnel: VPNTunnel) -> bool:
        """Запустить WireGuard туннель"""
        try:
            # Проверяем наличие wg-quick
            result = subprocess.run(
                ["which", "wg-quick"], capture_output=True, check=True
            )

            if not result.returncode == 0:
                logger.error("wg-quick not found, WireGuard not available")
                return False

            # Запускаем туннель
            subprocess.run(
                ["wg-quick", "up", str(tunnel.config_path)],
                check=True,
                capture_output=True,
            )

            logger.info(f"WireGuard tunnel {tunnel.name} started")

            # Обновляем метрики
            metrics = self.tunnel_metrics.get(tunnel.name)
            if metrics:
                metrics.status = TunnelStatus.UP
                metrics.last_check = datetime.utcnow()

            if vpn_tunnel_health:
                vpn_tunnel_health.labels(
                    tunnel_name=tunnel.name, tunnel_type=tunnel.tunnel_type
                ).set(1.0)

            return True

        except subprocess.CalledProcessError as e:
            logger.error("Failed to start WireGuard tunnel {tunnel.name}: %s", e)
            metrics = self.tunnel_metrics.get(tunnel.name)
            if metrics:
                metrics.status = TunnelStatus.DOWN

            vpn_tunnel_health.labels(
                tunnel_name=tunnel.name, tunnel_type=tunnel.tunnel_type
            ).set(0.0)

            return False
        except FileNotFoundError:
            logger.error("wg-quick command not found")
            return False

    async def stop_tunnel(self, tunnel: VPNTunnel) -> bool:
        """Остановить VPN туннель"""
        if tunnel.tunnel_type == "wireguard":
            try:
                subprocess.run(
                    ["wg-quick", "down", str(tunnel.config_path)],
                    check=True,
                    capture_output=True,
                )

                logger.info(f"WireGuard tunnel {tunnel.name} stopped")

                metrics = self.tunnel_metrics.get(tunnel.name)
                if metrics:
                    metrics.status = TunnelStatus.DOWN

                vpn_tunnel_health.labels(
                    tunnel_name=tunnel.name, tunnel_type=tunnel.tunnel_type
                ).set(0.0)

                return True

            except Exception as e:
                logger.error("Failed to stop WireGuard tunnel {tunnel.name}: %s", e)
                return False

        return False

    async def start_health_monitoring(self):
        """Запустить мониторинг здоровья туннелей"""
        if self._health_check_task and not self._health_check_task.done():
            return

        self._stop_event.clear()
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("VPN Manager health monitoring started")

    async def stop_health_monitoring(self):
        """Остановить мониторинг"""
        self._stop_event.set()
        if self._health_check_task:
            await self._health_check_task
        logger.info("VPN Manager health monitoring stopped")

    async def _health_check_loop(self):
        """Цикл проверки здоровья"""
        while not self._stop_event.is_set():
            try:
                await self._check_all_tunnels()
            except Exception as e:
                logger.error(f"Error in VPN health check loop: {e}", exc_info=True)

            try:
                await asyncio.wait_for(
                    self._stop_event.wait(), timeout=self.health_check_interval
                )
            except asyncio.TimeoutError:
                continue

    async def _check_all_tunnels(self):
        """Проверить все туннели"""
        tasks = []
        for tunnel in self.tunnels:
            if tunnel.enabled:
                tasks.append(self._check_tunnel(tunnel))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _check_tunnel(self, tunnel: VPNTunnel):
        """Проверить один туннель"""
        metrics = self.tunnel_metrics.get(tunnel.name)
        if not metrics:
            return

        try:
            if tunnel.tunnel_type == "wireguard":
                # Проверяем статус через wg show
                result = subprocess.run(
                    ["wg", "show", tunnel.name],
                    capture_output=True,
                    text=True,
                    timeout=5.0,
                )

                if result.returncode == 0:
                    metrics.status = TunnelStatus.UP
                    metrics.last_check = datetime.utcnow()

                    # Парсим метрики из вывода wg show
                    # (упрощённая версия)
                    metrics.latency_ms = 0.0  # Требует ping через туннель
                    metrics.throughput_bytes_per_sec = 0.0  # Требует измерения
                else:
                    metrics.status = TunnelStatus.DOWN
                    metrics.last_check = datetime.utcnow()

            # Обновляем Prometheus метрики
            if vpn_tunnel_health:
                vpn_tunnel_health.labels(
                    tunnel_name=tunnel.name, tunnel_type=tunnel.tunnel_type
                ).set(1.0 if metrics.status == TunnelStatus.UP else 0.0)

            if vpn_tunnel_latency_ms:
                vpn_tunnel_latency_ms.labels(
                    tunnel_name=tunnel.name, tunnel_type=tunnel.tunnel_type
                ).set(metrics.latency_ms)

            if vpn_tunnel_throughput_bytes:
                vpn_tunnel_throughput_bytes.labels(
                    tunnel_name=tunnel.name, tunnel_type=tunnel.tunnel_type
                ).set(metrics.throughput_bytes_per_sec)

        except Exception as e:
            logger.debug("Tunnel {tunnel.name} health check failed: %s", e)
            metrics.status = TunnelStatus.DOWN
            metrics.last_check = datetime.utcnow()

            if vpn_tunnel_health:
                vpn_tunnel_health.labels(
                    tunnel_name=tunnel.name, tunnel_type=tunnel.tunnel_type
                ).set(0.0)

    def get_healthy_tunnels(self) -> List[VPNTunnel]:
        """Получить список здоровых туннелей"""
        return [
            tunnel
            for tunnel in self.tunnels
            if tunnel.enabled
            and self.tunnel_metrics.get(
                tunnel.name, TunnelMetrics(tunnel.name, TunnelStatus.UNKNOWN)
            ).status
            == TunnelStatus.UP
        ]

    def get_tunnel_metrics(self) -> Dict[str, TunnelMetrics]:
        """Получить метрики всех туннелей"""
        return self.tunnel_metrics.copy()
