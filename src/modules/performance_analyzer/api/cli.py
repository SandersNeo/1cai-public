"""
API интерфейс (CLI) для анализатора производительности.
"""
import argparse
import json
import pkgutil
import importlib
from dataclasses import asdict
from typing import List
from src.modules.performance_analyzer.services.profiler import StartupProfiler


def get_submodules(package_name: str) -> List[str]:
    """
    Рекурсивно находит подмодули в пакете.
    """
    submodules = []
    try:
        package = importlib.import_module(package_name)
        if hasattr(package, "__path__"):
            for _, name, _ in pkgutil.iter_modules(package.__path__):
                full_name = f"{package_name}.{name}"
                submodules.append(full_name)
    except ImportError:
        print(f"⚠️ Не удалось импортировать пакет: {package_name}")
    return submodules


def main() -> None:
    """
    Основная функция запуска CLI.
    """
    parser = argparse.ArgumentParser(description="1cAI Performance Analyzer")
    parser.add_argument(
        "--modules",
        nargs="+",
        default=["src.ai", "src.modules"],
        help="Список пакетов для проверки (будут просканированы подмодули)",
    )
    parser.add_argument("--output", default="performance_report.json", help="Путь к файлу отчета")

    args = parser.parse_args()

    # Автоматическое обнаружение подмодулей
    target_modules = []
    for pkg in args.modules:
        found = get_submodules(pkg)
        if found:
            target_modules.extend(found)
        else:
            target_modules.append(pkg)

    print(f"🚀 Запуск анализа производительности для {len(target_modules)} модулей...")

    profiler = StartupProfiler()
    report = profiler.run_analysis(target_modules)

    print(f"⏱️ Общее время: {report.total_time_ms:.2f} ms")

    # Вывод топ-5 самых медленных
    sorted_imports = sorted(report.imports, key=lambda x: x.import_time_ms, reverse=True)
    print("\n🐢 Топ-5 самых медленных импортов:")
    for imp in sorted_imports[:5]:
        print(f"  - {imp.module_name}: {imp.import_time_ms:.2f} ms")

    # Сохранение отчета
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(asdict(report), f, indent=2, default=str, ensure_ascii=False)

    print(f"\n💾 Отчет сохранен в: {args.output}")


if __name__ == "__main__":
    main()
