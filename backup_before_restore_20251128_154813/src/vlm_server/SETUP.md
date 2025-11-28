# VLM Server Setup Instructions

## Шаг 1: Установка Ollama

Ollama уже должен быть установлен. Если нет:

```powershell
# Скачать и установить с https://ollama.com/download
# Или через winget (требует подтверждения пользователя)
winget install Ollama.Ollama
```

## Шаг 2: Загрузка модели LLaVA

```powershell
# Запустить Ollama (если не запущен)
ollama serve

# В новом терминале загрузить модель
ollama pull llava:7b

# Проверить установку
ollama list
```

**Ожидаемый вывод:**

```
NAME            ID              SIZE    MODIFIED
llava:7b        abc123def       7.0 GB  2 minutes ago
```

## Шаг 3: Установка Python зависимостей

```powershell
cd c:\1cAI\src\vlm_server
pip install -r requirements.txt
```

## Шаг 4: Запуск VLM Server

```powershell
cd c:\1cAI
python src\vlm_server\vlm_service.py
```

**Ожидаемый вывод:**

```
INFO:__main__:VLM Server starting...
INFO:__main__:✅ Ollama is running
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Шаг 5: Проверка работоспособности

### Вариант 1: Браузер

Открыть http://localhost:8000/health

**Ожидаемый ответ:**

```json
{
  "status": "healthy",
  "ollama": "running",
  "model": "llava:7b"
}
```

### Вариант 2: PowerShell

```powershell
# Health check
Invoke-RestMethod -Uri "http://localhost:8000/health"

# Тест анализа (нужен тестовый скриншот)
$file = Get-Item "path\to\screenshot.jpg"
$form = @{
    file = $file
}
Invoke-RestMethod -Uri "http://localhost:8000/analyze" -Method Post -Form $form
```

## Troubleshooting

### Проблема: "Ollama is not running"

**Решение:**

```powershell
# Запустить Ollama в отдельном терминале
ollama serve
```

### Проблема: "Model not found"

**Решение:**

```powershell
ollama pull llava:7b
```

### Проблема: Медленная обработка

**Решение:**

- Использовать квантизованную модель: `ollama pull llava:7b-q4_0`
- Проверить наличие GPU
- Уменьшить размер изображений

### Проблема: Port 8000 already in use

**Решение:**
Изменить порт в `vlm_service.py`:

```python
uvicorn.run(..., port=8001)
```

## Следующие шаги

После успешного запуска VLM Server:

1. Интегрировать с gRPC сервером
2. Протестировать анализ реальных скриншотов 1С
3. Настроить кэширование и оптимизацию
