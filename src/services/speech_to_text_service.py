"""
Speech-to-Text Service
Сервис распознавания речи из аудио файлов
Поддержка: OpenAI Whisper, локальные модели
"""

import logging
import os
import tempfile
from typing import Optional, Dict, Any
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


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
        language: str = "ru"
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
            from openai import OpenAI
            
            if not self.api_key:
                raise ValueError("OpenAI API key not provided")
            
            self.client = OpenAI(api_key=self.api_key)
            logger.info("OpenAI Whisper initialized")
            
        except ImportError:
            logger.error("OpenAI package not installed. Install: pip install openai")
            raise
    
    def _init_local_whisper(self):
        """Инициализация локального Whisper"""
        try:
            import whisper
            
            # Загружаем модель (base, small, medium, large)
            model_size = os.getenv("WHISPER_MODEL_SIZE", "base")
            self.whisper_model = whisper.load_model(model_size)
            logger.info(f"Local Whisper initialized (model: {model_size})")
            
        except ImportError:
            logger.error("Whisper package not installed. Install: pip install openai-whisper")
            raise
    
    def _init_vosk(self):
        """Инициализация Vosk (offline STT)"""
        try:
            from vosk import Model, KaldiRecognizer
            import json
            
            model_path = os.getenv("VOSK_MODEL_PATH", "models/vosk-model-ru")
            
            if not os.path.exists(model_path):
                raise ValueError(f"Vosk model not found at {model_path}")
            
            self.vosk_model = Model(model_path)
            logger.info(f"Vosk initialized (model: {model_path})")
            
        except ImportError:
            logger.error("Vosk package not installed. Install: pip install vosk")
            raise
    
    async def transcribe(
        self,
        audio_file_path: str,
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        response_format: str = "text"
    ) -> Dict[str, Any]:
        """
        Распознавание речи из аудио файла
        
        Args:
            audio_file_path: Путь к аудио файлу
            language: Язык (переопределяет self.language)
            prompt: Подсказка для улучшения распознавания
            response_format: Формат ответа (text, json, srt, vtt)
        
        Returns:
            Dict с текстом и метаданными
        """
        lang = language or self.language
        
        try:
            if self.provider == STTProvider.OPENAI_WHISPER:
                return await self._transcribe_openai(
                    audio_file_path,
                    lang,
                    prompt,
                    response_format
                )
            elif self.provider == STTProvider.LOCAL_WHISPER:
                return await self._transcribe_local_whisper(
                    audio_file_path,
                    lang
                )
            elif self.provider == STTProvider.VOSK:
                return await self._transcribe_vosk(audio_file_path)
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            raise
    
    async def _transcribe_openai(
        self,
        audio_file_path: str,
        language: str,
        prompt: Optional[str],
        response_format: str
    ) -> Dict[str, Any]:
        """Распознавание через OpenAI Whisper API"""
        
        try:
            with open(audio_file_path, "rb") as audio_file:
                # Параметры запроса
                kwargs = {
                    "model": self.model,
                    "file": audio_file,
                    "response_format": response_format
                }
                
                if language:
                    kwargs["language"] = language
                
                if prompt:
                    kwargs["prompt"] = prompt
                
                # Вызов API
                response = self.client.audio.transcriptions.create(**kwargs)
                
                # Формирование результата
                if response_format == "text":
                    text = response
                    result = {
                        "text": text,
                        "language": language,
                        "provider": "openai_whisper",
                        "model": self.model
                    }
                else:
                    # JSON, SRT, VTT
                    result = {
                        "text": response.text if hasattr(response, 'text') else str(response),
                        "language": language,
                        "provider": "openai_whisper",
                        "model": self.model,
                        "segments": response.segments if hasattr(response, 'segments') else None
                    }
                
                logger.info(f"OpenAI transcription completed: {len(result['text'])} chars")
                return result
                
        except Exception as e:
            logger.error(f"OpenAI transcription error: {e}")
            raise
    
    async def _transcribe_local_whisper(
        self,
        audio_file_path: str,
        language: str
    ) -> Dict[str, Any]:
        """Распознавание через локальный Whisper"""
        
        try:
            # Распознавание
            result = self.whisper_model.transcribe(
                audio_file_path,
                language=language,
                verbose=False
            )
            
            output = {
                "text": result["text"].strip(),
                "language": result["language"],
                "provider": "local_whisper",
                "model": self.whisper_model.__class__.__name__,
                "segments": result.get("segments", [])
            }
            
            logger.info(f"Local Whisper transcription completed: {len(output['text'])} chars")
            return output
            
        except Exception as e:
            logger.error(f"Local Whisper transcription error: {e}")
            raise
    
    async def _transcribe_vosk(self, audio_file_path: str) -> Dict[str, Any]:
        """Распознавание через Vosk (offline)"""
        
        try:
            from vosk import KaldiRecognizer
            import wave
            import json
            
            # Открываем аудио файл
            wf = wave.open(audio_file_path, "rb")
            
            # Создаем recognizer
            rec = KaldiRecognizer(self.vosk_model, wf.getframerate())
            rec.SetWords(True)
            
            # Распознавание
            full_text = []
            
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    if "text" in result and result["text"]:
                        full_text.append(result["text"])
            
            # Финальный результат
            final_result = json.loads(rec.FinalResult())
            if "text" in final_result and final_result["text"]:
                full_text.append(final_result["text"])
            
            text = " ".join(full_text).strip()
            
            output = {
                "text": text,
                "language": self.language,
                "provider": "vosk",
                "model": "vosk-model"
            }
            
            logger.info(f"Vosk transcription completed: {len(text)} chars")
            return output
            
        except Exception as e:
            logger.error(f"Vosk transcription error: {e}")
            raise
    
    async def transcribe_from_bytes(
        self,
        audio_bytes: bytes,
        filename: str = "audio.ogg",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Распознавание речи из bytes
        
        Args:
            audio_bytes: Аудио данные в bytes
            filename: Имя файла (для определения формата)
            **kwargs: Дополнительные параметры для transcribe()
        
        Returns:
            Dict с текстом и метаданными
        """
        # Сохраняем во временный файл
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=Path(filename).suffix
        ) as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name
        
        try:
            # Распознаем
            result = await self.transcribe(tmp_path, **kwargs)
            return result
            
        finally:
            # Удаляем временный файл
            try:
                os.unlink(tmp_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file {tmp_path}: {e}")
    
    def get_supported_formats(self) -> list:
        """Получить список поддерживаемых форматов аудио"""
        if self.provider == STTProvider.OPENAI_WHISPER:
            # OpenAI Whisper поддерживает множество форматов
            return [
                "mp3", "mp4", "mpeg", "mpga",
                "m4a", "wav", "webm", "ogg"
            ]
        elif self.provider == STTProvider.LOCAL_WHISPER:
            # Локальный Whisper поддерживает всё что ffmpeg
            return [
                "mp3", "mp4", "wav", "ogg", "flac",
                "m4a", "wma", "aac", "webm"
            ]
        elif self.provider == STTProvider.VOSK:
            # Vosk требует WAV 16kHz mono
            return ["wav"]
        
        return []
    
    async def is_supported_format(self, filename: str) -> bool:
        """Проверка поддерживается ли формат файла"""
        ext = Path(filename).suffix.lower().lstrip('.')
        return ext in self.get_supported_formats()


# Singleton instance
_stt_service: Optional[SpeechToTextService] = None


def get_stt_service() -> SpeechToTextService:
    """Получить глобальный экземпляр сервиса"""
    global _stt_service
    
    if _stt_service is None:
        # Определяем провайдера из env
        provider_str = os.getenv("STT_PROVIDER", "openai_whisper")
        provider = STTProvider(provider_str)
        
        _stt_service = SpeechToTextService(
            provider=provider,
            language=os.getenv("STT_LANGUAGE", "ru")
        )
    
    return _stt_service

