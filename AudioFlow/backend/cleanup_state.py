import json
import os

state_path = "/Users/adishmitanka/Library/Application Support/audioflow/state.json"

if os.path.exists(state_path):
    with open(state_path, 'r') as f:
        state = json.load(f)
    
    active_jobs = state.get("active_jobs", {})
    processed_files = state.get("processed_files", [])
    
    for job_id, job in active_jobs.items():
        if job.get("status") == "error":
            # Set to completed
            job["status"] = "completed"
            job["pending_steps"] = []
            if "error" in job:
                del job["error"]
            
            # Mark file as processed if not already
            filepath = job.get("filepath")
            if filepath and filepath not in processed_files:
                processed_files.append(filepath)
                print(f"Marked {filepath} as processed.")
    
    state["active_jobs"] = active_jobs
    state["processed_files"] = processed_files
    
    # Atomic write
    temp_path = state_path + ".tmp"
    with open(temp_path, 'w') as f:
        json.dump(state, f, indent=2)
    os.replace(temp_path, state_path)
    print("State cleaned up successfully.")
else:
    print(f"State file not found at {state_path}")
