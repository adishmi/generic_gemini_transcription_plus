import json
import os
import threading
import logging
from typing import Dict, Any, Optional

class StateManager:
    def __init__(self, config_path: str, state_path: str):
        self.config_path = config_path
        self.state_path = state_path
        self.lock = threading.Lock()
        self._ensure_files_exist()

    def _ensure_files_exist(self):
        if not os.path.exists(self.state_path):
            with open(self.state_path, 'w') as f:
                json.dump({"active_jobs": {}, "processed_files": []}, f, indent=2)
        
        # Config should ideally exist, but if not, create empty
        if not os.path.exists(self.config_path):
             with open(self.config_path, 'w') as f:
                json.dump({"watched_folders": [], "modes": []}, f, indent=2)

    def load_config(self) -> Dict[str, Any]:
        with self.lock:
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Failed to load config: {e}")
                return {"watched_folders": [], "modes": []}

    def load_state(self) -> Dict[str, Any]:
        with self.lock:
            try:
                with open(self.state_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Failed to load state: {e}")
                return {"active_jobs": {}, "processed_files": []}

    def save_state(self, state: Dict[str, Any]):
        with self.lock:
            try:
                # Write to temp file then rename for atomic write
                temp_path = self.state_path + ".tmp"
                with open(temp_path, 'w') as f:
                    json.dump(state, f, indent=2)
                os.replace(temp_path, self.state_path)
                logging.info(f"State saved successfully to {self.state_path}")
            except Exception as e:
                logging.error(f"Failed to save state: {e}")

    def update_job(self, job_id: str, updates: Dict[str, Any]):
        """Updates specific fields of a job in the state."""
        state = self.load_state()
        if job_id not in state["active_jobs"]:
             # If job doesn't exist, create it (merging with defaults if needed, but usually caller inits)
             state["active_jobs"][job_id] = {}
        
        # Merge updates
        state["active_jobs"][job_id].update(updates)
        self.save_state(state)

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        state = self.load_state()
        return state["active_jobs"].get(job_id)

    def remove_job(self, job_id: str):
        state = self.load_state()
        if job_id in state["active_jobs"]:
            del state["active_jobs"][job_id]
            self.save_state(state)

    def mark_file_processed(self, file_path: str):
        """Adds a file path to the processed_files list."""
        state = self.load_state()
        if "processed_files" not in state:
            state["processed_files"] = []
        
        if file_path not in state["processed_files"]:
            state["processed_files"].append(file_path)
            self.save_state(state)

    def is_file_processed(self, file_path: str) -> bool:
        """Checks if a file path is in the processed_files list."""
        state = self.load_state()
        return file_path in state.get("processed_files", [])
