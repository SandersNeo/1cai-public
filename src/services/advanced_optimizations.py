# [NEXUS IDENTITY] ID: 3863840099083275033 | DATE: 2025-11-19

"""
Advanced Optimizations для Embedding Service
============================================

Продвинутые техники оптимизации:
- Weighted GPU Scheduler
- SLO/SLI Tracker
- Memory-Aware Batcher
- Adaptive Quantizer с Calibration
- Semantic Cache ANN
- Predictive Batch Optimizer
- GPU Memory Pool (заготовка, требует GPU)

Версия: 2.2.0
"""

import logging
import time
from collections import deque
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class WeightedGPUScheduler:
    """Взвешенное распределение запросов между GPU"""

    def __init__(self, gpu_devices: List[int]):
        self.gpu_devices = gpu_devices
        self.gpu_weights = {gpu_id: 1.0 for gpu_id in gpu_devices}
        self.gpu_load = {gpu_id: 0.0 for gpu_id in gpu_devices}
        self.gpu_performance = {gpu_id: 1.0 for gpu_id in gpu_devices}
        self.gpu_request_count = {gpu_id: 0 for gpu_id in gpu_devices}

    def select_gpu(self, estimated_time: float = 0.1) -> int:
        """Выбрать GPU на основе весов и загрузки"""
        if not self.gpu_devices:
            return 0

        # Вычисляем score для каждого GPU
        scores = {}
        for gpu_id in self.gpu_devices:
            # Score = weight / (load + estimated_time + epsilon)
            # Чем больше weight и меньше load, тем выше score
            score = self.gpu_weights[gpu_id] / (
                self.gpu_load[gpu_id] + estimated_time + 0.1
            )
            scores[gpu_id] = score

        # Выбираем GPU с максимальным score
        selected_gpu = max(scores, key=scores.get)
        self.gpu_request_count[selected_gpu] += 1

        return selected_gpu

    def update_performance(
        self, gpu_id: int, actual_time: float, items_processed: int = 1
    ):
        """Обновить метрики производительности GPU"""
        if gpu_id not in self.gpu_devices:
            return

        # Обновляем загрузку (EMA)
        alpha = 0.2
        self.gpu_load[gpu_id] = (
            alpha * actual_time + (1 - alpha) * self.gpu_load[gpu_id]
        )

        # Обновляем вес на основе throughput (items/time)
        if actual_time > 0:
            throughput = items_processed / actual_time
            # EMA для веса (больше throughput = больше weight)
            self.gpu_weights[gpu_id] = (
                alpha * throughput + (1 - alpha) * self.gpu_weights[gpu_id]
            )

        self.gpu_performance[gpu_id] = 1.0 / max(actual_time, 0.001)

    def get_stats(self) -> Dict:
        """Получить статистику scheduler"""
        return {
            "gpu_weights": self.gpu_weights.copy(),
            "gpu_load": self.gpu_load.copy(),
            "gpu_performance": self.gpu_performance.copy(),
            "gpu_request_count": self.gpu_request_count.copy(),
        }


