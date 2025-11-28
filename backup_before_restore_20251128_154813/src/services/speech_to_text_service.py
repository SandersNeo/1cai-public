# [NEXUS IDENTITY] ID: -2950740570190882609 | DATE: 2025-11-19

"""
Speech-to-Text Service
Версия: 2.1.0

Улучшения:
- Добавлен timeout для транскрипции
- Улучшена обработка ошибок
- Structured logging
- Retry logic для внешних API с exponential backoff
- Input validation и sanitization
"""

import asyncio
import os
import tempfile
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class STTProvider(str, Enum):
    """Провайдеры Speech-to-Text"""

    OPENAI_WHISPER = "openai_whisper"
    LOCAL_WHISPER = "local_whisper"
    VOSK = "vosk"


class SpeechToTextService:
    """Сервис распознавания речи"""

    def __init__(
        self,
        provider: STTProvider = STTProvider.OPENAI_WHISPER,
        api_key: Optional[str] = None,
        model: str = "whisper-1",
        language: str = "ru",
    ):
        """
        Инициализация сервиса

        Args:
            provider: Провайдер STT
            api_key: API ключ (для OpenAI)
            model: Модель для распознавания
            language: Язык распознавания (ru, en)
        """
        self.provider = provider
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.language = language

        # Инициализация клиента
        if self.provider == STTProvider.OPENAI_WHISPER:
            self._init_openai()
        elif self.provider == STTProvider.LOCAL_WHISPER:
            self._init_local_whisper()
        elif self.provider == STTProvider.VOSK:
            self._init_vosk()

    def _init_openai(self):
        """Инициализация OpenAI Whisper"""
        try:
                "Unexpected error during transcription",
                extra = {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "audio_file_path": audio_file_path,
                    "provider": self.provider.value,
                    "language": lang,
                },
                exc_info = True,
            )
            raise

    async def _transcribe_openai(
        self,
        audio_file_path: str,
        language: str,
        prompt: Optional[str],
        response_format: str,
    ) -> Dict[str, Any]:
        """Распознавание через OpenAI Whisper API с retry logic"""

        max_retries = 3
        base_delay = 1.0

        for attempt in range(max_retries):
            try: