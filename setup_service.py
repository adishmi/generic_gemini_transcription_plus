import os
import sys
import argparse
import subprocess

TEMPLATE_FILE = "service.plist.template"
PLIST_NAME = "com.adishmitanka.podcastmonitor.plist"
LOG_FILE = "monitor.log"

def get_paths():
    """Determine the necessary absolute paths."""
    # Current working directory (where the script is run from)
    cwd = os.getcwd()
    
    # Path to the python interpreter currently running this script
    python_path = sys.executable
    
    # Path to the main monitor script
    script_path = os.path.join(cwd, "monitor.py")
    
    # Path to the log file
    log_path = os.path.join(cwd, LOG_FILE)
    
    return cwd, python_path, script_path, log_path

def generate_plist_content(cwd, python_path, script_path, log_path):
    """Read template and replace placeholders."""
    if not os.path.exists(TEMPLATE_FILE):
        print(f"Error: {TEMPLATE_FILE} not found.")
        sys.exit(1)
        
    with open(TEMPLATE_FILE, "r") as f:
        content = f.read()
        
    content = content.replace("{{PYTHON_PATH}}", python_path)
    content = content.replace("{{SCRIPT_PATH}}", script_path)
    content = content.replace("{{WORKING_DIRECTORY}}", cwd)
    content = content.replace("{{LOG_PATH}}", log_path)
    
    return content

def install_service(plist_content):
    """Write plist to LaunchAgents and load it."""
    
    # 1. Write the local plist file (for reference/backup)
    with open(PLIST_NAME, "w") as f:
        f.write(plist_content)
    print(f"Generated local file: {PLIST_NAME}")
    
    # 2. Define target path in ~/Library/LaunchAgents
    home = os.path.expanduser("~")
    launch_agents_dir = os.path.join(home, "Library", "LaunchAgents")
    target_path = os.path.join(launch_agents_dir, PLIST_NAME)
    
    if not os.path.exists(launch_agents_dir):
        os.makedirs(launch_agents_dir)
        
    # 3. Write/Overwrite the file in LaunchAgents
    with open(target_path, "w") as f:
        f.write(plist_content)
    print(f"Installed to: {target_path}")
    
    # 4. Reload the service using launchctl
    # Unload first (ignore errors if it wasn't running)
    subprocess.run(["launchctl", "unload", target_path], stderr=subprocess.DEVNULL)
    
    # Load it
    try:
        subprocess.run(["launchctl", "load", target_path], check=True)
        print("Service loaded successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error loading service: {e}")

def main():
    parser = argparse.ArgumentParser(description="Setup the Podcast Monitor Service")
    parser.add_argument("--dry-run", action="store_true", help="Print generated plist to stdout without writing files")
    parser.add_argument("--install", action="store_true", help="Install and start the service")
    args = parser.parse_args()
    
    cwd, python_path, script_path, log_path = get_paths()
    
    print(f"Configuration detected:")
    print(f"  Working Directory: {cwd}")
    print(f"  Python Interpreter: {python_path}")
    print(f"  Monitor Script: {script_path}")
    print(f"  Log File: {log_path}")
    print("-" * 30)
    
    plist_content = generate_plist_content(cwd, python_path, script_path, log_path)
    
    if args.dry_run:
        print("Generated Plist Content:")
        print(plist_content)
    elif args.install:
        install_service(plist_content)
    else:
        print("No action specified. Use --dry-run or --install")
        print("Writing local plist file only...")
        with open(PLIST_NAME, "w") as f:
            f.write(plist_content)
        print(f"Written to {PLIST_NAME}")

if __name__ == "__main__":
    main()
