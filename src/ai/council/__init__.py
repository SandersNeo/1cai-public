"""
LLM Council Module

Multi-agent consensus mechanism for improved AI response quality.
Based on Karpathy's llm-council architecture.

Architecture:
    Stage 1: First Opinions (parallel)
    Stage 2: Peer Review (cross-evaluation)
    Stage 3: Chairman Synthesis (final answer)
"""

from .chairman import Chairman, SynthesisResult
from .config import (
    CHAIRMAN_MODEL,
    COUNCIL_ENABLED,
    COUNCIL_MODELS,
    COUNCIL_TIMEOUT_SECONDS,
)
from .council_orchestrator import CouncilConfig, CouncilOrchestrator, CouncilResponse
from .peer_review import PeerReview, ReviewResult

__all__ = [
    "CouncilOrchestrator",
    "CouncilConfig",
    "CouncilResponse",
    "PeerReview",
    "ReviewResult",
    "Chairman",
    "SynthesisResult",
    "COUNCIL_MODELS",
    "CHAIRMAN_MODEL",
    "COUNCIL_ENABLED",
    "COUNCIL_TIMEOUT_SECONDS",
]
