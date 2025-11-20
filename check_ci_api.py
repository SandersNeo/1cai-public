import os
import sys
import json
import time
import urllib.request
import urllib.error

# Configuration
REPO_OWNER = "DmitrL-dev"
REPO_NAME = "1cai-public" 
GITHUB_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"

def get_json(url, token):
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Python-CI-Checker"
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                return json.loads(response.read().decode())
            else:
                print(f"Error fetching {url}: HTTP {response.status}")
                return None
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def get_workflow_runs(token):
    return get_json(f"{GITHUB_API_URL}/actions/runs?per_page=5", token)

def get_jobs(run_id, token):
    return get_json(f"{GITHUB_API_URL}/actions/runs/{run_id}/jobs", token)

def main():
    token = os.getenv("GH_TOKEN")
    if not token:
        if len(sys.argv) > 1:
            token = sys.argv[1]
        else:
            print("Error: GH_TOKEN required.")
            sys.exit(1)

    print(f"Checking CI status for {REPO_OWNER}/{REPO_NAME}...")
    
    runs = get_workflow_runs(token)
    if not runs or "workflow_runs" not in runs:
        sys.exit(1)
        
    print(f"\nAnalyzing Failures:")
    print("=" * 60)
    
    # Process only the most recent runs (top 3)
    for run in runs["workflow_runs"][:3]:
        if run["conclusion"] == "failure":
            print(f"Run: {run['name']} (ID: {run['id']})")
            
            jobs = get_jobs(run["id"], token)
            if jobs and "jobs" in jobs:
                for job in jobs["jobs"]:
                    if job["conclusion"] == "failure":
                        print(f"  Job: {job['name']} (ID: {job['id']})")
                        for step in job["steps"]:
                            # Print all steps for failed job to see where it stopped
                            icon = "X" if step["conclusion"] == "failure" else "v"
                            print(f"    [{icon}] {step['name']} ({step['conclusion']})")
            print("-" * 60)

if __name__ == "__main__":
    main()
