"""
Council Orchestrator

Main orchestration logic for LLM Council multi-agent consensus.
"""

import asyncio
import time
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional

from loguru import logger

from .chairman import Chairman, SynthesisResult
from .config import (
    CHAIRMAN_MODEL,
    COUNCIL_MODELS,
    COUNCIL_TIMEOUT_SECONDS,
    MAX_COUNCIL_SIZE,
    MIN_COUNCIL_SIZE,
)
from .peer_review import PeerReview, ReviewResult


@dataclass
class CouncilConfig:
    """Configuration for a council query"""

    models: List[str]
    chairman: str
    timeout: int = COUNCIL_TIMEOUT_SECONDS
    include_reviews: bool = True


@dataclass
class CouncilResponse:
    """Complete response from council process"""

    final_answer: str
    individual_opinions: List[Dict]
    peer_reviews: List[Dict]
    chairman_synthesis: str
    metadata: Dict

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


class CouncilOrchestrator:
    """
    Orchestrates the 3-stage LLM Council process.

    Stage 1: First Opinions (parallel)
    Stage 2: Peer Review (cross-evaluation)
    Stage 3: Chairman Synthesis (final answer)
    """

    def __init__(self, ai_orchestrator):
        """
        Initialize council orchestrator.

        Args:
            ai_orchestrator: Parent AI orchestrator with LLM providers
        """
        self.ai_orchestrator = ai_orchestrator
        self.peer_review = PeerReview(ai_orchestrator)

    async def process_query(
        self, query: str, context: Optional[Dict] = None, config: Optional[CouncilConfig] = None
    ) -> CouncilResponse:
        """
        Process query through full council workflow.

        Args:
            query: User query
            context: Optional context
            config: Optional council configuration

        Returns:
            CouncilResponse with all stages
        """
        start_time = time.time()

        # Use default config if not provided
        if config is None:
            config = CouncilConfig(models=COUNCIL_MODELS, chairman=CHAIRMAN_MODEL)

        # Validate config
        self._validate_config(config)

        logger.info(f"Starting council query with {len(config.models)} models")

        try:
            # Stage 1: First Opinions
            logger.info("Stage 1: Collecting first opinions")
            opinions = await asyncio.wait_for(
                self._stage1_first_opinions(query, config.models, context), timeout=config.timeout / 3
            )

            # Stage 2: Peer Review
            logger.info("Stage 2: Conducting peer review")
            reviews = await asyncio.wait_for(
                self._stage2_peer_review(query, opinions, context), timeout=config.timeout / 3
            )

            # Stage 3: Chairman Synthesis
            logger.info("Stage 3: Chairman synthesis")
            synthesis = await asyncio.wait_for(
                self._stage3_chairman_synthesis(
                    query, opinions, reviews, config.chairman, context),
                timeout=config.timeout / 3,
            )

            # Calculate metadata
            elapsed_time = time.time() - start_time
            metadata = {
                "council_size": len(config.models),
                "chairman": config.chairman,
                "latency_ms": int(elapsed_time * 1000),
                "cost_multiplier": len(config.models) + 1,  # +1 for chairman
                "stages_completed": 3,
            }

            logger.info(f"Council query completed in {elapsed_time:.2f}s")

            return CouncilResponse(
                final_answer=synthesis.final_response,
                individual_opinions=[{"model": o["model"],
                    "response": o["response"]} for o in opinions],
                peer_reviews=[
                    {"reviewer": r.reviewer_model, "rankings": r.rankings,
                        "reasoning": r.reasoning[:200]}  # Truncate
                    for r in reviews
                ]
                if config.include_reviews
                else [],
                chairman_synthesis=synthesis.synthesis_reasoning,
                metadata=metadata,
            )

        except asyncio.TimeoutError:
            logger.error(f"Council query timeout after {config.timeout}s")
            raise
        except Exception as e:
            logger.error("Council query error: %s", e)
            raise

    async def _stage1_first_opinions(self, query: str, models: List[str], context: Optional[Dict]) -> List[Dict]:
        """
        Stage 1: Collect first opinions from all models in parallel.

        Args:
            query: User query
            models: List of model names
            context: Optional context

        Returns:
            List of {"model": str, "response": str}
        """
        tasks = [self._single_model_query(model, query, context) for model in models]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_responses = []
        for model, response in zip(models, responses):
            if isinstance(response, Exception):
                logger.error("Error from %s: {response}", model)
            else:
                valid_responses.append({"model": model, "response": response})

        if len(valid_responses) < MIN_COUNCIL_SIZE:
            raise ValueError(
                f"Insufficient responses: {len(valid_responses)} < {MIN_COUNCIL_SIZE}")

        return valid_responses

    async def _single_model_query(self, model: str, query: str, context: Optional[Dict]) -> str:
        """
        Query a single model.

        Args:
            model: Model name
            query: User query
            context: Optional context

        Returns:
            Model response
        """
        provider = self.ai_orchestrator._get_provider(model)
        response = await provider.generate(prompt=query, context=context or {})
        return response

    async def _stage2_peer_review(
        self, query: str, opinions: List[Dict], context: Optional[Dict]
    ) -> List[ReviewResult]:
        """
        Stage 2: Peer review of all opinions.

        Args:
            query: Original query
            opinions: Opinions from Stage 1
            context: Optional context

        Returns:
            List of ReviewResult
        """
        return await self.peer_review.conduct_peer_review(query=query, responses=opinions, context=context)

    async def _stage3_chairman_synthesis(
        self,
        query: str,
        opinions: List[Dict],
        reviews: List[ReviewResult],
        chairman_model: str,
        context: Optional[Dict],
    ) -> SynthesisResult:
        """
        Stage 3: Chairman synthesizes final response.

        Args:
            query: Original query
            opinions: Opinions from Stage 1
            reviews: Reviews from Stage 2
            chairman_model: Chairman model name
            context: Optional context

        Returns:
            SynthesisResult
        """
        chairman = Chairman(self.ai_orchestrator, chairman_model)
        return await chairman.synthesize(query=query, responses=opinions, reviews=reviews, context=context)

    def _validate_config(self, config: CouncilConfig):
        """
        Validate council configuration.

        Args:
            config: CouncilConfig to validate

        Raises:
            ValueError: If config is invalid
        """
        if len(config.models) < MIN_COUNCIL_SIZE:
            raise ValueError(
                f"Council size {len(config.models)} < minimum {MIN_COUNCIL_SIZE}")

        if len(config.models) > MAX_COUNCIL_SIZE:
            raise ValueError(
                f"Council size {len(config.models)} > maximum {MAX_COUNCIL_SIZE}")

        if config.chairman not in config.models:
            logger.warning(
                f"Chairman {config.chairman} not in council models, " f"will use separate provider")
