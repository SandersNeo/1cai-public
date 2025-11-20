from typing import Dict, Any
import time
import re
from src.ai.strategies.base import AIStrategy
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class CodeGenerationStrategy(AIStrategy):
    def __init__(self, kimi_client=None, qwen_client=None):
        self.kimi_client = kimi_client
        self.qwen_client = qwen_client

    async def execute(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle code generation requests - prioritizes Kimi-K2-Thinking for complex reasoning"""

        # Try Kimi-K2-Thinking first (better for complex code generation)
        if self.kimi_client and self.kimi_client.is_configured:
            try:
                # Track metrics
                try:
                    from src.monitoring.prometheus_metrics import (
                        kimi_queries_total,
                        kimi_response_duration_seconds,
                        kimi_tokens_used_total,
                        orchestrator_queries_total,
                    )

                    start_time = time.time()
                    kimi_mode = "api" if not self.kimi_client.is_local else "local"
                except ImportError:
                    kimi_queries_total = None
                    kimi_response_duration_seconds = None
                    kimi_tokens_used_total = None
                    orchestrator_queries_total = None
                    start_time = None
                    kimi_mode = None

                system_prompt = context.get(
                    "system_prompt",
                    "You are an expert 1C:Enterprise developer. Generate clean, efficient BSL code.",
                )

                result = await self.kimi_client.generate(
                    prompt=query,
                    system_prompt=system_prompt,
                    temperature=1.0,
                    max_tokens=context.get("max_tokens", 4096),
                )

                # Record metrics
                if kimi_queries_total and kimi_mode:
                    duration = time.time() - start_time
                    kimi_queries_total.labels(mode=kimi_mode, status="success").inc()
                    kimi_response_duration_seconds.labels(mode=kimi_mode).observe(
                        duration
                    )

                    usage = result.get("usage", {})
                    if usage:
                        kimi_tokens_used_total.labels(
                            mode=kimi_mode, token_type="prompt"
                        ).inc(usage.get("prompt_tokens", 0))
                        kimi_tokens_used_total.labels(
                            mode=kimi_mode, token_type="completion"
                        ).inc(usage.get("completion_tokens", 0))
                        kimi_tokens_used_total.labels(
                            mode=kimi_mode, token_type="total"
                        ).inc(usage.get("total_tokens", 0))

                    orchestrator_queries_total.labels(
                        query_type="code_generation", selected_service="kimi_k2"
                    ).inc()

                # Extract code from response (may contain markdown)
                code_text = result.get("text", "")

                # Try to extract code block if present
                code_match = re.search(
                    r"```(?:bsl|1c)?\n?(.*?)```", code_text, re.DOTALL
                )
                if code_match:
                    code_text = code_match.group(1).strip()

                return {
                    "type": "code_generation",
                    "service": "kimi_k2",
                    "code": code_text,
                    "full_response": result.get("text"),
                    "reasoning": result.get("reasoning_content", ""),
                    "model": "Kimi-K2-Thinking",
                    "usage": result.get("usage", {}),
                }
            except Exception as e:
                # Track error metrics
                try:
                    from src.monitoring.prometheus_metrics import (
                        kimi_queries_total,
                        ai_errors_total,
                        orchestrator_fallback_total,
                    )

                    kimi_mode = "api" if not self.kimi_client.is_local else "local"
                    kimi_queries_total.labels(mode=kimi_mode, status="error").inc()
                    ai_errors_total.labels(
                        service="kimi_k2",
                        model="Kimi-K2-Thinking",
                        error_type=type(e).__name__,
                    ).inc()
                    orchestrator_fallback_total.labels(
                        from_service="kimi_k2", to_service="qwen_coder", reason="error"
                    ).inc()
                except ImportError:
                    pass

                logger.warning(
                    "Kimi code generation failed, falling back to Qwen",
                    extra={"error": str(e), "error_type": type(e).__name__},
                )
                # Fall through to Qwen

        # Fallback to Qwen3-Coder
        if not self.qwen_client:
            return {
                "type": "code_generation",
                "service": "qwen_coder",
                "error": "No code generation service available. Configure KIMI_API_KEY or start Ollama with: ollama pull qwen2.5-coder:7b",
            }

        try:
            # Extract function details from query if present
            function_name = context.get("function_name")
            parameters = context.get("parameters", [])

            if function_name:
                # Generate specific function
                result = await self.qwen_client.generate_function(
                    description=query,
                    function_name=function_name,
                    parameters=parameters,
                )
            else:
                # General code generation
                result = await self.qwen_client.generate_code(
                    prompt=query, context=context
                )

            return {
                "type": "code_generation",
                "service": "qwen_coder",
                "code": result.get("code"),
                "full_response": result.get("full_response"),
                "model": result.get("model"),
            }

        except Exception as e:
            logger.error(
                "Code generation error",
                extra={"error": str(e), "error_type": type(e).__name__},
                exc_info=True,
            )
            return {"type": "code_generation", "service": "qwen_coder", "error": str(e)}
