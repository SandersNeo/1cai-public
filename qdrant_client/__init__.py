"""
Легковесный stub для пакета `qdrant_client`, необходимый юнит-тестам.

Тесты патчат `qdrant_client.QdrantClient`, поэтому достаточно предоставить
одноимённый класс-заглушку.
"""


class QdrantClient:  # pragma: no cover - используется только как точка патча
    def __init__(self, *args, **kwargs):
        raise ImportError("qdrant-client not installed")

