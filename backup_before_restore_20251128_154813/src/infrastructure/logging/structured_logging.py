# [NEXUS IDENTITY] ID: -8276870050083533321 | DATE: 2025-11-19

"""
Structured Logging Setup with Context Propagation
Best Practices:
- JSON structured logging for ELK/Splunk
- Context propagation using contextvars (async-safe)
- Correlation IDs for request tracking
- Integration with OpenTelemetry traces
"""

import logging
import os
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime
from typing import Dict, Optional

from pythonjsonlogger import jsonlogger


class StructuredLogger:
    """
    Structured logging with correlation IDs

    Logs in JSON format for easy parsing in ELK/Splunk
    """

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.setup_json_logging()

    def setup_json_logging(self):
        """
        Setup JSON formatter with best practices

        Features:
        - JSON format for easy parsing
        - Automatic context injection
        - Configurable log level
        - File rotation support
        """
        import logging.handlers

        if self.logger.handlers:
            return

        log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
        handler_level = getattr(logging, log_level_name, logging.INFO)

        formatter = jsonlogger.JsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(message)s %(request_id)s %(user_id)s %(tenant_id)s",
            timestamp=True,
        )

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(handler_level)
        self.logger.addHandler(console_handler)

        log_dir = os.getenv("LOG_DIR", "logs")
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, "app.json.log")
        try:
