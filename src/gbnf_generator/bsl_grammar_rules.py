"""
BSL Grammar Rules - Упрощенная версия для GBNF генерации

Основные конструкции BSL (1С:Enterprise) для автогенерации GBNF.
Источник: Синтакс-помощник 1С + BSL Language Server
"""

# Ключевые слова BSL (русский + английский)
KEYWORDS = {
    # Условия
    'if': {'ru': ['Если', 'если', 'ЕСЛИ'], 'en': ['If', 'if', 'IF']},
    'then': {'ru': ['Тогда', 'тогда', 'ТОГДА'], 'en': ['Then', 'then', 'THEN']},
    'elsif': {'ru': ['ИначеЕсли', 'иначеесли', 'ИНАЧЕЕСЛИ'], 'en': ['ElsIf', 'elsif', 'ELSIF']},
    'else': {'ru': ['Иначе', 'иначе', 'ИНАЧЕ'], 'en': ['Else', 'else', 'ELSE']},
    'endif': {'ru': ['КонецЕсли', 'конецесли', 'КОНЕЦЕСЛИ'], 'en': ['EndIf', 'endif', 'ENDIF']},

    # Циклы
    'for': {'ru': ['Для', 'для', 'ДЛЯ'], 'en': ['For', 'for', 'FOR']},
    'each': {'ru': ['Каждого', 'каждого', 'КАЖДОГО'], 'en': ['Each', 'each', 'EACH']},
    'in': {'ru': ['Из', 'из', 'ИЗ'], 'en': ['In', 'in', 'IN']},
    'to': {'ru': ['По', 'по', 'ПО'], 'en': ['To', 'to', 'TO']},
    'while': {'ru': ['Пока', 'пока', 'ПОКА'], 'en': ['While', 'while', 'WHILE']},
    'do': {'ru': ['Цикл', 'цикл', 'ЦИКЛ'], 'en': ['Do', 'do', 'DO']},
    'enddo': {'ru': ['КонецЦикла', 'конеццикла', 'КОНЕЦЦИКЛА'], 'en': ['EndDo', 'enddo', 'ENDDO']},
    'break': {'ru': ['Прервать', 'прервать', 'ПРЕРВАТЬ'], 'en': ['Break', 'break', 'BREAK']},
    'continue': {'ru': ['Продолжить', 'продолжить', 'ПРОДОЛЖИТЬ'], 'en': ['Continue', 'continue', 'CONTINUE']},

    # Функции и процедуры
    'function': {'ru': ['Функция', 'функция', 'ФУНКЦИЯ'], 'en': ['Function', 'function', 'FUNCTION']},
    'endfunction': {'ru': ['КонецФункции', 'конецфункции', 'КОНЕЦФУНКЦИИ'], 'en': ['EndFunction', 'endfunction', 'ENDFUNCTION']},
    'procedure': {'ru': ['Процедура', 'процедура', 'ПРОЦЕДУРА'], 'en': ['Procedure', 'procedure', 'PROCEDURE']},
    'endprocedure': {'ru': ['КонецПроцедуры', 'конецпроцедуры', 'КОНЕЦПРОЦЕДУРЫ'], 'en': ['EndProcedure', 'endprocedure', 'ENDPROCEDURE']},
    'return': {'ru': ['Возврат', 'возврат', 'ВОЗВРАТ'], 'en': ['Return', 'return', 'RETURN']},

    # Переменные
    'var': {'ru': ['Перем', 'перем', 'ПЕРЕМ'], 'en': ['Var', 'var', 'VAR']},
    'export': {'ru': ['Экспорт', 'экспорт', 'ЭКСПОРТ'], 'en': ['Export', 'export', 'EXPORT']},

    # Объекты
    'new': {'ru': ['Новый', 'новый', 'НОВЫЙ'], 'en': ['New', 'new', 'NEW']},

    # Исключения
    'try': {'ru': ['Попытка', 'попытка', 'ПОПЫТКА'], 'en': ['Try', 'try', 'TRY']},
    'except': {'ru': ['Исключение', 'исключение', 'ИСКЛЮЧЕНИЕ'], 'en': ['Except', 'except', 'EXCEPT']},
    'endtry': {'ru': ['КонецПопытки', 'конецпопытки', 'КОНЕЦПОПЫТКИ'], 'en': ['EndTry', 'endtry', 'ENDTRY']},
    'raise': {'ru': ['ВызватьИсключение', 'вызватьисключение', 'ВЫЗВАТЬИСКЛЮЧЕНИЕ'], 'en': ['Raise', 'raise', 'RAISE']},

    # Логические значения
    'true': {'ru': ['Истина', 'истина', 'ИСТИНА'], 'en': ['True', 'true', 'TRUE']},
    'false': {'ru': ['Ложь', 'ложь', 'ЛОЖЬ'], 'en': ['False', 'false', 'FALSE']},
    'undefined': {'ru': ['Неопределено', 'неопределено', 'НЕОПРЕДЕЛЕНО'], 'en': ['Undefined', 'undefined', 'UNDEFINED']},
    'null': {'ru': ['NULL', 'null', 'Null'], 'en': ['NULL', 'null', 'Null']},

    # Логические операторы
    'and': {'ru': ['И', 'и'], 'en': ['And', 'and', 'AND']},
    'or': {'ru': ['Или', 'или', 'ИЛИ'], 'en': ['Or', 'or', 'OR']},
    'not': {'ru': ['Не', 'не', 'НЕ'], 'en': ['Not', 'not', 'NOT']},
}

