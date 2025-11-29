import os
import time
import subprocess
import logging

# Configuration
WATCH_DIRECTORY = os.environ.get("WATCH_DIRECTORY", "PodcastsFiles")
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

    # Initial scan to mark existing files as processed (to avoid processing old files)
    logging.info("Performing initial scan to ignore existing files...")
    for root, dirs, files in os.walk(WATCH_DIRECTORY):
        for file in files:
            if "final" in file.lower() and file.lower().endswith(".mp3"):
                if file not in processed_files:
                    logging.info(f"Marking existing file as processed: {file}")
                    processed_files.add(file)
                    save_processed_file(file) # Optional: save to log so we remember them across restarts

    logging.info("Initial scan complete. Monitoring for new files...")

    while True:
        try:
            # Recursive scan using os.walk
            for root, dirs, files in os.walk(WATCH_DIRECTORY):
                for file in files:
                    filepath = os.path.join(root, file)
                    
                    # Check for "Final" (case-insensitive) and mp3 extension
                    if "final" in file.lower() and file.lower().endswith(".mp3"):
                        if file not in processed_files:
                            # Check if file is not empty
                            if os.path.getsize(filepath) == 0:
                                logging.warning(f"File {file} is empty. Skipping.")
                                continue

                            # Process the file
                            process_file(filepath)
                            processed_files.add(file)
            
            time.sleep(POLL_INTERVAL)
            
        except Exception as e:
            logging.error(f"Error in monitor loop: {e}")
            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    monitor()
