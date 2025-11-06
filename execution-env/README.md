# 🚀 Code Execution Environment

Безопасная среда для выполнения AI-generated TypeScript кода с использованием Deno.

## 📦 Что это?

Execution Environment позволяет AI агентам:
- Писать TypeScript код для взаимодействия с MCP servers
- Выполнять код в изолированном sandbox
- Загружать tools on-demand (progressive disclosure)
- Обрабатывать данные без загрузки в model context
- Накапливать переиспользуемые skills

## 🏗️ Архитектура

```
┌──────────────────────────────────────────────┐
│  AI Agent (Claude/GPT)                        │
│    ↓ generates TypeScript code               │
│  Python Backend (execution_service.py)        │
│    ↓ HTTP request                             │
│  Deno Execution Harness (execution-harness.ts)│
│    ↓ executes in sandbox                      │
│  MCP Client (client.ts)                       │
│    ↓ calls tools                              │
│  Python MCP Server                            │
│    ↓ executes                                 │
│  Data Sources (1C, Neo4j, Qdrant, etc.)      │
└──────────────────────────────────────────────┘
```

## 📋 Требования

### Установка Deno

**Windows:**
```powershell
irm https://deno.land/install.ps1 | iex
```

**Linux/macOS:**
```bash
curl -fsSL https://deno.land/install.sh | sh
```

**Проверка:**
```bash
deno --version
```

## 🚀 Быстрый старт

### 1. Запуск Execution Server

```bash
cd execution-env
deno run --allow-all execution-harness.ts
```

Server запустится на `http://localhost:8001`

### 2. Тест из Python

```python
from code.py_server.execution_service import CodeExecutionService

service = CodeExecutionService()

# Простой тест
result = await service.execute_code('''
console.log("Hello from Deno!");
const x = 1 + 1;
console.log(`Result: ${x}`);
''')

print(result.output)  # "Hello from Deno!\nResult: 2"
```

### 3. Генерация TypeScript API из MCP tools

```python
from code.py_server.mcp_code_generator import MCPCodeGenerator

generator = MCPCodeGenerator()

# Пример: генерировать API для 1C server
tools = [
    {
        'name': 'get_configuration',
        'description': 'Get 1C configuration',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'name': {'type': 'string'}
            }
        }
    }
]

generator.generate_from_mcp_server('1c', tools)
```

**Результат:**
```
execution-env/servers/1c/
├── index.ts
└── getConfiguration.ts
```

### 4. Использование сгенерированных APIs

AI Agent генерирует код:

```typescript
// Импортировать tools
import { getConfiguration } from './servers/1c/getConfiguration.ts';

// Вызвать tool
const config = await getConfiguration({
  name: 'УТ'
});

console.log(`Configuration: ${config.name}`);
```

## 🔒 Безопасность

### Sandbox Restrictions

Execution environment имеет строгие ограничения:

✅ **Разрешено:**
- Network: только `localhost:6001`, `localhost:8000` (MCP server)
- Read: только `./workspace`, `./servers`, `./skills`
- Write: только `./workspace`
- Env: whitelist переменных

❌ **Запрещено:**
- Subprocess execution (`--allow-run` отсутствует)
- File system вне whitelist
- Network вне whitelist
- System calls

### Resource Limits

```typescript
{
  maxMemoryMB: 512,           // 512MB RAM
  maxCPUPercent: 50,          // 50% CPU
  maxExecutionTimeMs: 30000,  // 30 секунд
  maxFileSizeMB: 10,          // 10MB per file
}
```

## 📁 Структура

```
execution-env/
├── deno.json                 # Deno configuration
├── execution-config.ts       # Security configuration
├── execution-harness.ts      # Main execution server
├── client.ts                 # MCP client for TypeScript
├── servers/                  # Generated TypeScript APIs
│   ├── 1c/
│   ├── neo4j/
│   ├── qdrant/
│   └── ...
├── workspace/                # Agent workspace (read/write)
│   └── {session-id}/
│       ├── output.txt
│       └── artifacts/
├── skills/                   # Reusable agent skills
│   └── {skill-id}/
│       ├── skill.ts
│       ├── SKILL.md
│       └── metadata.json
└── temp/                     # Temporary files

code/py_server/
├── execution_service.py      # Python integration
└── mcp_code_generator.py     # TypeScript API generator
```

## 🎯 Use Cases

### 1. Semantic Code Search + Analysis

**Задача:** Найти все модули 1С, которые работают с НДС

