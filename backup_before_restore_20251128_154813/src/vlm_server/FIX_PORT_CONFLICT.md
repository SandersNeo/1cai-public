# Исправление проблемы с портом 8000

## Проблема

На порту 8000 запущено несколько процессов, что вызывает конфликты.

## Решение

### Шаг 1: Остановить все процессы на порту 8000

```powershell
# Найти все процессы
netstat -ano | findstr :8000

# Остановить процессы (замените PID на реальные из вывода выше)
Stop-Process -Id 24032 -Force
Stop-Process -Id 34320 -Force
Stop-Process -Id 7164 -Force

# Или остановить все Python процессы
Get-Process python | Stop-Process -Force
```

### Шаг 2: Подождать 10 секунд

Дайте системе время освободить порт.

### Шаг 3: Проверить что порт свободен

```powershell
netstat -ano | findstr :8000
```

Должно быть пусто.

### Шаг 4: Перезапустить VLM Server

```powershell
cd c:\1cAI
python src\vlm_server\vlm_service.py
```

### Шаг 5: Проверить в браузере

Открыть: http://localhost:8000/

## Если проблема повторяется

### Вариант 1: Использовать другой порт

Отредактировать `src\vlm_server\vlm_service.py` (строка ~200):

```python
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "vlm_service:app",
        host="0.0.0.0",
        port=8001,  # Изменить на 8001
        reload=True,
        log_level="info"
    )
```

Затем использовать http://localhost:8001/

### Вариант 2: Отключить reload режим

В `vlm_service.py` изменить:

```python
uvicorn.run(
    "vlm_service:app",
    host="0.0.0.0",
    port=8000,
    reload=False,  # Отключить auto-reload
    log_level="info"
)
```

Reload режим создает дополнительные процессы для отслеживания изменений файлов.

## После успешного запуска

Проверить endpoints:

- http://localhost:8000/ - информация о сервисе
- http://localhost:8000/health - проверка здоровья
- http://localhost:8000/docs - Swagger UI документация
