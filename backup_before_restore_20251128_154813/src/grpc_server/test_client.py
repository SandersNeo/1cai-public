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
            query="Как создать документ в 1С?",
            context="Разработка в 1C:Enterprise",
            user_id="test_user")

        try:
