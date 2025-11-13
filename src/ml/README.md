# ML Module

Компоненты для ML/ML Ops: обучение, метрики, эксперименты, A/B тесты.

| Подкаталог | Описание |
|------------|----------|
| `training/` | Тренеры моделей (см. `trainer.py`). |
| `models/` | Обёртки над моделями/предикторами (`predictor.py`). |
| `metrics/` | Сбор метрик ML (`collector.py`). |
| `experiments/` | Интеграция с MLflow, управление экспериментами (`mlflow_manager.py`). |
| `ab_testing/` | A/B тестирование моделей (`tester.py`).

Используется совместно с скриптами `scripts/dataset/`, `scripts/run_neural_training.py`, `scripts/finetune_qwen_smoltalk.py`. Подробнее — [docs/06-features/ML_DATASET_GENERATOR_GUIDE.md](../../docs/06-features/ML_DATASET_GENERATOR_GUIDE.md).
