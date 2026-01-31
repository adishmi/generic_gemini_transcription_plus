
import os
import sys
import logging
import json
from state_manager import StateManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)

def mark_current_files_as_processed():
    # Paths are usually passed relative to backend dir, or absolute.
    # We assume this script runs in backend/
    
    # Needs settings path and state path. Ideally we get them from args or typical location.
    # For this one-off script, we'll try to find audioflow settings relative to user home.
    
    user_home = os.path.expanduser("~")
    config_path = os.path.join(user_home, "Library/Application Support/audioflow/settings.json")
    state_path = os.path.join(user_home, "Library/Application Support/audioflow/state.json")
    
    if not os.path.exists(config_path) or not os.path.exists(state_path):
        print(f"Error: Config or State file not found.\nConfig: {config_path}\nState: {state_path}")
        return

    # Load Config
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Load State
    if os.path.exists(state_path):
        with open(state_path, 'r') as f:
            state = json.load(f)
    else:
        state = {"active_jobs": {}, "processed_files": []}
    
    if "processed_files" not in state:
        state["processed_files"] = []
        
    watched_folders = config.get("watched_folders", [])
    processed_set = set(state["processed_files"])
    
    count = 0
    for folder in watched_folders:
        if not os.path.isdir(folder):
            logging.warning(f"Folder not found: {folder}")
            continue
            
        logging.info(f"Scanning {folder}...")
        for root, dirs, files in os.walk(folder):
            # Skip Transcriptions folder
            if "Transcriptions" in root:
                continue
                
            for file in files:
                if file.lower().endswith('.mp3') or file.lower().endswith('.m4a'):
                    full_path = os.path.join(root, file)
                    if full_path not in processed_set:
                        processed_set.add(full_path)
                        logging.info(f"Marked as processed: {full_path}")
                        count += 1
                    else:
                        logging.debug(f"Already processed: {full_path}")

    # Write back
    state["processed_files"] = list(processed_set)
    with open(state_path, 'w') as f:
        json.dump(state, f, indent=2)

    logging.info(f"Done. Marked {count} existing files as processed.")

if __name__ == "__main__":
    mark_current_files_as_processed()