class SLOTracker:
    """Отслеживание SLO/SLI и Error Budgets"""

    def __init__(self):
        self.slos = {
            "latency_p95": {"target": 0.1, "window": 3600},  # 100ms за час
            "error_rate": {"target": 0.001, "window": 3600},  # 0.1% за час
            "availability": {"target": 0.999, "window": 86400},  # 99.9% за день
            "cache_hit_rate": {"target": 0.7, "window": 3600},  # 70% за час
        }

        self.error_budgets = {slo: 0.0 for slo in self.slos}
        self.sli_history = {slo: [] for slo in self.slos}

    def record_metric(self, slo_name: str, value: float, timestamp: float = None):
        """Записать метрику для SLO"""
        try:
            if timestamp is None:
                timestamp = time.time()

            if slo_name not in self.slos:
                logger.debug("Unknown SLO name: %s", slo_name)
                return

            # Валидация значения
            if not isinstance(value, (int, float)):
                logger.warning(
                    f"Invalid metric value type for {slo_name}: {type(value)}"
                )
                return

            if value < 0:
                logger.warning("Negative metric value for %s: {value}", slo_name)
                return

            self.sli_history[slo_name].append(
                {"value": float(value), "timestamp": float(timestamp)}
            )

            # Очищаем старые записи
            window = self.slos[slo_name]["window"]
            cutoff = timestamp - window
            self.sli_history[slo_name] = [
                h for h in self.sli_history[slo_name] if h["timestamp"] > cutoff
            ]

            # Вычисляем текущий SLI
            current_sli = self._calculate_sli(slo_name)

            # Обновляем error budget
            target = self.slos[slo_name]["target"]
            if slo_name == "availability":
                # Для availability: budget = 1 - SLI
                self.error_budgets[slo_name] = 1.0 - current_sli
            else:
                # Для других: budget = target - SLI
                self.error_budgets[slo_name] = target - current_sli
        except Exception as e:
            logger.error(f"Error recording SLO metric {slo_name}: {e}", exc_info=True)

    def _calculate_sli(self, slo_name: str) -> float:
        """Вычислить текущий SLI"""
        history = self.sli_history[slo_name]
        if not history:
            return 1.0

        values = [h["value"] for h in history]

        if slo_name == "latency_p95":
            return np.percentile(values, 95) if values else 0.0
        elif slo_name == "error_rate":
            # Процент ошибок
            total = len(history)
            errors = sum(1 for h in history if h["value"] > 0)
            return errors / total if total > 0 else 0.0
        elif slo_name == "availability":
            # Процент успешных запросов
            total = len(history)
            successful = sum(1 for h in history if h["value"] == 1)
            return successful / total if total > 0 else 1.0
        elif slo_name == "cache_hit_rate":
            # Средний hit rate
            return np.mean(values) if values else 0.0

        return 0.0

    def check_slo_violation(self) -> Dict[str, bool]:
        """Проверить нарушения SLO"""
        violations = {}
        for slo_name, config in self.slos.items():
            current_sli = self._calculate_sli(slo_name)
            target = config["target"]

            if slo_name == "availability":
                violation = current_sli < target
            else:
                violation = current_sli > target

            violations[slo_name] = violation

        return violations

    def get_error_budgets(self) -> Dict[str, float]:
        """Получить текущие error budgets"""
        return self.error_budgets.copy()

    def get_sli_status(self) -> Dict[str, Dict]:
        """Получить статус всех SLI"""
        status = {}
        for slo_name in self.slos:
            current_sli = self._calculate_sli(slo_name)
            target = self.slos[slo_name]["target"]
            budget = self.error_budgets[slo_name]

            status[slo_name] = {
                "sli": current_sli,
                "target": target,
                "error_budget": budget,
                "violation": (
                    current_sli < target
                    if slo_name == "availability"
                    else current_sli > target
                ),
            }

        return status


class MemoryAwareBatcher:
    """Память-осознанное формирование батчей"""

    def __init__(self, max_memory_mb: float = 1024):
        self.max_memory_mb = max_memory_mb
        self.current_batch = []
        self.current_memory = 0.0

    def add_text(self, text: str) -> Optional[List[str]]:
        """Добавить текст в батч, вернуть батч если готов"""
        try:
            if not isinstance(text, str):
                logger.warning(f"Invalid text type: {type(text)}")
                return None

            if not text:
                logger.debug("Empty text provided to batcher")
                return None

            text_memory = self._estimate_memory(text)

            # Проверяем, поместится ли текст
            if self.current_memory + text_memory > self.max_memory_mb:
                # Батч готов, возвращаем его
                batch = self.current_batch.copy()
                self.current_batch = [text]
                self.current_memory = text_memory
                return batch

            # Добавляем в текущий батч
            self.current_batch.append(text)
            self.current_memory += text_memory
            return None
        except Exception as e:
            logger.error(f"Error adding text to batcher: {e}", exc_info=True)
            return None

    def flush(self) -> Optional[List[str]]:
        """Завершить текущий батч"""
        if self.current_batch:
            batch = self.current_batch.copy()
            self.current_batch = []
            self.current_memory = 0.0
            return batch
        return None

    def _estimate_memory(self, text: str) -> float:
        """Оценить память для текста"""
        # Эмпирическая формула: ~1.5MB на embedding
        # + overhead токенизации
        base_memory = 0.0015  # MB
        token_overhead = len(text) * 0.000001  # ~1KB на 1000 символов
        return base_memory + token_overhead

    def get_stats(self) -> Dict:
        """Получить статистику batcher"""
        return {
            "current_batch_size": len(self.current_batch),
            "current_memory_mb": self.current_memory,
            "max_memory_mb": self.max_memory_mb,
        }


