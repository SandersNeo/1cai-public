# [NEXUS IDENTITY] ID: 4485128649121402769 | DATE: 2025-11-19

"""
Простые функциональные тесты для ML системы.
Тестирование основной логики без внешних зависимостей.
"""

import pytest
import numpy as np
from datetime import datetime

# Тестирование основных функций без внешних зависимостей


def test_requirements_accuracy_logic():
    """Тест логики расчета точности анализа требований"""

    def calculate_requirements_accuracy(predicted, actual):
        """Упрощенная версия расчета точности"""
        if not predicted or not actual:
            return 0.0

        # Преобразуем в множества для сравнения
        predicted_texts = {item.get("text", "").lower().strip() for item in predicted}
        actual_texts = {item.get("text", "").lower().strip() for item in actual}

        # Пересечение и объединение
        intersection = predicted_texts & actual_texts
        union = predicted_texts | actual_texts

        # Jaccard Similarity
        accuracy = len(intersection) / len(union) if union else 0.0

        return min(accuracy, 1.0)

    # Тест 1: Полное совпадение
    predicted = [
        {"text": "Система должна обрабатывать заказы"},
        {"text": "Время отклика до 2 секунд"},
    ]
    actual = [
        {"text": "Система должна обрабатывать заказы"},
        {"text": "Время отклика до 2 секунд"},
    ]

    accuracy = calculate_requirements_accuracy(predicted, actual)
    assert accuracy == 1.0, f"Ожидалась точность 1.0, получено {accuracy}"

    # Тест 2: Частичное совпадение
    predicted = [
        {"text": "Система должна обрабатывать заказы"},
        {"text": "Время отклика до 2 секунд"},
    ]
    actual = [
        {"text": "Система должна обрабатывать заказы"},
        {"text": "Время отклика до 5 секунд"},
    ]

    accuracy = calculate_requirements_accuracy(predicted, actual)
    assert (
        0.0 < accuracy < 1.0
    ), f"Ожидалась промежуточная точность, получено {accuracy}"

    # Тест 3: Нет совпадений
    predicted = [
        {"text": "Система должна обрабатывать заказы"},
        {"text": "Время отклика до 2 секунд"},
    ]
    actual = [
        {"text": "Система должна сохранять данные"},
        {"text": "Интерфейс должен быть удобным"},
    ]

    accuracy = calculate_requirements_accuracy(predicted, actual)
    assert accuracy == 0.0, f"Ожидалась точность 0.0, получено {accuracy}"


def test_diagram_quality_logic():
    """Тест логики оценки качества диаграммы"""

    def calculate_diagram_quality(diagram):
        """Упрощенная оценка качества диаграммы"""
        if not diagram:
            return 0.0

        quality_factors = []

        # Проверка наличия базовых элементов Mermaid
        mermaid_keywords = ["graph", "flowchart", "sequenceDiagram", "classDiagram"]
        keyword_score = sum(
            1 for keyword in mermaid_keywords if keyword in diagram.lower()
        )
        quality_factors.append(keyword_score / len(mermaid_keywords))

        # Проверка наличия узлов и связей
        node_score = 1.0 if diagram.count("-->") > 0 or diagram.count("->") > 0 else 0.0
        quality_factors.append(node_score)

        # Проверка корректной структуры
        structure_score = 1.0 if diagram.count("{") == diagram.count("}") else 0.0
        quality_factors.append(structure_score)

        return np.mean(quality_factors)

    # Тест хорошей диаграммы
    good_diagram = """
    graph TD
        A[Начало] --> B{Решение}
        B -->|Да| C[Действие 1]
        B -->|Нет| D[Действие 2]
    """

    quality = calculate_diagram_quality(good_diagram)
    assert quality > 0.5, f"Ожидалось высокое качество диаграммы, получено {quality}"

    # Тест плохой диаграммы
    bad_diagram = "Это не диаграмма, а просто текст"

    quality = calculate_diagram_quality(bad_diagram)
    assert quality < 0.5, f"Ожидалось низкое качество диаграммы, получено {quality}"


