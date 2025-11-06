# Service Communication Framework

Полнофункциональная система межсервисного взаимодействия для микросервисной архитектуры.

## 🚀 Возможности

- **Service Discovery** - автоматическое обнаружение и регистрация сервисов
- **Health Monitoring** - проверка состояния и доступности сервисов
- **Load Balancing** - интеллектуальное распределение нагрузки
- **Circuit Breaker** - защита от каскадных сбоев
- **Distributed Tracing** - трассировка запросов между сервисами
- **Async Communication** - асинхронные сообщения через Supabase Realtime
- **Event-Driven Architecture** - событийная коммуникация
- **Saga Pattern** - управление распределенными транзакциями
- **Event Sourcing** - событийное хранение и аудит
- **Monitoring & Observability** - метрики, логирование и алертинг

## 📦 Установка

```bash
npm install @shared/service-communication
# или
yarn add @shared/service-communication
```

## 🔧 Быстрый старт

### 1. Базовая инициализация

```typescript
import { ServiceCommunicationManager } from '@shared/service-communication';

const serviceComm = ServiceCommunicationManager.getInstance({
  serviceName: 'order-service',
  serviceVersion: '1.0.0',
  baseUrl: 'http://order-service:3002',
  supabaseUrl: process.env.SUPABASE_URL,
  supabaseKey: process.env.SUPABASE_SERVICE_ROLE_KEY,
  tracingEnabled: true,
  metricsEnabled: true
});

await serviceComm.initialize();
```

### 2. Создание Service Client

```typescript
const userClient = serviceComm.createServiceClient('user-service', {
  baseUrl: 'http://user-service:3001',
  timeout: 30000,
  retries: 3
});

// HTTP вызовы
const user = await userClient.get('/api/users/123');
const newOrder = await userClient.post('/api/orders', {
  userId: '123',
  items: [{ productId: 'prod-1', quantity: 2 }]
});
```

### 3. Асинхронная коммуникация

```typescript
// Подписка на сообщения
serviceComm.subscribeToMessages('user-events', (message) => {
  console.log('User event:', message.payload);
});

// Отправка сообщения
await serviceComm.sendAsyncMessage('order-events', {
  action: 'order.created',
  orderId: 'order-123'
});
```

### 4. Событийная архитектура

```typescript
// Подписка на события
serviceComm.subscribeToEvents('OrderCreated', (event) => {
  console.log('Order created:', event.aggregateId);
});

// Публикация события
await serviceComm.publishEvent('InventoryReserved', 'order-123', {
  items: [{ productId: 'prod-1', quantity: 2 }]
});
```

### 5. Saga Pattern

```typescript
// Создание саги для распределенной транзакции
const saga = serviceComm.createSaga('process_order', [
  {
    id: 'reserve-inventory',
    name: 'Reserve Inventory',
    service: 'inventory-service',
    operation: async () => ({ success: true }),
    compensate: async () => console.log('Compensating inventory')
  },
  {
    id: 'process-payment',
    name: 'Process Payment',
    service: 'payment-service',
    operation: async () => ({ success: true }),
    compensate: async () => console.log('Compensating payment')
  }
]);

const result = await serviceComm.executeSaga(saga.id);
if (result.status === 'FAILED') {
  await serviceComm.compensateSaga(saga.id);
}
```

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                 Service Communication Manager                 │
├─────────────────────────────────────────────────────────────┤
│  Service Registry  │  Health Checker  │  Load Balancer     │
│  Tracing Service   │  Metrics Collector│  Alerting System   │
│  Saga Orchestrator │  Event Sourcing   │  Audit Trail       │
├─────────────────────────────────────────────────────────────┤
│         Service Discovery & Communication Layer              │
├─────────────────────────────────────────────────────────────┤
│  HTTP/REST Client  │  Async Messaging  │  Event System     │
│  Service Clients   │  Circuit Breaker  │  Retry Logic      │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Компоненты

### Service Discovery
- `ServiceRegistry` - реестр сервисов с автоматической регистрацией
- `HealthChecker` - мониторинг состояния сервисов
- Поддержка heartbeat и cleanup

### Load Balancing
- `LoadBalancer` с поддержкой стратегий:
  - Round Robin
  - Least Connections
  - Random
  - Weighted Round Robin
  - IP Hash
