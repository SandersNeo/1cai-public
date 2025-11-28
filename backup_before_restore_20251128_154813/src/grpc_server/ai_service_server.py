"""
gRPC Server для 1C AI Stack

Базовый прототип gRPC сервера с mock реализацией всех сервисов.
"""

import asyncio
import logging
from concurrent import futures

# Импорт сгенерированных классов
import ai_service_pb2
import ai_service_pb2_grpc
import grpc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIOrchestratorServicer(ai_service_pb2_grpc.AIOrchestratorServicer):
    """Реализация сервиса AIOrchestrator"""

    async def ProcessQuery(self, request, context):
        """Обработка простого AI запроса"""
        logger.info("ProcessQuery: {request.query}")

        return ai_service_pb2.QueryResponse(
            response=f"Mock ответ на: {request.query}",
            sources=["source1", "source2"],
            confidence=0.95,
            model_used="mock_model",
        )

    async def StreamQuery(self, request, context):
        """Стриминг ответа AI"""
        logger.info("StreamQuery: {request.query}")

        words = f"Это длинный ответ на запрос: {request.query}".split()
        for i, word in enumerate(words):
            yield ai_service_pb2.QueryChunk(
                chunk=word + " ", is_final=(i == len(words) - 1)
            )
            await asyncio.sleep(0.1)

    async def StreamScreenContext(self, request_iterator, context):
        """Двунаправленный стрим для анализа экрана"""
        logger.info("StreamScreenContext started")

        async for frame in request_iterator:
            logger.info("Frame: {frame.window_title}, size: {len(frame.image_data)}")

            yield ai_service_pb2.ContextAnalysis(
                detected_context="1C:Enterprise Form",
                suggestions=["Suggestion 1", "Suggestion 2"],
                active_1c_object="Документ.РеализацияТоваровУслуг",
            )


class CodeGraphServiceServicer(ai_service_pb2_grpc.CodeGraphServiceServicer):
    """Реализация сервиса CodeGraphService"""

    async def SearchCode(self, request, context):
        """Семантический поиск по коду"""
        logger.info("SearchCode: {request.query}")

        result = ai_service_pb2.CodeResult(
            file_path="/src/Module.bsl",
            code_snippet="Функция Test()\n  Возврат Истина;\nКонецФункции",
            line_number=42,
            relevance_score=0.95,
            object_type="ОбщийМодуль",
        )

        return ai_service_pb2.CodeSearchResponse(results=[result], total_found=1)

    async def AnalyzeDependencies(self, request, context):
        """Анализ зависимостей"""
        logger.info("AnalyzeDependencies: {request.module_name}")

        dep = ai_service_pb2.Dependency(
            from_module=request.module_name,
            to_module="ОбщийМодуль.РаботаСДанными",
            dependency_type="import",
        )

        return ai_service_pb2.DependencyResponse(dependencies=[dep])

    async def GetMetadata(self, request, context):
        """Получение метаданных объекта 1С"""
        logger.info("GetMetadata: {request.object_name}")

        return ai_service_pb2.MetadataResponse(
            object_name=request.object_name,
            object_type=request.object_type,
            properties={"Дата": "Дата", "Номер": "Строка(11)"},
            methods=["ПриЗаписи", "Провести"],
        )


class ScenarioServiceServicer(ai_service_pb2_grpc.ScenarioServiceServicer):
    """Реализация сервиса ScenarioService"""

    async def GetRecommendations(self, request, context):
        """Получение рекомендаций сценариев"""
        logger.info("GetRecommendations: {request.current_context}")

        scenario = ai_service_pb2.Scenario(
            id="code_review",
            name="Code Review",
            description="Проверка кода на соответствие стандартам",
            relevance=0.9,
        )
        scenario.required_params.append("file_path")

        return ai_service_pb2.ScenarioResponse(scenarios=[scenario])

    async def ExecuteScenario(self, request, context):
        """Выполнение сценария"""
        logger.info("ExecuteScenario: {request.scenario_id}")

        stages = ["Инициализация", "Анализ", "Генерация", "Завершение"]

        for i, stage in enumerate(stages):
            yield ai_service_pb2.ExecutionStatus(
                stage=stage,
                progress=(i + 1) / len(stages),
                message=f"Выполняется: {stage}",
                is_complete=(i == len(stages) - 1),
                has_error=False,
                error_message="",
            )
            await asyncio.sleep(0.5)


async def serve():
    """Запуск gRPC сервера"""
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))

    # Регистрация сервисов
    ai_service_pb2_grpc.add_AIOrchestratorServicer_to_server(
        AIOrchestratorServicer(), server
    )
    ai_service_pb2_grpc.add_CodeGraphServiceServicer_to_server(
        CodeGraphServiceServicer(), server
    )
    ai_service_pb2_grpc.add_ScenarioServiceServicer_to_server(
        ScenarioServiceServicer(), server
    )

    # Запуск на порту 50051
    server.add_insecure_port("[::]:50051")
    logger.info("✅ gRPC сервер запущен на порту 50051")

    await server.start()
    await server.wait_for_termination()


if __name__ == "__main__":
    logger.info("Запуск gRPC сервера для 1C AI Stack...")
    asyncio.run(serve())
