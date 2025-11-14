"""
Code analyzers for different programming languages
Версия: 2.1.0

Улучшения:
- Structured logging
- Input validation
- Улучшена обработка ошибок
"""

from typing import Dict, List, Any
import re
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


def analyze_typescript_code(code: str) -> dict:
    """Базовый анализ TypeScript кода с input validation"""
    # Input validation
    if not isinstance(code, str) or not code.strip():
        logger.warning(
            "Invalid code in analyze_typescript_code",
            extra={"code_type": type(code).__name__ if code else None}
        )
        return {
            "suggestions": [],
            "metrics": {
                "complexity": 0,
                "maintainability": 0,
                "securityScore": 0,
                "performanceScore": 0,
                "codeQuality": 0
            },
            "statistics": {
                "totalLines": 0,
                "functions": 0,
                "variables": 0,
                "comments": 0,
                "potentialIssues": 0
            },
            "recommendations": []
        }
    
    # Limit code length (prevent DoS)
    max_code_length = 100000  # 100KB max
    if len(code) > max_code_length:
        logger.warning(
            "Code too long in analyze_typescript_code",
            extra={"code_length": len(code), "max_length": max_code_length}
        )
        code = code[:max_code_length]
    
    try:
        suggestions = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Проверка any типов
            if 'any' in line and ':' in line:
                suggestions.append({
                    "id": f"ts-any-{i}",
                    "type": "warning",
                    "severity": "medium",
                    "message": "Использование типа 'any' снижает типобезопасность",
                    "description": "TypeScript предоставляет строгую типизацию - используйте конкретные типы",
                    "suggestion": "Замените 'any' на конкретный тип или используйте 'unknown'",
                    "position": {"line": i, "column": 1},
                    "category": "best-practice",
                    "autoFixable": False,
                    "confidence": 0.8
                })
            
            # Проверка console.log в production коде
            if 'console.log' in line or 'console.error' in line:
                suggestions.append({
                    "id": f"ts-console-{i}",
                    "type": "hint",
                    "severity": "low",
                    "message": "Использование console.log в production коде",
                    "description": "Логирование должно использовать систему логирования",
                    "suggestion": "Используйте logger вместо console.log",
                    "position": {"line": i, "column": 1},
                    "category": "best-practice",
                    "autoFixable": True,
                    "confidence": 0.7
                })
            
            # Проверка неиспользуемых импортов (базовая)
            if line.strip().startswith('import') and 'from' in line:
                imported = re.search(r'import\s+.*?\s+from', line)
                if imported and '{' not in line:
                    # Простая проверка - в реальности нужен AST парсер
                    pass
        
        total_lines = len(lines)
        functions = len([l for l in lines if 'function' in l or '=>' in l or 'const.*=' in l])
        variables = len([l for l in lines if 'const ' in l or 'let ' in l or 'var ' in l])
        comments = len([l for l in lines if '//' in l or '/*' in l])
        
        critical_issues = len([s for s in suggestions if s["severity"] == "critical"])
        high_issues = len([s for s in suggestions if s["severity"] == "high"])
        
        complexity = min(100, int((total_lines / 100) * 50 + (len(suggestions) / 10) * 50))
        maintainability = max(0, 100 - (critical_issues * 20 + high_issues * 10))
        security_score = 85  # TypeScript более безопасен по умолчанию
        performance_score = 80
        
        code_quality = (maintainability + security_score + performance_score) / 3
        
        recommendations = []
        if maintainability < 70:
            recommendations.append("Код требует улучшения для лучшей поддерживаемости")
        
        return {
        "suggestions": suggestions,
        "metrics": {
            "complexity": complexity,
            "maintainability": maintainability,
            "securityScore": security_score,
            "performanceScore": performance_score,
            "codeQuality": int(code_quality)
        },
        "statistics": {
            "totalLines": total_lines,
            "functions": functions,
            "variables": variables,
            "comments": comments,
            "potentialIssues": len(suggestions)
        },
        "recommendations": recommendations
    }
    except Exception as e:
        logger.error(
            "Error analyzing TypeScript code",
            extra={"error": str(e), "error_type": type(e).__name__}
        )
        return {
            "suggestions": [],
            "metrics": {
                "complexity": 0,
                "maintainability": 0,
                "securityScore": 0,
                "performanceScore": 0,
                "codeQuality": 0
            },
            "statistics": {
                "totalLines": 0,
                "functions": 0,
                "variables": 0,
                "comments": 0,
                "potentialIssues": 0
            },
            "recommendations": ["Ошибка при анализе кода"]
        }


def analyze_python_code(code: str) -> dict:
    """Базовый анализ Python кода с input validation"""
    # Input validation
    if not isinstance(code, str) or not code.strip():
        logger.warning(
            "Invalid code in analyze_python_code",
            extra={"code_type": type(code).__name__ if code else None}
        )
        return {
            "suggestions": [],
            "metrics": {
                "complexity": 0,
                "maintainability": 0,
                "securityScore": 0,
                "performanceScore": 0,
                "codeQuality": 0
            },
            "statistics": {
                "totalLines": 0,
                "functions": 0,
                "variables": 0,
                "comments": 0,
                "potentialIssues": 0
            },
            "recommendations": []
        }
    
    # Limit code length (prevent DoS)
    max_code_length = 100000  # 100KB max
    if len(code) > max_code_length:
        logger.warning(
            "Code too long in analyze_python_code",
            extra={"code_length": len(code), "max_length": max_code_length}
        )
        code = code[:max_code_length]
    
    try:
        suggestions = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Проверка bare except
            if 'except:' in line and 'except Exception' not in line:
                suggestions.append({
                    "id": f"py-except-{i}",
                "type": "error",
                "severity": "high",
                "message": "Использование bare except не рекомендуется",
                "description": "Bare except перехватывает все исключения, включая SystemExit и KeyboardInterrupt",
                "suggestion": "Используйте 'except Exception:' или конкретные типы исключений",
                "position": {"line": i, "column": 1},
                "category": "best-practice",
                "autoFixable": True,
                "confidence": 0.9
            })
        
        # Проверка print в production
        if 'print(' in line:
            suggestions.append({
                "id": f"py-print-{i}",
                "type": "hint",
                "severity": "low",
                "message": "Использование print() вместо логирования",
                "description": "Для production кода используйте logging модуль",
                "suggestion": "Замените print() на logger.info() или logger.debug()",
                "position": {"line": i, "column": 1},
                "category": "best-practice",
                "autoFixable": True,
                "confidence": 0.8
            })
        
        # Проверка eval/exec
        if 'eval(' in line or 'exec(' in line:
            suggestions.append({
                "id": f"py-eval-{i}",
                "type": "error",
                "severity": "critical",
                "message": "Использование eval() или exec() опасно",
                "description": "eval/exec могут выполнить произвольный код",
                "suggestion": "Избегайте eval/exec, используйте безопасные альтернативы",
                "position": {"line": i, "column": 1},
                "category": "security",
                "autoFixable": False,
                "confidence": 1.0
            })
        
        # Проверка хардкода паролей
        if ('password' in line.lower() or 'secret' in line.lower()) and '=' in line:
            if '"' in line or "'" in line:
                suggestions.append({
                    "id": f"py-secret-{i}",
                    "type": "error",
                    "severity": "critical",
                    "message": "Обнаружен хардкод секрета",
                    "description": "Секреты не должны храниться в коде",
                    "suggestion": "Используйте переменные окружения или хранилище секретов",
                    "position": {"line": i, "column": 1},
                    "category": "security",
                    "autoFixable": False,
                    "confidence": 0.9
                })
        
        total_lines = len(lines)
        functions = len([l for l in lines if 'def ' in l])
        variables = len([l for l in lines if '=' in l and '==' not in l])
        comments = len([l for l in lines if '#' in l])
        
        critical_issues = len([s for s in suggestions if s["severity"] == "critical"])
        high_issues = len([s for s in suggestions if s["severity"] == "high"])
        
        complexity = min(100, int((total_lines / 100) * 50 + (len(suggestions) / 10) * 50))
        maintainability = max(0, 100 - (critical_issues * 20 + high_issues * 10))
        security_score = max(0, 100 - critical_issues * 25)
        performance_score = 80
        
        code_quality = (maintainability + security_score + performance_score) / 3
        
        recommendations = []
        if security_score < 70:
            recommendations.append("Рекомендуется усилить проверки безопасности в коде")
        if critical_issues > 0:
            recommendations.append(f"Обнаружено {critical_issues} критических проблем. Требуется немедленное исправление")
        
        return {
        "suggestions": suggestions,
        "metrics": {
            "complexity": complexity,
            "maintainability": maintainability,
            "securityScore": security_score,
            "performanceScore": performance_score,
            "codeQuality": int(code_quality)
        },
        "statistics": {
            "totalLines": total_lines,
            "functions": functions,
            "variables": variables,
            "comments": comments,
            "potentialIssues": len(suggestions)
        },
        "recommendations": recommendations
    }
    except Exception as e:
        logger.error(
            "Error analyzing Python code",
            extra={"error": str(e), "error_type": type(e).__name__}
        )
        return {
            "suggestions": [],
            "metrics": {
                "complexity": 0,
                "maintainability": 0,
                "securityScore": 0,
                "performanceScore": 0,
                "codeQuality": 0
            },
            "statistics": {
                "totalLines": 0,
                "functions": 0,
                "variables": 0,
                "comments": 0,
                "potentialIssues": 0
            },
            "recommendations": ["Ошибка при анализе кода"]
        }


