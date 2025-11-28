from typing import Any, Dict

from src.ai.clients.gigachat_client import GigaChatClient, GigaChatConfig
from src.ai.clients.naparnik_client import NaparnikClient, NaparnikConfig
from src.ai.clients.ollama_client import OllamaClient, OllamaConfig
from src.ai.clients.tabnine_client import TabnineClient, TabnineConfig
from src.ai.clients.yandexgpt_client import YandexGPTClient, YandexGPTConfig
from src.ai.strategies.base import AIStrategy
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class GigaChatStrategy(AIStrategy):
    def __init__(self):
        try:
