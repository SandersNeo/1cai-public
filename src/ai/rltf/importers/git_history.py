import os
import subprocess
import json
import uuid
from datetime import datetime
from typing import List, Optional
from src.ai.rltf.schemas import Trajectory, State, Action, Reward

class GitHistoryImporter:
    """
    Imports legacy Git history as RLTF Trajectories (Cold Start).
    
    Converts:
    - State: File content BEFORE commit.
    - Action: Commit Message + Diff.
    - Reward: +1.0 (assuming merged code is 'good').
    """
    
    def __init__(self, repo_path: str, output_path: str = "data/rltf/legacy_trajectories.jsonl"):
        self.repo_path = repo_path
        self.output_path = output_path
        self._ensure_storage()

    def _ensure_storage(self):
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

    def _run_git(self, args: List[str]) -> str:
        """Runs a git command in the repo directory."""
        result = subprocess.run(
            ["git"] + args, 
            cwd=self.repo_path, 
            capture_output=True, 
            text=True, 
            encoding='utf-8',
            errors='replace'
        )
        if result.returncode != 0:
            raise Exception(f"Git command failed: {result.stderr}")
        return result.stdout.strip()

    def import_history(self, limit: int = 100):
        """Iterates through git log and generates trajectories."""
        print(f"Importing last {limit} commits from {self.repo_path}...")
        
        # Get commit hashes
        log_output = self._run_git(["log", f"-n {limit}", "--pretty=format:%H"])
        commits = log_output.split('\n')
        
        count = 0
        for commit_hash in commits:
            if not commit_hash: continue
            try:
                trajectory = self._process_commit(commit_hash)
                if trajectory:
                    self._save_trajectory(trajectory)
                    count += 1
            except Exception as e:
                print(f"Skipping commit {commit_hash}: {e}")
                
        print(f"Successfully imported {count} trajectories to {self.output_path}")

    def _process_commit(self, commit_hash: str) -> Optional[Trajectory]:
        # 1. Get Commit Info (Action)
        msg = self._run_git(["show", "-s", "--format=%s", commit_hash])
        
        # 2. Get Diff (Action Detail)
        diff = self._run_git(["show", commit_hash])
        
        # 3. Get Changed Files
        files_changed = self._run_git(["show", "--name-only", "--format=", commit_hash]).split('\n')
        files_changed = [f for f in files_changed if f.strip()]
        
        if not files_changed:
            return None

        # 4. Construct State (Context)
        # For simplicity, we just list the files changed as the context summary.
        # In a deep import, we would read the file content from the PARENT commit (commit_hash^)
        context_summary = f"Editing files: {', '.join(files_changed[:3])}..."
        
        # 5. Create Objects
        state = State(
            context_summary=context_summary,
            open_files=files_changed,
            last_error=None
        )
        
        action = Action(
            tool_name="git_commit",
            tool_input={"message": msg, "diff_size": len(diff)},
            timestamp=datetime.now() # Ideally parse commit time
        )
        
        # 6. Assign Reward (Heuristic)
        # Default to +1.0 for existing history
        reward = Reward(
            source="git_history",
            value=1.0,
            message="Legacy commit assumed valid"
        )
        
        return Trajectory(
            session_id=f"git-{commit_hash}",
            state=state,
            action=action,
            reward=reward
        )

    def _save_trajectory(self, trajectory: Trajectory):
        with open(self.output_path, "a", encoding="utf-8") as f:
            f.write(trajectory.json() + "\n")

if __name__ == "__main__":
    # Example usage
    importer = GitHistoryImporter(repo_path=".")
    importer.import_history(limit=10)
