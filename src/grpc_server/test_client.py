"""
Простой тест gRPC клиента для проверки связи с сервером
"""

import asyncio

import ai_service_pb2
import ai_service_pb2_grpc
import grpc


async def test_process_query():
    """Тест простого запроса к AI"""
    async with grpc.aio.insecure_channel("localhost:50051") as channel:
        stub = ai_service_pb2_grpc.AIOrchestratorStub(channel)

        request = ai_service_pb2.QueryRequest(
            query="Как создать документ в 1С?", context="Разработка в 1C:Enterprise", user_id="test_user"
        )

        try:
            response = await stub.ProcessQuery(request)
            print(f"✅ ProcessQuery успешно:")
            print(f"   Ответ: {response.response}")
            print(f"   Источники: {list(response.sources)}")
            print(f"   Уверенность: {response.confidence}")
            print(f"   Модель: {response.model_used}")
            return True
        except grpc.RpcError as e:
            print(f"❌ Ошибка ProcessQuery: {e.code()} - {e.details()}")
            return False


async def test_stream_query():
    """Тест стриминга ответа"""
    async with grpc.aio.insecure_channel("localhost:50051") as channel:
        stub = ai_service_pb2_grpc.AIOrchestratorStub(channel)

        request = ai_service_pb2.QueryRequest(
            query="Объясни архитектуру 1С", user_id="test_user")

        try:
            print("✅ StreamQuery успешно:")
            print("   Ответ: ", end="")
            async for chunk in stub.StreamQuery(request):
                print(chunk.chunk, end="", flush=True)
            print()
            return True
        except grpc.RpcError as e:
            print(f"❌ Ошибка StreamQuery: {e.code()} - {e.details()}")
            return False


async def test_search_code():
    """Тест поиска по коду"""
    async with grpc.aio.insecure_channel("localhost:50051") as channel:
        stub = ai_service_pb2_grpc.CodeGraphServiceStub(channel)

        request = ai_service_pb2.CodeSearchRequest(
            query="ПолучитьЗначение", language="bsl", max_results=10)

        try:
            response = await stub.SearchCode(request)
            print(f"✅ SearchCode успешно:")
            print(f"   Найдено результатов: {response.total_found}")
            for result in response.results:
                print(f"   - {result.file_path}:{result.line_number}")
                print(f"     Релевантность: {result.relevance_score}")
            return True
        except grpc.RpcError as e:
            print(f"❌ Ошибка SearchCode: {e.code()} - {e.details()}")
            return False


async def test_get_recommendations():
    """Тест получения рекомендаций сценариев"""
    async with grpc.aio.insecure_channel("localhost:50051") as channel:
        stub = ai_service_pb2_grpc.ScenarioServiceStub(channel)

        request = ai_service_pb2.ScenarioRequest(
            current_context="Разработка документа", user_role="Developer")

        try:
            response = await stub.GetRecommendations(request)
            print(f"✅ GetRecommendations успешно:")
            print(f"   Найдено сценариев: {len(response.scenarios)}")
            for scenario in response.scenarios:
                print(f"   - {scenario.name}: {scenario.description}")
                print(f"     Релевантность: {scenario.relevance}")
            return True
        except grpc.RpcError as e:
            print(f"❌ Ошибка GetRecommendations: {e.code()} - {e.details()}")
            return False


async def run_all_tests():
    """Запуск всех тестов"""
    print("=" * 60)
    print("🧪 Запуск тестов gRPC клиента")
    print("=" * 60)
    print()

    results = []

    print("1️⃣ Тест AIOrchestrator.ProcessQuery")
    results.append(await test_process_query())
    print()

    print("2️⃣ Тест AIOrchestrator.StreamQuery")
    results.append(await test_stream_query())
    print()

    print("3️⃣ Тест CodeGraphService.SearchCode")
    results.append(await test_search_code())
    print()

    print("4️⃣ Тест ScenarioService.GetRecommendations")
    results.append(await test_get_recommendations())
    print()

    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"📊 Результаты: {passed}/{total} тестов пройдено")

    if passed == total:
        print("✅ Все тесты успешно пройдены!")
    else:
        print(f"⚠️ {total - passed} тест(ов) не пройдено")
    print("=" * 60)


if __name__ == "__main__":
    print("Убедитесь, что gRPC сервер запущен на localhost:50051")
    print("Запустите: python src/grpc_server/ai_service_server.py")
    print()

    asyncio.run(run_all_tests())
