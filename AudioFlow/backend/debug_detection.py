
import os
import sys
import json
import logging
from state_manager import StateManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)

def test_file_detection(test_file_path):
    # Paths
    user_home = os.path.expanduser("~")
    config_path = os.path.join(user_home, "Library/Application Support/audioflow/settings.json")
    state_path = os.path.join(user_home, "Library/Application Support/audioflow/state.json")
    
    if not os.path.exists(config_path) or not os.path.exists(state_path):
        print("Config or State not found.")
        return

    manager = StateManager(config_path, state_path)

    # 1. Check if processed
    is_processed = manager.is_file_processed(test_file_path)
    print(f"File: {test_file_path}")
    print(f"Is Processed in State? {is_processed}")
    
    if is_processed:
        state = manager.load_state()
        print("Processed Files List sample:")
        for f in state.get("processed_files", [])[-5:]:
            print(f" - {f}")

    # 2. Check Match Mode
    config = manager.load_config()
    filename = os.path.basename(test_file_path)
    
    matched_mode = None
    print(f"Testing filename: '{filename}'")
    for mode in config.get("modes", []):
        keywords = mode.get("trigger_keywords", [])
        print(f"Checking mode '{mode['name']}' keywords: {keywords}")
        if any(k.lower() in filename.lower() for k in keywords):
            matched_mode = mode
            break
            
    if matched_mode:
        print(f"MATCHED MODE: {matched_mode['name']}")
    else:
        print("NO MODE MATCHED.")

if __name__ == "__main__":
    test_path = "/Users/adishmitanka/Content/LongForm/Workshops/שיחות מכירה/Suf - 18.01/Suf_23y_not_relevant_ workshop.m4a"
    test_file_detection(test_path)
