import asyncio
import json
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from src.infrastructure.event_bus import get_event_bus, Event, EventType
from src.ai.rltf.collector import FeedbackCollector

async def test_reward_bus():
    print("Starting Reward Signal Bus Test...")
    
    # 1. Setup
    storage_path = "data/rltf/test_rewards.jsonl"
    if os.path.exists(storage_path):
        os.remove(storage_path)
        
    event_bus = get_event_bus()
    collector = FeedbackCollector(storage_path=storage_path)
    
    # Subscribe
    event_bus.subscribe(EventType.AI_FEEDBACK_RECEIVED, collector)
    
    # 2. Start Event Bus
    await event_bus.start()
    
    # 3. Publish Simulated OPA Reward
    # This simulates what OPA would send after a policy check
    payload = {
        "source": "opa_policy_enforcer",
        "value": -100.0,
        "message": "Deployment denied: 'latest' tag used"
    }
    
    event = Event(
        type=EventType.AI_FEEDBACK_RECEIVED,
        payload=payload,
        correlation_id="session-deploy-fail-001"
    )
    
    print(f"Publishing Reward Event: {event.id}")
    await event_bus.publish(event)
    
    # Allow time for processing
    await asyncio.sleep(1)
    
    # 4. Verify Storage
    if not os.path.exists(storage_path):
        print("FAIL: Storage file not created.")
        return
        
    with open(storage_path, "r") as f:
        lines = f.readlines()
        
    if len(lines) == 0:
        print("FAIL: No rewards saved.")
        return
        
    trajectory = json.loads(lines[0])
    print(f"Saved Reward Trajectory: {json.dumps(trajectory, indent=2)}")
    
    # Assertions
    assert trajectory["session_id"] == "session-deploy-fail-001"
    assert trajectory["reward"]["source"] == "opa_policy_enforcer"
    assert trajectory["reward"]["value"] == -100.0
    
    print("SUCCESS: Reward Signal correctly captured.")
    
    # Cleanup
    await event_bus.stop()
    if os.path.exists(storage_path):
        os.remove(storage_path)

if __name__ == "__main__":
    asyncio.run(test_reward_bus())
