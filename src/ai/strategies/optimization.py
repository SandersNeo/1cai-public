import time
from typing import Any, Dict

from src.ai.strategies.base import AIStrategy
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class OptimizationStrategy(AIStrategy):
    def __init__(self, kimi_client=None, qwen_client=None, neo4j_client=None):
        self.kimi_client = kimi_client
        self.qwen_client = qwen_client
        self.neo4j_client = neo4j_client

    async def execute(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle code optimization requests - prioritizes Kimi-K2-Thinking for complex reasoning"""

        code = context.get("code")
        if not code:
            return {"type": "optimization", "error": "No code provided in context"}

        # Try Kimi-K2-Thinking first (better for complex optimization with reasoning)
        if self.kimi_client and self.kimi_client.is_configured:
            try:
                # Track metrics
                try:
                    from src.monitoring.prometheus_metrics import (
                        kimi_queries_total, kimi_response_duration_seconds,
                        kimi_tokens_used_total, orchestrator_queries_total)

                    start_time = time.time()
                    kimi_mode = "api" if not self.kimi_client.is_local else "local"
                except ImportError:
                    kimi_queries_total = None
                    kimi_response_duration_seconds = None
                    kimi_tokens_used_total = None
                    orchestrator_queries_total = None
                    start_time = None
                    kimi_mode = None

                optimization_prompt = f"""Оптимизируй следующий BSL код:
{code}

Проанализируй код и предложи оптимизированную версию с объяснением улучшений."""

                system_prompt = context.get(
                    "system_prompt",
                    "You are an expert 1C:Enterprise developer specializing in code optimization. Provide optimized code with detailed explanations.",
                )

                result = await self.kimi_client.generate(
                    prompt=optimization_prompt,
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
                        query_type="optimization", selected_service="kimi_k2"
                    ).inc()

                optimized_text = result.get("text", "")

                # Try to extract optimized code and explanation
                import re

                code_match = re.search(
                    r"```(?:bsl|1c)?\n?(.*?)```", optimized_text, re.DOTALL
                )
                optimized_code = (
                    code_match.group(1).strip() if code_match else optimized_text
                )

                return {
                    "type": "optimization",
                    "services": ["kimi_k2"],
                    "original_code": code,
                    "optimized_code": optimized_code,
                    "explanation": result.get("reasoning_content", "")
                    or optimized_text,
                    "model": "Kimi-K2-Thinking",
                    "usage": result.get("usage", {}),
                }
            except Exception as e:
                # Track error metrics
                try:
                    from src.monitoring.prometheus_metrics import (
                        ai_errors_total, kimi_queries_total,
                        orchestrator_fallback_total)

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
                    "Kimi optimization failed, falling back to Qwen",
                    extra={"error": str(e), "error_type": type(e).__name__},
                )
                # Fall through to Qwen

        # Fallback to Qwen3-Coder
        if not self.qwen_client:
            return {
                "type": "optimization",
                "error": "No optimization service available. Configure KIMI_API_KEY or start Ollama with: ollama pull qwen2.5-coder:7b",
            }

        try:
            # TODO: Get dependencies from Neo4j if available
            dependencies = None
            if self.neo4j_client:
                # Get function dependencies
                pass

            # Optimize with Qwen3-Coder
            result = await self.qwen_client.optimize_code(
                code=code, context={"dependencies": dependencies}
            )

            return {
                "type": "optimization",
                "services": ["qwen_coder"],
                "original_code": code,
                "optimized_code": result.get("optimized_code"),
                "explanation": result.get("explanation"),
                "improvements": result.get("improvements"),
                "model": result.get("model"),
            }

        except Exception as e:
            logger.error(
                "Optimization error",
                extra={"error": str(e), "error_type": type(e).__name__},
                exc_info=True,
            )
            return {"type": "optimization", "error": str(e)}
