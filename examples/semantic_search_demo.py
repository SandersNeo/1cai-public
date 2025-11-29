# [NEXUS IDENTITY] ID: 4332099721619756315 | DATE: 2025-11-19

"""
Пример: семантический поиск по коду 1C AI Stack.

Перед запуском убедитесь, что сервер API запущен:
    docker-compose up -d
"""

import argparse
import sys
from typing import Optional

import requests


def semantic_search(
    query: str,
    api_url: str = "http://localhost:8080",
    configuration: Optional[str] = None,
    limit: int = 5,
) -> None:
    payload = {
        "query": query,
        "limit": limit,
    }
    if configuration:
        payload["configuration"] = configuration

    endpoint = f"{api_url.rstrip('/')}/api/search/semantic"
    response = requests.post(endpoint, json=payload, timeout=30)
    if response.status_code != 200:
        print(f"⚠️  Request failed: {response.status_code} {response.text}")
        sys.exit(1)

    data = response.json()
    results = data.get("results", [])
    if not results:
        print("Нет результатов. Проверьте, что Qdrant и embeddings доступны.")
        return

    print(f"🔎 Найдено результатов: {len(results)} (показаны первые {limit})\n")
    for idx, result in enumerate(results[:limit], start=1):
        score = result.get("score", 0)
        module = result.get("module_name", "unknown module")
        function = result.get("function_name", "unknown function")
        source = result.get("source_path", "")
        snippet = result.get("code_snippet", "")

        print(f"{idx}. {module}.{function}()  (score={score:.4f})")
        if source:
            print(f"   Source: {source}")
        if snippet:
            print("   Snippet:")
            print("   " + "\n   ".join(snippet.splitlines()))
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Semantic code search demo")
    parser.add_argument("query", help='Поисковый запрос, например "как рассчитать налог"')
    parser.add_argument(
        "--config",
        help="Фильтр по конфигурации (например, ERP, ERPCPM)",
        default=None,
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Количество результатов (по умолчанию 5)",
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8080",
        help="URL API (по умолчанию http://localhost:8080)",
    )

    args = parser.parse_args()
    try:
        semantic_search(
            query=args.query,
            api_url=args.api_url,
            configuration=args.config,
            limit=args.limit,
        )
    except requests.RequestException as exc:
        print(f"⚠️  Не удалось выполнить запрос: {exc}")
        print("Убедитесь, что API запущено и доступно по указанному адресу.")
        sys.exit(1)


if __name__ == "__main__":
    main()