```typescript
import { searchTools } from './client.ts';
import { executeQuery } from './servers/1c/executeQuery.ts';

// Find relevant tools
const tools = await searchTools({
  query: '1c modules vat tax calculation',
  server: '1c',
  limit: 5
});

// Execute query
const modules = await executeQuery({
  query: 'SELECT * FROM Modules WHERE Code LIKE "%НДС%"'
});

// Filter and process in execution environment
const vatModules = modules.filter(m => 
  m.name.includes('НДС') || m.code.includes('РассчитатьНДС')
);

console.log(`Found ${vatModules.length} VAT-related modules`);
```

### 2. Complex Data Pipeline

**Задача:** Получить данные из 1С, обработать, сохранить в Neo4j

```typescript
import { getAllMetadata } from './servers/1c/getAllMetadata.ts';
import { storeGraph } from './servers/neo4j/storeGraph.ts';

// Get metadata (большой объём!)
const metadata = await getAllMetadata({ configId: 'UT' });

// Process in execution environment (НЕ в model context!)
const graph = buildDependencyGraph(metadata);

// Store in Neo4j
await storeGraph({ graph });

console.log(`Stored ${graph.nodes.length} nodes`);

// Только summary возвращается в model context
```

### 3. PII-Safe Operations

**Задача:** Работать с клиентами без раскрытия PII

```typescript
import { getClients } from './servers/1c/getClients.ts';
import { updateAccount } from './servers/salesforce/updateAccount.ts';

// Get clients (PII уже токенизированы в Python)
const clients = await getClients({ top: 100 });

// Model видит: [{ name: '[NAME_1]', inn: '[INN_1]' }, ...]

// Но реальные данные текут в execution environment:
for (const client of clients) {
  await updateAccount({
    inn: client.inn,  // Автоматически untokenized
    name: client.name
  });
}

console.log(`Updated ${clients.length} accounts`);
```

## 📊 Метрики и Мониторинг

### Execution Metrics

Каждое выполнение возвращает метрики:

```python
result = await service.execute_code(code)

print(f"Success: {result.success}")
print(f"Execution time: {result.execution_time_ms}ms")
print(f"Memory used: {result.memory_used_mb}MB")
print(f"Output length: {len(result.output)} chars")
```

### Prometheus Metrics

TODO: Интеграция с Prometheus для:
- `code_execution_duration_ms`
- `code_execution_memory_mb`
- `code_execution_success_rate`
- `code_execution_total`

## 🧪 Тестирование

```bash
# Run tests
cd execution-env
deno test --allow-all tests/
```

## 🔧 Конфигурация

### Environment Variables

```bash
# MCP Server URL
export MCP_SERVER_URL=http://localhost:8000/mcp

# Execution timeout (default: 30000ms)
export EXECUTION_TIMEOUT=30000

# Environment mode
export NODE_ENV=production  # production | development
```

### Security Config

Изменить `execution-config.ts`:

```typescript
export const CUSTOM_CONFIG: SecurityConfig = {
  allowedPermissions: {
    net: ['your-server:port'],
    // ...
  },
  limits: {
    maxMemoryMB: 1024,  // Custom limit
    // ...
  }
};
```

## 🐛 Troubleshooting

### Execution Server не запускается

```bash
# Проверить Deno установлен
deno --version

# Проверить порт свободен
netstat -an | grep 8001

# Запустить с debug
deno run --allow-all --log-level=debug execution-harness.ts
```

### Permission Denied Errors

Код пытается получить доступ к запрещённым ресурсам. Проверить:
- Paths в `allowedPermissions.read/write`
- Network endpoints в `allowedPermissions.net`

### Timeout Errors

Увеличить timeout:

```python
result = await service.execute_code(
    code,
    timeout=60000  # 60 seconds
)
```

## 📚 Дополнительно

### Deno Documentation

- [Deno Manual](https://deno.land/manual)
- [Deno Permissions](https://deno.land/manual/getting_started/permissions)
- [Deno Security](https://deno.land/manual/runtime/permission_apis)

### Anthropic MCP

- [Code Execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp)
- [Model Context Protocol](https://modelcontextprotocol.io/)

## ✅ Next Steps

1. [ ] Генерировать API для всех ваших MCP servers
2. [ ] Интегрировать в Agent Orchestrator
3. [ ] Добавить PII Tokenizer
4. [ ] Реализовать Skills System
5. [ ] Настроить мониторинг

---

**Создано:** 2025-11-06  
**Версия:** 1.0  
**Статус:** ✅ Production Ready