def test_risk_precision_logic():
    """Тест логики расчета точности оценки рисков"""

    def calculate_risk_precision(predicted_risks, actual_risks):
        """Упрощенный расчет точности рисков"""
        if not predicted_risks or not actual_risks:
            return 0.0

        # Извлекаем описания рисков
        predicted_descriptions = {
            risk.get("description", "").lower().strip() for risk in predicted_risks
        }
        actual_descriptions = {
            risk.get("description", "").lower().strip() for risk in actual_risks
        }

        # Пересечение и точность
        intersection = predicted_descriptions & actual_descriptions

        precision = (
            len(intersection) / len(predicted_descriptions)
            if predicted_descriptions
            else 0.0
        )

        return min(precision, 1.0)

    # Тест точного совпадения рисков
    predicted_risks = [
        {"description": "Высокая нагрузка на систему"},
        {"description": "Проблемы с интеграцией"},
    ]

    actual_risks = [
        {"description": "Высокая нагрузка на систему"},
        {"description": "Проблемы с интеграцией"},
    ]

    precision = calculate_risk_precision(predicted_risks, actual_risks)
    assert precision == 1.0, f"Ожидалась точность 1.0, получено {precision}"

    # Тест частичного совпадения
    predicted_risks = [
        {"description": "Высокая нагрузка на систему"},
        {"description": "Проблемы с интеграцией"},
        {"description": "Уязвимости безопасности"},
    ]

    actual_risks = [
        {"description": "Высокая нагрузка на систему"},
        {"description": "Проблемы с интеграцией"},
        {"description": "Недостаток памяти"},
    ]

    precision = calculate_risk_precision(predicted_risks, actual_risks)
    expected_precision = 2.0 / 3.0  # 2 совпадения из 3 предсказанных
    assert (
        abs(precision - expected_precision) < 0.01
    ), f"Ожидалась точность {expected_precision}, получено {precision}"


def test_ml_pipeline_simulation():
    """Симуляция ML пайплайна без внешних зависимостей"""

    def simulate_model_training():
        """Симуляция обучения модели"""
        # Генерация синтетических данных
        np.random.seed(42)
        n_samples = 100
        n_features = 5

        # Создание признаков
        X = np.random.randn(n_samples, n_features)

        # Создание целевой переменной (бинарная классификация)
        y = (X[:, 0] + X[:, 1] + np.random.randn(n_samples) * 0.5 > 0).astype(int)

        # Разделение на train/test
        split_point = int(n_samples * 0.8)
        X_train, X_test = X[:split_point], X[split_point:]
        y_train, y_test = y[:split_point], y[split_point:]

        # Простая модель (логистическая регрессия из numpy)
        # y = sigmoid(X @ w + b)

        # Инициализация весов
        w = np.random.randn(n_features) * 0.1
        b = 0.0

        # Функция сигмоида
        def sigmoid(z):
            return 1 / (1 + np.exp(-np.clip(z, -250, 250)))

        # Функция предсказания
        def predict(X):
            z = X @ w + b
            return sigmoid(z)

        # Простое обучение (градиентный спуск)
        learning_rate = 0.01
        n_epochs = 100

        for epoch in range(n_epochs):
            # Предсказания
            y_pred = predict(X_train)

            # Вычисление градиентов
            dw = (X_train.T @ (y_pred - y_train)) / len(X_train)
            db = np.mean(y_pred - y_train)

            # Обновление весов
            w -= learning_rate * dw
            b -= learning_rate * db

        # Оценка на тестовых данных
        y_test_pred = predict(X_test)
        y_test_binary = (y_test_pred > 0.5).astype(int)

        # Вычисление метрик
        accuracy = np.mean(y_test_binary == y_test)
        precision = (
            np.sum((y_test_binary == 1) & (y_test == 1)) / np.sum(y_test_binary == 1)
            if np.sum(y_test_binary == 1) > 0
            else 0
        )
        recall = (
            np.sum((y_test_binary == 1) & (y_test == 1)) / np.sum(y_test == 1)
            if np.sum(y_test == 1) > 0
            else 0
        )
        f1_score = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0
        )

        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "training_samples": len(X_train),
            "test_samples": len(X_test),
        }

    # Запуск симуляции
    results = simulate_model_training()

    # Проверка результатов
    assert 0 <= results["accuracy"] <= 1, "Точность должна быть в диапазоне [0, 1]"
    assert 0 <= results["precision"] <= 1, "Precision должна быть в диапазоне [0, 1]"
    assert 0 <= results["recall"] <= 1, "Recall должна быть в диапазоне [0, 1]"
    assert 0 <= results["f1_score"] <= 1, "F1-score должна быть в диапазоне [0, 1]"

    print(f"Симуляция ML пайплайна завершена:")
    print(f"  Точность: {results['accuracy']:.3f}")
    print(f"  Precision: {results['precision']:.3f}")
    print(f"  Recall: {results['recall']:.3f}")
    print(f"  F1-score: {results['f1_score']:.3f}")


def test_ab_test_statistics():
    """Тест статистики A/B тестирования"""

    def calculate_ab_test_stats(control_data, treatment_data, alpha=0.05):
        """Расчет статистики A/B теста"""

        # Базовые статистики
        control_mean = np.mean(control_data)
        treatment_mean = np.mean(treatment_data)

        # Размер выборки
        n_control = len(control_data)
        n_treatment = len(treatment_data)

        # Объединенное стандартное отклонение
        pooled_std = np.sqrt(
            (np.var(control_data) / n_control) + (np.var(treatment_data) / n_treatment)
        )

        # T-статистика (приближенно)
        if pooled_std > 0:
            t_stat = (treatment_mean - control_mean) / pooled_std
        else:
            t_stat = 0

        # Упрощенное вычисление p-value (нормальное приближение)
        from scipy.stats import norm

        p_value = 2 * (1 - norm.cdf(abs(t_stat)))

        # Доверительный интервал (95%)
        diff_mean = treatment_mean - control_mean
        margin_error = 1.96 * pooled_std  # 95% CI

        confidence_interval = (diff_mean - margin_error, diff_mean + margin_error)

        # Улучшение в процентах
        improvement = (
            (treatment_mean - control_mean) / control_mean * 100
            if control_mean != 0
            else 0
        )

        return {
            "control_mean": control_mean,
            "treatment_mean": treatment_mean,
            "improvement_percent": improvement,
            "p_value": p_value,
            "confidence_interval": confidence_interval,
            "is_significant": p_value < alpha,
            "n_control": n_control,
            "n_treatment": n_treatment,
        }

    # Генерация данных для A/B теста
    np.random.seed(42)

    # Контрольная группа: среднее значение 0.7
    control_data = np.random.normal(0.7, 0.1, 100)

    # Treatment группа: среднее значение 0.75 (улучшение)
    treatment_data = np.random.normal(0.75, 0.1, 100)

    # Расчет статистики
    results = calculate_ab_test_stats(control_data, treatment_data)

    # Проверка результатов
    assert results["n_control"] == 100, "Неверный размер контрольной группы"
    assert results["n_treatment"] == 100, "Неверный размер treatment группы"
    assert results["improvement_percent"] > 0, "Ожидалось положительное улучшение"
    assert 0 <= results["p_value"] <= 1, "P-value должен быть в диапазоне [0, 1]"

    print(f"A/B тест статистика:")
    print(f"  Контроль: {results['control_mean']:.3f}")
    print(f"  Treatment: {results['treatment_mean']:.3f}")
    print(f"  Улучшение: {results['improvement_percent']:.1f}%")
    print(f"  P-value: {results['p_value']:.3f}")
    print(f"  Значимо: {results['is_significant']}")


