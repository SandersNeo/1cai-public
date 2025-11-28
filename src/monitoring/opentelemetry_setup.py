# Обратная совместимость - реэкспорт из нового расположения
from src.infrastructure.monitoring.opentelemetry_setup import (
    OPENTELEMETRY_AVAILABLE,
    get_meter,
    get_tracer,
    instrument_asyncpg,
    instrument_fastapi_app,
    instrument_httpx,
    instrument_redis,
    setup_opentelemetry,
)

__all__ = [
    "setup_opentelemetry",
    "instrument_fastapi_app",
    "instrument_asyncpg",
    "instrument_httpx",
    "instrument_redis",
    "get_tracer",
    "get_meter",
    "OPENTELEMETRY_AVAILABLE",
]
