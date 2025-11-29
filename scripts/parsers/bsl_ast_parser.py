# [NEXUS IDENTITY] ID: -4725101862841903164 | DATE: 2025-11-19

#!/usr/bin/env python3
"""
BSL AST Parser - интеграция с bsl-language-server
Строит полноценное Abstract Syntax Tree для BSL кода

Зависимости:
- bsl-language-server (Java): https://github.com/1c-syntax/bsl-language-server
- Запустить: docker run -p 8080:8080 ghcr.io/1c-syntax/bsl-language-server

Преимущества AST парсинга:
- Полное понимание структуры кода
- Control flow graph
- Data flow analysis
- Точное извлечение всех конструкций
- Поддержка сложных случаев (вложенные функции, условия)

Версия: 1.0.0
"""

import logging
import os
from typing import Any, Dict, List, Optional

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BSLLanguageServerClient:
    """
    Клиент для bsl-language-server
    
    Запуск сервера:
    docker run -d -p 8080:8080 --name bsl-ls ghcr.io/1c-syntax/bsl-language-server
    
    Или скачать jar:
    https://github.com/1c-syntax/bsl-language-server/releases
    java -jar bsl-language-server.jar --server.port=8080
    """
    
    def __init__(self, server_url: Optional[str] = None, timeout: float = 2.0):
        self.server_url = server_url or os.getenv("BSL_LANGUAGE_SERVER_URL", "http://localhost:8080")
        self.timeout = timeout
        if not self._check_server():
            raise RuntimeError(
                "BSL Language Server недоступен. Запустите его (например, 'make bsl-ls-up') "
                f"или задайте верный BSL_LANGUAGE_SERVER_URL (текущий: {self.server_url})."
            )
    
    def _check_server(self) -> bool:
        """Проверка доступности сервера"""
        try:
            response = requests.get(f"{self.server_url}/actuator/health", timeout=self.timeout)
            if response.status_code == 200:
                logger.info(f"✅ BSL Language Server доступен: {self.server_url}")
                return True
            logger.warning(
                "⚠️ BSL Language Server вернул статус %s по адресу %s",
                response.status_code,
                self.server_url,
            )
            return False
        except requests.exceptions.RequestException as e:
            logger.error("❌ BSL Language Server недоступен (%s): %s", self.server_url, e)
            logger.error(
                "Подсказка: 'make bsl-ls-up' или docker run -p 8080:8080 ghcr.io/1c-syntax/bsl-language-server"
            )
            return False
    
    def parse_to_ast(self, code: str, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Парсит BSL код в AST
        
        Args:
            code: BSL код
            file_path: Путь к файлу (опционально, для лучшей диагностики)
        
        Returns:
            AST дерево в JSON формате
        """
        try:
            # Language Server Protocol: textDocument/didOpen
            response = requests.post(
                f"{self.server_url}/lsp/parse",
                json={
                    "text": code,
                    "uri": file_path or "untitled:module.bsl",
                    "languageId": "bsl",
                },
                timeout=10,
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Ошибка парсинга: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"Ошибка обращения к BSL LS: {e}")
            return {}
    
    def get_diagnostics(self, code: str) -> List[Dict[str, Any]]:
        """
        Получение диагностики (ошибки, предупреждения)
        
        Returns:
            Список диагностических сообщений
        """
        try:
            response = requests.post(
                f"{self.server_url}/lsp/diagnostics",
                json={"text": code},
                timeout=10,
            )
            
            if response.status_code == 200:
                return response.json().get('diagnostics', [])
            return []
            
        except Exception as e:
            logger.error(f"Ошибка получения диагностики: {e}")
            return []


class BSLASTParser:
    """
    Advanced BSL Parser с использованием AST
    
    Строит полноценное AST дерево и извлекает:
    - Функции/процедуры с полным контекстом
    - Control flow graph
    - Data flow analysis
    - Variable scopes
    - Function calls graph
    - Cyclomatic complexity
    """
    
    def __init__(self, use_language_server: bool = True):
        self.use_language_server = use_language_server
        self.fallback_parser = None
        if use_language_server:
            try:
                self.lsp_client = BSLLanguageServerClient()
                logger.info("✅ AST парсинг через bsl-language-server активирован (%s)", self.lsp_client.server_url)
            except Exception as exc:
                logger.warning("⚠️ bsl-language-server недоступен: %s", exc)
                logger.warning("Используется fallback regex parser")
                self.use_language_server = False
                self._ensure_fallback_parser()
        else:
            self._ensure_fallback_parser()
    
    def parse(self, code: str, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Парсинг BSL кода с построением AST
        
        Returns:
            Расширенный результат парсинга с AST
        """
        if self.use_language_server:
            return self._parse_with_ast(code, file_path)
        else:
            return self._parse_fallback(code)
    
    def _parse_with_ast(self, code: str, file_path: Optional[str]) -> Dict[str, Any]:
        """Парсинг с использованием AST от Language Server"""
        
        # Получаем AST
        ast = self.lsp_client.parse_to_ast(code, file_path)
        
        if not ast:
            # Fallback на regex
            logger.warning("AST не получен, используем fallback")
            return self._parse_fallback(code)
        
        # Извлекаем структурированные данные из AST
        result = {
            'ast': ast,  # Полное AST дерево
            'functions': self._extract_functions_from_ast(ast),
            'procedures': self._extract_procedures_from_ast(ast),
            'regions': self._extract_regions_from_ast(ast),
            'variables': self._extract_variables_from_ast(ast),
            'api_usage': self._extract_api_usage_from_ast(ast),
            'control_flow': self._build_control_flow_graph(ast),
            'data_flow': self._analyze_data_flow(ast),
            'complexity': self._calculate_complexity(ast),
            'diagnostics': self.lsp_client.get_diagnostics(code)
        }
        
        # Статистика
        result['statistics'] = {
            'total_functions': len(result['functions']),
            'total_procedures': len(result['procedures']),
            'total_variables': len(result['variables']),
            'cyclomatic_complexity': result['complexity']['cyclomatic'],
            'lines_of_code': len(code.split('\n')),
            'has_errors': any(d['severity'] == 'error' for d in result['diagnostics'])
        }
        
        return result
    
    def _parse_fallback(self, code: str) -> Dict[str, Any]:
        """Fallback парсинг без AST"""
        self._ensure_fallback_parser()
        result = self.fallback_parser.parse(code)
        result['ast'] = None
        result['control_flow'] = None
        result['data_flow'] = None
        result['complexity'] = {'cyclomatic': 0}
        return result

    def _ensure_fallback_parser(self) -> None:
        """Ленивая инициализация fallback парсера."""
        if self.fallback_parser is None:
            from scripts.parsers.improve_bsl_parser import ImprovedBSLParser

            self.fallback_parser = ImprovedBSLParser()
    
    def _extract_functions_from_ast(self, ast: Dict) -> List[Dict[str, Any]]:
        """Извлечение функций из AST"""
        functions = []
        
        # Обходим AST дерево
        for node in self._traverse_ast(ast):
            if node.get('type') == 'FunctionDeclaration':
                func = {
                    'name': node.get('name', 'Unknown'),
                    'type': 'Функция',
                    'params': self._extract_params_from_node(node),
                    'return_type': node.get('returnType'),
                    'exported': node.get('isExport', False),
                    'async': node.get('isAsync', False),
                    'body': node.get('body'),
                    'comments': node.get('leadingComments', []),
                    'line_start': node.get('loc', {}).get('start', {}).get('line'),
                    'line_end': node.get('loc', {}).get('end', {}).get('line'),
                    'complexity': self._calculate_node_complexity(node)
                }
                functions.append(func)
        
        return functions
    
    def _extract_procedures_from_ast(self, ast: Dict) -> List[Dict[str, Any]]:
        """Извлечение процедур из AST"""
        procedures = []
        
        for node in self._traverse_ast(ast):
            if node.get('type') == 'ProcedureDeclaration':
                proc = {
                    'name': node.get('name', 'Unknown'),
                    'type': 'Процедура',
                    'params': self._extract_params_from_node(node),
                    'exported': node.get('isExport', False),
                    'body': node.get('body'),
                    'comments': node.get('leadingComments', []),
                    'line_start': node.get('loc', {}).get('start', {}).get('line'),
                    'line_end': node.get('loc', {}).get('end', {}).get('line'),
                    'complexity': self._calculate_node_complexity(node)
                }
                procedures.append(proc)
        
        return procedures
    
    def _extract_regions_from_ast(self, ast: Dict) -> List[Dict[str, Any]]:
        """Извлечение областей из AST"""
        regions = []
        
        for node in self._traverse_ast(ast):
            if node.get('type') == 'RegionDeclaration':
                region = {
                    'name': node.get('name', ''),
                    'start_line': node.get('loc', {}).get('start', {}).get('line'),
                    'end_line': node.get('loc', {}).get('end', {}).get('line')
                }
                regions.append(region)
        
        return regions
    
    def _extract_variables_from_ast(self, ast: Dict) -> List[Dict[str, Any]]:
        """Извлечение переменных из AST"""
        variables = []
        
        for node in self._traverse_ast(ast):
            if node.get('type') == 'VariableDeclaration':
                for var in node.get('declarations', []):
                    variable = {
                        'name': var.get('name'),
                        'type': var.get('varType'),
                        'export': var.get('isExport', False),
                        'scope': node.get('scope', 'module'),
                        'line': node.get('loc', {}).get('start', {}).get('line')
                    }
                    variables.append(variable)
        
        return variables
    
    def _extract_api_usage_from_ast(self, ast: Dict) -> List[Dict[str, Any]]:
        """Извлечение использования 1С API из AST"""
        api_usage = []
        
        # Известные API объекты 1С
        api_objects = {
            'Запрос', 'ТаблицаЗначений', 'Структура', 
            'Справочники', 'Документы', 'РегистрыСведений'
        }
        
        for node in self._traverse_ast(ast):
            if node.get('type') == 'CallExpression':
                callee = node.get('callee', {})
                
                # Проверяем обращение к API
                if callee.get('object') in api_objects:
                    usage = {
                        'api_object': callee.get('object'),
                        'method': callee.get('property'),
                        'arguments': len(node.get('arguments', [])),
                        'line': node.get('loc', {}).get('start', {}).get('line')
                    }
                    api_usage.append(usage)
        
        return api_usage
    
    def _build_control_flow_graph(self, ast: Dict) -> Dict[str, Any]:
        """Построение control flow graph"""
        cfg = {
            'nodes': [],
            'edges': [],
            'entry': None,
            'exits': []
        }
        
        # Упрощенная версия - подсчитываем ветвления
        for node in self._traverse_ast(ast):
            if node.get('type') in ['IfStatement', 'WhileStatement', 'ForStatement']:
                cfg['nodes'].append({
                    'type': node.get('type'),
                    'line': node.get('loc', {}).get('start', {}).get('line')
                })
        
        return cfg
    
    def _analyze_data_flow(self, ast: Dict) -> Dict[str, Any]:
        """Анализ потоков данных"""
        data_flow = {
            'assignments': [],
            'reads': [],
            'dependencies': []
        }
        
        for node in self._traverse_ast(ast):
            if node.get('type') == 'AssignmentExpression':
                data_flow['assignments'].append({
                    'variable': node.get('left', {}).get('name'),
                    'line': node.get('loc', {}).get('start', {}).get('line')
                })
        
        return data_flow
    
    def _calculate_complexity(self, ast: Dict) -> Dict[str, int]:
        """Вычисление метрик сложности"""
        complexity = {
            'cyclomatic': 1,  # Начальная сложность
            'cognitive': 0,
            'nesting_depth': 0
        }
        
        # Цикломатическая сложность
        for node in self._traverse_ast(ast):
            if node.get('type') in [
                'IfStatement', 'WhileStatement', 'ForStatement',
                'CaseStatement', 'TernaryExpression'
            ]:
                complexity['cyclomatic'] += 1
        
        return complexity
    
    def _calculate_node_complexity(self, node: Dict) -> int:
        """Вычисление сложности узла"""
        complexity = 1
        
        for child in self._traverse_ast(node):
            if child.get('type') in ['IfStatement', 'WhileStatement', 'ForStatement']:
                complexity += 1
        
        return complexity
    
    def _extract_params_from_node(self, node: Dict) -> List[Dict[str, Any]]:
        """Извлечение параметров из AST узла"""
        params = []
        
        for param in node.get('params', []):
            params.append({
                'name': param.get('name'),
                'type': param.get('type'),
                'default_value': param.get('default'),
                'by_value': param.get('byValue', False),
                'required': param.get('default') is None
            })
        
        return params
    
    def _traverse_ast(self, node: Any) -> List[Dict]:
        """Рекурсивный обход AST дерева"""
        nodes = []
        
        if isinstance(node, dict):
            nodes.append(node)
            
            for key, value in node.items():
                if isinstance(value, (dict, list)):
                    nodes.extend(self._traverse_ast(value))
        
        elif isinstance(node, list):
            for item in node:
                if isinstance(item, (dict, list)):
                    nodes.extend(self._traverse_ast(item))
        
        return nodes


def example_usage():
    """Пример использования BSL AST Parser"""
    
    # Пример BSL кода
    test_code = """
#Область ПрограммныйИнтерфейс

// Функция для расчета НДС
//
// Параметры:
//  Сумма - Число - сумма без НДС
//  Ставка - Число - ставка НДС (по умолчанию 20)
//
// Возвращаемое значение:
//  Число - сумма НДС
//
Функция РассчитатьНДС(Сумма, Ставка = 20) Экспорт
    
    Если Ставка <= 0 Тогда
        ВызватьИсключение "Ставка должна быть больше 0";
    КонецЕсли;
    
    СуммаНДС = Сумма * Ставка / 100;
    
    Возврат СуммаНДС;
    
КонецФункции

// Процедура для записи в лог
Процедура ЗаписатьВЖурнал(Событие, Комментарий) Экспорт
    
    ЗаписьЖурналаРегистрации(
        Событие,
        УровеньЖурналаРегистрации.Информация,
        ,
        ,
        Комментарий
    );
    
КонецПроцедуры

#КонецОбласти
    """
    
    print("=" * 70)
    print("ПРИМЕР: BSL AST Parser")
    print("=" * 70)
    
    # Создаем парсер
    parser = BSLASTParser(use_language_server=True)
    
    # Парсим код
    result = parser.parse(test_code)
    
    # Выводим результаты
    print("\n📊 Статистика:")
    for key, value in result['statistics'].items():
        print(f"  {key}: {value}")
    
    print("\n🔧 Функции:")
    for func in result['functions']:
        print(f"  - {func['name']} ({len(func['params'])} параметров)")
        print(f"    Экспорт: {func['exported']}")
        print(f"    Сложность: {func['complexity']}")
        print(f"    Строки: {func['line_start']}-{func['line_end']}")
    
    print("\n⚙️ Процедуры:")
    for proc in result['procedures']:
        print(f"  - {proc['name']} ({len(proc['params'])} параметров)")
        print(f"    Экспорт: {proc['exported']}")
        print(f"    Сложность: {proc['complexity']}")
    
    print("\n🔍 Метрики сложности:")
    print(f"  Cyclomatic Complexity: {result['complexity']['cyclomatic']}")
    
    if result['ast']:
        print("\n✅ AST построен успешно!")
        print(f"  Узлов в AST: {len(list(parser._traverse_ast(result['ast'])))}")
    else:
        print("\n⚠️ AST не построен (используется fallback)")
    
    # Диагностика
    if result.get('diagnostics'):
        print("\n🔴 Диагностика:")
        for diag in result['diagnostics']:
            print(f"  [{diag.get('severity')}] {diag.get('message')}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    example_usage()





