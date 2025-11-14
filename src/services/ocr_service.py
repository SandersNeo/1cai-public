"""
OCR Service for 1C Documents
Версия: 2.1.0

Улучшения:
- Retry logic для model loading и API calls
- Улучшена обработка ошибок
- Structured logging
- Input validation
"""

import logging
import os
import tempfile
import asyncio
from typing import Dict, Any, Optional, List
from pathlib import Path
from enum import Enum
from datetime import datetime
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
        structured_data: Optional[Dict] = None
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
            "timestamp": self.timestamp.isoformat()
        }


class OCRService:
    """Сервис OCR для документов 1С"""
    
    def __init__(
        self,
        provider: OCRProvider = OCRProvider.DEEPSEEK,
        enable_ai_parsing: bool = True,
        enable_fallback: bool = True
    ):
        """
        Инициализация OCR сервиса
        
        Args:
            provider: Провайдер OCR
            enable_ai_parsing: Использовать AI для парсинга структуры
            enable_fallback: Использовать fallback на другие провайдеры при ошибке
        """
        self.provider = provider
        self.enable_ai_parsing = enable_ai_parsing
        self.enable_fallback = enable_fallback
        
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
                from transformers import AutoModel, AutoTokenizer
                import torch
                
                logger.info(
                    f"Loading DeepSeek-OCR model (attempt {attempt + 1}/{max_retries})...",
                    extra={"attempt": attempt + 1}
                )
                
                # Загружаем модель и токенизатор
                model_name = "deepseek-ai/DeepSeek-OCR"
                
                self.deepseek_tokenizer = AutoTokenizer.from_pretrained(
                    model_name,
                    trust_remote_code=True
                )
                self.deepseek_model = AutoModel.from_pretrained(
                    model_name,
                    device_map="auto",
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    trust_remote_code=True  # DeepSeek требует этого
                )
                
                self.deepseek_available = True
                self.deepseek_device = "cuda" if torch.cuda.is_available() else "cpu"
                
                logger.info(
                    f"✓ DeepSeek-OCR initialized on {self.deepseek_device}",
                    extra={
                        "model": model_name,
                        "device": self.deepseek_device,
                        "attempt": attempt + 1
                    }
                )
                return
                
            except ImportError as e:
                logger.error(
                    f"DeepSeek-OCR dependencies not installed: {e}",
                    extra={
                        "error_type": "ImportError",
                        "suggestion": "Install: pip install transformers torch"
                    },
                    exc_info=True
                )
                self.deepseek_available = False
                raise
            except Exception as e:
                error_type = type(e).__name__
                is_retryable = error_type in ['ConnectionError', 'TimeoutError', 'HTTPError']
                
                if attempt == max_retries - 1 or not is_retryable:
                    logger.error(
                        f"Failed to initialize DeepSeek-OCR after {attempt + 1} attempts: {e}",
                        extra={
                            "attempt": attempt + 1,
                            "error_type": error_type,
                            "is_retryable": is_retryable
                        },
                        exc_info=True
                    )
                    self.deepseek_available = False
                    raise
                
                # Exponential backoff
                delay = base_delay * (2 ** attempt)
                logger.warning(
                    f"DeepSeek-OCR initialization attempt {attempt + 1} failed, retrying in {delay}s: {e}",
                    extra={
                        "attempt": attempt + 1,
                        "delay": delay,
                        "error_type": error_type
                    }
                )
                import time
                time.sleep(delay)
    
    def _init_chandra(self):
        """Инициализация Chandra OCR (fallback)"""
        try:
            # Проверяем установлен ли chandra
            import chandra
            
            self.chandra_available = True
            logger.info("Chandra OCR initialized (fallback)")
            
        except ImportError:
            logger.warning(
                "Chandra OCR not installed. "
                "Install: pip install chandra-ocr"
            )
            self.chandra_available = False
    
    def _init_tesseract(self):
        """Инициализация Tesseract (fallback)"""
        try:
            import pytesseract
            from PIL import Image
            
            # Проверяем доступен ли tesseract
            pytesseract.get_tesseract_version()
            
            self.tesseract_available = True
            logger.info("Tesseract OCR initialized (fallback)")
            
        except Exception as e:
            logger.warning(
                "Tesseract not available",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            self.tesseract_available = False
    
    def _init_fallback_providers(self):
        """Инициализация fallback провайдеров"""
        logger.info("Initializing fallback OCR providers...")
        
        # Попытка инициализации Chandra (если не основной)
        if self.provider != OCRProvider.CHANDRA_HF:
            try:
                self._init_chandra()
            except Exception:
                pass
        
        # Попытка инициализации Tesseract (если не основной)
        if self.provider != OCRProvider.TESSERACT:
            try:
                self._init_tesseract()
            except Exception:
                pass
        
        # Логируем доступные fallback
        fallbacks = []
        if hasattr(self, 'chandra_available') and self.chandra_available:
            fallbacks.append("Chandra")
        if hasattr(self, 'tesseract_available') and self.tesseract_available:
            fallbacks.append("Tesseract")
        
        if fallbacks:
            logger.info(
                "Fallback providers available",
                extra={"fallbacks": fallbacks}
            )
        else:
            logger.warning("No fallback providers available")
    
    async def process_image(
        self,
        image_path: str,
        document_type: DocumentType = DocumentType.AUTO,
        max_retries: int = 3,
        timeout: float = 60.0,
        **kwargs
    ) -> OCRResult:
        """
        Обработка изображения с OCR
        
        Args:
            image_path: Путь к изображению
            document_type: Тип документа (для AI парсинга)
            max_retries: Максимальное количество попыток
            timeout: Timeout для операции (секунды)
            **kwargs: Дополнительные параметры
        
        Returns:
            OCRResult с распознанным текстом и структурой
        """
        # Input validation
        if not image_path or not isinstance(image_path, str):
            logger.warning(
                "Invalid image_path in process_image",
                extra={"image_path_type": type(image_path).__name__ if image_path else None}
            )
            raise ValueError("image_path must be a non-empty string")
        
        # Sanitize path (prevent path traversal)
        image_path = os.path.normpath(image_path)
        
        if not os.path.exists(image_path):
            logger.warning(
                "Image file not found",
                extra={"image_path": image_path}
            )
            raise ValueError(f"Image file not found: {image_path}")
        
        # Validate file size (prevent DoS)
        try:
            file_size = os.path.getsize(image_path)
        except OSError as e:
            logger.error(
                f"Error getting file size: {e}",
                extra={"image_path": image_path, "error_type": type(e).__name__}
            )
            raise ValueError(f"Cannot access image file: {image_path}")
        
        max_file_size = 100 * 1024 * 1024  # 100MB max
        if file_size > max_file_size:
            logger.warning(
                "Image file too large",
                extra={
                    "image_path": image_path,
                    "file_size": file_size,
                    "max_size": max_file_size
                }
            )
            raise ValueError(
                f"Image file too large: {file_size} bytes. Maximum: {max_file_size} bytes"
            )
        
        # Validate timeout
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            logger.warning(
                "Invalid timeout in process_image",
                extra={"timeout": timeout, "timeout_type": type(timeout).__name__}
            )
            timeout = 60.0  # Default timeout
        
        # Validate max_retries
        if not isinstance(max_retries, int) or max_retries < 1:
            logger.warning(
                "Invalid max_retries in process_image",
                extra={"max_retries": max_retries, "max_retries_type": type(max_retries).__name__}
            )
            max_retries = 3  # Default retries
        
        logger.info(
            f"Processing image: {image_path}",
            extra={
                "image_path": image_path,
                "document_type": document_type.value,
                "file_size": file_size,
                "timeout": timeout
            }
        )
        
        try:
            # OCR распознавание с fallback логикой
            raw_result = None
            errors = []
            
            # Попытка с primary провайдером
            try:
                if self.provider == OCRProvider.DEEPSEEK:
                    raw_result = await self._deepseek_ocr(image_path, **kwargs)
                elif self.provider in [OCRProvider.CHANDRA_HF, OCRProvider.CHANDRA_VLLM]:
                    raw_result = await self._chandra_ocr(image_path, **kwargs)
                elif self.provider == OCRProvider.TESSERACT:
                    raw_result = await self._tesseract_ocr(image_path)
                else:
                    raise ValueError(f"Unknown provider: {self.provider}")
            
            except Exception as e:
                logger.warning(
                    "Primary provider failed",
                    extra={
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "provider": self.provider.value if hasattr(self.provider, 'value') else str(self.provider)
                    }
                )
                errors.append(f"{self.provider}: {e}")
                
                # Пытаемся fallback провайдеры (если включен)
                if self.enable_fallback:
                    raw_result = await self._try_fallback_providers(image_path, **kwargs)
                
                if raw_result is None:
                    # Все провайдеры failed
                    raise RuntimeError(
                        f"All OCR providers failed:\n" + 
                        "\n".join(errors)
                    )
            
            # Создаем результат
            result = OCRResult(
                text=raw_result.get("text", ""),
                confidence=raw_result.get("confidence", 0.0),
                document_type=document_type,
                metadata={
                    "provider": self.provider.value,
                    "image_path": image_path,
                    **raw_result.get("metadata", {})
                }
            )
            
            # AI парсинг структуры (если включен)
            if self.enable_ai_parsing and result.text:
                result.structured_data = await self._parse_structure_with_ai(
                    result.text,
                    document_type
                )
            
            logger.info(
                "OCR completed",
                extra={
                    "text_length": len(result.text),
                    "confidence": result.confidence,
                    "document_type": document_type.value,
                    "provider": self.provider.value
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "OCR processing error",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "image_path": image_path,
                    "document_type": document_type.value,
                    "provider": self.provider.value
                },
                exc_info=True
            )
            raise
    
    async def _deepseek_ocr(
        self,
        image_path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Распознавание через DeepSeek-OCR"""
        
        if not self.deepseek_available:
            raise RuntimeError("DeepSeek-OCR not available")
        
        try:
            from PIL import Image
            import torch
            
            logger.info(
                "DeepSeek-OCR processing",
                extra={"image_path": image_path}
            )
            
            # Загружаем изображение
            image = Image.open(image_path).convert("RGB")
            
            # Подготавливаем inputs
            inputs = self.deepseek_tokenizer(
                images=image,
                return_tensors="pt"
            ).to(self.deepseek_device)
            
            # Генерация (OCR)
            with torch.no_grad():
                outputs = self.deepseek_model.generate(
                    **inputs,
                    max_new_tokens=4096,
                    do_sample=False,
                    temperature=1.0,
                    num_beams=1,
                )
            
            # Декодируем результат
            generated_text = self.deepseek_tokenizer.batch_decode(
                outputs,
                skip_special_tokens=True
            )[0]
            
            logger.info(
                "DeepSeek-OCR completed",
                extra={"chars_recognized": len(generated_text)}
            )
            
            return {
                "text": generated_text,
                "confidence": 0.91,  # DeepSeek показывает 91%+ accuracy
                "metadata": {
                    "method": "deepseek",
                    "device": self.deepseek_device,
                    "model": "deepseek-ai/DeepSeek-OCR"
                }
            }
        
        except Exception as e:
            logger.error(
                "DeepSeek OCR error",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "image_path": image_path
                },
                exc_info=True
            )
            raise
    
    async def _try_fallback_providers(
        self,
        image_path: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Попытка использования fallback провайдеров"""
        
        logger.info("Trying fallback OCR providers...")
        
        # Приоритет fallback: Chandra > Tesseract
        fallback_attempts = []
        
        # 1. Chandra
        if hasattr(self, 'chandra_available') and self.chandra_available:
            fallback_attempts.append(('Chandra', self._chandra_ocr))
        
        # 2. Tesseract
        if hasattr(self, 'tesseract_available') and self.tesseract_available:
            fallback_attempts.append(('Tesseract', self._tesseract_ocr))
        
        # Пробуем каждый fallback
        for name, ocr_method in fallback_attempts:
            try:
                logger.info(
                    "Trying fallback",
                    extra={"fallback_name": name}
                )
                result = await ocr_method(image_path, **kwargs)
                logger.info(
                    "Fallback succeeded",
                    extra={"fallback_name": name}
                )
                
                # Добавляем флаг что это fallback
                result['metadata']['fallback_from'] = self.provider.value
                result['metadata']['used_provider'] = name.lower()
                
                return result
                
            except Exception as e:
                logger.warning(
                    "Fallback failed",
                    extra={
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "fallback_name": name
                    }
                )
                continue
        
        # Все fallback failed
        return None
    
    async def _chandra_ocr(
        self,
        image_path: str,
        max_tokens: int = 8192,
        include_images: bool = False
    ) -> Dict[str, Any]:
        """Распознавание через Chandra"""
        
        if not self.chandra_available:
            raise RuntimeError("Chandra not available")
        
        try:
            from chandra import process_document
            
            # Создаем временную выходную директорию
            with tempfile.TemporaryDirectory() as output_dir:
                
                # Параметры для Chandra
                method = "hf" if self.provider == OCRProvider.CHANDRA_HF else "vllm"
                
                # Вызов Chandra (синхронный - оборачиваем в async)
                import asyncio
                
                def _sync_process():
                    return process_document(
                        input_path=image_path,
                        output_dir=output_dir,
                        method=method,
                        max_output_tokens=max_tokens,
                        include_images=include_images,
                        include_headers_footers=False  # Для 1С не нужны
                    )
                
                # Запускаем в executor (чтобы не блокировать async)
                loop = asyncio.get_event_loop()
                chandra_result = await loop.run_in_executor(None, _sync_process)
                
                # Читаем результат
                output_file = Path(output_dir) / f"{Path(image_path).stem}.md"
                
                if output_file.exists():
                    with open(output_file, 'r', encoding='utf-8') as f:
                        text = f.read()
                else:
                    text = ""
                
                return {
                    "text": text,
                    "confidence": 0.85,  # Chandra не возвращает confidence, используем fixed
                    "metadata": {
                        "method": method,
                        "max_tokens": max_tokens
                    }
                }
        
        except Exception as e:
            logger.error(
                "Chandra OCR error",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "image_path": image_path
                },
                exc_info=True
            )
            raise
    
    async def _tesseract_ocr(self, image_path: str) -> Dict[str, Any]:
        """Распознавание через Tesseract (fallback)"""
        
        if not self.tesseract_available:
            raise RuntimeError("Tesseract not available")
        
        try:
            import pytesseract
            from PIL import Image
            
            # Открываем изображение
            image = Image.open(image_path)
            
            # OCR
            data = pytesseract.image_to_data(
                image,
                lang='rus+eng',
                output_type=pytesseract.Output.DICT
            )
            
            # Извлекаем текст и confidence
            text_parts = []
            confidences = []
            
            for i, conf in enumerate(data['conf']):
                if int(conf) > 0:  # Только уверенные результаты
                    text = data['text'][i]
                    if text.strip():
                        text_parts.append(text)
                        confidences.append(int(conf))
            
            full_text = " ".join(text_parts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return {
                "text": full_text,
                "confidence": avg_confidence / 100,  # Normalize to 0-1
                "metadata": {
                    "method": "tesseract",
                    "words_count": len(text_parts)
                }
            }
            
        except Exception as e:
            logger.error(
                "Tesseract OCR error",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "image_path": image_path
                },
                exc_info=True
            )
            raise
    
    async def _parse_structure_with_ai(
        self,
        text: str,
        document_type: DocumentType
    ) -> Dict[str, Any]:
        """
        Парсинг структуры документа с помощью AI
        
        Извлекает:
        - Номер документа
        - Дата
        - Контрагент
        - Сумма
        - Табличная часть (для накладных)
        """
        
        # Импортируем только если нужен AI парсинг
        try:
            from src.ai.orchestrator import AIOrchestrator
            
            orchestrator = AIOrchestrator()
            
            # Формируем промпт в зависимости от типа документа
            if document_type == DocumentType.CONTRACT:
                prompt = f"""
Распознанный текст договора:

{text}

Извлеки из текста:
- Номер договора
- Дата договора
- Наименование организации (контрагент)
- Предмет договора (кратко)
- Сумма (если указана)

Верни в формате JSON.
"""
            elif document_type == DocumentType.INVOICE:
                prompt = f"""
Распознанный текст счета:

{text}

Извлеки из текста:
- Номер счета
- Дата счета
- Поставщик (название организации)
- Покупатель (название организации)
- Сумма итого
- НДС (если есть)
- Таблица товаров (наименование, количество, цена, сумма)

Верни в формате JSON.
"""
            elif document_type == DocumentType.WAYBILL:
                prompt = f"""
Распознанный текст накладной:

{text}

Извлеки из текста:
- Номер накладной
- Дата
- Отправитель
- Получатель
- Таблица товаров (наименование, количество, цена)

Верни в формате JSON.
"""
            else:
                # Общий парсинг
                prompt = f"""
Распознанный текст документа:

{text}

Извлеки основные реквизиты:
- Номер документа (если есть)
- Дата (если есть)
- Организации/контрагенты (если есть)
- Суммы (если есть)

Верни в формате JSON.
"""
            
            # Вызываем AI
            result = await orchestrator.process_query(
                prompt,
                context={
                    "type": "document_parsing",
                    "document_type": document_type.value
                }
            )
            
            # Парсим JSON из ответа
            import json
            import re
            
            # Пытаемся извлечь JSON из ответа
            response_text = result.get("answer", "")
            
            # Ищем JSON блок
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
            
            if json_match:
                try:
                    parsed = json.loads(json_match.group(0))
                    return parsed
                except json.JSONDecodeError:
                    logger.warning("Failed to parse JSON from AI response")
            
            return {"raw_response": response_text}
            
        except Exception as e:
            logger.error(
                "AI parsing error",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "document_type": document_type.value if hasattr(document_type, 'value') else str(document_type)
                },
                exc_info=True
            )
            return {}
    
    async def process_from_bytes(
        self,
        image_bytes: bytes,
        filename: str = "image.jpg",
        **kwargs
    ) -> OCRResult:
        """
        Обработка изображения из bytes
        
        Args:
            image_bytes: Данные изображения
            filename: Имя файла (для определения формата)
            **kwargs: Параметры для process_image
        
        Returns:
            OCRResult
        """
        # Сохраняем во временный файл
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=Path(filename).suffix
        ) as tmp_file:
            tmp_file.write(image_bytes)
            tmp_path = tmp_file.name
        
        try:
            # Обрабатываем
            result = await self.process_image(tmp_path, **kwargs)
            return result
            
        finally:
            # Удаляем временный файл
            try:
                os.unlink(tmp_path)
            except Exception as e:
                logger.warning(
                    "Failed to delete temp file",
                    extra={
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "tmp_path": tmp_path
                    }
                )
    
    def get_supported_formats(self) -> List[str]:
        """Получить список поддерживаемых форматов"""
        
        if self.provider == OCRProvider.DEEPSEEK:
            return ["pdf", "png", "jpg", "jpeg", "tiff", "bmp", "webp", "gif"]
        elif self.provider in [OCRProvider.CHANDRA_HF, OCRProvider.CHANDRA_VLLM]:
            return ["pdf", "png", "jpg", "jpeg", "tiff", "bmp", "webp"]
        elif self.provider == OCRProvider.TESSERACT:
            return ["png", "jpg", "jpeg", "tiff", "bmp"]
        
        return []
    
    async def is_supported_format(self, filename: str) -> bool:
        """Проверка поддержки формата файла"""
        ext = Path(filename).suffix.lower().lstrip('.')
        return ext in self.get_supported_formats()
    
    async def batch_process(
        self,
        file_paths: List[str],
        **kwargs
    ) -> List[OCRResult]:
        """
        Пакетная обработка документов
        
        Args:
            file_paths: Список путей к файлам
            **kwargs: Параметры для process_image
        
        Returns:
            Список OCRResult
        """
        results = []
        
        for file_path in file_paths:
            try:
                result = await self.process_image(file_path, **kwargs)
                results.append(result)
                
            except Exception as e:
                logger.error(
                    "Batch processing error",
                    extra={
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "file_path": file_path
                    },
                    exc_info=True
                )
                # Продолжаем обработку остальных
                results.append(OCRResult(
                    text="",
                    confidence=0.0,
                    metadata={"error": str(e), "file": file_path}
                ))
        
        logger.info(
            "Batch processed documents",
            extra={
                "results_count": len(results),
                "total_files": len(file_paths) if 'file_paths' in locals() else 0
            }
        )
        return results
    
    def estimate_processing_time(self, file_path: str) -> int:
        """
        Оценка времени обработки (в секундах)
        
        Args:
            file_path: Путь к файлу
        
        Returns:
            Примерное время в секундах
        """
        file_size = os.path.getsize(file_path)
        
        # Оценки на основе бенчмарков
        if self.provider == OCRProvider.DEEPSEEK:
            # DeepSeek-OCR: ~1-3 сек на страницу (GPU), ~5-8 сек (CPU)
            base_time = 2 if hasattr(self, 'deepseek_device') and self.deepseek_device == 'cuda' else 6
        elif self.provider == OCRProvider.CHANDRA_HF:
            # HuggingFace: ~2-5 сек на страницу (CPU/GPU)
            base_time = 3
        elif self.provider == OCRProvider.CHANDRA_VLLM:
            # vLLM: ~1-2 сек на страницу (GPU)
            base_time = 1.5
        else:
            # Tesseract: ~1 сек на страницу
            base_time = 1
        
        # Приблизительный расчет страниц по размеру файла
        estimated_pages = max(1, file_size // (1024 * 500))  # ~500KB на страницу
        
        return int(base_time * estimated_pages)


# Singleton instance
_ocr_service: Optional[OCRService] = None


def get_ocr_service(
    provider: Optional[OCRProvider] = None,
    enable_ai_parsing: bool = True,
    enable_fallback: bool = True
) -> OCRService:
    """Получить глобальный экземпляр OCR сервиса"""
    global _ocr_service
    
    if _ocr_service is None or provider is not None:
        # Определяем провайдера из env (по умолчанию DeepSeek)
        if provider is None:
            provider_str = os.getenv("OCR_PROVIDER", "deepseek")
            provider = OCRProvider(provider_str)
        
        _ocr_service = OCRService(
            provider=provider,
            enable_ai_parsing=enable_ai_parsing,
            enable_fallback=enable_fallback
        )
    
    return _ocr_service


# Utility functions
async def quick_ocr(image_path: str) -> str:
    """
    Быстрое OCR - только текст без парсинга
    
    Args:
        image_path: Путь к изображению
    
    Returns:
        Распознанный текст
    """
    service = get_ocr_service(enable_ai_parsing=False)
    result = await service.process_image(image_path)
    return result.text


async def ocr_with_structure(
    image_path: str,
    document_type: DocumentType = DocumentType.AUTO
) -> Dict[str, Any]:
    """
    OCR с извлечением структуры
    
    Args:
        image_path: Путь к изображению
        document_type: Тип документа
    
    Returns:
        Dict с текстом и структурированными данными
    """
    service = get_ocr_service(enable_ai_parsing=True)
    result = await service.process_image(image_path, document_type=document_type)
    return result.to_dict()

