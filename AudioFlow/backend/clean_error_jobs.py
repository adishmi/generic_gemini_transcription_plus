import json
import os

state_path = "/Users/adishmitanka/Library/Application Support/audioflow/state.json"

if not os.path.exists(state_path):
    print("State file not found.")
    exit()

with open(state_path, 'r') as f:
    state = json.load(f)

active_jobs = state.get("active_jobs", {})
jobs_to_remove = []

for job_id, job_data in active_jobs.items():
    if job_data.get("status") == "error":
        print(f"Found error job to remove: {job_id} - {job_data.get('filepath')}")
        jobs_to_remove.append(job_id)

for job_id in jobs_to_remove:
    del active_jobs[job_id]

state["active_jobs"] = active_jobs

with open(state_path, 'w') as f:
    json.dump(state, f, indent=2)

print(f"Removed {len(jobs_to_remove)} error jobs.")