# Операторы
OPERATORS = {
    'assignment': '=',
    'plus': '+',
    'minus': '-',
    'multiply': '*',
    'divide': '/',
    'modulo': '%',
    'equal': '=',
    'not_equal': '<>',
    'less': '<',
    'less_equal': '<=',
    'greater': '>',
    'greater_equal': '>=',
}

# Грамматические правила (упрощенная BNF)
GRAMMAR_RULES = {
    'file': 'module_header? module_body',
    'module_header': 'var_declaration*',
    'module_body': 'method_declaration*',

    'method_declaration': 'function_declaration | procedure_declaration',

    'function_declaration': '''
        kw_function identifier "(" parameter_list? ")" export?
            statement*
        kw_endfunction
    ''',

    'procedure_declaration': '''
        kw_procedure identifier "(" parameter_list? ")" export?
            statement*
        kw_endprocedure
    ''',

    'parameter_list': 'parameter ("," parameter)*',
    'parameter': 'identifier ("=" expression)?',

    'var_declaration': 'kw_var identifier ("," identifier)* ";"',

    'statement': '''
        assignment
        | if_statement
        | for_statement
        | while_statement
        | for_each_statement
        | try_statement
        | return_statement
        | break_statement
        | continue_statement
        | expression_statement
    ''',

    'assignment': 'identifier "=" expression ";"',

    'if_statement': '''
        kw_if expression kw_then
            statement*
        (kw_elsif expression kw_then statement*)*
        (kw_else statement*)?
        kw_endif
    ''',

    'for_statement': '''
        kw_for identifier "=" expression kw_to expression kw_do
            statement*
        kw_enddo
    ''',

    'for_each_statement': '''
        kw_for kw_each identifier kw_in expression kw_do
            statement*
        kw_enddo
    ''',

    'while_statement': '''
        kw_while expression kw_do
            statement*
        kw_enddo
    ''',

    'try_statement': '''
        kw_try
            statement*
        kw_except
            statement*
        kw_endtry
    ''',

    'return_statement': 'kw_return expression? ";"',
    'break_statement': 'kw_break ";"',
    'continue_statement': 'kw_continue ";"',
    'expression_statement': 'expression ";"',

    'expression': '''
        logical_or_expression
    ''',

    'logical_or_expression': 'logical_and_expression (kw_or logical_and_expression)*',
    'logical_and_expression': 'equality_expression (kw_and equality_expression)*',
    'equality_expression': 'relational_expression (("=" | "<>") relational_expression)*',
    'relational_expression': 'additive_expression (("<" | "<=" | ">" | ">=") additive_expression)*',
    'additive_expression': 'multiplicative_expression (("+" | "-") multiplicative_expression)*',
    'multiplicative_expression': 'unary_expression (("*" | "/" | "%") unary_expression)*',

    'unary_expression': '''
        kw_not unary_expression
        | "-" unary_expression
        | primary_expression
    ''',

    'primary_expression': '''
        literal
        | identifier
        | function_call
        | new_expression
        | "(" expression ")"
    ''',

    'function_call': 'identifier "(" argument_list? ")"',
    'argument_list': 'expression ("," expression)*',

    'new_expression': 'kw_new identifier "(" argument_list? ")"',

    'literal': '''
        number
        | string
        | kw_true
        | kw_false
        | kw_undefined
        | kw_null
    ''',

    'identifier': r'[a-zA-Zа-яА-Я_][a-zA-Zа-яА-Я0-9_]*',
    'number': r'[0-9]+ ("." [0-9]+)?',
    'string': r'" [^"]* " | "\'" [^\']* "\'"',
}
