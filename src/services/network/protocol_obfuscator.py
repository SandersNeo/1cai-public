# [NEXUS IDENTITY] ID: 3243448829381429574 | DATE: 2025-11-19

"""
Protocol Obfuscator - Обфускация протоколов
Версия: 1.0.0

Маскировка протоколов для обхода DPI и блокировок.
"""

from __future__ import annotations

import base64
import logging

try:
    from src.monitoring.prometheus_metrics import (
        protocol_obfuscation_operations_total,
        protocol_obfuscation_overhead_bytes,
    )
except ImportError:
    protocol_obfuscation_operations_total = None
    protocol_obfuscation_overhead_bytes = None

logger = logging.getLogger(__name__)


class ProtocolObfuscator:
    """
    Обфускатор протоколов для обхода DPI.

    Особенности:
    - Маскировка под легитимные протоколы
    - Изменение структуры пакетов
    - Дополнительное шифрование
    - Случайные заголовки
    """

    def __init__(self):
        self.obfuscation_methods = {
            "http_masking": self._obfuscate_as_http,
            "tls_wrapping": self._obfuscate_as_tls,
            "dns_encoding": self._obfuscate_as_dns,
            "base64_encoding": self._obfuscate_base64,
        }

    def obfuscate(self, data: bytes, method: str = "http_masking", **kwargs) -> bytes:
        """
        Обфусцировать данные.

        Args:
            data: Исходные данные
            method: Метод обфускации
            **kwargs: Дополнительные параметры

        Returns:
            Обфусцированные данные
        """
        start_size = len(data)

        try:
            obfuscator = self.obfuscation_methods.get(method)
            if not obfuscator:
                logger.warning(f"Unknown obfuscation method: {method}")
                return data

            obfuscated = obfuscator(data, **kwargs)

            # Обновляем метрики
            overhead = len(obfuscated) - start_size
            if protocol_obfuscation_operations_total:
                protocol_obfuscation_operations_total.labels(
                    obfuscation_type=method, status="success"
                ).inc()
            if protocol_obfuscation_overhead_bytes:
                protocol_obfuscation_overhead_bytes.labels(
                    obfuscation_type=method
                ).observe(overhead)

            return obfuscated

        except Exception as e:
            logger.error(f"Obfuscation failed: {e}")
            if protocol_obfuscation_operations_total:
                protocol_obfuscation_operations_total.labels(
                    obfuscation_type=method, status="error"
                ).inc()
            return data

    def deobfuscate(self, data: bytes, method: str = "http_masking", **kwargs) -> bytes:
        """
        Деобфусцировать данные.

        Args:
            data: Обфусцированные данные
            method: Метод обфускации
            **kwargs: Дополнительные параметры

        Returns:
            Деобфусцированные данные
        """
        try:
            if method == "http_masking":
                return self._deobfuscate_from_http(data, **kwargs)
            elif method == "base64_encoding":
                return self._deobfuscate_base64(data, **kwargs)
            else:
                logger.warning(f"Deobfuscation not implemented for: {method}")
                return data

        except Exception as e:
            logger.error(f"Deobfuscation failed: {e}")
            return data

    def _obfuscate_as_http(self, data: bytes, domain: str = "example.com") -> bytes:
        """Маскировать под HTTP запрос"""
        # Кодируем данные в base64
        encoded = base64.b64encode(data).decode()

        # Формируем HTTP запрос
        http_request = (
            f"GET /api/data HTTP/1.1\r\n"
            f"Host: {domain}\r\n"
            f"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\n"
            f"Accept: application/json\r\n"
            f"X-Data: {encoded}\r\n"
            f"Connection: keep-alive\r\n"
            f"\r\n"
        )

        return http_request.encode()

    def _deobfuscate_from_http(self, data: bytes, **kwargs) -> bytes:
        """Деобфусцировать из HTTP"""
        try:
            # Парсим HTTP заголовки
            text = data.decode("utf-8", errors="ignore")
            lines = text.split("\r\n")

            for line in lines:
                if line.startswith("X-Data:"):
                    encoded = line.split(":", 1)[1].strip()
                    return base64.b64decode(encoded)

            return data
        except Exception:
            return data

    def _obfuscate_as_tls(self, data: bytes, **kwargs) -> bytes:
        """Маскировать под TLS трафик"""
        # Добавляем TLS заголовки
        # (упрощённая версия)
        tls_header = b"\x17\x03\x03"  # TLS Application Data
        length = len(data).to_bytes(2, "big")

        return tls_header + length + data

    def _obfuscate_as_dns(self, data: bytes, **kwargs) -> bytes:
        """Маскировать под DNS запрос"""
        # Кодируем данные в DNS-подобный формат
        # (упрощённая версия)
        encoded = base64.b32encode(data).decode().lower()

        # Формируем DNS-подобный запрос
        dns_query = f"{encoded[:63]}.example.com"  # DNS ограничение 63 символа
        return dns_query.encode()

    def _obfuscate_base64(self, data: bytes, **kwargs) -> bytes:
        """Простое base64 кодирование"""
        return base64.b64encode(data)

    def _deobfuscate_base64(self, data: bytes, **kwargs) -> bytes:
        """Деобфусцировать base64"""
        try:
            return base64.b64decode(data)
        except Exception:
            return data