class AdaptiveQuantizer:
    """Адаптивная квантизация с калибровкой на реальных данных"""

    def __init__(
        self,
        dtype: str = "int8",
        auto_recalibrate: bool = True,
        recalibrate_interval: int = 1000,
    ):
        self.dtype = dtype
        self.scale = 1.0
        self.calibrated = False
        self.calibration_data = []
        self.max_calibration_samples = 1000
        self.auto_recalibrate = auto_recalibrate
        self.recalibrate_interval = recalibrate_interval
        self.samples_since_calibration = 0
        self.last_calibration_time = time.time()

    def calibrate(
        self, embeddings: List[List[float]], percentile: float = 99.9
    ) -> float:
        """Калибровка на основе реальных данных"""
        if not embeddings:
            return self.scale

        # Собираем статистику
        all_values = []
        for emb in embeddings:
            all_values.extend(emb)

        if not all_values:
            return self.scale

        # Определяем scale на основе percentile
        all_values_array = np.array(all_values, dtype=np.float32)
        max_val = np.percentile(np.abs(all_values_array), percentile)

        if self.dtype == "int8":
            self.scale = 127.0 / max_val if max_val > 0 else 1.0
        elif self.dtype == "int16":
            self.scale = 32767.0 / max_val if max_val > 0 else 1.0
        else:
            self.scale = 1.0

        self.calibrated = True
        logger.info(
            f"Adaptive quantization calibrated: scale={self.scale:.6f}, dtype={self.dtype}"
        )

        return self.scale

    def quantize(self, embedding: List[float]) -> Tuple[List[int], float]:
        """Квантизировать embedding с калиброванным scale"""
        try:
            if not embedding:
                logger.warning("Empty embedding provided for quantization")
                return [], self.scale

            if not isinstance(embedding, list):
                logger.warning(f"Invalid embedding type: {type(embedding)}")
                return [], self.scale

            # Автоматическая перекалибровка
            if self.auto_recalibrate and self.calibrated:
                self.samples_since_calibration += 1
                # Сохраняем embedding для перекалибровки
                if len(self.calibration_data) < self.max_calibration_samples:
                    self.calibration_data.append(embedding)

                # Перекалибровка каждые N образцов или через интервал времени
                should_recalibrate = (
                    self.samples_since_calibration >= self.recalibrate_interval
                    or (time.time() - self.last_calibration_time) > 3600  # Каждый час
                )

                if should_recalibrate and len(self.calibration_data) >= 10:
                    try:
                        self.calibrate(self.calibration_data)
                        self.samples_since_calibration = 0
                        self.last_calibration_time = time.time()
                        # Очищаем старые данные, оставляем последние 100
                        self.calibration_data = self.calibration_data[-100:]
                        logger.info(
                            f"Auto-recalibrated quantizer on {len(self.calibration_data)} samples"
                        )
                    except Exception as e:
                        logger.debug("Error in auto-recalibration: %s", e)

            if not self.calibrated:
                # Используем простую квантизацию без калибровки
                return self._simple_quantize(embedding)

            arr = np.array(embedding, dtype=np.float32)
            if arr.size == 0:
                logger.warning("Empty embedding array")
                return [], self.scale

            scaled = arr * self.scale

            if self.dtype == "int8":
                quantized = np.clip(scaled, -128, 127).astype(np.int8)
            elif self.dtype == "int16":
                quantized = np.clip(scaled, -32768, 32767).astype(np.int16)
            else:
                quantized = arr.astype(np.int32)

            return quantized.tolist(), self.scale
        except Exception as e:
            logger.error(f"Error quantizing embedding: {e}", exc_info=True)
            # Fallback: возвращаем пустой список и scale
            return [], self.scale

    def _simple_quantize(self, embedding: List[float]) -> Tuple[List[int], float]:
        """Простая квантизация без калибровки"""
        arr = np.array(embedding, dtype=np.float32)
        max_val = np.max(np.abs(arr))

        if self.dtype == "int8":
            scale = 127.0 / max_val if max_val > 0 else 1.0
            quantized = (arr * scale).astype(np.int8)
        elif self.dtype == "int16":
            scale = 32767.0 / max_val if max_val > 0 else 1.0
            quantized = (arr * scale).astype(np.int16)
        else:
            scale = 1.0
            quantized = arr.astype(np.int32)

        return quantized.tolist(), scale

    def dequantize(self, quantized: List[int], scale: float) -> List[float]:
        """Де-квантизировать embedding"""
        try:
            if not quantized:
                logger.warning("Empty quantized embedding provided")
                return []

            if not isinstance(quantized, list):
                logger.warning(f"Invalid quantized type: {type(quantized)}")
                return []

            if scale <= 0:
                logger.warning("Invalid scale for dequantization: %s", scale)
                scale = 1.0

            arr = np.array(
                quantized, dtype=np.int8 if self.dtype == "int8" else np.int16
            )
            if arr.size == 0:
                return []

            dequantized = arr.astype(np.float32) / scale
            return dequantized.tolist()
        except Exception as e:
            logger.error(f"Error dequantizing embedding: {e}", exc_info=True)
            return []


