import os
import sys
import time
import asyncio
import signal
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from state_manager import StateManager
from chunker import AudioChunker
from processor import GeminiProcessor

# Configure logging to stdout for Electron to capture
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)

class AudioFlowEngine:
    def __init__(self, config_path, state_path, api_key):
        self.state_manager = StateManager(config_path, state_path)
        self.chunker = AudioChunker()
        self.processor = GeminiProcessor(api_key)
        self.semaphore = asyncio.Semaphore(5)
        self.loop = asyncio.new_event_loop()
        self.observer = None
        self.running = True

    def start(self):
        """Starts the engine: loads state, resumes jobs, starts watchdog."""
        logging.info("Starting AudioFlow Engine...")
        
        # Load config to get watched folders
        config = self.state_manager.load_config()
        watched_folders = config.get("watched_folders", [])
        
        # Start Watchdog
        self.observer = Observer()
        handler = NewFileHandler(self)
        
        for folder in watched_folders:
            if os.path.isdir(folder):
                logging.info(f"Watching folder: {folder}")
                self.observer.schedule(handler, folder, recursive=True)
                
                # Startup Scan (Recursive)
                logging.info(f"Performing startup scan for {folder}...")
                for root, dirs, files in os.walk(folder):
                    if "Transcriptions" in root: continue
                    for file in files:
                        if file.lower().endswith('.mp3') or file.lower().endswith('.m4a'):
                            self.handle_new_file(os.path.join(root, file))

            else:
                logging.warning(f"Watched folder not found: {folder}")
                
        self.observer.start()

        # Resume incomplete jobs
        self.resume_jobs()

        # Run asyncio loop
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            self.shutdown()

    def shutdown(self):
        logging.info("Shutting down engine...")
        self.running = False
        if self.observer:
            self.observer.stop()
            self.observer.join()
        self.loop.stop()
        sys.exit(0)

    def resume_jobs(self):
        state = self.state_manager.load_state()
        active_jobs = state.get("active_jobs", {})
        
        for job_id, job_data in active_jobs.items():
            if job_data["status"] == "processing":
                logging.info(f"Resuming job: {job_id}")
                asyncio.run_coroutine_threadsafe(self.process_job(job_id), self.loop)

    def handle_new_file(self, file_path):
        """Called by watchdog when a new file is detected."""
        # Check if already processed
        if self.state_manager.is_file_processed(file_path):
             # logging.info(f"Skipping already processed file: {os.path.basename(file_path)}")
             return

        # Check against modes
        config = self.state_manager.load_config()
        filename = os.path.basename(file_path)
        
        matched_mode = None
        for mode in config.get("modes", []):
            keywords = mode.get("trigger_keywords", [])
            if any(k.lower() in filename.lower() for k in keywords):
                matched_mode = mode
                break
        
        if matched_mode:
            logging.info(f"File matches mode '{matched_mode['name']}': {filename}")
            
            # Create Job ID (hash of path + timestamp or similar, simple for now)
            job_id = f"job_{int(time.time())}_{os.path.basename(filename)}"
            
            # Init Job State
            logging.info(f"Initializing job state for {job_id}...")
            self.state_manager.update_job(job_id, {
                "filepath": file_path,
                "mode_id": matched_mode["id"],
                "status": "processing",
                "completed_steps": [],
                "pending_steps": [s["id"] for s in matched_mode["steps"]],
                "temp_data": {}
            })
            logging.info(f"Job state initialized for {job_id}. Scheduling processing...")
            
            # Schedule processing
            asyncio.run_coroutine_threadsafe(self.process_job(job_id), self.loop)
        else:
            logging.info(f"Ignored file (no mode match): {filename}")

    async def process_job(self, job_id):
        logging.info(f"Starting process_job for {job_id}")
        job = self.state_manager.get_job(job_id)
        if not job:
            logging.error(f"Job {job_id} not found in state during processing start.")
            return

        config = self.state_manager.load_config()
        # Find mode definition again using ID
        mode_def = next((m for m in config["modes"] if m["id"] == job["mode_id"]), None)
        if not mode_def:
            logging.error(f"Mode definition not found for job {job_id}")
            self.state_manager.update_job(job_id, {"status": "error", "error": "Mode not found"})
            return

        # Pre-process: Chunks/Compress
        # Ideally check if already chunked in temp_data if resuming
        chunks = job["temp_data"].get("chunks")
        output_dir = os.path.join(os.path.dirname(job["filepath"]), "Transcriptions")
        
        if not chunks:
            try:
                logging.info(f"Starting chunking for {job_id}...")
                # Run sync chunker in executor
                chunks = await self.loop.run_in_executor(None, self.chunker.process_audio, job["filepath"], output_dir)
                logging.info(f"Chunking completed for {job_id}: {chunks}")
                self.state_manager.update_job(job_id, {"temp_data": {**job["temp_data"], "chunks": chunks}})
            except Exception as e:
                logging.error(f"Chunking failed for {job_id}: {e}", exc_info=True)
                self.state_manager.update_job(job_id, {"status": "error", "error": str(e)})
                return

        # Execute steps
        steps = mode_def.get("steps", [])
        action_definitions = config.get("action_definitions", {})
        
        for step in steps:
            step_id = step["id"]
            if step_id in job["completed_steps"]:
                continue
                
            action_def_id = step["action_def_id"]
            action_def = action_definitions.get(action_def_id)
            
            if not action_def:
                logging.error(f"Action definition '{action_def_id}' not found for step {step_id}")
                self.state_manager.update_job(job_id, {"status": "error", "error": f"Action def {action_def_id} missing"})
                return

            logging.info(f"Executing step {step_id} (Action: {action_def['name']}) for job {job_id}")
            
            try:
                # Resolve dependency input
                input_text = ""
                dependency_id = step.get("dependency")
                if dependency_id:
                    # Look up output of the dependent step
                    # The dependent step output is stored in temp_data with key "{dependency_id}_output"
                    input_text = job["temp_data"].get(f"{dependency_id}_output", "")
                    if not input_text:
                         logging.warning(f"Dependency {dependency_id} yielded no output for step {step_id}")

                result = await self.execute_action(action_def, job, chunks, output_dir, input_text)
                
                # Update State
                completed = job["completed_steps"] + [step_id]
                pending = [s for s in job["pending_steps"] if s != step_id]
                
                # Store result in temp_data with step_id as key for dependency reference
                temp_updates = {f"{step_id}_output": result}
                
                self.state_manager.update_job(job_id, {
                    "completed_steps": completed,
                    "pending_steps": pending,
                    "temp_data": {**job["temp_data"], **temp_updates}
                })
                
                # Refresh job data for local loop
                job = self.state_manager.get_job(job_id)

            except Exception as e:
                logging.error(f"Step {step_id} failed: {e}")
                self.state_manager.update_job(job_id, {"status": "error", "error": str(e)})
                return

        logging.info(f"Job {job_id} completed successfully.")
        self.state_manager.update_job(job_id, {"status": "completed"})
        self.state_manager.mark_file_processed(job["filepath"])

    async def execute_action(self, action_def, job, audio_chunks, output_dir, input_text=""):
        """Executes a single action."""
        action_type = action_def["type"]
        model = action_def.get("model", "gemini-1.5-flash") # Default
        
        if action_type == "transcription":
            # Parallel Transcription
            tasks = []
            for chunk_path in audio_chunks:
                sys_prompt = action_def.get("prompt") # In new schema, 'prompt' holds the instruction
                # Ensure we use semantic semaphore for concurrency limit
                tasks.append(self.transcribe_chunk_throttled(chunk_path, model, sys_prompt))
            
            results = await asyncio.gather(*tasks)
            
            # Consolidate
            full_text = ""
            for i, text in enumerate(results):
                # Calculate offset
                # We need know the duration of previous chunks to calculate offset.
                # Simplified: reusing main.py logic requires known durations. 
                # For now, just concatenating. Ideally chunker returns metadata (start_time).
                # To Fix: Chunker should return tuples (path, start_ms).
                # Assuming simple concat for now as chunker handles split logic, but timestamp adjustment is tricky without offsets.
                # Re-reading main.py: main.py calculates offset based on i * CHUNK_LENGTH.
                # I will replicate simple offset assumption here based on chunker constant.
                offset_sec = i * (50 * 60) # 50 mins in seconds
                adjusted_text = self.processor.adjust_timestamps(text, offset_sec)
                full_text += adjusted_text + "\n"

            # Save to file
            filename = f"{os.path.basename(job['filepath'])}_Transcription.txt"
            out_path = os.path.join(output_dir, filename)
            with open(out_path, 'w') as f:
                f.write(full_text)
            return full_text

        # Generic Text Generation (Summary, LinkedIn, Sales, Description, etc.)
        # If type isn't transcription, treat it as text generation
        else:
             prompt_template = action_def.get("prompt", "")
             # Render simple prompt or Jinja
             # We can pass input_text as variable 'context' or just append it
             final_prompt = f"{prompt_template}\n\nContext:\n{input_text}"
             
             # Call Gemini
             async with self.semaphore:
                 # No file upload needed if text-to-text, usually.
                 # But processor.generate_content expects contents list.
                 response_text = await self.loop.run_in_executor(
                     None, 
                     self.processor.generate_content, 
                     model, 
                     [final_prompt]
                 )
             
             # Save
             suffix = action_def.get("id", action_type).replace("_", "") # Use ID (e.g. 'linkedin') as suffix
             filename = f"{os.path.basename(job['filepath'])}_{suffix}.txt"
             out_path = os.path.join(output_dir, filename)
             with open(out_path, 'w') as f:
                 f.write(response_text)
             return response_text
             
        return ""

    async def transcribe_chunk_throttled(self, chunk_path, model, system_instruction):
        async with self.semaphore:
             # Upload file
             remote_file = await self.loop.run_in_executor(None, self.processor.upload_file, chunk_path)
             # Generate
             text = await self.loop.run_in_executor(
                 None, 
                 self.processor.generate_content, 
                 model, 
                 [system_instruction, remote_file] if system_instruction else [remote_file]
             )
             return text

