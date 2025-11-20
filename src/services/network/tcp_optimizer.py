# [NEXUS IDENTITY] ID: 7100517214000717799 | DATE: 2025-11-19

"""
TCP Optimizer - Адаптивные TCP параметры
Версия: 1.0.0

Оптимизация TCP параметров для быстрого обнаружения недоступности
и эффективного использования ресурсов.
"""

from __future__ import annotations

import logging
import platform
import subprocess
from dataclasses import dataclass
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class TCPConfig:
    """Конфигурация TCP параметров"""

    tcp_syn_retries: int = 3  # Быстрое обнаружение недоступности
    tcp_keepalive_time: int = 30  # Проверка соединения каждые 30 сек
    tcp_keepalive_probes: int = 3  # 3 попытки перед закрытием
    tcp_keepalive_intvl: int = 10  # Интервал между попытками
    tcp_fin_timeout: int = 10  # Быстрое закрытие соединений
    tcp_tw_reuse: int = 1  # Переиспользование TIME_WAIT сокетов
    tcp_max_syn_backlog: int = 2048  # Размер очереди SYN
    tcp_synack_retries: int = 2  # Повторы SYN-ACK


class TCPOptimizer:
    """
    Оптимизатор TCP параметров для улучшения отказоустойчивости.

    Особенности:
    - Быстрое обнаружение недоступности серверов
    - Эффективное использование ресурсов
    - Адаптивные параметры на основе ОС
    """

    def __init__(self, config: Optional[TCPConfig] = None):
        self.config = config or TCPConfig()
        self.is_linux = platform.system() == "Linux"
        self.is_windows = platform.system() == "Windows"
        self.is_macos = platform.system() == "Darwin"

        # Текущие значения (для отката)
        self.original_values: Dict[str, str] = {}

    def apply_optimizations(self) -> bool:
        """
        Применить TCP оптимизации.

        Returns:
            True если успешно, False если ошибка
        """
        if not self.is_linux:
            logger.warning("TCP optimizations are only supported on Linux")
            return False

        try:
            # Сохраняем текущие значения
            self._save_current_values()

            # Применяем оптимизации
            self._apply_tcp_syn_retries()
            self._apply_tcp_keepalive()
            self._apply_tcp_fin_timeout()
            self._apply_tcp_tw_reuse()
            self._apply_tcp_max_syn_backlog()
            self._apply_tcp_synack_retries()

            logger.info("TCP optimizations applied successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to apply TCP optimizations: {e}", exc_info=True)
            # Пытаемся откатить изменения
            self._restore_original_values()
            return False

    def _save_current_values(self):
        """Сохранить текущие значения для отката"""
        if not self.is_linux:
            return

        params = [
            "tcp_syn_retries",
            "net.ipv4.tcp_keepalive_time",
            "net.ipv4.tcp_keepalive_probes",
            "net.ipv4.tcp_keepalive_intvl",
            "net.ipv4.tcp_fin_timeout",
            "net.ipv4.tcp_tw_reuse",
            "net.ipv4.tcp_max_syn_backlog",
            "net.ipv4.tcp_synack_retries",
        ]

        for param in params:
            try:
                result = subprocess.run(
                    ["sysctl", "-n", param], capture_output=True, text=True, check=True
                )
                self.original_values[param] = result.stdout.strip()
            except Exception:
                pass

    def _apply_tcp_syn_retries(self):
        """Установить количество SYN retries"""
        subprocess.run(
            ["sysctl", "-w", f"net.ipv4.tcp_syn_retries={self.config.tcp_syn_retries}"],
            check=True,
        )

    def _apply_tcp_keepalive(self):
        """Установить параметры keepalive"""
        subprocess.run(
            [
                "sysctl",
                "-w",
                f"net.ipv4.tcp_keepalive_time={self.config.tcp_keepalive_time}",
            ],
            check=True,
        )
        subprocess.run(
            [
                "sysctl",
                "-w",
                f"net.ipv4.tcp_keepalive_probes={self.config.tcp_keepalive_probes}",
            ],
            check=True,
        )
        subprocess.run(
            [
                "sysctl",
                "-w",
                f"net.ipv4.tcp_keepalive_intvl={self.config.tcp_keepalive_intvl}",
            ],
            check=True,
        )

    def _apply_tcp_fin_timeout(self):
        """Установить FIN timeout"""
        subprocess.run(
            ["sysctl", "-w", f"net.ipv4.tcp_fin_timeout={self.config.tcp_fin_timeout}"],
            check=True,
        )

    def _apply_tcp_tw_reuse(self):
        """Включить переиспользование TIME_WAIT"""
        subprocess.run(
            ["sysctl", "-w", f"net.ipv4.tcp_tw_reuse={self.config.tcp_tw_reuse}"],
            check=True,
        )

    def _apply_tcp_max_syn_backlog(self):
        """Установить размер очереди SYN"""
        subprocess.run(
            [
                "sysctl",
                "-w",
                f"net.ipv4.tcp_max_syn_backlog={self.config.tcp_max_syn_backlog}",
            ],
            check=True,
        )

    def _apply_tcp_synack_retries(self):
        """Установить количество SYN-ACK retries"""
        subprocess.run(
            [
                "sysctl",
                "-w",
                f"net.ipv4.tcp_synack_retries={self.config.tcp_synack_retries}",
            ],
            check=True,
        )

    def _restore_original_values(self):
        """Восстановить оригинальные значения"""
        for param, value in self.original_values.items():
            try:
                subprocess.run(["sysctl", "-w", f"{param}={value}"], check=True)
            except Exception as e:
                logger.warning(f"Failed to restore {param}: {e}")

    def get_current_config(self) -> Dict[str, str]:
        """Получить текущую конфигурацию TCP"""
        if not self.is_linux:
            return {}

        params = [
            "net.ipv4.tcp_syn_retries",
            "net.ipv4.tcp_keepalive_time",
            "net.ipv4.tcp_keepalive_probes",
            "net.ipv4.tcp_keepalive_intvl",
            "net.ipv4.tcp_fin_timeout",
            "net.ipv4.tcp_tw_reuse",
            "net.ipv4.tcp_max_syn_backlog",
            "net.ipv4.tcp_synack_retries",
        ]

        config = {}
        for param in params:
            try:
                result = subprocess.run(
                    ["sysctl", "-n", param], capture_output=True, text=True, check=True
                )
                config[param] = result.stdout.strip()
            except Exception:
                pass

        return config


# Глобальный экземпляр
_tcp_optimizer: Optional[TCPOptimizer] = None


def get_tcp_optimizer() -> TCPOptimizer:
    """Получить глобальный экземпляр TCP Optimizer"""
    global _tcp_optimizer
    if _tcp_optimizer is None:
        _tcp_optimizer = TCPOptimizer()
    return _tcp_optimizer
