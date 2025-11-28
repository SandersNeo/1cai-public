"""
Peer Review Module

Implements Stage 2 of council process: cross-evaluation of responses.
"""

import asyncio
import random
from dataclasses import dataclass
from typing import Dict, List, Optional

from loguru import logger

from .config import ANONYMIZE_RESPONSES


@dataclass
class ReviewResult:
    """Result of peer review process"""

    reviewer_model: str
    rankings: List[int]  # Rankings of other models' responses (1=best)
    reasoning: str  # Explanation of rankings
    confidence: float  # Confidence in rankings (0-1)


class PeerReview:
    """
    Peer review implementation for LLM Council.

    Each model reviews and ranks others' responses anonymously.
    """

    def __init__(self, orchestrator):
        """
        Initialize peer review.

        Args:
            orchestrator: Parent AI orchestrator with LLM providers
        """
        self.orchestrator = orchestrator

    async def conduct_peer_review(
        self, query: str, responses: List[Dict], context: Optional[Dict] = None
    ) -> List[ReviewResult]:
        """
        Conduct peer review of all responses.

        Args:
            query: Original user query
            responses: List of responses from Stage 1
                      [{"model": "kimi", "response": "..."}, ...]
            context: Optional context

        Returns:
            List of ReviewResult objects
        """
        logger.info(f"Starting peer review with {len(responses)} responses")

        # Anonymize responses if configured
        if ANONYMIZE_RESPONSES:
            anonymized_responses = self._anonymize_responses(responses)
        else:
            anonymized_responses = responses

        # Each model reviews all others
        review_tasks = []
        for i, reviewer_data in enumerate(responses):
            reviewer_model = reviewer_data["model"]

            # Get responses from other models (exclude self)
            other_responses = [r for j, r in enumerate(anonymized_responses) if j != i]

            task = self._single_review(
                reviewer_model=reviewer_model, query=query, responses_to_review=other_responses, context=context
            )
            review_tasks.append(task)

        # Execute reviews in parallel
        reviews = await asyncio.gather(*review_tasks, return_exceptions=True)

        # Filter out exceptions
        valid_reviews = [r for r in reviews if isinstance(r, ReviewResult)]

        logger.info(f"Completed {len(valid_reviews)} peer reviews")
        return valid_reviews

    async def _single_review(
        self, reviewer_model: str, query: str, responses_to_review: List[Dict], context: Optional[Dict] = None
    ) -> ReviewResult:
        """
        Single model reviews other responses.

        Args:
            reviewer_model: Model conducting the review
            query: Original query
            responses_to_review: Responses to review
            context: Optional context

        Returns:
            ReviewResult
        """
        try:
            # Create review prompt
            review_prompt = self._create_review_prompt(
                query=query, responses=responses_to_review)

            # Get provider for reviewer model
            provider = self.orchestrator._get_provider(reviewer_model)

            # Generate review
            review_response = await provider.generate(prompt=review_prompt, context=context or {})

            # Parse rankings from response
            rankings, reasoning = self._parse_review_response(
                review_response, num_responses=len(responses_to_review))

            return ReviewResult(
                reviewer_model=reviewer_model,
                rankings=rankings,
                reasoning=reasoning,
                confidence=0.8,  # TODO: Calculate actual confidence
            )

        except Exception as e:
            logger.error(f"Error in peer review by {reviewer_model}: {e}")
            # Return default rankings on error
            return ReviewResult(
                reviewer_model=reviewer_model,
                rankings=list(range(1, len(responses_to_review) + 1)),
                reasoning=f"Error during review: {str(e)}",
                confidence=0.0,
            )

    def _anonymize_responses(self, responses: List[Dict]) -> List[Dict]:
        """
        Anonymize model identities in responses.

        Args:
            responses: Original responses with model names

        Returns:
            Anonymized responses with labels like "Response A", "Response B"
        """
        labels = [chr(65 + i) for i in range(len(responses))]  # A, B, C, ...

        # Shuffle to prevent position bias
        shuffled_indices = list(range(len(responses)))
        random.shuffle(shuffled_indices)

        anonymized = []
        for i, idx in enumerate(shuffled_indices):
            anonymized.append(
                {"label": f"Response {labels[i]}", "response": responses[idx]
                    ["response"], "original_index": idx}
            )

        return anonymized

    def _create_review_prompt(self, query: str, responses: List[Dict]) -> str:
        """
        Create prompt for peer review.

        Args:
            query: Original query
            responses: Responses to review

        Returns:
            Review prompt
        """
        # Format responses
        responses_text = "\n\n".join(
            [f"{r.get('label', f'Response {i+1}')}:\n{r['response']}" for i,
                      r in enumerate(responses)]
        )

        prompt = f"""You are an expert reviewer evaluating multiple AI responses to a query.

Original Query:
{query}

Responses to Review:
{responses_text}

Your task:
1. Carefully analyze each response for:
   - Accuracy and correctness
   - Completeness and depth
   - Clarity and coherence
   - Practical applicability
   - Potential issues or errors

2. Rank the responses from best to worst (1 = best, {len(responses)} = worst)

3. Provide your rankings in this format:
   Rankings: [1, 2, 3, ...]

4. Explain your reasoning for the rankings.

Please provide your review now."""

        return prompt

    def _parse_review_response(self, review_response: str, num_responses: int) -> tuple[List[int], str]:
        """
        Parse rankings from review response.

        Args:
            review_response: LLM's review response
            num_responses: Expected number of responses

        Returns:
            (rankings, reasoning)
        """
        import re

        # Try to extract rankings
        # Look for patterns like "Rankings: [1, 2, 3]" or "1, 2, 3"
        patterns = [r"Rankings?:\s*\[([0-9,\s]+)\]",
                                      r"Rankings?:\s*([0-9,\s]+)", r"\[([0-9,\s]+)\]"]

        rankings = None
        for pattern in patterns:
            match = re.search(pattern, review_response, re.IGNORECASE)
            if match:
                try:
                    rankings_str = match.group(1)
                    rankings = [int(x.strip()) for x in rankings_str.split(",")]
                    if len(rankings) == num_responses:
                        break
                except (ValueError, IndexError):
                    continue

        # Default rankings if parsing failed
        if not rankings or len(rankings) != num_responses:
            logger.warning(f"Failed to parse rankings, using default")
            rankings = list(range(1, num_responses + 1))

        # Extract reasoning (everything after rankings)
        reasoning = review_response

        return rankings, reasoning

    def aggregate_rankings(self, reviews: List[ReviewResult], num_responses: int) -> List[float]:
        """
        Aggregate rankings from all reviewers.

        Args:
            reviews: All review results
            num_responses: Number of responses

        Returns:
            Average rankings for each response
        """
        # Initialize scores
        scores = [0.0] * num_responses
        counts = [0] * num_responses

        for review in reviews:
            for i, rank in enumerate(review.rankings):
                if 0 <= i < num_responses:
                    # Weight by confidence
                    scores[i] += rank * review.confidence
                    counts[i] += review.confidence

        # Calculate averages
        avg_rankings = [scores[i] / counts[i] if counts[i] >
            0 else float(i + 1) for i in range(num_responses)]

        return avg_rankings
