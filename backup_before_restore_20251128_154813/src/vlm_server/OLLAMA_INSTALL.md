# Установка Ollama для VLM Server

## Проблема

Ollama не установлен в системе.

## Решение

### Вариант 1: Установка через winget (Рекомендуется)

```powershell
winget install Ollama.Ollama
```

**После установки:**

1. Перезапустить PowerShell (чтобы обновился PATH)
2. Проверить установку: `ollama --version`

### Вариант 2: Ручная установка

1. Скачать установщик: https://ollama.com/download/windows
2. Запустить `OllamaSetup.exe`
3. Следовать инструкциям установщика
4. Перезапустить PowerShell

### Вариант 3: Альтернатива - Использовать облачный VLM API

Если установка Ollama вызывает сложности, можно использовать облачные API:

#### OpenAI GPT-4 Vision

```python
# В vlm_service.py заменить на:
import openai

async def analyze_image(self, image_bytes: bytes):
    response = openai.ChatCompletion.create(
        model="gpt-4-vision-preview",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "Проанализируй этот скриншот 1С..."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]
        }]
    )
    return response.choices[0].message.content
```

#### Anthropic Claude Vision

```python
import anthropic

async def analyze_image(self, image_bytes: bytes):
    client = anthropic.Anthropic(api_key="your-api-key")
    response = client.messages.create(
        model="claude-3-opus-20240229",
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": base64_image}},
                {"type": "text", "text": "Проанализируй этот скриншот 1С..."}
            ]
        }]
    )
    return response.content[0].text
```

## Проверка установки Ollama

После установки проверить:

```powershell
# Проверить версию
ollama --version

# Запустить сервер
ollama serve

# В новом терминале - проверить список моделей
ollama list
```

**Ожидаемый вывод:**

```
NAME    ID    SIZE    MODIFIED
```

## Следующие шаги

После успешной установки Ollama:

1. Загрузить модель LLaVA:

```powershell
ollama pull llava:7b
```

2. Запустить VLM Server:

```powershell
python src\vlm_server\vlm_service.py
```

## Troubleshooting

### "ollama" не распознано

- Перезапустить PowerShell
- Проверить PATH: `$env:Path -split ';' | Select-String ollama`
- Переустановить Ollama

### Ollama установлен, но не запускается

```powershell
# Проверить процесс
Get-Process ollama -ErrorAction SilentlyContinue

# Убить зависший процесс
Stop-Process -Name ollama -Force

# Запустить заново
ollama serve
```

### Нет прав администратора для установки

Использовать Вариант 3 (облачные API) или попросить администратора установить Ollama.
