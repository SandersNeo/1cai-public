# [NEXUS IDENTITY] ID: -7667832680072902877 | DATE: 2025-11-19

"""
Unit Tests для OCRService
"""

import pytest

from src.services.ocr_service import (DocumentType, OCRProvider, OCRResult,
                                      OCRService, ocr_with_structure,
                                      quick_ocr)


class TestOCRService:
    """Тесты для OCRService"""

    @pytest.fixture
    def ocr_service(self):
        """Fixture для OCR сервиса (без AI парсинга для быстрых тестов)"""
        return OCRService(provider=OCRProvider.CHANDRA_HF, enable_ai_parsing=False)

    @pytest.fixture
    def sample_image_path(self, tmp_path):
        """Создает тестовое изображение"""
        # Создаем простое изображение с текстом
        try:
            from PIL import Image, ImageDraw

            img = Image.new("RGB", (800, 600), color="white")
            draw = ImageDraw.Draw(img)

            # Рисуем текст
            text = """
            ДОГОВОР № 123
            от 01.11.2024

            Поставщик: ООО "Рога и Копыта"
            Покупатель: ООО "Тестовая Компания"

            Сумма: 100,000.00 руб
            """

            draw.text((50, 50), text, fill="black")

            # Сохраняем
            image_path = tmp_path / "test_contract.png"
            img.save(image_path)

            return str(image_path)

        except ImportError:
            pytest.skip("PIL not installed")

    def test_service_initialization(self, ocr_service):
        """Тест инициализации сервиса"""
        assert ocr_service is not None
        assert ocr_service.provider == OCRProvider.CHANDRA_HF
        assert ocr_service.enable_ai_parsing == False

    def test_supported_formats(self, ocr_service):
        """Тест поддерживаемых форматов"""
        formats = ocr_service.get_supported_formats()

        assert "pdf" in formats
        assert "png" in formats
        assert "jpg" in formats
        assert "jpeg" in formats

    @pytest.mark.asyncio
    async def test_is_supported_format(self, ocr_service):
        """Тест проверки формата файла"""
        assert await ocr_service.is_supported_format("test.pdf") == True
        assert await ocr_service.is_supported_format("test.png") == True
        assert await ocr_service.is_supported_format("test.jpg") == True
        assert await ocr_service.is_supported_format("test.txt") == False
        assert await ocr_service.is_supported_format("test.bsl") == False

    def test_estimate_processing_time(self, ocr_service, sample_image_path):
        """Тест оценки времени обработки"""
        estimate = ocr_service.estimate_processing_time(sample_image_path)

        assert isinstance(estimate, int)
        assert estimate > 0
        assert estimate < 60  # Не больше минуты для одного файла

    @pytest.mark.asyncio
    @pytest.mark.slow  # Помечаем как медленный тест (требует Chandra)
    async def test_process_image_basic(self, ocr_service, sample_image_path):
        """Тест базового OCR распознавания"""

        # Пропускаем если Chandra не установлен
        try:
            pass
        except ImportError:
            pytest.skip("Chandra not installed")

        result = await ocr_service.process_image(sample_image_path)

        assert isinstance(result, OCRResult)
        assert result.text is not None
        assert result.confidence >= 0.0
        assert result.confidence <= 1.0
        assert result.document_type is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_process_with_document_type(self, ocr_service, sample_image_path):
        """Тест OCR с указанием типа документа"""

        try:
            pass
        except ImportError:
            pytest.skip("Chandra not installed")

        result = await ocr_service.process_image(
            sample_image_path, document_type=DocumentType.CONTRACT
        )

        assert result.document_type == DocumentType.CONTRACT

    @pytest.mark.asyncio
    async def test_process_from_bytes(self, ocr_service, sample_image_path):
        """Тест обработки из bytes"""

        try:
            pass
        except ImportError:
            pytest.skip("Chandra not installed")

        # Читаем файл в bytes
        with open(sample_image_path, "rb") as f:
            image_bytes = f.read()

        result = await ocr_service.process_from_bytes(image_bytes, filename="test.png")

        assert isinstance(result, OCRResult)
        assert result.text is not None

    def test_ocr_result_to_dict(self):
        """Тест конвертации OCRResult в словарь"""
        result = OCRResult(
            text="Test text",
            confidence=0.95,
            document_type=DocumentType.CONTRACT,
            metadata={"test": "value"},
            structured_data={"number": "123"},
        )

        d = result.to_dict()

        assert d["text"] == "Test text"
        assert d["confidence"] == 0.95
        assert d["document_type"] == "contract"
        assert d["metadata"]["test"] == "value"
        assert d["structured_data"]["number"] == "123"
        assert "timestamp" in d


class TestOCRIntegration:
    """Интеграционные тесты OCR"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_batch_processing(self, tmp_path):
        """Тест пакетной обработки"""

        try:
            from PIL import Image, ImageDraw
        except ImportError:
            pytest.skip("Chandra or PIL not installed")

        # Создаем несколько тестовых изображений
        file_paths = []

        for i in range(3):
            img = Image.new("RGB", (400, 300), color="white")
            draw = ImageDraw.Draw(img)
            draw.text((50, 50), f"Document {i+1}", fill="black")

            img_path = tmp_path / f"doc_{i}.png"
            img.save(img_path)
            file_paths.append(str(img_path))

        # Batch обработка
        service = OCRService(enable_ai_parsing=False)
        results = await service.batch_process(file_paths)

        assert len(results) == 3

        for result in results:
            assert isinstance(result, OCRResult)

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_ocr_with_ai_parsing(self, sample_image_path):
        """Тест OCR с AI парсингом структуры"""

        try:
            pass
        except ImportError:
            pytest.skip("Chandra not installed")

        # OCR с AI парсингом
        service = OCRService(enable_ai_parsing=True)
        result = await service.process_image(
            sample_image_path, document_type=DocumentType.CONTRACT
        )

        # Должен быть текст
        assert result.text

        # Могут быть структурированные данные (зависит от AI)
        # assert result.structured_data  # Опционально

    @pytest.mark.asyncio
    async def test_quick_ocr_function(self, sample_image_path):
        """Тест утилитарной функции quick_ocr"""

        try:
            pass
        except ImportError:
            pytest.skip("Chandra not installed")

        text = await quick_ocr(sample_image_path)

        assert isinstance(text, str)

    @pytest.mark.asyncio
    async def test_ocr_with_structure_function(self, sample_image_path):
        """Тест утилитарной функции ocr_with_structure"""

        try:
            pass
        except ImportError:
            pytest.skip("Chandra not installed")

        result_dict = await ocr_with_structure(
            sample_image_path, document_type=DocumentType.INVOICE
        )

        assert isinstance(result_dict, dict)
        assert "text" in result_dict
        assert "confidence" in result_dict
        assert "document_type" in result_dict


class TestOCRErrorHandling:
    """Тесты обработки ошибок"""

    @pytest.mark.asyncio
    async def test_missing_file(self):
        """Тест обработки несуществующего файла"""
        service = OCRService(enable_ai_parsing=False)

        with pytest.raises(Exception):
            await service.process_image("non_existent_file.png")

    @pytest.mark.asyncio
    async def test_invalid_format(self, tmp_path):
        """Тест обработки неподдерживаемого формата"""
        # Создаем текстовый файл
        text_file = tmp_path / "test.txt"
        text_file.write_text("Not an image")

        service = OCRService(enable_ai_parsing=False)

        # Должна быть ошибка при попытке обработать
        # (или пропуск если формат не поддерживается)
        with pytest.raises(Exception):
            await service.process_image(str(text_file))


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
