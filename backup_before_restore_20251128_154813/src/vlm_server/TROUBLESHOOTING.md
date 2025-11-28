# Диагностика проблемы VLM Server

## Проблема

```
❌ Ошибка: Server disconnected without sending a response.
```

Это означает, что VLM Server не отвечает на запросы.

## Возможные причины

### 1. VLM Server не запущен на порту 8000

Проверить:

```powershell
netstat -ano | findstr :8000
```

Если пусто - сервер не запущен.

### 2. VLM Server запущен, но с ошибками

Проверить логи в терминале где запущен VLM Server.

### 3. Ollama не запущен

Проверить:

```powershell
ollama list
```

## Решение

### Вариант 1: Перезапустить VLM Server

1. Остановить текущий VLM Server (Ctrl+C в терминале)

2. Убедиться что Ollama запущен:

```powershell
# В отдельном терминале
ollama serve
```

3. Запустить VLM Server заново:

```powershell
cd c:\1cAI
python src\vlm_server\vlm_service.py
```

**Ожидаемый вывод:**

```
INFO:__main__:VLM Server starting...
INFO:__main__:✅ Ollama is running
INFO:     Started server process [12345]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Вариант 2: Проверить через браузер

Открыть в браузере: http://localhost:8000/

Должны увидеть:

```json
{
  "service": "VLM Server",
  "version": "1.0.0",
  "model": "llava:7b",
  "status": "running"
}
```

### Вариант 3: Проверить health через curl/PowerShell

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/health"
```

## Если проблема сохраняется

### Проверить зависимости

```powershell
pip list | Select-String "fastapi|uvicorn|httpx"
```

Должны быть установлены:

- fastapi
- uvicorn
- httpx
- pillow
- python-multipart

### Установить недостающие

```powershell
pip install -r src\vlm_server\requirements.txt
```

### Проверить конфликт портов

```powershell
# Найти процесс на порту 8000
netstat -ano | findstr :8000

# Если занят - убить процесс
Stop-Process -Id <PID> -Force

# Или изменить порт в vlm_service.py (строка ~200):
# uvicorn.run(..., port=8001)
```

## Альтернатива: Упрощенная версия без Ollama

Если Ollama вызывает проблемы, можно временно использовать mock VLM:

```python
# В vlm_service.py заменить analyze_image на:
async def analyze_image(self, image_bytes: bytes) -> Dict[str, Any]:
    """Mock анализ без Ollama"""
    return {
        "analysis": json.dumps({
            "object_type": "Документ",
            "object_name": "Реализация товаров и услуг",
            "ui_elements": ["Кнопка Провести", "Поле Дата", "Поле Контрагент"],
            "fields": ["Дата: 22.11.2025", "Номер: 00000001"],
            "buttons": ["Провести", "Записать", "Закрыть"],
            "issues": []
        }),
        "model": "mock",
        "processing_time": 0.1,
        "image_size": [800, 600]
    }
```

Это позволит продолжить интеграцию с gRPC пока решаем проблемы с Ollama.
