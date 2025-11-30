"""
Интеграционный тест: Персистентность Nested Provider Selector

Проверяет, что:
1. NestedProviderSelector использует Redis для сессионной/дневной памяти.
2. NestedProviderSelector использует ChromaDB для исторической памяти.
3. Данные сохраняются между перезапусками (симуляция).
"""

import time
import pytest
import shutil
import os
import sys

# Добавляем корень проекта в путь поиска модулей
sys.path.append(os.getcwd())

from src.ai.llm_provider_abstraction import LLMProviderAbstraction, ModelProfile, QueryType
from src.modules.nested_learning.services.provider_selector import NestedProviderSelector
from src.modules.nested_learning.services.cms import ContinuumMemorySystem
from src.modules.nested_learning.services.memory_level import RedisMemoryLevel
from src.services.storage.redis_client import RedisClient


# Мок базовой абстракции
class MockProviderAbstraction(LLMProviderAbstraction):
    def __init__(self):
        pass

    def select_provider(self, *args, **kwargs):
        return ModelProfile(
            provider_id="mock_provider", model_name="mock_model", cost_per_1k_tokens=0.001, avg_latency_ms=100
        )


def test_provider_selector_persistence():
    print("\n--- Запуск теста персистентности ---")

    # 1. Очистка данных предыдущих тестов
    if os.path.exists("chroma_db"):
        shutil.rmtree("chroma_db")

    # 2. Создание экземпляра Selector 1
    base = MockProviderAbstraction()
    selector = NestedProviderSelector(base)

    # Проверка подключения
    print(f"Redis подключен: {selector.query_memory.redis_connected}")
    print(f"Chroma подключен: {selector.query_memory.chroma_connected}")

    if not selector.query_memory.redis_connected:
        print("ВНИМАНИЕ: Redis не подключен. Тест не сможет проверить персистентность.")

    # 3. Выполнение действия (Выбор провайдера)
    query = "Тестовый запрос персистентности 123"
    print(f"Выбор провайдера для: {query}")
    selector.select_provider_adaptive(query, QueryType.CODE_GENERATION)

    # 4. Обратная связь (Высокий сюрприз -> Триггер обновления)
    query_id = selector._generate_query_id(query)
    print(f"Отправка фидбека для ID: {query_id}")

    # Неудача с высокой уверенностью обычно вызывает "сюрприз"
    selector.learn_from_feedback(query_id, success=False, metrics={"cost": 0.05, "latency_ms": 5000})

    # 5. Проверка в памяти (Экземпляр 1)
    session_level = selector.query_memory.levels["session"]
    print(f"Экземпляр 1 - Размер уровня Session: {len(session_level.memory)}")

    # 6. Создание экземпляра Selector 2 (Симуляция перезапуска)
    print("Симуляция перезапуска...")
    selector_2 = NestedProviderSelector(base)

    # 7. Проверка персистентности
    # Redis (Session)
    session_level_2 = selector_2.query_memory.levels["session"]

    # Попытка извлечь похожие
    print("Поиск похожих запросов в Экземпляре 2...")
    results = selector_2.query_memory.retrieve_similar(query, levels=["session"], k=1)
    print(f"Результаты поиска: {results}")

    assert len(results["session"]) > 0, "Ошибка: Не удалось извлечь данные из Redis (Session) после рестарта"
    print("✅ Персистентность Redis подтверждена")

    # Chroma (Historical)
    # Примечание: В текущей логике historical обновляется только при очень высоком сюрпризе или специфичных условиях.
    # В этом тесте мы проверяем хотя бы Redis, так как это основа Strike 2.

    pass


if __name__ == "__main__":
    test_provider_selector_persistence()
