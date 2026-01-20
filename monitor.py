import os
import time
import subprocess
import logging
import json
from dotenv import load_dotenv

load_dotenv()

# Constants
CONFIG_FILE = "config.json"
PROCESSED_LOG = "processed_files.log"
POLL_INTERVAL = 10  # Seconds

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("monitor.log")
    ]
)

def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"Configuration file {CONFIG_FILE} not found.")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing {CONFIG_FILE}: {e}")
        return None

def load_processed_files():
    if not os.path.exists(PROCESSED_LOG):
        return set()
    with open(PROCESSED_LOG, "r") as f:
        return set(line.strip() for line in f)

def save_processed_file(filename):
    with open(PROCESSED_LOG, "a") as f:
        f.write(filename + "\n")

def get_speakers(filename, mode):
    # Logic:
    # If WORKSHOP matches mode -> ["Adi", "Speaker 1", "Speaker 2"]
    # If "Solo" in filename -> ["Adi"]
    # Else -> [First Word of Filename, "Adi"]
    
    if mode.upper() == "WORKSHOP":
        return ["Adi", "Speaker 1", "Speaker 2"]
        
    base_name = os.path.basename(filename)
    name_without_ext = os.path.splitext(base_name)[0]
    
    if "Solo" in name_without_ext:
        return ["Adi"]
    else:
        # Extract first word
        # Assuming filename like "GuestName_Final.mp3" or "Guest Name Final.mp3"
        # We'll split by underscore or space and take the first part
        first_word = name_without_ext.replace("_", " ").split(" ")[0]
        return [first_word, "Adi"]

def determine_mode_and_actions(filename, config_modes):
    filename_lower = filename.lower()
    
    # 1. Check for specific keywords in filename
    for mode_name, mode_config in config_modes.items():
        for keyword in mode_config.get("keywords", []):
            if keyword.lower() in filename_lower:
                return mode_name, mode_config.get("actions", [])
    
    return None, []

def process_file(filepath, mode, actions, python_interpreter):
    filename = os.path.basename(filepath)
    logging.info(f"Processing new file: {filename} | Mode: {mode} | Actions: {actions}")
    
    speakers = get_speakers(filename, mode)
    logging.info(f"Identified speakers: {speakers}")
    
    # Construct command
    # python main.py --file "path/to/file" --mode PODCAST --speakers "Speaker1" "Speaker2" --actions action1 action2
    
    cmd = [
        python_interpreter, "main.py",
        "--file", filepath,
        "--mode", mode,
        "--speakers"
    ] + speakers + ["--actions"] + actions
    
    logging.info(f"Running command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        logging.info(f"Successfully processed {filename}")
        save_processed_file(filename)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error processing {filename}: {e}")

def monitor():
    logging.info("Monitoring for new files...")

    while True:
        try:
            config = load_config()
            if not config:
                time.sleep(POLL_INTERVAL)
                continue

            processed_files = load_processed_files()
            python_interpreter = config.get("general", {}).get("python_interpreter", "python3")
            
            # Validation of watch paths
            watch_paths = []
            for entry in config.get("watch_paths", []):
                directory = entry.get("path")
                if os.path.exists(directory):
                     watch_paths.append(entry)
                # We skip noisy logging here since it runs every loop
            
            if not watch_paths:
                logging.error("No valid watch directories found.")
                time.sleep(POLL_INTERVAL)
                continue
                
            for entry in watch_paths:
                directory = entry["path"]
                
                for root, dirs, files in os.walk(directory):
                    # 1. Prevent recursion: Do not walk into Transcriptions folders
                    if "Transcriptions" in dirs:
                        dirs.remove("Transcriptions")

                    for file in files:
                        filepath = os.path.join(root, file)
                        ext = os.path.splitext(file)[1].lower()
                        
                        # 2. Skip generated intermediate files if they sit in the root for some reason
                        if "_compressed" in file or "_part" in file:
                            continue

                        if ext in [".mp3", ".m4a", ".wav", ".flac"]:
                             # Determine if we should process it
                             mode, actions = determine_mode_and_actions(file, config.get("modes", {}))
                             
                             if mode and file not in processed_files and os.path.getsize(filepath) > 0:
                                 # Found a matching mode and file is not processed
                                 process_file(filepath, mode, actions, python_interpreter)
                                 # Refresh processed files for the next inner file check if needed
                                 # but processed_files.add(file) is enough for the current loop
                                 processed_files.add(file)
            
            time.sleep(POLL_INTERVAL)
            
        except Exception as e:
            logging.error(f"Error in monitor loop: {e}")
            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    monitor()