class SemanticCacheANN:
    """Семантический кэш с Approximate Nearest Neighbor поиском"""

    def __init__(
        self, index_type: str = "linear", dimension: int = 384, max_size: int = 10000
    ):
        self.index_type = index_type
        self.dimension = dimension
        self.max_size = max_size
        self.index = None
        self.embeddings = []
        self.texts = []
        self._rebuild_threshold = 0.8  # Перестроить индекс при 80% заполнения
        self._build_index()

    def _build_index(self):
        """Построить ANN индекс"""
        if self.index_type == "linear":
            # Линейный поиск (fallback)
            self.index = None
        elif self.index_type == "faiss":
            try:
                import faiss

                # HNSW индекс для быстрого поиска
                self.index = faiss.IndexHNSWFlat(self.dimension, 32)
                self.index.hnsw.efConstruction = 200
                logger.info("FAISS HNSW index initialized")
            except ImportError:
                logger.warning("FAISS not available, falling back to linear search")
                self.index = None
        elif self.index_type == "hnswlib":
            try:
                import hnswlib

                self.index = hnswlib.Index(space="cosine", dim=self.dimension)
                self.index.init_index(max_elements=10000, ef_construction=200, M=16)
                logger.info("HNSWlib index initialized")
            except ImportError:
                logger.warning("HNSWlib not available, falling back to linear search")
                self.index = None
        else:
            self.index = None

    def add(self, embedding: List[float], text: str):
        """Добавить embedding в индекс"""
        try:
            if not embedding:
                logger.warning("Empty embedding provided to ANN cache")
                return

            if not isinstance(embedding, list):
                logger.warning(f"Invalid embedding type: {type(embedding)}")
                return

            if len(embedding) != self.dimension:
                logger.warning(
                    f"Embedding dimension mismatch: {len(embedding)} != {self.dimension}"
                )
                return

            if not isinstance(text, str):
                logger.warning(f"Invalid text type: {type(text)}")
                return

            # Проверяем размер и удаляем старые записи если нужно
            if len(self.embeddings) >= self.max_size:
                # Удаляем самые старые (FIFO)
                self.embeddings.pop(0)
                self.texts.pop(0)
                # Перестраиваем индекс если используется
                if self.index is not None and len(self.embeddings) > 0:
                    self._rebuild_index()

            self.embeddings.append(embedding)
            self.texts.append(text)

            # Инкрементальное обновление индекса
            if self.index is not None:
                try:
                    if self.index_type == "faiss":
                        pass

                        # Проверяем, нужно ли перестроить индекс
                        if len(self.embeddings) % 100 == 0:  # Каждые 100 записей
                            self._rebuild_index()
                        else:
                            embedding_array = np.array([embedding], dtype=np.float32)
                            self.index.add(embedding_array)
                    elif self.index_type == "hnswlib":
                        # HNSWlib поддерживает инкрементальное добавление
                        self.index.add_items(
                            np.array([embedding], dtype=np.float32),
                            [len(self.embeddings) - 1],
                        )
                except Exception as e:
                    logger.warning(
                        f"Error adding to ANN index: {e}, rebuilding index",
                        exc_info=True,
                    )
                    self._rebuild_index()
        except Exception as e:
            logger.error(f"Error adding embedding to ANN cache: {e}", exc_info=True)

    def _rebuild_index(self):
        """Перестроить индекс с нуля"""
        try:
            if not self.embeddings:
                return

            self._build_index()

            # Добавляем все embeddings заново
            if self.index is not None:
                if self.index_type == "faiss":
                    pass

                    embeddings_array = np.array(self.embeddings, dtype=np.float32)
                    self.index.add(embeddings_array)
                elif self.index_type == "hnswlib":
                    embeddings_array = np.array(self.embeddings, dtype=np.float32)
                    labels = list(range(len(self.embeddings)))
                    self.index.add_items(embeddings_array, labels)

            logger.debug(f"Rebuilt ANN index with {len(self.embeddings)} embeddings")
        except Exception as e:
            logger.warning(f"Error rebuilding ANN index: {e}", exc_info=True)

    def search(
        self, query_embedding: List[float], k: int = 1, threshold: float = 0.95
    ) -> Optional[Tuple[List[float], float, str]]:
        """Поиск похожих embeddings"""
        if not self.embeddings:
            return None

        if self.index is None:
            return self._linear_search(query_embedding, threshold)

        try:
            if self.index_type == "faiss":
                pass

                query_array = np.array([query_embedding], dtype=np.float32)
                self.index.hnsw.efSearch = 64
                distances, indices = self.index.search(
                    query_array, min(k, len(self.embeddings))
                )

                if len(indices[0]) > 0 and distances[0][0] < (1 - threshold):
                    idx = indices[0][0]
                    similarity = 1.0 - distances[0][0]
                    return self.embeddings[idx], similarity, self.texts[idx]

            elif self.index_type == "hnswlib":
                self.index.set_ef(64)
                labels, distances = self.index.knn_query(
                    np.array([query_embedding], dtype=np.float32),
                    k=min(k, len(self.embeddings)),
                )

                if len(labels[0]) > 0:
                    idx = labels[0][0]
                    similarity = 1.0 - distances[0][0]
                    if similarity >= threshold:
                        return self.embeddings[idx], similarity, self.texts[idx]

        except Exception as e:
            logger.warning("Error in ANN search: %s, falling back to linear", e)
            return self._linear_search(query_embedding, threshold)

        return None

    def _linear_search(
        self, query: List[float], threshold: float
    ) -> Optional[Tuple[List[float], float, str]]:
        """Fallback: линейный поиск"""
        best_similarity = 0.0
        best_embedding = None
        best_text = None

        query_np = np.array(query, dtype=np.float32)
        query_norm = np.linalg.norm(query_np)

        if query_norm == 0:
            return None

        for i, emb in enumerate(self.embeddings):
            emb_np = np.array(emb, dtype=np.float32)
            emb_norm = np.linalg.norm(emb_np)

            if emb_norm == 0:
                continue

            similarity = np.dot(query_np, emb_np) / (query_norm * emb_norm)

            if similarity > best_similarity:
                best_similarity = similarity
                best_embedding = emb
                best_text = self.texts[i]

        if best_similarity >= threshold:
            return best_embedding, best_similarity, best_text

        return None

    def clear(self):
        """Очистить индекс"""
        self.embeddings = []
        self.texts = []
        if self.index is not None:
            self._build_index()


