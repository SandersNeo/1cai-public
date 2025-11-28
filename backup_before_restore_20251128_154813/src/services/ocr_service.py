# [NEXUS IDENTITY] ID: 8592565162179014522 | DATE: 2025-11-19

"""
OCR Service for 1C Documents
Версия: 2.2.0
Refactored: Non-blocking execution for CPU/GPU intensive tasks
"""

import asyncio
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class OCRProvider(str, Enum):
    """Провайдеры OCR"""

    DEEPSEEK = "deepseek"  # DeepSeek-OCR (primary, best accuracy 91%+)
    CHANDRA_HF = "chandra_hf"  # Chandra with HuggingFace (fallback)
    CHANDRA_VLLM = "chandra_vllm"  # Chandra with vLLM (faster)
    TESSERACT = "tesseract"  # Fallback для простых случаев


class DocumentType(str, Enum):
    """Типы документов 1С"""

    AUTO = "auto"  # Автоопределение
    CONTRACT = "contract"  # Договор
    ACT = "act"  # Акт
    INVOICE = "invoice"  # Счет
    WAYBILL = "waybill"  # Накладная
    FORM = "form"  # Бланк/форма
    TABLE = "table"  # Таблица
    OTHER = "other"


class OCRResult:
    """Результат OCR распознавания"""

    def __init__(
        self,
        text: str,
        confidence: float = 0.0,
        document_type: DocumentType = DocumentType.OTHER,
        metadata: Optional[Dict] = None,
        structured_data: Optional[Dict] = None,
    ):
        self.text = text
        self.confidence = confidence
        self.document_type = document_type
        self.metadata = metadata or {}
        self.structured_data = structured_data or {}
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь"""
        return {
            "text": self.text,
            "confidence": self.confidence,
            "document_type": self.document_type.value,
            "metadata": self.metadata,
            "structured_data": self.structured_data,
            "timestamp": self.timestamp.isoformat(),
        }


class OCRService:
    """Сервис OCR для документов 1С"""

    def __init__(
        self,
        provider: OCRProvider = OCRProvider.DEEPSEEK,
        enable_ai_parsing: bool = True,
        enable_fallback: bool = True,
    ):
        self.provider = provider
        self.enable_ai_parsing = enable_ai_parsing
        self.enable_fallback = enable_fallback
        self._executor = ThreadPoolExecutor(max_workers=2)

        # Инициализация провайдера
        if provider == OCRProvider.DEEPSEEK:
            self._init_deepseek()
        elif provider == OCRProvider.CHANDRA_HF or provider == OCRProvider.CHANDRA_VLLM:
            self._init_chandra()
        elif provider == OCRProvider.TESSERACT:
            self._init_tesseract()

        # Инициализация fallback провайдеров (если включен)
        if enable_fallback:
            self._init_fallback_providers()

    def _init_deepseek(self):
        """Инициализация DeepSeek-OCR с retry logic"""
        max_retries = 3
        base_delay = 2.0

        for attempt in range(max_retries):
            try:
                    logger.error("Failed to initialize DeepSeek-OCR: %s")
                    self.deepseek_available = False
                    raise

                import time

                time.sleep(base_delay * (2**attempt))

    def _init_chandra(self):
        try: