"""
Council Configuration

Settings for LLM Council multi-agent consensus.
"""

from typing import List

# Council member models (from existing providers)
COUNCIL_MODELS: List[str] = [
    "kimi",  # Moonshot AI - best for BSL code generation
    "qwen",  # Alibaba Qwen - strong reasoning
    "gigachat",  # Sber GigaChat - Russian language support
    "yandexgpt",  # Yandex GPT - local Russian model
]

# Chairman model (synthesizes final response)
CHAIRMAN_MODEL: str = "kimi"  # Best model as chairman

# Council feature flag
COUNCIL_ENABLED: bool = False  # Default: disabled (opt-in)

# Timeout for council operations (seconds)
COUNCIL_TIMEOUT_SECONDS: int = 60  # 1 minute for all 3 stages

# Minimum council size
MIN_COUNCIL_SIZE: int = 2

# Maximum council size
MAX_COUNCIL_SIZE: int = 8

# Peer review settings
ANONYMIZE_RESPONSES: bool = True  # Hide model identities during review
REQUIRE_RANKINGS: bool = True  # Require numerical rankings

# Chairman synthesis settings
INCLUDE_ALL_OPINIONS: bool = True  # Include all opinions in synthesis
INCLUDE_PEER_REVIEWS: bool = True  # Include peer reviews in synthesis
