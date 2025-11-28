"""
Тестовый скрипт для проверки VLM Server
"""

import asyncio

import httpx


async def test_health():
    """Проверка health endpoint"""
    print("1️⃣ Тест Health Check...")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8000/health", timeout=5.0)
            result = response.json()

            print(f"   ✅ Status: {result['status']}")
            print(f"   ✅ Ollama: {result['ollama']}")
            print(f"   ✅ Model: {result['model']}")
            return True
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            return False


async def test_root():
    """Проверка root endpoint"""
    print("\n2️⃣ Тест Root Endpoint...")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8000/", timeout=5.0)
            result = response.json()

            print(f"   ✅ Service: {result['service']}")
            print(f"   ✅ Version: {result['version']}")
            return True
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            return False


async def test_analyze_mock():
    """Тест анализа с mock изображением"""
    print("\n3️⃣ Тест Анализа Изображения (Mock)...")

    # Создаем простое тестовое изображение
    import io

    from PIL import Image, ImageDraw

    # Создаем изображение с текстом "1С:Предприятие"
    img = Image.new("RGB", (800, 600), color="white")
    draw = ImageDraw.Draw(img)

    # Рисуем простую "форму"
    draw.rectangle([50, 50, 750, 550], outline="black", width=2)
    draw.text((100, 100), "1С:Предприятие", fill="black")
    draw.text((100, 150), "Документ: Реализация товаров и услуг", fill="black")
    draw.rectangle([100, 200, 300, 240], outline="blue", width=2)
    draw.text((110, 210), "Кнопка: Провести", fill="blue")

    # Сохраняем в байты
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            files = {"file": ("test.jpg", img_bytes, "image/jpeg")}
            response = await client.post("http://localhost:8000/analyze", files=files)
            result = response.json()

            print(f"   ✅ Model: {result['model']}")
            print(f"   ✅ Processing time: {result['processing_time']:.2f}s")
            print(f"   ✅ Image size: {result['image_size']}")
            print(f"\n   📊 Analysis result:")
            print(f"   {result['analysis'][:500]}...")  # Первые 500 символов

            return True
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            return False


async def run_all_tests():
    """Запуск всех тестов"""
    print("=" * 60)
    print("🧪 Тестирование VLM Server")
    print("=" * 60)
    print()

    results = []

    # Тест 1: Health
    results.append(await test_health())

    # Тест 2: Root
    results.append(await test_root())

    # Тест 3: Analyze
    results.append(await test_analyze_mock())

    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"📊 Результаты: {passed}/{total} тестов пройдено")

    if passed == total:
        print("✅ Все тесты успешно пройдены!")
    else:
        print(f"⚠️ {total - passed} тест(ов) не пройдено")
    print("=" * 60)


if __name__ == "__main__":
    print("Убедитесь, что VLM Server запущен на localhost:8000")
    print("Запустите: python src/vlm_server/vlm_service.py")
    print()

    asyncio.run(run_all_tests())
