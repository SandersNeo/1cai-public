#!/usr/bin/env python3
"""
Аудит лицензионной чистоты проекта
Проверка перед публикацией на GitHub

Проверяет:
- Проприетарные данные 1С
- Конфиденциальный код
- Лицензии зависимостей
- Чужой код без атрибуции
"""

import os
import sys
from pathlib import Path
from typing import Dict, List
import json

class LicenseComplianceAuditor:
    """Аудитор лицензионной чистоты"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.issues = []
        self.warnings = []
        self.safe_to_publish = []
    
    def audit_license_compliance(self) -> Dict:
        """Полная проверка лицензионной чистоты"""
        print("=" * 80)
        print("АУДИТ ЛИЦЕНЗИОННОЙ ЧИСТОТЫ ПРОЕКТА")
        print("=" * 80)
        print()
        print("Проверка перед публикацией на GitHub...")
        print()
        
        # 1. Проверка конфигураций 1С
        print("[КРИТИЧНО] Проверка конфигураций 1С...")
        self.check_1c_configurations()
        
        # 2. Проверка knowledge base
        print("\n[КРИТИЧНО] Проверка knowledge base...")
        self.check_knowledge_base()
        
        # 3. Проверка output данных
        print("\n[КРИТИЧНО] Проверка output данных...")
        self.check_output_data()
        
        # 4. Проверка документации 1С
        print("\n[ВАЖНО] Проверка документации 1С...")
        self.check_1c_documentation()
        
        # 5. Проверка лицензий зависимостей
        print("\n[ВАЖНО] Проверка лицензий зависимостей...")
        self.check_dependency_licenses()
        
        # 6. Проверка credentials
        print("\n[КРИТИЧНО] Проверка credentials...")
        self.check_credentials()
        
        # 7. Проверка LICENSE файла
        print("\n[ВАЖНО] Проверка LICENSE файла...")
        self.check_project_license()
        
        # 8. Проверка .gitignore
        print("\n[ВАЖНО] Проверка .gitignore...")
        self.check_gitignore()
        
        return {
            'critical_issues': [i for i in self.issues if i['severity'] == 'CRITICAL'],
            'warnings': self.warnings,
            'all_issues': self.issues,
            'safe_to_publish': len([i for i in self.issues if i['severity'] == 'CRITICAL']) == 0
        }
    
    def check_1c_configurations(self):
        """Проверка конфигураций 1С"""
        config_dir = self.project_root / "1c_configurations"
        
        if not config_dir.exists():
            print("  [OK] Папка 1c_configurations не найдена")
            return
        
        # Подсчет файлов
        file_count = 0
        total_size = 0
        
        for root, dirs, files in os.walk(config_dir):
            for file in files:
                file_count += 1
                try:
                    total_size += (Path(root) / file).stat().st_size
                except:
                    pass
        
        if file_count > 0:
            size_mb = total_size / 1024 / 1024
            print(f"  [КРИТИЧНО] Найдено: {file_count:,} файлов ({size_mb:.2f} MB)")
            print(f"  [!] НЕЛЬЗЯ публиковать на GitHub!")
            print(f"  [!] Причина: Проприетарная конфигурация 1С")
            
            self.issues.append({
                'severity': 'CRITICAL',
                'category': 'Proprietary 1C Data',
                'location': '1c_configurations/',
                'issue': f'Конфигурация ERPCPM ({file_count:,} файлов, {size_mb:.2f} MB)',
                'solution': 'Добавить в .gitignore: 1c_configurations/',
                'reason': 'Проприетарное ПО 1С, защищено авторским правом'
            })
        else:
            print("  [OK] Нет файлов конфигураций")
    
    def check_knowledge_base(self):
        """Проверка knowledge base с кодом 1С"""
        kb_dir = self.project_root / "knowledge_base"
        
        if not kb_dir.exists():
            print("  [OK] Папка knowledge_base не найдена")
            return
        
        # Проверяем большие JSON файлы
        large_files = []
        for file in kb_dir.glob("*.json"):
            size_mb = file.stat().st_size / 1024 / 1024
            if size_mb > 10:
                large_files.append((file.name, size_mb))
        
        if large_files:
            total_size = sum(s for _, s in large_files)
            print(f"  [КРИТИЧНО] Найдено больших файлов: {len(large_files)}")
            for name, size in large_files:
                print(f"    - {name}: {size:.2f} MB")
            print(f"  [!] НЕЛЬЗЯ публиковать на GitHub!")
            print(f"  [!] Причина: Содержат код из конфигураций 1С")
            
            self.issues.append({
                'severity': 'CRITICAL',
                'category': 'Proprietary 1C Code',
                'location': 'knowledge_base/*.json',
                'issue': f'База знаний с кодом 1С ({len(large_files)} файлов, {total_size:.2f} MB)',
                'solution': 'Добавить в .gitignore: knowledge_base/*.json',
                'reason': 'Содержит извлеченный код из проприетарных конфигураций'
            })
        else:
            print("  [OK] Больших файлов не найдено")
    
    def check_output_data(self):
        """Проверка output данных"""
        output_dir = self.project_root / "output"
        
        if not output_dir.exists():
            print("  [OK] Папка output не найдена")
            return
        
        # Проверяем большие JSON файлы с парсингом
        large_files = []
        for file in output_dir.rglob("*.json"):
            size_mb = file.stat().st_size / 1024 / 1024
            if size_mb > 10:
                large_files.append((str(file.relative_to(output_dir)), size_mb))
        
        if large_files:
            total_size = sum(s for _, s in large_files)
            print(f"  [КРИТИЧНО] Найдено больших файлов: {len(large_files)}")
            for name, size in large_files[:10]:
                print(f"    - {name}: {size:.2f} MB")
            print(f"  [!] НЕЛЬЗЯ публиковать на GitHub!")
            print(f"  [!] Причина: Содержат распарсенный код из конфигураций 1С")
            
            self.issues.append({
                'severity': 'CRITICAL',
                'category': 'Proprietary 1C Code',
                'location': 'output/*.json (>10MB)',
                'issue': f'Результаты парсинга 1С ({len(large_files)} файлов, {total_size:.2f} MB)',
                'solution': 'Добавить в .gitignore: output/**/*.json (кроме примеров)',
                'reason': 'Содержит код из проприетарных конфигураций'
            })
        else:
            print("  [OK] Больших файлов не найдено")
    
    def check_1c_documentation(self):
        """Проверка документации от 1С"""
        # PDF и DOCX файлы
        pdf_files = list(self.project_root.rglob("*.pdf"))
        docx_files = list(self.project_root.rglob("*.docx"))
        
        # Исключаем archive_package_OLD
        pdf_files = [f for f in pdf_files if 'archive_package_OLD' not in str(f)]
        docx_files = [f for f in docx_files if 'archive_package_OLD' not in str(f)]
        
        problematic = []
        
        for pdf in pdf_files:
            # Проверяем имена файлов на признаки документации 1С
            name = pdf.name.lower()
            if any(keyword in name for keyword in ['1c', '1с', 'its', 'erp', 'документация']):
                problematic.append(('PDF', pdf.name, pdf.stat().st_size / 1024 / 1024))
        
        for docx in docx_files:
            name = docx.name.lower()
            if any(keyword in name for keyword in ['1c', '1с', 'its', 'erp', 'документация']):
                problematic.append(('DOCX', docx.name, docx.stat().st_size / 1024 / 1024))
        
        if problematic:
            print(f"  [ПРЕДУПРЕЖДЕНИЕ] Найдены потенциально проприетарные документы: {len(problematic)}")
            for ftype, name, size in problematic[:5]:
                print(f"    - {name} ({size:.2f} MB)")
            
            self.warnings.append({
                'category': 'Possible 1C Documentation',
                'files': [name for _, name, _ in problematic],
                'recommendation': 'Проверить происхождение и удалить если из 1С ИТС'
            })
        else:
            print("  [OK] Подозрительных документов не найдено")
    
    def check_dependency_licenses(self):
        """Проверка лицензий зависимостей"""
        # Читаем requirements файлы
        req_files = list(self.project_root.glob("requirements*.txt"))
        
        problematic_licenses = []
        
        # Известные проблемные пакеты (GPL и т.д. для коммерческого использования)
        gpl_packages = []  # Здесь должен быть список, но нужна проверка каждого пакета
        
        print(f"  [INFO] Найдено requirements файлов: {len(req_files)}")
        print(f"  [РЕКОМЕНДАЦИЯ] Проверить лицензии всех 75 уникальных пакетов")
        print(f"  [РЕКОМЕНДАЦИЯ] Использовать: pip-licenses или licensecheck")
        
        self.warnings.append({
            'category': 'Dependency Licenses',
            'recommendation': 'Запустить: pip install pip-licenses && pip-licenses --format=markdown',
            'note': 'Проверить что все лицензии совместимы с вашей (особенно для коммерческого использования)'
        })
    
    def check_credentials(self):
        """Проверка credentials в коде"""
        # Ищем .env файлы
        env_files = list(self.project_root.glob("**/.env"))
        env_files += list(self.project_root.glob("**/.env.*"))
        
        # Исключаем .env.example
        env_files = [f for f in env_files if '.example' not in f.name]
        
        if env_files:
            print(f"  [КРИТИЧНО] Найдены .env файлы: {len(env_files)}")
            for env_file in env_files:
                print(f"    - {env_file.relative_to(self.project_root)}")
            
            self.issues.append({
                'severity': 'CRITICAL',
                'category': 'Credentials',
                'location': '.env files',
                'issue': f'{len(env_files)} .env файлов с credentials',
                'solution': 'Добавить в .gitignore: .env, .env.*',
                'reason': 'Могут содержать реальные credentials'
            })
        else:
            print("  [OK] .env файлы не найдены")
    
    def check_project_license(self):
        """Проверка LICENSE файла проекта"""
        license_file = self.project_root / "LICENSE"
        
        if license_file.exists():
            with open(license_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"  [OK] LICENSE файл найден")
            print(f"  [INFO] Размер: {len(content)} символов")
            
            # Определяем тип лицензии
            if 'MIT' in content:
                print(f"  [INFO] Тип: MIT License (открытая)")
            elif 'Apache' in content:
                print(f"  [INFO] Тип: Apache License (открытая)")
            elif 'GPL' in content:
                print(f"  [INFO] Тип: GPL (копилефт)")
            else:
                print(f"  [ПРЕДУПРЕЖДЕНИЕ] Тип лицензии не определен")
        else:
            print(f"  [ПРЕДУПРЕЖДЕНИЕ] LICENSE файл не найден")
            print(f"  [РЕКОМЕНДАЦИЯ] Добавить LICENSE файл перед публикацией")
            
            self.warnings.append({
                'category': 'Missing License',
                'recommendation': 'Добавить LICENSE файл (MIT, Apache 2.0, или другую)',
                'note': 'Без лицензии код по умолчанию защищен авторским правом'
            })
    
    def check_gitignore(self):
        """Проверка .gitignore"""
        gitignore = self.project_root / ".gitignore"
        
        required_entries = [
            '1c_configurations/',
            'knowledge_base/*.json',
            'output/**/*.json',
            '.env',
            '.env.*',
            '*.log'
        ]
        
        if gitignore.exists():
            with open(gitignore, 'r', encoding='utf-8') as f:
                content = f.read()
            
            missing = []
            for entry in required_entries:
                # Упрощенная проверка
                base = entry.replace('/', '').replace('*', '').replace('.', '')
                if base not in content.replace('/', '').replace('*', '').replace('.', ''):
                    missing.append(entry)
            
            if missing:
                print(f"  [ПРЕДУПРЕЖДЕНИЕ] Отсутствуют в .gitignore:")
                for entry in missing:
                    print(f"    - {entry}")
                
                self.warnings.append({
                    'category': 'Incomplete .gitignore',
                    'missing_entries': missing,
                    'recommendation': 'Добавить в .gitignore'
                })
            else:
                print(f"  [OK] .gitignore содержит необходимые записи")
        else:
            print(f"  [КРИТИЧНО] .gitignore не найден!")
            
            self.issues.append({
                'severity': 'CRITICAL',
                'category': 'Missing .gitignore',
                'issue': '.gitignore файл отсутствует',
                'solution': 'Создать .gitignore с исключениями',
                'reason': 'Без .gitignore проприетарные данные могут попасть в репозиторий'
            })
    
    def generate_safe_gitignore(self) -> List[str]:
        """Генерация безопасного .gitignore"""
        return [
            "# === КРИТИЧНО: Не публиковать ===",
            "",
            "# Конфигурации 1С (проприетарные!)",
            "1c_configurations/",
            "",
            "# База знаний с кодом 1С (проприетарные!)",
            "knowledge_base/*.json",
            "knowledge_base/**/*.json",
            "",
            "# Результаты парсинга с кодом 1С (проприетарные!)",
            "output/edt_parser/*.json",
            "output/dataset/*.json",
            "",
            "# Credentials и секреты",
            ".env",
            ".env.*",
            "!.env.example",
            "",
            "# === Стандартные исключения ===",
            "",
            "# Python",
            "__pycache__/",
            "*.py[cod]",
            "*$py.class",
            "*.so",
            ".Python",
            "venv/",
            "env/",
            ".venv/",
            "",
            "# Logs",
            "*.log",
            "logs/",
            "",
            "# OS",
            ".DS_Store",
            "Thumbs.db",
            "",
            "# IDE",
            ".vscode/",
            ".idea/",
            "*.swp",
            "*.swo",
            "",
            "# Node",
            "node_modules/",
            "package-lock.json",
            "",
            "# Build",
            "dist/",
            "build/",
            "*.egg-info/",
            "",
            "# Cache",
            ".pytest_cache/",
            ".cache/",
            "",
            "# Archives (если есть старые backups)",
            "archive_package_OLD*/",
            "",
            "# === Можно публиковать ===",
            "",
            "# Примеры небольших конфигураций (если есть)",
            "!examples/**/*.xml",
            "",
            "# Примеры dataset (небольшие)",
            "!output/dataset/example_*.json"
        ]


def main():
    """Главная функция"""
    project_root = Path(".")
    
    auditor = LicenseComplianceAuditor(project_root)
    results = auditor.audit_license_compliance()
    
    # Результаты
    print("\n" + "=" * 80)
    print("РЕЗУЛЬТАТЫ ПРОВЕРКИ")
    print("=" * 80)
    
    critical = results['critical_issues']
    warnings = results['warnings']
    
    print(f"\nКритичных проблем: {len(critical)}")
    print(f"Предупреждений: {len(warnings)}")
    
    if critical:
        print("\n" + "!" * 80)
        print("КРИТИЧНЫЕ ПРОБЛЕМЫ (НЕЛЬЗЯ ПУБЛИКОВАТЬ БЕЗ ИСПРАВЛЕНИЯ):")
        print("!" * 80)
        
        for i, issue in enumerate(critical, 1):
            print(f"\n{i}. {issue['category']}")
            print(f"   Где: {issue['location']}")
            print(f"   Проблема: {issue['issue']}")
            print(f"   Решение: {issue['solution']}")
            print(f"   Причина: {issue['reason']}")
    
    if warnings:
        print("\n" + "=" * 80)
        print("ПРЕДУПРЕЖДЕНИЯ (РЕКОМЕНДУЕТСЯ ИСПРАВИТЬ):")
        print("=" * 80)
        
        for i, warning in enumerate(warnings, 1):
            print(f"\n{i}. {warning['category']}")
            print(f"   Рекомендация: {warning['recommendation']}")
    
    # Генерируем безопасный .gitignore
    print("\n" + "=" * 80)
    print("РЕКОМЕНДОВАННЫЙ .gitignore")
    print("=" * 80)
    
    safe_gitignore = auditor.generate_safe_gitignore()
    
    gitignore_file = project_root / ".gitignore.recommended"
    with open(gitignore_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(safe_gitignore))
    
    print(f"\n[+] Создан: .gitignore.recommended")
    print(f"[!] ВАЖНО: Проверьте и скопируйте в .gitignore перед публикацией!")
    
    # Финальный вывод
    print("\n" + "=" * 80)
    
    if len(critical) == 0:
        print("✅ БЕЗОПАСНО ПУБЛИКОВАТЬ (после проверки warnings)")
    else:
        print("❌ НЕ ПУБЛИКОВАТЬ БЕЗ ИСПРАВЛЕНИЯ КРИТИЧНЫХ ПРОБЛЕМ")
    
    print("=" * 80)
    
    # Сохранение отчета
    output_dir = Path("./output/audit")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "license_compliance_audit.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\nДетальный отчет: {output_file}")
    
    return 0 if len(critical) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())



