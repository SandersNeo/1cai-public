"""
Enhanced Developer AI Agent with Real LLM Integration

Extends DeveloperAISecure with:
- Real BSL code generation using Adaptive LLM Selector
- Self-Healing integration
- Code DNA integration
- Predictive code generation
"""

from typing import Any, Dict, List, Optional

from src.ai.agents.base_agent import AgentCapability, BaseAgent
from src.ai.agents.developer_agent_secure import DeveloperAISecure
from src.ai.llm import TaskType


class DeveloperAgentEnhanced(BaseAgent):
    """
    Enhanced Developer Agent with real LLM integration.

    Inherits from BaseAgent for unified interface and metrics.
    Uses DeveloperAISecure for security checks.
    """

    def __init__(self):
        super().__init__(
            agent_name="developer_agent_enhanced",
            capabilities=[
                AgentCapability.CODE_GENERATION,
                AgentCapability.CODE_REVIEW,
                AgentCapability.PERFORMANCE_OPTIMIZATION
            ]
        )

        # Security layer
        self.secure_agent = DeveloperAISecure()

        # BSL-specific patterns
        self.bsl_patterns = {
            "function": "Функция {name}({params}) Экспорт\n{body}\nКонецФункции",
            "procedure": "Процедура {name}({params}) Экспорт\n{body}\nКонецПроцедуры",
            "module": "// Модуль: {name}\n// Описание: {description}\n\n{content}",
        }
        # Revolutionary Components (stubs for future integration)
        # Will be initialized when Code DNA is available
        self.code_dna = None
        # Will be initialized when Predictive Gen is available
        self.predictive_gen = None

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process code generation request.

        Args:
            input_data: {
                "action": "generate_code" | "review_code" | "fix_code",
                "prompt": str,
                "language": "bsl" | "python" | etc,
                "context": optional dict
            }
        """
        action = input_data.get("action", "generate_code")

        if action == "generate_code":
            return await self.generate_bsl_code(
                prompt=input_data.get("prompt", ""),
                context=input_data.get("context", {})
            )
        elif action == "review_code":
            return await self.review_code(
                code=input_data.get("code", ""),
                context=input_data.get("context", {})
            )
        elif action == "fix_code":
            return await self.fix_code(
                code=input_data.get("code", ""),
                issues=input_data.get("issues", []),
                context=input_data.get("context", {})
            )
        else:
            return {"error": f"Unknown action: {action}"}

    async def generate_bsl_code(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate BSL code using LLM.

        Args:
            prompt: Code generation prompt
            context: Additional context

        Returns:
            Generated code with safety analysis
        """
        context = context or {}
        context["language"] = "bsl"
        context["framework"] = "1C:Enterprise 8.3"

        # Build BSL-specific prompt
        bsl_prompt = self._build_bsl_prompt(prompt, context)

        # Generate with LLM
        if self.llm_selector:
            try:
                llm_response = await self.llm_selector.generate(
                    task_type=TaskType.CODE_GENERATION,
                    prompt=bsl_prompt,
                    context=context
                )

                generated_code = llm_response["response"]
            except Exception as e:
                self.logger.error("LLM generation failed: %s", e)
                # Fallback to placeholder
                generated_code = self._generate_placeholder_bsl(prompt)
        else:
            # No LLM available
            generated_code = self._generate_placeholder_bsl(prompt)

        # Security analysis
        safety = self.secure_agent._analyze_code_safety(generated_code)

        # Self-Healing if enabled and needed
        if self.use_self_healing and safety["score"] < 0.8:
            generated_code = await self._apply_self_healing(
                generated_code,
                safety["concerns"]
            )
            # Re-analyze after healing
            safety = self.secure_agent._analyze_code_safety(generated_code)

        # Audit log
        self._log_audit(
            action="code_generated",
            details={
                "language": "bsl",
                "safety_score": safety["score"],
                "lines": len(generated_code.split("\n"))
            }
        )

        return {
            "code": generated_code,
            "safety": safety,
            "requires_approval": safety["score"] < 0.95,
            "language": "bsl"
        }

    async def review_code(
        self,
        code: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Review code using LLM.

        Args:
            code: Code to review
            context: Additional context

        Returns:
            Review results
        """
        context = context or {}

        if self.llm_selector:
            try:
                review = await self.llm_selector.generate(
                    task_type=TaskType.CODE_REVIEW,
                    prompt=f"""
                    Review this BSL code for 1C:Enterprise:

                    {code}

                    Check for:
                    - Clean Code principles
                    - 1C best practices
                    - Performance issues
                    - Security vulnerabilities
                    - Naming conventions

                    Provide detailed feedback in Russian.
                    """,
                    context={"language": "bsl"}
                )

                review_text = review["response"]
            except Exception as e:
                self.logger.error("Code review failed: %s", e)
                review_text = "Review unavailable"
        else:
            review_text = "LLM not available for review"

        # Security analysis
        safety = self.secure_agent._analyze_code_safety(code)

        return {
            "review": review_text,
            "safety": safety,
            "score": safety["score"] * 10,  # 0-10 scale
            "approved": safety["score"] >= 0.8
        }

    async def fix_code(
        self,
        code: str,
        issues: List[Dict],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Fix code issues using LLM.

        Args:
            code: Code with issues
            issues: List of issues to fix
            context: Additional context

        Returns:
            Fixed code
        """
        context = context or {}

        if self.llm_selector:
            try:
                fixed = await self.llm_selector.generate(
                    task_type=TaskType.CODE_FIX,
                    prompt=f"""
                    Fix these issues in BSL code:

                    Code:
                    {code}

                    Issues:
                    {issues}

                    Provide fixed code maintaining 1C conventions.
                    """,
                    context={"language": "bsl"}
                )

                fixed_code = fixed["response"]
            except Exception as e:
                self.logger.error("Code fix failed: %s", e)
                fixed_code = code  # Return original if fix fails
        else:
            fixed_code = code

        # Verify fix
        safety_before = self.secure_agent._analyze_code_safety(code)
        safety_after = self.secure_agent._analyze_code_safety(fixed_code)

        return {
            "fixed_code": fixed_code,
            "safety_before": safety_before,
            "safety_after": safety_after,
            "improved": safety_after["score"] > safety_before["score"]
        }

    def _build_bsl_prompt(self, prompt: str, context: Dict) -> str:
        """Build production-ready BSL-specific prompt following Clean Architecture"""
        module_type = context.get('module_type', 'general')

        # Base prompt with Clean Architecture principles
        base_prompt = f"""
Сгенерируй production-ready код на языке BSL для платформы 1С:Предприятие 8.3.

Требование: {prompt}

Контекст:
- Тип модуля: {module_type}
- Описание: {context.get('description', 'Нет дополнительного контекста')}
- Версия платформы: {context.get('platform_version', '8.3.24')}

ОБЯЗАТЕЛЬНЫЕ ТРЕБОВАНИЯ (Clean Architecture):

1. **Структура кода:**
   - Разделяй бизнес-логику и инфраструктуру
   - Используй модульную структуру
   - Избегай God Objects (большие монолитные функции)
   - Один уровень абстракции на функцию

2. **Именование (русский язык):**
   - Функции: ПолучитьДанныеКлиента(), СоздатьДокумент()
   - Переменные: СписокТоваров, ДатаНачала, РезультатОбработки
   - Параметры: ИдентификаторКлиента, ПараметрыОтбора
   - Используй говорящие имена (не Дан1, Рез2)

3. **Обработка ошибок:**
   ```bsl
   Попытка
       // Основная логика
   Исключение
       ЗаписьЖурналаРегистрации("Описание операции",
           УровеньЖурналаРегистрации.Ошибка,,,
           ПодробноеПредставлениеОшибки(ИнформацияОбОшибке()));
       ВызватьИсключение;
   КонецПопытки;
   ```

4. **Комментарии (обязательно):**
   - Описание функции/процедуры
   - Параметры с типами
   - Возвращаемое значение
   - Примеры использования (для сложной логики)

5. **Стандарты 1С:**
   - Используй "Экспорт" для публичных функций
   - Избегай устаревших конструкций
   - Используй СтрШаблон() вместо конкатенации
   - Проверяй ЗначениеЗаполнено() перед использованием

6. **Производительность:**
   - Минимизируй обращения к БД
   - Используй пакетные операции где возможно
   - Избегай вложенных циклов по большим данным

7. **Безопасность:**
   - Валидация входных параметров
   - Проверка прав доступа
   - Экранирование данных для запросов

Формат ответа: Верни ТОЛЬКО код без объяснений и markdown разметки.
"""

        # Add module-specific guidelines
        if module_type == 'common_module':
            base_prompt += """

Дополнительно для Общего модуля:
- Все функции должны быть с "Экспорт"
- Избегай глобальных переменных
- Функции должны быть stateless
"""
        elif module_type == 'object_module':
            base_prompt += """

Дополнительно для Модуля объекта:
- Используй ЭтотОбъект для доступа к реквизитам
- Обработчики событий: ПередЗаписью(), ПриЗаписи(), ПередУдалением()
- Валидация данных в ПередЗаписью()
"""
        elif module_type == 'manager_module':
            base_prompt += """

Дополнительно для Модуля менеджера:
- Функции создания объектов
- Общие методы работы с объектами
- Все функции с "Экспорт"
"""

        return base_prompt

    def _generate_placeholder_bsl(self, prompt: str) -> str:
        """Generate placeholder BSL code"""
        return f"""// Сгенерировано для: {prompt}
// TODO: Реализовать функциональность

Функция ПримерФункции() Экспорт
    // Ваш код здесь
    Возврат Неопределено;
КонецФункции
"""

    async def _apply_self_healing(
        self,
        code: str,
        concerns: List[Dict]
    ) -> str:
        """
        Apply self-healing to fix code issues.

        Args:
            code: Code with issues
            concerns: List of concerns from safety analysis

        Returns:
            Healed code
        """
        if not self.use_self_healing:
            return code

        # TODO: Integrate with Self-Healing Code component
        # For now, use LLM to fix auto-fixable issues
        auto_fixable = [c for c in concerns if c.get("auto_fixable", False)]

        if not auto_fixable:
            self.logger.info("No auto-fixable concerns found")
            return code

        self.logger.info(f"Attempting to fix {len(auto_fixable)} concerns")

        try:
            # Use LLM to fix issues
            fixed_code = await self.fix_code(
                code=code,
                issues=auto_fixable,
                context={"language": "bsl"}
            )

            return fixed_code.get("fixed_code", code)
        except Exception as e:
            self.logger.error("Self-healing failed: %s", e)
            return code

    def _validate_bsl_code(self, code: str) -> Dict[str, Any]:
        """
        Validate BSL code structure and syntax.

        Args:
            code: BSL code to validate

        Returns:
            Validation results
        """
        issues = []

        # Check for basic BSL structure
        if not code.strip():
            issues.append({"type": "error", "message": "Empty code"})
            return {"valid": False, "issues": issues}

        # Check for proper function/procedure endings
        function_count = code.count("Функция ")
        end_function_count = code.count("КонецФункции")
        procedure_count = code.count("Процедура ")
        end_procedure_count = code.count("КонецПроцедуры")

        if function_count != end_function_count:
            issues.append({
                "type": "error",
                "message": f"Mismatch: {function_count} functions but {end_function_count} endings"
            })

        if procedure_count != end_procedure_count:
            issues.append({
                "type": "error",
                "message": f"Mismatch: {procedure_count} procedures but {end_procedure_count} endings"
            })

        # Check for error handling
        has_try = "Попытка" in code
        has_exception = "Исключение" in code

        if has_try and not has_exception:
            issues.append({
                "type": "warning",
                "message": "Try block without exception handler"
            })

        # Check for comments
        if "//" not in code:
            issues.append({
                "type": "warning",
                "message": "No comments found - add documentation"
            })

        # Check for deprecated constructions (basic check)
        deprecated = []
        if "Сообщить(" in code:
            deprecated.append("Сообщить() - use ЗаписьЖурналаРегистрации()")

        if deprecated:
            issues.append({
                "type": "warning",
                "message": f"Deprecated constructions: {', '.join(deprecated)}"
            })

        return {
            "valid": len([i for i in issues if i["type"] == "error"]) == 0,
            "issues": issues,
            "stats": {
                "functions": function_count,
                "procedures": procedure_count,
                "lines": len(code.split("\n")),
                "has_error_handling": has_try and has_exception
            }
        }

    async def evolve_code(self, code: str, target_metrics: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Evolve code using Code DNA (stub for future integration).

        Args:
            code: Code to evolve
            target_metrics: Target metrics for evolution

        Returns:
            Evolution results
        """
        if not self.code_dna:
            self.logger.warning("Code DNA not available - returning original code")
            return {
                "original": code,
                "evolved": code,
                "improvements": [],
                "status": "code_dna_not_available"
            }

        # TODO: Implement Code DNA integration
        target_metrics = target_metrics or {
            "complexity": "low",
            "maintainability": "high",
            "performance": "optimized"
        }

        self.logger.info("Code DNA evolution with targets: %s", target_metrics)

        return {
            "original": code,
            "evolved": code,  # Placeholder
            "improvements": [],
            "status": "pending_implementation"
        }

    async def predict_next_code(self, current_context: str) -> Dict[str, Any]:
        """
        Predict next code using Predictive Generation (stub for future integration).

        Args:
            current_context: Current code context

        Returns:
            Predictions
        """
        if not self.predictive_gen:
            self.logger.warning("Predictive Generation not available")
            return {
                "suggestions": [],
                "confidence": 0.0,
                "reasoning": "Predictive Generation not initialized",
                "status": "predictive_gen_not_available"
            }

        # TODO: Implement Predictive Generation integration
        self.logger.info("Predictive Generation requested")

        return {
            "suggestions": [],
            "confidence": 0.0,
            "reasoning": "Pending implementation",
            "status": "pending_implementation"
        }


__all__ = ["DeveloperAgentEnhanced"]