def test_feature_importance_simulation():
    """Тест симуляции важности признаков"""

    def simulate_feature_importance():
        """Симуляция важности признаков"""

        # Генерация данных
        np.random.seed(42)
        n_samples = 200
        n_features = 8

        X = np.random.randn(n_samples, n_features)

        # Создание целевой переменной с влиянием разных признаков
        # feature_0 и feature_1 имеют сильное влияние
        # feature_2 и feature_3 имеют среднее влияние
        # остальные признаки имеют слабое влияние

        y = (
            X[:, 0] * 2.0
            + X[:, 1] * 1.8  # сильное влияние
            + X[:, 2] * 1.0  # сильное влияние
            + X[:, 3] * 0.8  # среднее влияние
            + X[:, 4] * 0.3  # среднее влияние
            + X[:, 5] * 0.2  # слабое влияние
            + X[:, 6] * 0.1  # слабое влияние
            + X[:, 7] * 0.1  # слабое влияние
            + np.random.randn(n_samples) * 0.5  # слабое влияние  # шум
        )

        # Бинаризация для классификации
        y_binary = (y > np.median(y)).astype(int)

        # Расчет важности признаков (корреляция с целевой переменной)
        feature_names = [f"feature_{i}" for i in range(n_features)]
        feature_importance = {}

        for i, feature_name in enumerate(feature_names):
            # Абсолютная корреляция как мера важности
            correlation = abs(np.corrcoef(X[:, i], y_binary)[0, 1])
            feature_importance[feature_name] = (
                correlation if not np.isnan(correlation) else 0.0
            )

        # Нормализация важности
        total_importance = sum(feature_importance.values())
        if total_importance > 0:
            for feature in feature_importance:
                feature_importance[feature] /= total_importance

        return feature_importance

    # Запуск симуляции
    importance = simulate_feature_importance()

    # Проверка результатов
    assert len(importance) == 8, "Должно быть 8 признаков"

    # Проверка, что важные признаки имеют большую важность
    feature_0_importance = importance["feature_0"]
    feature_4_importance = importance["feature_4"]

    assert (
        feature_0_importance > feature_4_importance
    ), "Feature 0 должна иметь большую важность чем Feature 4"

    # Проверка суммы важности
    total_importance = sum(importance.values())
    assert (
        abs(total_importance - 1.0) < 0.01
    ), f"Сумма важности должна быть ~1.0, получено {total_importance}"

    print("Важность признаков:")
    for feature, imp in sorted(importance.items(), key=lambda x: x[1], reverse=True):
        print(f"  {feature}: {imp:.3f}")


def test_metrics_aggregation():
    """Тест агрегации метрик"""

    def aggregate_metrics(time_series_data):
        """Агрегация временных рядов метрик"""

        if not time_series_data:
            return {}

        values = [item["value"] for item in time_series_data]

        return {
            "mean": np.mean(values),
            "median": np.median(values),
            "std": np.std(values),
            "min": np.min(values),
            "max": np.max(values),
            "count": len(values),
            "trend": "increasing" if values[-1] > values[0] else "decreasing",
        }

    # Создание тестовых данных метрик
    np.random.seed(42)
    metric_values = np.random.normal(0.75, 0.1, 50)

    time_series = []
    for i, value in enumerate(metric_values):
        time_series.append({"timestamp": datetime.now().isoformat(), "value": value})

    # Агрегация метрик
    aggregated = aggregate_metrics(time_series)

    # Проверка результатов
    assert "mean" in aggregated
    assert "median" in aggregated
    assert "std" in aggregated
    assert "min" in aggregated
    assert "max" in aggregated
    assert "count" in aggregated
    assert "trend" in aggregated

    assert aggregated["count"] == 50
    assert aggregated["mean"] == pytest.approx(np.mean(metric_values), abs=0.01)

    print(f"Агрегация метрик:")
    print(f"  Среднее: {aggregated['mean']:.3f}")
    print(f"  Медиана: {aggregated['median']:.3f}")
    print(f"  Стандартное отклонение: {aggregated['std']:.3f}")
    print(f"  Тренд: {aggregated['trend']}")


if __name__ == "__main__":
    # Запуск всех тестов
    print("Запуск функциональных тестов ML системы...\n")

    test_requirements_accuracy_logic()
    print("✓ Тест точности анализа требований")

    test_diagram_quality_logic()
    print("✓ Тест качества диаграммы")

    test_risk_precision_logic()
    print("✓ Тест точности оценки рисков")

    test_ml_pipeline_simulation()
    print("✓ Симуляция ML пайплайна")

    test_ab_test_statistics()
    print("✓ Статистика A/B тестирования")

    test_feature_importance_simulation()
    print("✓ Симуляция важности признаков")

    test_metrics_aggregation()
    print("✓ Агрегация метрик")

    print("\n🎉 Все функциональные тесты пройдены успешно!")
