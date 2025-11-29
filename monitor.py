import os
import time
import subprocess
import logging

# Configuration
WATCH_DIRECTORY = "PodcastsFiles"
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

def get_speakers(filename):
    # Logic:
    # If "Solo" in filename -> ["Adi"]
    # Else -> [First Word of Filename, "Adi"]
    
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

def process_file(filepath):
    filename = os.path.basename(filepath)
    logging.info(f"Processing new file: {filename}")
    
    speakers = get_speakers(filename)
    logging.info(f"Identified speakers: {speakers}")
    
    # Construct command
    # python main.py --file "path/to/file" --mode PODCAST --speakers "Speaker1" "Speaker2"
    
    import sys
    cmd = [
        sys.executable, "main.py",
        "--file", filepath,
        "--mode", "PODCAST",
        "--speakers"
    ] + speakers
    
    logging.info(f"Running command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        logging.info(f"Successfully processed {filename}")
        save_processed_file(filename)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error processing {filename}: {e}")

def monitor():
    logging.info(f"Starting monitor on directory: {os.path.abspath(WATCH_DIRECTORY)}")
    processed_files = load_processed_files()
    
    # Ensure watch directory exists
    if not os.path.exists(WATCH_DIRECTORY):
        logging.error(f"Directory {WATCH_DIRECTORY} does not exist.")
        return

    while True:
        try:
            # List all files in directory
            files = os.listdir(WATCH_DIRECTORY)
            
            for file in files:
                filepath = os.path.join(WATCH_DIRECTORY, file)
                
                # Check if it's a file and not a directory
                if not os.path.isfile(filepath):
                    continue
                
                # Check for "Final" (case-insensitive) and mp3 extension (optional, but good practice)
                if "final" in file.lower() and file.lower().endswith(".mp3"):
                    if file not in processed_files:
                        # Check if file is not empty
                        if os.path.getsize(filepath) == 0:
                            logging.warning(f"File {filename} is empty. Skipping.")
                            continue

                        # Double check if file is fully written (simple check: size stable?)
                        # For now, we assume if it's there it's ready, or we can wait a bit.
                        # A simple way is to just try processing.
                        
                        process_file(filepath)
                        processed_files.add(file)
            
            time.sleep(POLL_INTERVAL)
            
        except Exception as e:
            logging.error(f"Error in monitor loop: {e}")
            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    monitor()
