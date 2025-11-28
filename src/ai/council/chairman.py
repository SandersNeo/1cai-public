"""
Chairman Module

Implements Stage 3 of council process: synthesis of final response.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

from loguru import logger


@dataclass
class SynthesisResult:
    """Result of chairman synthesis"""

    final_response: str
    synthesis_reasoning: str
    confidence: float


class Chairman:
    """
    Chairman synthesizes final response from council opinions and reviews.
    """

    def __init__(self, orchestrator, chairman_model: str):
        """
        Initialize chairman.

        Args:
            orchestrator: Parent AI orchestrator
            chairman_model: Model to use as chairman
        """
        self.orchestrator = orchestrator
        self.chairman_model = chairman_model

    async def synthesize(
        self, query: str, responses: List[Dict], reviews: List, context: Optional[Dict] = None
    ) -> SynthesisResult:
        """
        Synthesize final response from all opinions and reviews.

        Args:
            query: Original query
            responses: All responses from Stage 1
            reviews: All reviews from Stage 2
            context: Optional context

        Returns:
            SynthesisResult
        """
        logger.info(f"Chairman ({self.chairman_model}) synthesizing final response")

        try:
            # Create synthesis prompt
            synthesis_prompt = self._create_synthesis_prompt(
                query=query, responses=responses, reviews=reviews)

            # Get chairman provider
            provider = self.orchestrator._get_provider(self.chairman_model)

            # Generate synthesis
            final_response = await provider.generate(prompt=synthesis_prompt, context=context or {})

            return SynthesisResult(
                final_response=final_response,
                synthesis_reasoning="Chairman synthesis based on council consensus",
                confidence=0.9,
            )

        except Exception as e:
            logger.error("Error in chairman synthesis: %s", e)
            # Fallback: return best-ranked response
            return self._fallback_synthesis(responses, reviews)

    def _create_synthesis_prompt(self, query: str, responses: List[Dict], reviews: List) -> str:
        """
        Create prompt for chairman synthesis.

        Args:
            query: Original query
            responses: All responses
            reviews: All reviews

        Returns:
            Synthesis prompt
        """
        # Format responses
        responses_text = "\n\n".join(
            [f"Response from {r['model']}:\n{r['response']}" for r in responses])

        # Format reviews summary
        reviews_text = "\n".join(
            [f"{r.reviewer_model} rankings: {r.rankings}" for r in reviews])

        prompt = f"""You are the Chairman of an LLM Council. Multiple AI models have provided responses to a query, and each has reviewed the others' work.

Your task is to synthesize the BEST POSSIBLE final answer by:
1. Considering all responses
2. Weighing the peer review rankings
3. Combining the strongest points from each
4. Correcting any errors or inconsistencies
5. Producing a comprehensive, accurate final answer

Original Query:
{query}

Council Responses:
{responses_text}

Peer Review Rankings:
{reviews_text}

Please provide the final synthesized answer that represents the council's best collective response."""

        return prompt

    def _fallback_synthesis(self, responses: List[Dict], reviews: List) -> SynthesisResult:
        """
        Fallback synthesis if chairman fails.

        Returns best-ranked response based on peer reviews.
        """
        # Calculate average rankings
        if reviews:
            from .peer_review import PeerReview

            peer_review = PeerReview(self.orchestrator)
            avg_rankings = peer_review.aggregate_rankings(reviews, len(responses))

            # Find best-ranked response
            best_idx = avg_rankings.index(min(avg_rankings))
            best_response = responses[best_idx]

            return SynthesisResult(
                final_response=best_response["response"],
                synthesis_reasoning=f"Fallback: Best-ranked response from {best_response['model']}",
                confidence=0.6,
            )
        else:
            # No reviews, return first response
            return SynthesisResult(
                final_response=responses[0]["response"],
                synthesis_reasoning="Fallback: First response (no reviews available)",
                confidence=0.5,
            )