class PredictiveBatchOptimizer:
    """Предиктивная оптимизация batch size на основе истории"""

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.history = deque(maxlen=max_history)
        self.model = None
        self.model_trained = False

    def predict_optimal_batch_size(
        self,
        text_length: int,
        available_memory: float,
        historical_pattern: Optional[Dict] = None,
    ) -> int:
        """Предсказать оптимальный batch size"""
        try:
            # Валидация входных данных
            if not isinstance(text_length, int) or text_length < 0:
                logger.warning("Invalid text_length: %s", text_length)
                text_length = 1000  # Default

            if not isinstance(available_memory, (int, float)) or available_memory <= 0:
                logger.warning("Invalid available_memory: %s", available_memory)
                available_memory = 1024.0  # Default MB

            # Если есть обученная модель, используем её
            if self.model_trained and self.model and len(self.history) > 50:
                try:
                    features = self._extract_features(text_length, available_memory)
                    predicted = self.model.predict([features])[0]
                    optimal_batch = int(np.clip(predicted, 8, 256))
                    return optimal_batch
                except Exception as e:
                    logger.debug(
                        f"Error in model prediction: {e}, falling back to empirical formula"
                    )

            # Иначе используем эмпирическую формулу
            return self._empirical_formula(text_length, available_memory)
        except Exception as e:
            logger.error(f"Error predicting optimal batch size: {e}", exc_info=True)
            # Fallback: возвращаем безопасное значение
            return 32

    def _extract_features(
        self, text_length: int, available_memory: float
    ) -> List[float]:
        """Извлечь признаки для ML модели"""
        # Базовые признаки
        features = [
            text_length,
            available_memory,
            text_length / max(available_memory, 0.1),  # Плотность
            np.log1p(text_length),  # Логарифм длины (для нормализации)
            np.log1p(available_memory),  # Логарифм памяти
        ]

        # Статистика из истории
        if len(self.history) > 0:
            recent = list(self.history)[-50:]  # Последние 50 записей
            avg_time = np.mean([h["actual_time"] for h in recent])
            avg_efficiency = np.mean([h["efficiency"] for h in recent])
            std_time = (
                np.std([h["actual_time"] for h in recent]) if len(recent) > 1 else 0.0
            )
            std_efficiency = (
                np.std([h["efficiency"] for h in recent]) if len(recent) > 1 else 0.0
            )
            features.extend([avg_time, avg_efficiency, std_time, std_efficiency])
        else:
            features.extend([0.0, 0.0, 0.0, 0.0])

        return features

    def _empirical_formula(self, text_length: int, available_memory: float) -> int:
        """Эмпирическая формула для batch size"""
        # Базовый расчёт: ~1.5MB на embedding + overhead
        estimated_memory_per_item = 0.0015 + (text_length * 0.000001)  # MB

        # Оставляем 20% памяти в резерве
        available_memory_mb = available_memory * 0.8

        # Вычисляем оптимальный batch size
        optimal_batch = int(available_memory_mb / estimated_memory_per_item)

        # Ограничиваем разумными пределами
        optimal_batch = max(8, min(optimal_batch, 256))

        return optimal_batch

    def update_model(
        self, text_length: int, batch_size: int, actual_time: float, memory_used: float
    ):
        """Обновить модель на основе результатов"""
        efficiency = batch_size / max(actual_time, 0.001)  # throughput

        self.history.append(
            {
                "text_length": text_length,
                "batch_size": batch_size,
                "actual_time": actual_time,
                "memory_used": memory_used,
                "efficiency": efficiency,
            }
        )

        # Переобучаем модель каждые 100 записей
        if len(self.history) % 100 == 0 and len(self.history) >= 50:
            self._retrain_model()

    def _retrain_model(self):
        """Переобучить ML модель"""
        try:
            # Пробуем разные модели в порядке приоритета
            models_to_try = []

            # 1. XGBoost (если доступен)
            try:
                import xgboost as xgb

                models_to_try.append(
                    (
                        "xgboost",
                        xgb.XGBRegressor(
                            n_estimators=50,
                            max_depth=6,
                            learning_rate=0.1,
                            random_state=42,
                        ),
                    )
                )
            except ImportError:
                pass

            # 2. LightGBM (если доступен)
            try:
                import lightgbm as lgb

                models_to_try.append(
                    (
                        "lightgbm",
                        lgb.LGBMRegressor(
                            n_estimators=50,
                            max_depth=6,
                            learning_rate=0.1,
                            random_state=42,
                            verbose=-1,
                        ),
                    )
                )
            except ImportError:
                pass

            # 3. RandomForest (fallback)
            try:
                from sklearn.ensemble import RandomForestRegressor

                models_to_try.append(
                    (
                        "random_forest",
                        RandomForestRegressor(
                            n_estimators=50, max_depth=10, random_state=42
                        ),
                    )
                )
            except ImportError:
                pass

            if not models_to_try:
                logger.debug("No ML libraries available, skipping model training")
                return

            X = []
            y = []

            for h in self.history:
                features = self._extract_features(h["text_length"], h["memory_used"])
                X.append(features)
                y.append(h["batch_size"])

            if len(X) < 10:
                return

            # Пробуем модели в порядке приоритета
            for model_name, model in models_to_try:
                try:
                    model.fit(X, y)
                    self.model = model
                    self.model_trained = True
                    logger.info(
                        f"Predictive batch optimizer retrained with {model_name} on {len(X)} samples"
                    )
                    return
                except Exception as e:
                    logger.debug("Error training %s: {e}, trying next model", model_name)
                    continue

            logger.warning("Failed to train any model")
        except Exception as e:
            logger.warning(f"Error retraining model: {e}", exc_info=True)

    def get_stats(self) -> Dict:
        """Получить статистику optimizer"""
        if not self.history:
            return {"history_size": 0, "model_trained": False}

        return {
            "history_size": len(self.history),
            "model_trained": self.model_trained,
            "avg_efficiency": (
                np.mean([h["efficiency"] for h in self.history])
                if self.history
                else 0.0
            ),
        }
