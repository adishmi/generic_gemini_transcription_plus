import os
import time
import subprocess
import logging
from dotenv import load_dotenv

load_dotenv()

# Configuration
WATCH_CONFIGS = [
    {
        "directory": "/Users/adishmitanka/Content/LongForm/נקודה למחשבה",
        "filter_word": "final",
        "mode": "PODCAST"
    },
    {
        "directory": "/Users/adishmitanka/Content/LongForm/Workshops",
        "filter_word": "workshop",
        "mode": "WORKSHOP"
    }
]

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
    # If WORKSHOP mode -> ["Adi", "Speaker 1", "Speaker 2"]
    # If "Solo" in filename -> ["Adi"]
    # Else -> [First Word of Filename, "Adi"]
    
    if mode == "WORKSHOP":
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

def process_file(filepath, mode):
    filename = os.path.basename(filepath)
    logging.info(f"Processing new file ({mode}): {filename}")
    
    speakers = get_speakers(filename, mode)
    logging.info(f"Identified speakers: {speakers}")
    
    # Check if it's a draft
    is_draft = "draft" in filename.lower()
    
    # Construct command
    # python main.py --file "path/to/file" --mode PODCAST --speakers "Speaker1" "Speaker2"
    
    # Use the specific python interpreter that has the dependencies installed
    python_path = "/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"
    cmd = [
        python_path, "main.py",
        "--file", filepath,
        "--mode", mode,
        "--speakers"
    ] + speakers
    
    if is_draft:
        cmd.append("--transcribe-only")
        logging.info("Detected DRAFT file - setting transcribe-only mode")
    
    logging.info(f"Running command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        logging.info(f"Successfully processed {filename}")
        save_processed_file(filename)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error processing {filename}: {e}")

def monitor():
    processed_files = load_processed_files()
    
    # Validation
    valid_configs = []
    for config in WATCH_CONFIGS:
        if os.path.exists(config["directory"]):
            logging.info(f"Monitoring folder: {config['directory']} (Mode: {config['mode']}, Filter: {config['filter_word']})")
            valid_configs.append(config)
        else:
            logging.error(f"Directory {config['directory']} does not exist. Skipping.")
    
    if not valid_configs:
        logging.error("No valid watch directories found. Exiting.")
        return

    logging.info("Monitoring for new files...")

    while True:
        try:
            for config in valid_configs:
                for root, dirs, files in os.walk(config["directory"]):
                    for file in files:
                        filepath = os.path.join(root, file)
                        ext = os.path.splitext(file)[1].lower()
                        
                        # Add 'draft' to the filter check
                        is_target = config["filter_word"] in file.lower() or "draft" in file.lower()
                        
                        if is_target and ext in [".mp3", ".m4a", ".wav", ".flac"]:
                            if file not in processed_files:
                                if os.path.getsize(filepath) == 0:
                                    logging.warning(f"File {file} is empty. Skipping.")
                                    continue

                                process_file(filepath, config["mode"])
                                processed_files.add(file)
            
            time.sleep(POLL_INTERVAL)
            
        except Exception as e:
            logging.error(f"Error in monitor loop: {e}")
            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    monitor()
