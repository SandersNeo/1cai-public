import os
import json
import sys
import shutil

# Add project root to path
sys.path.append(os.getcwd())

from src.ai.rltf.training.trainer import MockTrainer
from src.ai.rltf.schemas import Trajectory, State, Action, Reward

def test_training_loop():
    print("Starting Training Loop Test...")
    
    # 1. Setup Paths
    data_path = "data/rltf/test_training_data.jsonl"
    model_path = "models/test_v1"
    
    # Cleanup
    if os.path.exists(data_path):
        os.remove(data_path)
    if os.path.exists(model_path):
        shutil.rmtree(model_path)
        
    # 2. Generate Dummy Data
    print("Generating dummy trajectories...")
    os.makedirs(os.path.dirname(data_path), exist_ok=True)
    
    dummy_trajectory = {
        "id": "traj-1",
        "session_id": "sess-1",
        "state": {
            "context_summary": "test context",
            "open_files": [],
            "last_error": None
        },
        "action": {
            "tool_name": "test_tool",
            "tool_input": {},
            "timestamp": "2025-01-01T12:00:00"
        },
        "reward": {
            "source": "test",
            "value": 1.0,
            "message": "good job",
            "timestamp": "2025-01-01T12:00:00"
        },
        "next_state": None
    }
    
    with open(data_path, "w") as f:
        for i in range(10):
            dummy_trajectory["id"] = f"traj-{i}"
            f.write(json.dumps(dummy_trajectory) + "\n")
            
    # 3. Run Trainer
    print("Running MockTrainer...")
    trainer = MockTrainer(data_path=data_path, model_path=model_path)
    trainer.train_epoch()
    
    # 4. Verify Model Update
    version_file = os.path.join(model_path, "version.json")
    if not os.path.exists(version_file):
        print("FAIL: Model version file not created.")
        return
        
    with open(version_file, "r") as f:
        version_data = json.load(f)
        
    print(f"Model Version: {json.dumps(version_data, indent=2)}")
    
    assert version_data["version"] == 1
    assert version_data["status"] == "trained"
    
    # Run again to check increment
    print("Running Epoch 2...")
    trainer.train_epoch()
    
    with open(version_file, "r") as f:
        version_data = json.load(f)
        
    assert version_data["version"] == 2
    print(f"Model Version Updated: {version_data['version']}")
    
    print("SUCCESS: Training loop verified.")
    
    # Cleanup
    if os.path.exists(data_path):
        os.remove(data_path)
    if os.path.exists(model_path):
        shutil.rmtree(model_path)

if __name__ == "__main__":
    test_training_loop()
