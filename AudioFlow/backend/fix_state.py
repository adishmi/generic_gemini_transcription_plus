import json
import os
import sys

state_path = "/Users/adishmitanka/Library/Application Support/audioflow/state.json"
target_filename = "Suf_Code_Test workshop.m4a"

print(f"Loading state from: {state_path}")

if not os.path.exists(state_path):
    print("State file not found!")
    sys.exit(1)

with open(state_path, "r") as f:
    state = json.load(f)

processed_files = state.get("processed_files", [])
print(f"Total processed files: {len(processed_files)}")

found = False
new_processed = []
for p in processed_files:
    if target_filename in p:
        print(f"FOUND target in processed files: {p}")
        found = True
        # Do not add to new_processed (remove it)
    else:
        new_processed.append(p)

if found:
    print("Removing file from processed list and saving...")
    state["processed_files"] = new_processed
    # Also clean strict equal just in case
    
    with open(state_path, "w") as f:
        json.dump(state, f, indent=2)
    print("State updated. Please restart the engine.")
else:
    print("Target file NOT found in processed_files.")
    
# Also check active jobs just in case
for job_id, job in state.get("active_jobs", {}).items():
    if target_filename in job.get("filepath", ""):
        print(f"WARNING: File found in active job: {job_id} with status: {job.get('status')}")
