"""
VLM Server для анализа скриншотов 1С

Использует LLaVA-1.6 через Ollama для анализа UI и извлечения контекста.
"""

import base64
import io
import logging
import time
from typing import Any, Dict

import httpx
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="VLM Server",
              description="Vision-Language Model сервер для анализа скриншотов 1С", version="1.0.0")

# Конфигурация
OLLAMA_URL = "http://localhost:11434"
MODEL = "llava:7b"
MAX_IMAGE_SIZE = 1024


class VLMService:
    """Сервис для работы с VLM моделью"""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def check_ollama_health(self) -> bool:
        """Проверка доступности Ollama"""
        try:
            response = await self.client.get(f"{OLLAMA_URL}/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.error("Ollama health check failed: %s", e)
            return False

    async def analyze_image(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Анализ изображения через LLaVA

        Args:
            image_bytes: Байты изображения

        Returns:
            Dict с результатами анализа
        """
        start_time = time.time()

        try:
            # Загрузка и обработка изображения
            image = Image.open(io.BytesIO(image_bytes))
            logger.info(f"Image loaded: {image.size}, mode: {image.mode}")

            # Resize если нужно
            if max(image.size) > MAX_IMAGE_SIZE:
                image.thumbnail((MAX_IMAGE_SIZE, MAX_IMAGE_SIZE))
                logger.info(f"Image resized to: {image.size}")

            # Конвертация в RGB если нужно
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Конвертация в base64
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG", quality=85)
            img_base64 = base64.b64encode(buffered.getvalue()).decode()

            # Промпт для анализа 1С
            prompt = """Проанализируй этот скриншот программы 1С:Enterprise.

Определи и верни в формате JSON:
{
  "object_type": "тип объекта (Документ/Справочник/Отчет/Обработка/Форма)",
  "object_name": "название объекта если видно",
  "ui_elements": ["список видимых элементов UI"],
  "fields": ["список полей и их значений"],
  "buttons": ["список кнопок"],
  "issues": ["возможные проблемы или ошибки если есть"]
}

Если это не 1С, укажи что видишь на скриншоте."""

            # Запрос к Ollama
            payload = {
                "model": MODEL,
                "prompt": prompt,
                "images": [img_base64],
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Низкая температура для точности
                    "num_predict": 500,  # Максимум токенов
                },
            }

            logger.info("Sending request to Ollama (model: %s)", MODEL)
            response = await self.client.post(f"{OLLAMA_URL}/api/generate", json=payload)
            response.raise_for_status()

            result = response.json()
            processing_time = time.time() - start_time

            logger.info(f"Analysis completed in {processing_time:.2f}s")

            return {
                "analysis": result.get("response", ""),
                "model": MODEL,
                "processing_time": processing_time,
                "image_size": image.size,
            }

        except Exception as e:
            logger.error("Image analysis failed: %s", e)
            raise HTTPException(status_code=500, detail=str(e))


# Инициализация сервиса
vlm_service = VLMService()


@app.get("/")
async def root():
    """Корневой endpoint"""
    return {"service": "VLM Server", "version": "1.0.0", "model": MODEL, "status": "running"}


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    ollama_healthy = await vlm_service.check_ollama_health()

    return {
        "status": "healthy" if ollama_healthy else "degraded",
        "ollama": "running" if ollama_healthy else "not running",
        "model": MODEL,
    }


@app.post("/analyze")
async def analyze_screenshot(file: UploadFile = File(...)):
    """
    Анализ скриншота

    Args:
        file: Загруженное изображение (JPEG/PNG)

    Returns:
        JSON с результатами анализа
    """
    # Валидация типа файла
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400, detail=f"Invalid file type: {file.content_type}. Expected image/*")

    # Чтение файла
    image_bytes = await file.read()

    # Валидация размера (макс 10 MB)
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400, detail="Image too large. Maximum size is 10 MB")

    logger.info(f"Analyzing image: {file.filename}, size: {len(image_bytes)} bytes")

    # Анализ
    result = await vlm_service.analyze_image(image_bytes)

    return JSONResponse(content=result)


@app.on_event("startup")
async def startup_event():
    """Действия при запуске"""
    logger.info("VLM Server starting...")

    # Проверка Ollama
    if await vlm_service.check_ollama_health():
        logger.info("✅ Ollama is running")
    else:
        logger.warning("⚠️ Ollama is not running. Please start it with: ollama serve")


@app.on_event("shutdown")
async def shutdown_event():
    """Действия при остановке"""
    logger.info("VLM Server shutting down...")
    await vlm_service.client.aclose()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("vlm_service:app", host="0.0.0.0",
                port=8000, reload=True, log_level="info")
