import unittest
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from unittest.mock import MagicMock, patch
from src.ai.orchestrator import AIOrchestrator


class TestOrchestratorListener(unittest.IsolatedAsyncioTestCase):
    async def test_start_listener(self):
        """Test that start_listener initializes correctly."""
        # Mock dependencies to avoid full initialization
        with patch("src.ai.orchestrator.QueryClassifier"), patch("src.ai.orchestrator.EventPublisher"), patch(
            "src.ai.orchestrator.get_event_bus"
        ):
            orchestrator = AIOrchestrator()

            # Mock logger to verify calls
            with patch("src.ai.orchestrator.logger") as mock_logger:
                await orchestrator.start_listener()

                # Verify that it logged the start message
                mock_logger.info.assert_any_call("Starting AI Orchestrator Event Listener...")
                mock_logger.info.assert_any_call("Subscribed to '1c.sync.event'")


if __name__ == "__main__":
    unittest.main()
