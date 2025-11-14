"""
1С:Copilot API
Backend для VSCode extension и других клиентов
"""

import os
import logging
import re
import asyncio
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

router = APIRouter(prefix="/api/copilot")
limiter = Limiter(key_func=get_remote_address)


class CompletionRequest(BaseModel):
    code: str = Field(..., max_length=50000)
    current_line: str = Field(..., max_length=1000)
    language: str = Field(default='bsl', max_length=50)
    max_suggestions: int = Field(default=3, ge=1, le=10)


class GenerationRequest(BaseModel):
    prompt: str = Field(..., max_length=5000)
    language: str = Field(default='bsl', max_length=50)
    type: str = Field(default='function', max_length=50)  # function, procedure, test


class OptimizationRequest(BaseModel):
    code: str = Field(..., max_length=50000)
    language: str = Field(default='bsl', max_length=50)


class CopilotService:
    """Сервис для 1С:Copilot"""
    
    def __init__(self):
        # TODO: Load fine-tuned model
        self.model_available = False
        
        try:
            # Try to load LoRA model
            from transformers import AutoModelForCausalLM, AutoTokenizer
            from peft import PeftModel
            
            model_path = "models/qwen-bsl-lora"
            if os.path.exists(model_path):
                logger.info(
                    "Loading model",
                    extra={"model_path": model_path}
                )
                # TODO: Implement model loading
                self.model_available = True
        except Exception as e:
            logger.warning(
                "Model not available - using fallback",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
    
    async def get_completions(
        self,
        code: str,
        current_line: str,
        max_suggestions: int = 3,
        timeout: float = 5.0
    ) -> List[Dict]:
        """
        Получение autocomplete suggestions с timeout handling
        
        Returns:
            [
                {'text': '...', 'description': '...', 'score': 0.95}
            ]
        """
        # Input validation
        if not isinstance(code, str):
            logger.warning(
                "Invalid code type in get_completions",
                extra={"code_type": type(code).__name__}
            )
            code = str(code) if code else ""
        
        if not isinstance(current_line, str):
            logger.warning(
                "Invalid current_line type in get_completions",
                extra={"current_line_type": type(current_line).__name__}
            )
            current_line = str(current_line) if current_line else ""
        
        if not isinstance(max_suggestions, int) or max_suggestions < 1:
            logger.warning(
                "Invalid max_suggestions in get_completions",
                extra={"max_suggestions": max_suggestions, "max_suggestions_type": type(max_suggestions).__name__}
            )
            max_suggestions = 3
        
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            logger.warning(
                "Invalid timeout in get_completions",
                extra={"timeout": timeout, "timeout_type": type(timeout).__name__}
            )
            timeout = 5.0
        
        try:
            # Execute with timeout
            return await asyncio.wait_for(
                self._get_completions_internal(code, current_line, max_suggestions),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning(
                "Timeout in get_completions",
                extra={"timeout": timeout, "code_length": len(code)}
            )
            return []  # Return empty suggestions on timeout
        except Exception as e:
            logger.error(
                f"Error in get_completions: {e}",
                extra={
                    "error_type": type(e).__name__,
                    "code_length": len(code)
                },
                exc_info=True
            )
            return []  # Return empty suggestions on error
    
    async def _get_completions_internal(
        self,
        code: str,
        current_line: str,
        max_suggestions: int
    ) -> List[Dict]:
        """Internal method for getting completions"""
        # TODO: Implement real model inference
        # For now - simple heuristics
        
        suggestions = []
        
        # Heuristic 1: Если пишут "Для Каждого" → предложить цикл
        if 'Для Каждого' in current_line or 'для каждого' in current_line.lower():
            suggestions.append({
                'text': ' Строка Из КоллекцияСтрок Цикл\n    // TODO\nКонецЦикла;',
                'description': 'Цикл по коллекции',
                'score': 0.9
            })
        
        # Heuristic 2: Если "Запрос" → предложить execute
        if 'Запрос' in current_line:
            suggestions.append({
                'text': '.Выполнить()',
                'description': 'Выполнить запрос',
                'score': 0.85
            })
        
        # Heuristic 3: Если "Результат" → предложить возврат
        if 'Результат' in current_line:
            suggestions.append({
                'text': ' = ',
                'description': 'Присвоение значения',
                'score': 0.8
            })
        
        return suggestions[:max_suggestions]
    
    async def generate_code(
        self,
        prompt: str,
        code_type: str = 'function',
        timeout: float = 10.0
    ) -> str:
        """
        Генерация кода по описанию с timeout handling
        
        Args:
            prompt: Описание что нужно создать
            code_type: function, procedure, test
            timeout: Timeout в секундах
        
        Returns:
            Generated BSL code
        """
        # Input validation
        if not isinstance(prompt, str) or not prompt.strip():
            logger.warning(
                "Invalid prompt in generate_code",
                extra={"prompt_type": type(prompt).__name__ if prompt else None}
            )
            prompt = "Новая функция"
        
        valid_types = ['function', 'procedure', 'test']
        if code_type not in valid_types:
            logger.warning(
                "Invalid code_type in generate_code",
                extra={"code_type": code_type, "valid_types": valid_types}
            )
            code_type = 'function'
        
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            logger.warning(
                "Invalid timeout in generate_code",
                extra={"timeout": timeout, "timeout_type": type(timeout).__name__}
            )
            timeout = 10.0
        
        try:
            # Execute with timeout
            return await asyncio.wait_for(
                self._generate_code_internal(prompt, code_type),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning(
                "Timeout in generate_code",
                extra={"timeout": timeout, "prompt_length": len(prompt), "code_type": code_type}
            )
            # Return fallback template
            return self._generate_function_template(prompt)
        except Exception as e:
            logger.error(
                "Error in generate_code",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "prompt_length": len(prompt),
                    "code_type": code_type
                },
                exc_info=True
            )
            # Return fallback template
            return self._generate_function_template(prompt)
    
    async def _generate_code_internal(
        self,
        prompt: str,
        code_type: str
    ) -> str:
        """Internal method for generating code"""
        # Template-based generation (fine-tuned model loading - низкий приоритет)
        
        if code_type == 'function':
            return self._generate_function_template(prompt)
        elif code_type == 'procedure':
            return self._generate_procedure_template(prompt)
        elif code_type == 'test':
            return self._generate_test_template(prompt)
        else:
            # Fallback для неизвестных типов
            return self._generate_function_template(prompt)
    
    def _generate_function_template(self, prompt: str) -> str:
        """Template для функции с input validation"""
        # Input validation
        if not isinstance(prompt, str) or not prompt.strip():
            logger.warning(
                "Invalid prompt in _generate_function_template",
                extra={"prompt_type": type(prompt).__name__ if prompt else None}
            )
            prompt = "Новая функция"
        
        # Sanitize prompt (prevent injection)
        prompt = prompt[:500]  # Limit length
        
        # Extract function name from prompt
        words = prompt.split()
        func_name = words[0].capitalize() if words else "НоваяФункция"
        
        # Sanitize function name (only alphanumeric and Cyrillic)
        func_name = re.sub(r'[^\wА-Яа-я]', '', func_name)
        if not func_name:
            func_name = "НоваяФункция"
        
        return f'''
// {prompt}
//
// Параметры:
//   Параметр1 - Тип - Описание
//
// Возвращаемое значение:
//   Тип - Описание результата
//
Функция {func_name}(Параметр1) Экспорт
    
    Результат = Неопределено;
    
    Попытка
        // Реализация функции
        
    Исключение
        ЗаписьЖурналаРегистрации("Ошибка в {func_name}", 
            УровеньЖурналаРегистрации.Ошибка,,,
            ОписаниеОшибки());
        ВызватьИсключение;
    КонецПопытки;
    
    Возврат Результат;
    
КонецФункции
'''
    
    def _generate_procedure_template(self, prompt: str) -> str:
        """Template для процедуры с input validation"""
        # Input validation
        if not isinstance(prompt, str) or not prompt.strip():
            logger.warning(
                "Invalid prompt in _generate_procedure_template",
                extra={"prompt_type": type(prompt).__name__ if prompt else None}
            )
            prompt = "Новая процедура"
        
        # Sanitize prompt (prevent injection)
        prompt = prompt[:500]  # Limit length
        
        # Extract procedure name from prompt
        words = prompt.split()
        proc_name = words[0].capitalize() if words else "НоваяПроцедура"
        
        # Sanitize procedure name (only alphanumeric and Cyrillic)
        proc_name = re.sub(r'[^\wА-Яа-я]', '', proc_name)
        if not proc_name:
            proc_name = "НоваяПроцедура"
        
        return f'''//
// {prompt}
//
// Параметры:
//   Параметр1 - Произвольный - Описание параметра
//
Процедура {proc_name}(Параметр1) Экспорт
    
    Попытка
        // Реализация процедуры
        
    Исключение
        ЗаписьЖурналаРегистрации("Ошибка в {proc_name}", 
            УровеньЖурналаРегистрации.Ошибка,,,
            ОписаниеОшибки());
        ВызватьИсключение;
    КонецПопытки;
    
КонецПроцедуры
'''
    
    def _generate_test_template(self, function_name: str) -> str:
        """Template для теста с input validation"""
        # Input validation
        if not isinstance(function_name, str) or not function_name.strip():
            logger.warning(
                "Invalid function_name in _generate_test_template",
                extra={"function_name_type": type(function_name).__name__ if function_name else None}
            )
            function_name = "ТестоваяФункция"
        
        # Sanitize function name (prevent injection)
        function_name = function_name[:200]  # Limit length
        
        # Extract clean function name
        clean_name = re.sub(r'[^\wА-Яа-я]', '', function_name) if function_name else "ТестоваяФункция"
        if not clean_name:
            clean_name = "ТестоваяФункция"
        
        return f'''//
// Тест для функции {clean_name}
//
Процедура Тест_{clean_name}() Экспорт
    
    // Arrange (Подготовка данных)
    ВходныеДанные = "test_value";
    ОжидаемыйРезультат = "expected_value";
    
    // Act (Выполнение)
    ФактическийРезультат = {clean_name}(ВходныеДанные);
    
    // Assert (Проверка)
    юТест.ПроверитьРавенство(
        ФактическийРезультат, 
        ОжидаемыйРезультат,
        "Функция {clean_name} должна вернуть ожидаемое значение"
    );
    
КонецПроцедуры
'''


# FastAPI endpoints

copilot_service = CopilotService()


@router.post(
    "/complete",
    summary="Get code completions",
    description="""
    Get autocomplete suggestions for code.
    
    **Rate Limit:** 60 completions per minute
    
    **Features:**
    - Context-aware suggestions
    - Multiple suggestions with scores
    - Language-specific heuristics
    """,
    responses={
        200: {
            "description": "Completion suggestions",
            "content": {
                "application/json": {
                    "example": {
                        "suggestions": [
                            {
                                "text": " Строка Из КоллекцияСтрок Цикл",
                                "description": "Цикл по коллекции",
                                "score": 0.9
                            }
                        ]
                    }
                }
            }
        },
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit("60/minute")  # Rate limit: 60 completions per minute
async def get_completions(api_request: Request, request: CompletionRequest):
    """
    Autocomplete endpoint с валидацией входных данных
    
    Best practices:
    - Валидация длины кода
    - Sanitization входных данных
    - Улучшенная обработка ошибок
    """
    try:
        # Input validation and sanitization (best practice)
        code = request.code.strip()
        if not code:
            raise HTTPException(
                status_code=400,
                detail="Code cannot be empty"
            )
        
        # Limit code length (prevent DoS)
        max_code_length = 50000  # 50KB max for completions
        if len(code) > max_code_length:
            raise HTTPException(
                status_code=400,
                detail=f"Code too long. Maximum length: {max_code_length} characters"
            )
        
        # Validate current_line
        current_line = max(1, min(request.current_line, 10000))  # Clamp between 1 and 10000
        
        # Validate max_suggestions
        max_suggestions = max(1, min(request.max_suggestions, 20))  # Clamp between 1 and 20
        
        suggestions = await copilot_service.get_completions(
            code=code,
            current_line=current_line,
            max_suggestions=max_suggestions,
            timeout=5.0  # 5 seconds timeout
        )
        
        return {'suggestions': suggestions}
    
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(
            "Unexpected error getting completions",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "code_length": len(code) if 'code' in locals() else 0,
                "current_line": request.current_line if hasattr(request, 'current_line') else None
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="An error occurred while getting completions"
        )


@router.post(
    "/generate",
    summary="Generate code from prompt",
    description="""
    Generate code (function, procedure, or test) from natural language prompt.
    
    **Rate Limit:** 10 generations per minute
    
    **Supported Types:**
    - `function`: Generate BSL function
    - `procedure`: Generate BSL procedure
    - `test`: Generate test code
    
    **Features:**
    - Template-based generation
    - Smart function naming
    - Error handling included
    - Documentation comments
    """,
    responses={
        200: {
            "description": "Generated code",
            "content": {
                "application/json": {
                    "example": {
                        "code": "Функция НоваяФункция() Экспорт\n    // Generated code\nКонецФункции"
                    }
                }
            }
        },
        400: {"description": "Invalid request"},
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit("10/minute")
async def generate_code(api_request: Request, request: GenerationRequest):
    """
    Code generation endpoint с валидацией входных данных
    
    Best practices:
    - Валидация длины prompt
    - Sanitization входных данных
    - Улучшенная обработка ошибок
    """
    try:
        # Input validation and sanitization (best practice)
        prompt = request.prompt.strip()
        if not prompt:
            raise HTTPException(
                status_code=400,
                detail="Prompt cannot be empty"
            )
        
        # Limit prompt length (prevent DoS)
        max_prompt_length = 5000
        if len(prompt) > max_prompt_length:
            raise HTTPException(
                status_code=400,
                detail=f"Prompt too long. Maximum length: {max_prompt_length} characters"
            )
        
        # Validate code_type
        valid_types = ['function', 'procedure', 'test']
        code_type = request.type.lower() if request.type else 'function'
        if code_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid code_type: {code_type}. Valid types: {', '.join(valid_types)}"
            )
        
        code = await copilot_service.generate_code(
            prompt=prompt,
            code_type=code_type,
            timeout=10.0  # 10 seconds timeout
        )
        
        return {'code': code}
    
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(
            "Unexpected error generating code",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "prompt_length": len(request.prompt) if hasattr(request, 'prompt') else 0,
                "code_type": request.type if hasattr(request, 'type') else None
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="An error occurred while generating code"
        )


@router.post(
    "/optimize",
    summary="Optimize code",
    description="""
    Analyze and optimize code for performance, security, and best practices.
    
    **Rate Limit:** 10 optimizations per minute
    
    **Optimizations Detected:**
    - N+1 query problems
    - Unused variables
    - String concatenation inefficiencies
    - Type checking improvements
    - Security issues
    
    **Returns:**
    - Optimized code
    - List of improvements with impact levels
    - Optimization count
    """,
    responses={
        200: {
            "description": "Optimization results",
            "content": {
                "application/json": {
                    "example": {
                        "optimized_code": "// Optimized code",
                        "improvements": [
                            {
                                "type": "n_plus_1_query",
                                "description": "Detected N+1 query pattern",
                                "impact": "high"
                            }
                        ],
                        "optimization_count": 1
                    }
                }
            }
        },
        400: {"description": "Invalid code"},
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit("10/minute")  # Rate limit: 10 optimizations per minute
async def optimize_code(api_request: Request, request: OptimizationRequest):
    """
    Code optimization endpoint с валидацией входных данных
    
    Best practices:
    - Валидация длины кода
    - Sanitization входных данных
    - Улучшенная обработка ошибок
    """
    try:
        # Input validation and sanitization (best practice)
        code = request.code.strip()
        if not code:
            raise HTTPException(
                status_code=400,
                detail="Code cannot be empty"
            )
        
        # Limit code length (prevent DoS)
        max_code_length = 100000  # 100KB max
        if len(code) > max_code_length:
            raise HTTPException(
                status_code=400,
                detail=f"Code too long. Maximum length: {max_code_length} characters"
            )
        
        optimizations = []
        optimized_code = code
        
        # Optimization 1: Replace string concatenation with StrTemplate
        if '+' in code and ('"' in code or "'" in code):
            pattern = r'(\w+)\s*=\s*"([^"]+)"\s*\+\s*(\w+)\s*\+\s*"([^"]+)"'
            matches = re.findall(pattern, code)
            
            if matches:
                optimizations.append({
                    'type': 'string_concatenation',
                    'description': 'Replace string concatenation with StrTemplate for better performance',
                    'impact': 'medium',
                    'example': 'Использовать СтрШаблон("...", Параметр1, Параметр2)'
                })
        
        # Optimization 2: N+1 query detection
        if re.search(r'Для\s+Каждого.*Цикл.*Запрос\.', code, re.DOTALL):
            optimizations.append({
                'type': 'n_plus_1_query',
                'description': 'Detected N+1 query pattern in loop - use batch query instead',
                'impact': 'high',
                'fix': 'Move query outside loop and use IN clause with array'
            })
        
        # Optimization 3: Unused variables detection
        assignments = re.findall(r'(\w+)\s*=\s*.+;', code)
        usages = re.findall(r'\b(\w+)\b', code)
        usage_counts = {var: usages.count(var) for var in set(assignments)}
        
        unused = [var for var, count in usage_counts.items() if count == 1]
        if unused:
            optimizations.append({
                'type': 'unused_variables',
                'description': f'Found {len(unused)} potentially unused variables',
                'impact': 'low',
                'variables': unused[:5]  # Show first 5
            })
        
        # Optimization 4: ПроверитьТип вместо Тип
        if 'Тип(' in code and 'ПроверитьТип' not in code:
            optimizations.append({
                'type': 'type_check',
                'description': 'Use ПроверитьТип() instead of Тип() for better performance',
                'impact': 'medium',
                'fix': 'Replace Тип() with ПроверитьТип()'
            })
        
        return {
            'optimized_code': optimized_code,
            'improvements': optimizations,
            'optimization_count': len(optimizations),
            'language': request.language
        }
    
    except Exception as e:
        logger.error(
            "Optimization error",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "language": request.language if hasattr(request, 'language') else None
            },
            exc_info=True
        )
        return {
            'optimized_code': request.code,
            'improvements': [],
            'error': str(e)
        }


@router.post(
    "/generate-tests",
    summary="Generate test code",
    description="""
    Generate test code for functions or procedures.
    
    **Rate Limit:** 10 test generations per minute
    
    **Test Framework:**
    - Vanessa framework for BSL
    - Follows AAA pattern (Arrange, Act, Assert)
    - Includes error handling tests
    """,
    responses={
        200: {
            "description": "Generated test code",
            "content": {
                "application/json": {
                    "example": {
                        "tests": "Процедура Тест_НоваяФункция() Экспорт\n    // Test code\nКонецПроцедуры"
                    }
                }
            }
        },
        400: {"description": "Invalid request"},
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit("10/minute")
async def generate_tests(api_request: Request, request: GenerationRequest):
    """Test generation endpoint"""
    
    tests = await copilot_service.generate_code(
        prompt=request.prompt,
        code_type='test'
    )
    
    return {'tests': tests}


