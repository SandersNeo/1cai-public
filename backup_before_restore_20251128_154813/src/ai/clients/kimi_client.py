# [NEXUS IDENTITY] ID: -1815072424517257065 | DATE: 2025-11-19

"""
Async client for Kimi-K2-Thinking API (Moonshot AI).

Kimi-K2-Thinking is a state-of-the-art thinking model with:
- 1T parameters (MoE), 32B activated
- 256k context window
- Native INT4 quantization
- Deep thinking & tool orchestration
- Stable long-horizon agency (200-300 tool calls)

API: https://platform.moonshot.ai (OpenAI-compatible)

Best practices:
- Use temperature=1.0 (recommended)
- Supports tool calling (same as Kimi-K2-Instruct)
- Returns reasoning_content for thinking steps
- Graceful fallback when not configured
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx
from tenacity import (retry, retry_if_exception_type, stop_after_attempt,
                      wait_exponential)

from src.utils.structured_logging import StructuredLogger

from .exceptions import LLMCallError, LLMNotConfiguredError

try:  # Optional dependency for local mode