- Circuit breaker для защиты от сбоев

### Communication
- `HttpCommunication` - синхронное HTTP/REST взаимодействие
- `AsyncMessageCommunication` - асинхронные сообщения через Supabase
- `EventDrivenCommunication` - событийная архитектура

### Service Client SDK
- `ServiceClient` - универсальный клиент для всех типов коммуникации
- Автоматические retry и circuit breaker
- Distributed tracing
- Метрики и мониторинг

### Error Handling
- `ErrorHandler` - структурированная обработка ошибок
- `RetryManager` - управление повторными попытками
- Поддержка экспоненциальной задержки

### Distributed Tracing
- `TracingService` - полная трассировка запросов
- Correlation IDs для отслеживания цепочки вызовов
- Экспорт в формате Jaeger

### Saga Pattern
- `SagaOrchestrator` - оркестрация распределенных транзакций
- `SagaFactory` - готовые шаблоны саг
- Автоматическая компенсация при ошибках

### Event Sourcing
- `EventStore` - хранение событий
- `EventSourcingRepository` - репозиторий для агрегатов
- `AuditTrail` - полный аудит действий

### Monitoring
- `MetricsCollector` - сбор метрик
- `AlertingSystem` - система алертов
- `StructuredLogger` - структурированное логирование

## ⚙️ Конфигурация

```typescript
interface ServiceCommunicationConfig {
  serviceName: string;
  serviceVersion: string;
  baseUrl: string;
  healthCheckPath?: string;
  
  // Supabase конфигурация
  supabaseUrl?: string;
  supabaseKey?: string;
  
  // Load balancer
  loadBalancerStrategy?: LoadBalancingStrategy;
  circuitBreakerEnabled?: boolean;
  maxRetries?: number;
  retryDelay?: number;
  
  // Tracing
  tracingEnabled?: boolean;
  
  // Monitoring
  metricsEnabled?: boolean;
  alertRules?: AlertRule[];
}
```

## 🔍 Мониторинг

### Метрики
- Request rate, latency, error rate
- CPU, memory, disk usage
- Service dependencies status

### Алерты
- Высокая латентность
- Высокий error rate
- Сервисы недоступны

### Логирование
- Структурированные JSON логи
- Correlation IDs для трейсинга
- Error context и stack traces

## 🧪 Тестирование

```bash
# Запуск примеров
npm run examples

# Unit тесты
npm test

# Lint
npm run lint
```

## 📚 Документация

- 
- [Примеры использования](examples.ts)
- [API Reference](src/index.ts)

## 🔗 Интеграция

### С Supabase Realtime
```typescript
const asyncClient = new AsyncMessageCommunication(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

// Подписка и публикация сообщений
await asyncClient.subscribe('channel', handler);
await asyncClient.publish('channel', message);
```

### С системой мониторинга
```typescript
const metricsCollector = new MetricsCollector(tracingService);

// Автоматический сбор метрик
metricsCollector.recordHttpRequest(
  serviceName, method, path, statusCode, duration, error
);
```

## 🚀 Развертывание

1. **Установите зависимости** в каждый микросервис
2. **Инициализируйте ServiceCommunicationManager** в main приложения
3. **Настройте переменные окружения** (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
4. **Реализуйте health check endpoints** (`/health`)
5. **Настройте централизованное логирование**

## 📊 Лучшие практики

- ✅ Все операции должны быть **идемпотентными**
- ✅ Используйте **circuit breaker** для внешних зависимостей
- ✅ Всегда передавайте **correlation IDs**
- ✅ Настройте meaningful **health checks**
- ✅ Мониторьте ключевые метрики (latency, error rate)
- ✅ Используйте **saga pattern** для сложных бизнес-процессов
- ✅ Применяйте **event sourcing** для критически важных данных

## 🔧 Расширение

Система легко расширяется:

- Добавление новых стратегий load balancing
- Кастомные health checks
- Дополнительные notification channels
- Интеграция с внешними системами мониторинга

## 📄 Лицензия

MIT License

## 🤝 Вклад в развитие

1. Fork репозитория
2. Создайте feature branch
3. Добавьте тесты
4. Запустите lint и тесты
5. Создайте Pull Request

## 📞 Поддержка

- Создайте issue для багов
- Обсуждение в discussions
- Документация в `/docs`