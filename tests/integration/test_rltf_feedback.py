import asyncio
import json
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from src.infrastructure.event_bus import get_event_bus, Event, EventType
from src.ai.rltf.collector import FeedbackCollector

async def test_feedback_collection():
    print("Starting RLTF Feedback Collection Test...")
    
    # 1. Setup
    storage_path = "data/rltf/test_trajectories.jsonl"
    if os.path.exists(storage_path):
        os.remove(storage_path)
        
    event_bus = get_event_bus()
    collector = FeedbackCollector(storage_path=storage_path)
    
    # Subscribe manually for this test (in real app, Orchestrator does this)
    for event_type in collector.event_types:
        event_bus.subscribe(event_type, collector)
        
    print("Collector subscribed.")
    
    # 2. Start Event Bus
    await event_bus.start()
    
    # 3. Publish Simulated Event
    payload = {
        "service": "test_service",
        "duration": 0.5,
        "success": True,
        "query_type": "code_generation"
    }
    
    event = Event(
        type=EventType.STRATEGY_PERFORMANCE_RECORDED,
        payload=payload,
        correlation_id="test-session-123"
    )
    
    print(f"Publishing event: {event.id}")
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
        print("FAIL: No trajectories saved.")
        return
        
    trajectory = json.loads(lines[0])
    print(f"Saved Trajectory: {json.dumps(trajectory, indent=2)}")
    
    # Assertions
    assert trajectory["session_id"] == "test-session-123"
    assert trajectory["action"]["tool_name"] == "test_service"
    assert trajectory["reward"]["value"] == 1.0
    
    print("SUCCESS: Trajectory correctly saved.")
    
    # Cleanup
    await event_bus.stop()
    if os.path.exists(storage_path):
        os.remove(storage_path)

if __name__ == "__main__":
    asyncio.run(test_feedback_collection())
