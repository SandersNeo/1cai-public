# gRPC Server для 1C AI Stack

Базовый прототип gRPC сервера для интеграции с Desktop Client (Everywhere).

## Структура

- `ai_service_server.py` - Основной сервер с реализацией всех сервисов
- `ai_service_pb2.py` - Сгенерированные Protocol Buffers классы (генерируется)
- `ai_service_pb2_grpc.py` - Сгенерированные gRPC классы (генерируется)

## Генерация кода из proto

```bash
cd c:\1cAI
python -m grpc_tools.protoc -I./proto --python_out=./src/grpc_server --grpc_python_out=./src/grpc_server ./proto/ai_service.proto
```

## Установка зависимостей

```bash
pip install grpcio grpcio-tools
```

## Запуск сервера

```bash
python src/grpc_server/ai_service_server.py
```

Сервер запустится на порту `50051`.

## Реализованные сервисы

### AIOrchestrator

- ✅ `ProcessQuery` - Обработка AI запросов (mock)
- ✅ `StreamQuery` - Стриминг ответов (mock)
- ✅ `StreamScreenContext` - Анализ экрана (mock)

### CodeGraphService

- ✅ `SearchCode` - Поиск по коду (mock)
- ✅ `AnalyzeDependencies` - Анализ зависимостей (mock)
- ✅ `GetMetadata` - Метаданные объектов (mock)

### ScenarioService

- ✅ `GetRecommendations` - Рекомендации сценариев (mock)
- ✅ `ExecuteScenario` - Выполнение сценариев (mock)

## Следующие шаги

1. Сгенерировать код из proto файлов
2. Интегрировать с существующим AI Orchestrator
3. Добавить реальную логику вместо mock ответов
4. Настроить mTLS для безопасности
