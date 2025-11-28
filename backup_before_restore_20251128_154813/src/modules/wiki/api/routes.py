"""
Wiki API Routes

Note: Wiki service implementation is in src/services/wiki/
This is just a re-export for the modular structure.
"""

import sys

# Import from existing wiki implementation
from src.api.wiki import router

sys.path.insert(0, "C:/1cAI/src")


__all__ = ["router"]
