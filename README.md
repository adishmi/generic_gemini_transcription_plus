# Gemini Transcribe - Podcast Automation

This tool automates the process of transcribing audio files using Google Gemini. It can also generate summaries, LinkedIn posts, and episode descriptions.

## Setup

1.  **Clone the repository.**
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    (Note: You might need to set up a virtual environment first. Ensure `config.json` points to the correct python interpreter path for your environment.)
3.  **System Prerequisites (MacOS):**
    This project uses `pydub` to handle audio files, which requires `ffmpeg`.
    ```bash
    brew install ffmpeg
    ```

4.  **Get a Gemini API Key:**
    *   Go to [Google AI Studio](https://aistudio.google.com/app/apikey).
    *   Click "Create API Key".
    *   Copy the key string.

5.  **Environment Variables:**
    Create a `.env` file in the project root:
    ```
    GOOGLE_API_KEY="your_api_key_here"
    ```
    (This file is already in the `.gitignore` to keep your key safe).

## Configuration

The behavior of the monitor is controlled by `config.json`. You can customize:
-   Which folders to watch.
-   What happens when a file is detected (based on keywords).
-   Default behavior for specific folders.

### `watch_paths`
List of directories to monitor.
```json
{
  "path": "/Users/username/Podcasts/MyShow"
}
```
-   `path`: Absolute path to the folder.

### `modes`
Defines the different processing modes. **Files are only processed if their filename contains a keyword.**
```json
{
  "Podcast": {
    "keywords": ["final", "podcast"],
    "actions": ["transcribe_podcast", "summary", "linkedin", "description"]
  },
  "Workshop": {
    "keywords": ["workshop"],
    "actions": ["transcribe_workshop"]
  }
}
```
-   `keywords`: If a filename contains one of these words, this mode is enabled.
-   `actions`: List of tasks to perform.
    *   `transcribe_podcast`: Transcribe using the podcast prompt.
    *   `transcribe_workshop`: Transcribe using the workshop prompt.
    *   `summary`: Generate a summary.
    *   `linkedin`: Generate a LinkedIn post.
    *   `description`: Generate an episode description.

### `general`
Settings for the runner.
-   `python_interpreter`: Path to the python executable to use for running the processing script.

## Usage

Run the monitor service:
```bash
python monitor.py
```

It will watch the configured folders. When a supported audio file (`.mp3`, `.m4a`, `.wav`, `.flac`) is added, it will process it based on the configuration.

## Background Service (MacOS)

To run the monitor automatically in the background (even after restarts):

1.  Edit `config.json` to your liking.
2.  Run the setup script:
    ```bash
    python3 setup_service.py --install
    ```
    This will generate a launchd plist file customized for your machine and install it to `~/Library/LaunchAgents/`.

You may change the 'config.json' as you want, and simply "install" again. It will automatically stop the running serivce and restart it with the new configuration.

To uninstall/stop the service:
```bash
launchctl unload ~/Library/LaunchAgents/com.adishmitanka.podcastmonitor.plist
```