def analyze_javascript_code(code: str) -> dict:
    """Базовый анализ JavaScript кода с input validation"""
    # Input validation
    if not isinstance(code, str) or not code.strip():
        logger.warning(
            "Invalid code in analyze_javascript_code",
            extra={"code_type": type(code).__name__ if code else None}
        )
        return {
            "suggestions": [],
            "metrics": {
                "complexity": 0,
                "maintainability": 0,
                "securityScore": 0,
                "performanceScore": 0,
                "codeQuality": 0
            },
            "statistics": {
                "totalLines": 0,
                "functions": 0,
                "variables": 0,
                "comments": 0,
                "potentialIssues": 0
            },
            "recommendations": []
        }
    
    # Limit code length (prevent DoS)
    max_code_length = 100000  # 100KB max
    if len(code) > max_code_length:
        logger.warning(
            "Code too long in analyze_javascript_code",
            extra={"code_length": len(code), "max_length": max_code_length}
        )
        code = code[:max_code_length]
    
    try:
        suggestions = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Проверка var (устаревший)
            if re.search(r'\bvar\s+', line):
                suggestions.append({
                    "id": f"js-var-{i}",
                    "type": "warning",
                    "severity": "medium",
                    "message": "Использование 'var' устарело",
                    "description": "'var' имеет function scope и может привести к неожиданному поведению",
                    "suggestion": "Используйте 'const' или 'let' вместо 'var'",
                    "position": {"line": i, "column": 1},
                    "category": "best-practice",
                    "autoFixable": True,
                    "confidence": 0.8
                })
            
            # Проверка == вместо ===
            if ' == ' in line and ' === ' not in line:
                suggestions.append({
                    "id": f"js-equals-{i}",
                    "type": "warning",
                    "severity": "medium",
                    "message": "Использование == вместо ===",
                    "description": "== выполняет приведение типов, что может привести к ошибкам",
                    "suggestion": "Используйте === для строгого сравнения",
                    "position": {"line": i, "column": 1},
                    "category": "best-practice",
                    "autoFixable": True,
                    "confidence": 0.9
                })
            
            # Проверка eval
            if 'eval(' in line:
                suggestions.append({
                    "id": f"js-eval-{i}",
                    "type": "error",
                    "severity": "critical",
                    "message": "Использование eval() опасно",
                    "description": "eval может выполнить произвольный код",
                    "suggestion": "Избегайте eval(), используйте безопасные альтернативы",
                    "position": {"line": i, "column": 1},
                    "category": "security",
                    "autoFixable": False,
                    "confidence": 1.0
                })
        
        total_lines = len(lines)
        functions = len([l for l in lines if 'function' in l or '=>' in l or 'const.*=' in l])
        variables = len([l for l in lines if 'const ' in l or 'let ' in l or 'var ' in l])
        comments = len([l for l in lines if '//' in l or '/*' in l])
        
        critical_issues = len([s for s in suggestions if s["severity"] == "critical"])
        high_issues = len([s for s in suggestions if s["severity"] == "high"])
        
        complexity = min(100, int((total_lines / 100) * 50 + (len(suggestions) / 10) * 50))
        maintainability = max(0, 100 - (critical_issues * 20 + high_issues * 10))
        security_score = max(0, 100 - critical_issues * 25)
        performance_score = 75
        
        code_quality = (maintainability + security_score + performance_score) / 3
        
        recommendations = []
        if security_score < 70:
            recommendations.append("Рекомендуется усилить проверки безопасности в коде")
        
        return {
            "suggestions": suggestions,
            "metrics": {
                "complexity": complexity,
                "maintainability": maintainability,
                "securityScore": security_score,
                "performanceScore": performance_score,
                "codeQuality": int(code_quality)
            },
            "statistics": {
                "totalLines": total_lines,
                "functions": functions,
                "variables": variables,
                "comments": comments,
                "potentialIssues": len(suggestions)
            },
            "recommendations": recommendations
        }
    except Exception as e:
        logger.error(
            "Error analyzing JavaScript code",
            extra={"error": str(e), "error_type": type(e).__name__}
        )
        return {
            "suggestions": [],
            "metrics": {
                "complexity": 0,
                "maintainability": 0,
                "securityScore": 0,
                "performanceScore": 0,
                "codeQuality": 0
            },
            "statistics": {
                "totalLines": 0,
                "functions": 0,
                "variables": 0,
                "comments": 0,
                "potentialIssues": 0
            },
            "recommendations": ["Ошибка при анализе кода"]
        }