class NewFileHandler(FileSystemEventHandler):
    def __init__(self, engine):
        self.engine = engine
        self._stable_timers = {}

    def on_created(self, event):
        if event.is_directory or not event.src_path.lower().endswith('.mp3'): # Just mp3/m4a support
             # Expand extensions as needed
             if not (event.src_path.lower().endswith('.mp3') or event.src_path.lower().endswith('.m4a')):
                 return
        
        # Ignore files in Transcriptions folder to avoid loops with chunks/outputs
        if "Transcriptions" in event.src_path:
             return

        logging.info(f"Detected new file: {event.src_path}")
        # Debounce/Check stability logic
        # For simplicity in this step, assume stable or use a delay.
        # Impl: Wait 2 seconds then check size stability.
        # Since this is a callback, we shouldn't block. We can spawn a thread or task in engine.
        threading_timer = threading.Timer(2.0, self.check_stability, args=[event.src_path])
        threading_timer.start()

    def check_stability(self, path):
        # Initial check
        try:
            size1 = os.path.getsize(path)
            time.sleep(1)
            size2 = os.path.getsize(path)
            if size1 == size2 and size1 > 0:
                 self.engine.handle_new_file(path)
            else:
                 # Retry
                 threading.Timer(2.0, self.check_stability, args=[path]).start()
        except FileNotFoundError:
            pass

import threading

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--state", required=True)
    args = parser.parse_args()
    
    # Load API Key from env
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logging.error("GOOGLE_API_KEY not found in env.")
        sys.exit(1)

    engine = AudioFlowEngine(args.config, args.state, api_key)
    
    # Signal handling
    def signal_handler(sig, frame):
        engine.shutdown()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    engine.start()
