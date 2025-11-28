"""
Temporal Graph Neural Network

Time-aware graph neural network for code evolution tracking.
Implements temporal attention and multi-scale aggregation.

Based on:
- Temporal Graph Networks (TGN)
- Nested Learning paradigm
"""

from typing import Dict, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

# Check for torch_geometric
try:
