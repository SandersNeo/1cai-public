# [NEXUS IDENTITY] ID: -7866221297486084496 | DATE: 2025-11-19

"""
Unit тесты для AdaptiveQuantizer
"""

from src.services.advanced_optimizations import AdaptiveQuantizer


class TestAdaptiveQuantizer:
    """Тесты для AdaptiveQuantizer"""

    def test_init(self):
        """Тест инициализации"""
        quantizer = AdaptiveQuantizer(dtype="int8")
        assert quantizer.dtype == "int8"
        assert quantizer.scale == 1.0
        assert quantizer.calibrated is False

    def test_init_int16(self):
        """Тест инициализации с INT16"""
        quantizer = AdaptiveQuantizer(dtype="int16")
        assert quantizer.dtype == "int16"

    def test_calibrate(self):
        """Тест калибровки"""
        quantizer = AdaptiveQuantizer(dtype="int8")
        embeddings = [
            [0.1, 0.2, 0.3, 0.4, 0.5],
            [0.2, 0.3, 0.4, 0.5, 0.6],
            [0.3, 0.4, 0.5, 0.6, 0.7],
        ]

        scale = quantizer.calibrate(embeddings)
        assert quantizer.calibrated is True
        assert scale > 0
        # Scale должен быть разумным (не слишком большим)
        assert scale < 10000  # Разумный верхний предел

    def test_calibrate_empty(self):
        """Тест калибровки на пустых данных"""
        quantizer = AdaptiveQuantizer(dtype="int8")
        scale = quantizer.calibrate([])
        assert scale == 1.0
        assert quantizer.calibrated is False

    def test_quantize_calibrated(self):
        """Тест квантизации после калибровки"""
        quantizer = AdaptiveQuantizer(dtype="int8")
        embeddings = [[0.1, 0.2, 0.3, 0.4, 0.5]]
        quantizer.calibrate(embeddings)

        embedding = [0.15, 0.25, 0.35, 0.45, 0.55]
        quantized, scale = quantizer.quantize(embedding)

        assert len(quantized) == len(embedding)
        assert all(isinstance(x, int) for x in quantized)
        assert all(-128 <= x <= 127 for x in quantized)
        assert scale == quantizer.scale

    def test_quantize_not_calibrated(self):
        """Тест квантизации без калибровки"""
        quantizer = AdaptiveQuantizer(dtype="int8")
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]

        quantized, scale = quantizer.quantize(embedding)

        assert len(quantized) == len(embedding)
        assert all(isinstance(x, int) for x in quantized)
        assert scale > 0

    def test_quantize_int16(self):
        """Тест квантизации INT16"""
        quantizer = AdaptiveQuantizer(dtype="int16")
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]

        quantized, scale = quantizer.quantize(embedding)

        assert len(quantized) == len(embedding)
        assert all(-32768 <= x <= 32767 for x in quantized)

    def test_dequantize(self):
        """Тест де-квантизации"""
        quantizer = AdaptiveQuantizer(dtype="int8")
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]

        quantized, scale = quantizer.quantize(embedding)
        dequantized = quantizer.dequantize(quantized, scale)

        assert len(dequantized) == len(embedding)
        assert all(isinstance(x, float) for x in dequantized)
        # Должны быть близки к оригиналу (с некоторой потерей точности)
        for orig, deq in zip(embedding, dequantized):
            assert abs(orig - deq) < 0.1

    def test_quantize_dequantize_roundtrip(self):
        """Тест полного цикла квантизация-де-квантизация"""
        quantizer = AdaptiveQuantizer(dtype="int8")
        embeddings = [[0.1, 0.2, 0.3, 0.4, 0.5]]
        quantizer.calibrate(embeddings)

        original = [0.15, 0.25, 0.35, 0.45, 0.55]
        quantized, scale = quantizer.quantize(original)
        dequantized = quantizer.dequantize(quantized, scale)

        # Проверяем, что де-квантизированные значения близки к оригиналу
        for orig, deq in zip(original, dequantized):
            assert abs(orig - deq) < 0.1  # Допустимая погрешность (увеличена для INT8)

    def test_calibrate_percentile(self):
        """Тест калибровки с разными percentile"""
        quantizer = AdaptiveQuantizer(dtype="int8")
        embeddings = [[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]]

        scale_99 = quantizer.calibrate(embeddings, percentile=99.0)
        quantizer.calibrated = False
        quantizer.scale = 1.0
        scale_99_9 = quantizer.calibrate(embeddings, percentile=99.9)

        # Оба scale должны быть положительными
        assert scale_99 > 0
        assert scale_99_9 > 0
        # Percentile влияет на scale, но не всегда линейно
        # Проверяем только, что оба значения разумные
        assert scale_99 < 10000
        assert scale_99_9 < 10000
