# VLM Server

Vision-Language Model сервер для анализа скриншотов 1С.

## Требования

- Python 3.11+
- Ollama
- LLaVA-1.6 модель

## Установка

### 1. Установка Ollama

```bash
# Windows
winget install Ollama.Ollama

# Или скачать с https://ollama.com/download
```

### 2. Загрузка модели

```bash
# Загрузить LLaVA-1.6 (7B)
ollama pull llava:7b

# Или квантизованную версию (4 GB)
ollama pull llava:7b-q4_0

# Проверить
ollama list
```

### 3. Установка Python зависимостей

```bash
pip install fastapi uvicorn pillow httpx python-multipart
```

## Запуск

### 1. Запустить Ollama (если не запущен)

```bash
ollama serve
```

### 2. Запустить VLM Server

```bash
cd c:\1cAI
python src/vlm_server/vlm_service.py
```

Сервер запустится на `http://localhost:8000`

## API Endpoints

### GET /

Информация о сервисе

### GET /health

Проверка здоровья сервиса и Ollama

### POST /analyze

Анализ скриншота

**Request:**

- Content-Type: multipart/form-data
- Body: file (image/jpeg или image/png)

**Response:**

```json
{
  "analysis": "JSON с результатами анализа",
  "model": "llava:7b",
  "processing_time": 1.5,
  "image_size": [1024, 768]
}
```

## Использование

### cURL

```bash
curl -X POST "http://localhost:8000/analyze" \
  -F "file=@screenshot.jpg"
```

### Python

```python
import httpx

async with httpx.AsyncClient() as client:
    with open("screenshot.jpg", "rb") as f:
        files = {"file": ("screenshot.jpg", f, "image/jpeg")}
        response = await client.post("http://localhost:8000/analyze", files=files)
        result = response.json()
        print(result["analysis"])
```

### C# (для Everywhere)

```csharp
using var client = new HttpClient();
using var content = new MultipartFormDataContent();
using var fileContent = new ByteArrayContent(imageBytes);
fileContent.Headers.ContentType = new MediaTypeHeaderValue("image/jpeg");
content.Add(fileContent, "file", "screenshot.jpg");

var response = await client.PostAsync("http://localhost:8000/analyze", content);
var result = await response.Content.ReadAsStringAsync();
```

## Конфигурация

Настройки в `vlm_service.py`:

- `OLLAMA_URL` - URL Ollama сервера (по умолчанию: http://localhost:11434)
- `MODEL` - Используемая модель (по умолчанию: llava:7b)
- `MAX_IMAGE_SIZE` - Максимальный размер изображения (по умолчанию: 1024px)

## Мониторинг

Логи выводятся в stdout:

```
INFO:__main__:VLM Server starting...
INFO:__main__:✅ Ollama is running
INFO:__main__:Analyzing image: screenshot.jpg, size: 245678 bytes
INFO:__main__:Image loaded: (1920, 1080), mode: RGB
INFO:__main__:Image resized to: (1024, 576)
INFO:__main__:Sending request to Ollama (model: llava:7b)
INFO:__main__:Analysis completed in 1.52s
```

## Оптимизация

### Для систем с ограниченными ресурсами:

1. Использовать квантизованную модель:

```bash
ollama pull llava:7b-q4_0
```

2. Уменьшить MAX_IMAGE_SIZE в конфиге:

```python
MAX_IMAGE_SIZE = 768  # Вместо 1024
```

3. Использовать CPU (если нет GPU):

```bash
# Ollama автоматически использует CPU если нет GPU
```

## Troubleshooting

### Ollama не запускается

```bash
# Проверить статус
ollama list

# Перезапустить
ollama serve
```

### Модель не найдена

```bash
# Загрузить модель
ollama pull llava:7b
```

### Медленная обработка

- Проверить наличие GPU
- Использовать квантизованную модель
- Уменьшить размер изображений
