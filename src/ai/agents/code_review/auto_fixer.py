"""
Auto-Fixer
Автоматическое исправление найденных проблем
"""

import re
from typing import Dict, List, Optional
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class AutoFixer:
    """
    Автоматическое исправление кода
    
    Умеет исправлять:
    - SQL Injection (замена на параметры)
    - Отсутствие обработки ошибок
    - Naming conventions
    - Missing documentation
    """
    
    def __init__(self):
        self.fixes_applied = []
    
    def fix_sql_injection(self, code: str, issue: Dict) -> str:
        """
        Автоматическое исправление SQL injection
        
        Преобразует:
        Запрос.Текст = "SELECT * WHERE Field = '" + Value + "'"
        
        В:
        Запрос.Текст = "SELECT * WHERE Field = &Parameter"
        Запрос.УстановитьПараметр("Parameter", Value)
        """
        
        fixed_code = code
        
        # Pattern: Запрос.Текст = "..." + Variable + "..."
        pattern = r'Запрос\.Текст\s*=\s*"([^"]*)"\s*\+\s*(\w+)(?:\s*\+\s*"([^"]*)")?'
        
        def replace_with_param(match):
            before = match.group(1)
            variable = match.group(2)
            after = match.group(3) or ""
            
            # Generate parameter name
            param_name = f"Param_{variable}"
            
            # New query text with parameter
            new_query = f'Запрос.Текст = "{before}&{param_name}{after}";\n    Запрос.УстановитьПараметр("{param_name}", {variable})'
            
            self.fixes_applied.append({
                'type': 'SQL_INJECTION_FIX',
                'original': match.group(0),
                'fixed': new_query
            })
            
            return new_query
        
        fixed_code = re.sub(pattern, replace_with_param, fixed_code, flags=re.IGNORECASE)
        
        return fixed_code
    
    def add_error_handling(self, code: str, issue: Dict) -> str:
        """
        Добавление обработки ошибок
        
        Оборачивает критичные операции в Попытка...Исключение
        """
        
        fixed_code = code
        
        operation = issue.get('operation', '')
        function_name = issue.get('function', '')
        
        # Find function body
        func_pattern = rf'(Функция\s+{function_name}\s*\([^)]*\)[^\n]*\n)(.*?)(КонецФункции)'
        
        match = re.search(func_pattern, code, re.IGNORECASE | re.DOTALL)
        
        if match:
            func_header = match.group(1)
            func_body = match.group(2)
            func_end = match.group(3)
            
            # Wrap body in try-catch
            wrapped_body = f'''    
    Попытка
        {func_body.strip()}
    Исключение
        ЗаписьЖурналаРегистрации(
            "Ошибка в {function_name}",
            УровеньЖурналаРегистрации.Ошибка,
            ,
            ,
            ПодробноеПредставлениеОшибки(ИнформацияОбОшибке())
        );
        
        Возврат Неопределено;
    КонецПопытки;
    '''
            
            fixed_function = func_header + wrapped_body + '\n' + func_end
            fixed_code = code.replace(match.group(0), fixed_function)
            
            self.fixes_applied.append({
                'type': 'ERROR_HANDLING_ADDED',
                'function': function_name
            })
        
        return fixed_code
    
    def fix_naming_convention(self, code: str, issue: Dict) -> str:
        """Исправление naming conventions"""
        
        old_name = issue.get('function', '')
        
        if old_name and old_name[0].islower():
            new_name = old_name[0].upper() + old_name[1:]
            
            # Replace all occurrences
            fixed_code = re.sub(
                rf'\b{old_name}\b',
                new_name,
                code
            )
            
            self.fixes_applied.append({
                'type': 'NAMING_FIX',
                'old_name': old_name,
                'new_name': new_name
            })
            
            return fixed_code
        
        return code
    
    def add_documentation(self, code: str, issue: Dict) -> str:
        """Добавление документации к функции"""
        
        function_name = issue.get('function', '')
        
        # Find function declaration
        pattern = rf'(Функция\s+{function_name}\s*\([^)]*\)[^\n]*)'
        
        match = re.search(pattern, code, re.IGNORECASE)
        
        if match:
            # Generate basic documentation
            doc = f'''
// Функция {function_name}
//
// Параметры:
//   TODO: Описать параметры
//
// Возвращаемое значение:
//   TODO: Описать возвращаемое значение
//
'''
            
            # Insert before function
            fixed_code = code.replace(match.group(0), doc + match.group(0))
            
            self.fixes_applied.append({
                'type': 'DOCUMENTATION_ADDED',
                'function': function_name
            })
            
            return fixed_code
        
        return code
    
    def auto_fix_all(
        self,
        code: str,
        issues: List[Dict],
        fix_types: List[str] = None
    ) -> Dict[str, any]:
        """
        Автоматическое исправление всех возможных проблем
        
        Args:
            code: Исходный код
            issues: Список найденных проблем
            fix_types: Какие типы исправлять (если None - все)
        
        Returns:
            {
                'fixed_code': '...',
                'fixes_applied': [...],
                'unfixable_issues': [...]
            }
        """
        
        fixed_code = code
        self.fixes_applied = []
        unfixable = []
        
        for issue in issues:
            issue_type = issue.get('type')
            
            # Skip if not in fix_types
            if fix_types and issue_type not in fix_types:
                continue
            
            try:
                if issue_type == 'SQL_INJECTION_RISK':
                    fixed_code = self.fix_sql_injection(fixed_code, issue)
                
                elif issue_type == 'MISSING_ERROR_HANDLING':
                    fixed_code = self.add_error_handling(fixed_code, issue)
                
                elif issue_type == 'NAMING_CONVENTION':
                    fixed_code = self.fix_naming_convention(fixed_code, issue)
                
                elif issue_type == 'MISSING_DOCUMENTATION':
                    fixed_code = self.add_documentation(fixed_code, issue)
                
                else:
                    # Cannot auto-fix this type
                    unfixable.append(issue)
                    
            except Exception as e:
                logger.error(
                    "Failed to fix issue",
                    extra={
                        "issue_type": issue_type,
                        "error": str(e),
                        "error_type": type(e).__name__
                    },
                    exc_info=True
                )
                unfixable.append(issue)
        
        return {
            'fixed_code': fixed_code,
            'fixes_applied': self.fixes_applied,
            'fixes_count': len(self.fixes_applied),
            'unfixable_issues': unfixable,
            'unfixable_count': len(unfixable)
        }


