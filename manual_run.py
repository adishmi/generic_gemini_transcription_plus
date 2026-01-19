import argparse
import os
import sys
import logging
from monitor import process_file

# Setup logging to stdout for manual run
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

def main():
    parser = argparse.ArgumentParser(description="Manually process a podcast audio file.")
    parser.add_argument("file", help="Path to the audio file to process")
    args = parser.parse_args()

    filepath = args.file
    
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found.")
        sys.exit(1)
        
    print(f"Starting manual processing for: {filepath}")
    
    # Reuse the process_file function from monitor.py
    # This handles speaker detection and calling main.py
    try:
        # Default to PODCAST mode for manual runs, monitor's process_file handles the Draft check
        process_file(filepath, mode="PODCAST")
        print("Manual processing completed successfully.")
    except Exception as e:
        print(f"Error during processing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
