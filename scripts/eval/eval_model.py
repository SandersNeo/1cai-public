"""
Простой скрипт для проверки качества обученной ML‑модели 1C AI Stack.

Usage:
    python scripts/eval/eval_model.py --model ./models/demo-model --questions output/dataset/DEMO_qa.jsonl --limit 10
    python scripts/eval/eval_model.py --config-name ERPCPM --save reports/eval/ERPCPM.json
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Optional

from scripts.ml.config_utils import get_config, load_configs, format_config_info


def load_dataset(path: Path, limit: int) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fh:
        lines = fh.readlines()

    samples: List[Dict[str, Any]] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            samples.append(json.loads(line))
        except json.JSONDecodeError:
            continue
        if 0 < limit <= len(samples):
            break
    return samples


def evaluate(
    model_path: Path,
    dataset_path: Path,
    dataset: List[Dict[str, Any]],
    config_name: Optional[str],
) -> Dict[str, Any]:
    if not model_path.exists():
        raise FileNotFoundError(f"Model path not found: {model_path}")

    print(f"📁 Model path: {model_path}")
    print(f"📊 Samples to evaluate: {len(dataset)}")
    print("\n⚠️  Demo evaluator: проверяются только структура и наличие ответов.\n")

    missing_answer = 0
    missing_metadata = 0
    answer_lengths: List[int] = []
    question_lengths: List[int] = []

    for sample in dataset:
        answer = sample.get("answer")
        if not answer:
            missing_answer += 1
        else:
            answer_lengths.append(len(str(answer).split()))

        metadata = sample.get("metadata")
        if not metadata:
            missing_metadata += 1

        question = sample.get("question") or sample.get("prompt")
        if question:
            question_lengths.append(len(str(question).split()))

    total = len(dataset)

    print("Результаты проверки:")
    print(f"  • Всего примеров: {total}")
    print(f"  • Без answer: {missing_answer}")
    print(f"  • Без metadata: {missing_metadata}")

    if total > 0:
        quality_score = ((total - missing_answer) / total) * 100
        print(f"\nОценка (условная): {quality_score:.1f}% заполненных ответов.")
    else:
        print("\nДатасет пустой — ничего оценивать.")

    summary = {
        "config_name": config_name,
        "model_path": str(model_path),
        "dataset_path": str(dataset_path),
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "total_samples": total,
        "answered_samples": total - missing_answer,
        "missing_answer": missing_answer,
        "missing_metadata": missing_metadata,
        "answer_coverage": 0.0 if total == 0 else (total - missing_answer) / total,
        "metadata_coverage": 0.0 if total == 0 else (total - missing_metadata) / total,
        "avg_answer_tokens": round(mean(answer_lengths), 2) if answer_lengths else 0.0,
        "avg_question_tokens": round(mean(question_lengths), 2) if question_lengths else 0.0,
    }

    return summary


def print_summary(summary: Dict[str, Any]) -> None:
    print("\n📈 Summary")
    print(f"  • Answer coverage     : {summary['answer_coverage'] * 100:.1f}%")
    print(f"  • Metadata coverage   : {summary['metadata_coverage'] * 100:.1f}%")
    print(f"  • Avg answer tokens   : {summary['avg_answer_tokens']}")
    print(f"  • Avg question tokens : {summary['avg_question_tokens']}")


def list_configs() -> None:
    for name in sorted(load_configs()):
        print(name)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate 1C AI demo model")
    parser.add_argument("--model", help="Путь к сохранённой модели (директория или файл)")
    parser.add_argument("--questions", help="JSONL файл с вопросами/ответами")
    parser.add_argument("--limit", type=int, help="Сколько примеров проверить (по умолчанию из конфигурации или 20)")
    parser.add_argument("--config-name", help="Имя набора из config/ml_datasets.json")
    parser.add_argument("--save", help="Путь для сохранения JSON отчёта (по умолчанию из конфигурации)")
    parser.add_argument("--list-configs", action="store_true", help="Показать доступные конфигурации и выйти")

    args = parser.parse_args()

    if args.list_configs:
        list_configs()
        return

    config = None
    if args.config_name:
        config = get_config(args.config_name)
        print(format_config_info(args.config_name, config))

    model_arg = args.model or (config.get("model_host") if config else None)
    questions_arg = args.questions or (config.get("qa_host") if config else None)

    if not model_arg or not questions_arg:
        raise SystemExit("Specify --model and --questions or use --config-name with predefined paths.")

    limit = args.limit
    if limit is None:
        if config and config.get("evaluation_limit"):
            limit = int(config["evaluation_limit"])
        else:
            limit = 20

    model_path = Path(model_arg)
    dataset_path = Path(questions_arg)

    dataset = load_dataset(dataset_path, limit)
    summary = evaluate(model_path, dataset_path, dataset, args.config_name)
    print_summary(summary)

    save_path: Optional[Path] = None
    if args.save:
        save_path = Path(args.save)
    elif config and config.get("eval_report"):
        save_path = Path(config["eval_report"])

    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with save_path.open("w", encoding="utf-8") as handle:
            json.dump(summary, handle, ensure_ascii=False, indent=2)
        print(f"\n💾 Report saved to: {save_path}")


if __name__ == "__main__":
    main()

