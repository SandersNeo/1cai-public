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

app = FastAPI(
    title="VLM Server",
    description="Vision-Language Model сервер для анализа скриншотов 1С",
    version="1.0.0")

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
