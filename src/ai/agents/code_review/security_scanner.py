"""
Security Scanner для BSL кода
Детекция уязвимостей безопасности
"""

import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class SecurityScanner:
    """Сканер безопасности для BSL кода"""
    
    def __init__(self):
        self.vulnerabilities = []
        self._load_patterns()
    
    def _load_patterns(self):
        """Загрузка паттернов уязвимостей"""
        self.sql_injection_patterns = [
            r'Запрос\.Текст\s*=\s*.*\+',  # Конкатенация в запросе
            r'ВыполнитьЗапрос\([^&]*\+',   # Динамический запрос с конкатенацией
        ]
        
        self.xss_patterns = [
            r'HTTPСервисОтвет.*УстановитьТелоИзСтроки\(',
        ]
        
        self.credential_patterns = [
            (r'Пароль\s*=\s*"[^"]+"', 'Password'),
            (r'Password\s*=\s*"[^"]+"', 'Password'),
            (r'Token\s*=\s*"[A-Za-z0-9]{20,}"', 'Token'),
            (r'APIKey\s*=\s*"[A-Za-z0-9]{20,}"', 'API Key'),
            (r'SecretKey\s*=\s*"[^"]+"', 'Secret Key'),
        ]
    
    def scan(self, code: str, ast: Dict) -> List[Dict]:
        """
        Полное сканирование безопасности
        
        Returns:
            List of security issues
        """
        issues = []
        
        issues.extend(self.scan_sql_injection(code, ast))
        issues.extend(self.scan_xss(code))
        issues.extend(self.scan_hardcoded_credentials(code))
        issues.extend(self.scan_insecure_crypto(code))
        
        return issues
    
    def scan_sql_injection(self, code: str, ast: Dict) -> List[Dict]:
        """Проверка на SQL injection"""
        issues = []
        
        # Pattern 1: Конкатенация в Запрос.Текст
        if re.search(r'Запрос\.Текст\s*=\s*"[^"]*"\s*\+', code, re.IGNORECASE):
            line_num = self._find_line_number(code, 'Запрос.Текст')
            issues.append({
                'type': 'SQL_INJECTION_RISK',
                'severity': 'CRITICAL',
                'line': line_num,
                'message': 'Опасность SQL Injection! Используется конкатенация строк в тексте запроса.',
                'description': '''
SQL Injection - одна из самых опасных уязвимостей!

Злоумышленник может:
- Прочитать всю БД
- Изменить/удалить данные
- Получить admin доступ
- Выполнить OS команды (в некоторых СУБД)

Пример атаки:
Если код: Запрос.Текст = "ВЫБРАТЬ * ГДЕ Логин = \\"" + Логин + "\\""
Атакующий вводит: admin" OR "1"="1

Получится: ВЫБРАТЬ * ГДЕ Логин = "admin" OR "1"="1"
→ Вернет всех пользователей!
''',
                'recommendation': '''
✅ ВСЕГДА используйте параметры запроса:

// ❌ ОПАСНО:
Запрос.Текст = "ВЫБРАТЬ * ГДЕ Поле = \\"" + Значение + "\\"";

// ✅ БЕЗОПАСНО:
Запрос.Текст = "ВЫБРАТЬ * ГДЕ Поле = &Параметр";
Запрос.УстановитьПараметр("Параметр", Значение);
''',
                'cwe_id': 'CWE-89',
                'owasp': 'A03:2021 - Injection',
                'auto_fix_available': True
            })
        
        # Pattern 2: Выполнить() с динамической строкой
        if re.search(r'Выполнить\s*\([^"]*\+', code, re.IGNORECASE):
            line_num = self._find_line_number(code, 'Выполнить(')
            issues.append({
                'type': 'CODE_INJECTION_RISK',
                'severity': 'CRITICAL',
                'line': line_num,
                'message': 'Опасность Code Injection! Динамическое выполнение кода.',
                'recommendation': 'Избегайте Выполнить() с пользовательским вводом. Используйте статический код.',
                'cwe_id': 'CWE-94',
                'owasp': 'A03:2021 - Injection'
            })
        
        return issues
    
    def scan_xss(self, code: str) -> List[Dict]:
        """Проверка на XSS уязвимости"""
        issues = []
        
        # HTTP сервисы без экранирования
        if 'HTTPСервисОтвет' in code or 'HTTPСервис' in code:
            # Проверяем есть ли экранирование
            has_escaping = any(pattern in code for pattern in [
                'СтрЗаменить',
                'HTMLEncode',
                'XMLСтрока',
                'ЭкранироватьHTML'
            ])
            
            if not has_escaping:
                line_num = self._find_line_number(code, 'HTTPСервис')
                issues.append({
                    'type': 'XSS_VULNERABILITY',
                    'severity': 'HIGH',
                    'line': line_num,
                    'message': 'Возможна XSS уязвимость! Пользовательские данные не экранируются.',
                    'description': '''
XSS (Cross-Site Scripting) позволяет атакующему:
- Внедрить JavaScript в страницу
- Украсть cookies/tokens
- Выполнить действия от имени пользователя
- Редирект на фишинговую страницу
''',
                    'recommendation': '''
✅ Экранируйте все пользовательские данные:

// Для HTML:
БезопасноеЗначение = СтрЗаменить(ПользовательскийВвод, "<", "&lt;");
БезопасноеЗначение = СтрЗаменить(БезопасноеЗначение, ">", "&gt;");

// Для XML:
БезопасноеЗначение = XMLСтрока(ПользовательскийВвод);

Ответ.УстановитьТелоИзСтроки(БезопасноеЗначение);
''',
                    'cwe_id': 'CWE-79',
                    'owasp': 'A03:2021 - Injection'
                })
        
        return issues
    
    def scan_hardcoded_credentials(self, code: str, _: Dict | None = None) -> List[Dict]:
        """Поиск захардкоженных паролей"""
        issues = []
        
        for pattern, cred_type in self.credential_patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE)
            
            for match in matches:
                # Исключаем очевидные плейсхолдеры
                value = match.group(0)
                if any(placeholder in value.lower() for placeholder in [
                    'your_password',
                    'your_token',
                    'example',
                    'placeholder',
                    'xxxxx'
                ]):
                    continue
                
                line_num = code[:match.start()].count('\n') + 1
                
                issues.append({
                    'type': 'HARDCODED_CREDENTIALS',
                    'severity': 'CRITICAL',
                    'line': line_num,
                    'credential_type': cred_type,
                    'message': f'{cred_type} захардкожен в коде!',
                    'description': '''
Hardcoded credentials - КРИТИЧНАЯ уязвимость!

Риски:
- Код часто в Git → credentials в истории навсегда
- Если код утечет → instant breach
- Нельзя ротировать без изменения кода
- Compliance violations (PCI DSS, SOC 2)
''',
                    'recommendation': '''
✅ Используйте безопасное хранение:

// Вариант 1: Переменные окружения
Пароль = ПолучитьПеременнуюОкружения("DB_PASSWORD");

// Вариант 2: Защищенное хранилище 1С
Пароль = ХранилищеОбщихНастроек.Загрузить("Безопасность", "ПарольБД");

// Вариант 3: Внешнее хранилище (HashiCorp Vault, AWS Secrets Manager)
Пароль = ПолучитьИзVault("database/password");
''',
                    'cwe_id': 'CWE-798',
                    'owasp': 'A07:2021 - Identification and Authentication Failures'
                })
        
        return issues
    
    def scan_insecure_crypto(self, code: str) -> List[Dict]:
        """Проверка небезопасной криптографии"""
        issues = []
        
        # MD5/SHA1 (устаревшие)
        if re.search(r'(MD5|SHA1)\s*\(', code, re.IGNORECASE):
            line_num = self._find_line_number(code, 'MD5')
            issues.append({
                'type': 'WEAK_CRYPTOGRAPHY',
                'severity': 'HIGH',
                'line': line_num,
                'message': 'Использование устаревшего hash algorithm (MD5/SHA1)',
                'recommendation': '''
MD5 и SHA1 считаются небезопасными (collision attacks)!

✅ Используйте современные алгоритмы:
- SHA-256 (для hash)
- bcrypt или Argon2 (для паролей)
- AES-256 (для шифрования)
''',
                'cwe_id': 'CWE-327'
            })
        
        return issues
    
    def _find_line_number(self, code: str, search_text: str) -> int:
        """Находит номер строки с текстом"""
        pos = code.find(search_text)
        if pos == -1:
            return 1
        return code[:pos].count('\n') + 1


