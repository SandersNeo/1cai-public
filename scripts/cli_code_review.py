# [NEXUS IDENTITY] ID: 84852357476285808 | DATE: 2025-11-19

#!/usr/bin/env python3
"""
CLI инструмент для Code Review
Версия: 1.0.0
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Optional
import httpx
from datetime import datetime


class CodeReviewCLI:
    """CLI инструмент для анализа кода"""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.client = httpx.Client(timeout=30.0)
    
    def analyze_file(self, file_path: str, language: Optional[str] = None, output_format: str = "json") -> dict:
        """Анализ файла"""
        path = Path(file_path)
        
        if not path.exists():
            print(f"❌ Файл не найден: {file_path}", file=sys.stderr)
            sys.exit(1)
        
        # Определение языка по расширению
        if not language:
            ext = path.suffix.lower()
            lang_map = {
                '.bsl': 'bsl',
                '.ts': 'typescript',
                '.js': 'javascript',
                '.py': 'python'
            }
            language = lang_map.get(ext, 'bsl')
        
        # Чтение файла
        try:
            with open(path, 'r', encoding='utf-8') as f:
                code = f.read()
        except Exception as e:
            print(f"❌ Ошибка чтения файла: {e}", file=sys.stderr)
            sys.exit(1)
        
        # Анализ через API
        try:
            response = self.client.post(
                f"{self.api_url}/api/code-review/analyze",
                json={
                    "content": code,
                    "language": language,
                    "fileName": path.name
                }
            )
            response.raise_for_status()
            result = response.json()
            
            # Форматирование вывода
            if output_format == "json":
                return result
            elif output_format == "pretty":
                return self._format_pretty(result)
            else:
                return result
                
        except httpx.HTTPError as e:
            print(f"❌ Ошибка API: {e}", file=sys.stderr)
            sys.exit(1)
    
    def analyze_directory(self, directory: str, language: Optional[str] = None, recursive: bool = False) -> dict:
        """Анализ директории"""
        dir_path = Path(directory)
        
        if not dir_path.is_dir():
            print(f"❌ Директория не найдена: {directory}", file=sys.stderr)
            sys.exit(1)
        
        results = []
        
        # Поиск файлов
        pattern = "**/*" if recursive else "*"
        
        for ext in ['.bsl', '.ts', '.js', '.py']:
            for file_path in dir_path.glob(pattern):
                if file_path.is_file() and file_path.suffix == ext:
                    print(f"📄 Анализ: {file_path}", file=sys.stderr)
                    result = self.analyze_file(str(file_path), language)
                    results.append({
                        "file": str(file_path),
                        "analysis": result
                    })
        
        return {
            "directory": str(dir_path),
            "total_files": len(results),
            "analyses": results,
            "timestamp": datetime.now().isoformat()
        }
    
    def _format_pretty(self, result: dict) -> str:
        """Красивое форматирование результата"""
        lines = []
        lines.append(f"📊 Результат анализа кода\n")
        lines.append("=" * 80 + "\n\n")
        
        # Метрики
        metrics = result.get("metrics", {})
        lines.append("📈 Метрики:\n")
        lines.append(f"  Сложность: {metrics.get('complexity', 0)}/100\n")
        lines.append(f"  Поддерживаемость: {metrics.get('maintainability', 0)}/100\n")
        lines.append(f"  Безопасность: {metrics.get('securityScore', 0)}/100\n")
        lines.append(f"  Производительность: {metrics.get('performanceScore', 0)}/100\n")
        lines.append(f"  Качество кода: {metrics.get('codeQuality', 0)}/100\n\n")
        
        # Предложения
        suggestions = result.get("suggestions", [])
        if suggestions:
            lines.append(f"💡 Предложения ({len(suggestions)}):\n\n")
            
            for suggestion in suggestions:
                severity_icons = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢"
                }
                icon = severity_icons.get(suggestion.get("severity", "medium"), "⚪")
                
                lines.append(f"{icon} [{suggestion.get('severity', 'medium').upper()}] {suggestion.get('message', '')}\n")
                lines.append(f"   Строка: {suggestion.get('position', {}).get('line', 0)}\n")
                lines.append(f"   Категория: {suggestion.get('category', 'unknown')}\n")
                if suggestion.get('suggestion'):
                    lines.append(f"   💡 Предложение: {suggestion['suggestion']}\n")
                lines.append("\n")
        else:
            lines.append("✅ Проблем не обнаружено!\n\n")
        
        # Рекомендации
        recommendations = result.get("recommendations", [])
        if recommendations:
            lines.append("📋 Рекомендации:\n")
            for rec in recommendations:
                lines.append(f"  • {rec}\n")
            lines.append("\n")
        
        return ''.join(lines)


def main():
    """Главная функция CLI"""
    parser = argparse.ArgumentParser(
        description="CLI инструмент для Code Review",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:

  # Анализ одного файла
  python scripts/cli_code_review.py analyze file.bsl

  # Анализ с указанием языка
  python scripts/cli_code_review.py analyze file.bsl --language bsl

  # Анализ директории
  python scripts/cli_code_review.py analyze-dir src/

  # Рекурсивный анализ
  python scripts/cli_code_review.py analyze-dir src/ --recursive

  # Вывод в формате JSON
  python scripts/cli_code_review.py analyze file.bsl --format json

  # Вывод в красивом формате
  python scripts/cli_code_review.py analyze file.bsl --format pretty
        """
    )
    
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="URL API сервера (по умолчанию: http://localhost:8000)"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Команды')
    
    # Команда analyze
    analyze_parser = subparsers.add_parser('analyze', help='Анализ файла')
    analyze_parser.add_argument('file', help='Путь к файлу для анализа')
    analyze_parser.add_argument('--language', choices=['bsl', 'typescript', 'javascript', 'python'], help='Язык программирования')
    analyze_parser.add_argument('--format', choices=['json', 'pretty'], default='pretty', help='Формат вывода')
    analyze_parser.add_argument('--output', help='Файл для сохранения результата')
    
    # Команда analyze-dir
    dir_parser = subparsers.add_parser('analyze-dir', help='Анализ директории')
    dir_parser.add_argument('directory', help='Путь к директории для анализа')
    dir_parser.add_argument('--language', choices=['bsl', 'typescript', 'javascript', 'python'], help='Язык программирования')
    dir_parser.add_argument('--recursive', action='store_true', help='Рекурсивный поиск файлов')
    dir_parser.add_argument('--output', help='Файл для сохранения результата')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    cli = CodeReviewCLI(api_url=args.api_url)
    
    try:
        if args.command == 'analyze':
            result = cli.analyze_file(args.file, args.language, args.format)
            
            if args.format == 'json':
                output = json.dumps(result, indent=2, ensure_ascii=False)
            else:
                output = result
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(output)
                print(f"✅ Результат сохранен в: {args.output}")
            else:
                print(output)
        
        elif args.command == 'analyze-dir':
            result = cli.analyze_directory(args.directory, args.language, args.recursive)
            
            output = json.dumps(result, indent=2, ensure_ascii=False)
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(output)
                print(f"✅ Результат сохранен в: {args.output}")
            else:
                print(output)
    
    except KeyboardInterrupt:
        print("\n⚠️  Прервано пользователем", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"❌ Ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()







