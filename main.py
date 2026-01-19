import os
import time
from jinja2 import Template
from google import genai
from pydub import AudioSegment
import math
import re


import argparse
import sys
import json
from dotenv import load_dotenv

load_dotenv()

# --- General Variables ---
# Best practice: store your API key in an environment variable
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    print("Error: GOOGLE_API_KEY environment variable not set.")
    print("Please set it by running 'export GOOGLE_API_KEY=\"YOUR_API_KEY\"' in your terminal.")
    sys.exit(1)

client = genai.Client(api_key=api_key)

# --- Helper Functions ---

def _extract_text_from_response(response):
    """Return best-effort textual content from a GenerateContentResponse."""
    try:
        if getattr(response, "text", None):
            return response.text
        # Fallback: concatenate any text parts from candidates
        parts = []
        for candidate in getattr(response, "candidates", []) or []:
            content = getattr(candidate, "content", None)
            for part in getattr(content, "parts", []) or []:
                text = getattr(part, "text", None)
                if text:
                    parts.append(text)
        return "\n".join(parts)
    except Exception:
        return ""



# Validates that JSON is valid
def load_config():
    try:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load config.json: {e}")
        return {}

CONFIG = load_config()

def get_prompt(key, default_prompt):
    return CONFIG.get("prompts", {}).get(key, default_prompt)

def _transcribe_segment(file_path, speakers_list, model_name, prompt_key="transcription_podcast"):
    """Helper function to transcribe a single audio file."""
    print(f"Uploading file {file_path}...")
    podcast_file = client.files.upload(file=file_path)

    default_prompt_podcast = """Generate a transcript of the episode. The episode is in Hebrew. Include timestamps and identify speakers.
Speakers are: 
{% for speaker in speakers %}- {{ speaker }}{% if not loop.last %}\\n{% endif %}{% endfor %}
eg:
[00:00] Brady: Hello there.
[00:02] Tim: Hi Brady.
It is important to include the correct speaker names. Use the names you identified earlier. If you really don't know the speaker's name, identify them with a letter of the alphabet, eg there may be an unknown speaker 'A' and another unknown speaker 'B'.
If there is music or a short jingle playing, signify like so:
[01:02] [MUSIC] or [01:02] [JINGLE]
If you can identify the name of the music or jingle playing then use that instead, eg:
[01:02] [Firework by Katy Perry] or [01:02] [The Sofa Shop jingle]
If there is some other sound playing try to identify the sound, eg:
[01:02] [Bell ringing]
Each individual caption should be quite short, a few short sentences at most.
Signify the end of the episode with [END].
Don't use any markdown formatting, like bolding or italics.
Only use characters from the Hebrew alphabet, unless you genuinely believe foreign characters are correct.
It is important that you use the correct words and spell everything correctly. Use the context of the podcast to help.
If the hosts discuss something like a movie, book or celebrity, make sure the movie, book, or celebrity name is spelled correctly."""

    default_prompt_workshop = """Generate a transcript of the workshop. The audio is in Hebrew. Include timestamps and identify speakers.
The main speaker is HOST. Identify other speakers as SPEAKER_1, SPEAKER_2, etc.
eg:
[00:00] HOST: Welcome everyone.
[00:05] SPEAKER_1: I have a question.
[00:10] HOST: Go ahead.

If there is music or a short jingle playing, signify like so:
[01:02] [MUSIC] or [01:02] [JINGLE]
If you can identify the name of the music or jingle playing then use that instead, eg:
[01:02] [Firework by Katy Perry] or [01:02] [The Sofa Shop jingle]
If there is some other sound playing try to identify the sound, eg:
[01:02] [Bell ringing]
Each individual caption should be quite short, a few short sentences at most.
Signify the end of the episode with [END].
Don't use any markdown formatting, like bolding or italics.
Only use characters from the Hebrew alphabet, unless you genuinely believe foreign characters are correct.
It is important that you use the correct words and spell everything correctly. Use the context to help.
"""

    if prompt_key == "transcription_workshop":
        default_prompt = default_prompt_workshop
        prompt_str = get_prompt(prompt_key, default_prompt)
        prompt_template = Template(prompt_str)
        prompt = prompt_template.render()
    else:
        # Default fallback to podcast if key unknown, or if explicit podcast key
        default_prompt = default_prompt_podcast
        prompt_str = get_prompt(prompt_key, default_prompt)
        prompt_template = Template(prompt_str)
        prompt = prompt_template.render(speakers=speakers_list)

    print("Generating transcript...")
    response = client.models.generate_content(
        model=model_name,
        contents=[prompt, podcast_file],
    )

    text = _extract_text_from_response(response)
    if not text:
        raise RuntimeError(f"Empty text from model response during transcription of {file_path}.")
    
    return text


def adjust_timestamps(text, offset_seconds):
    """Adjusts timestamps in the text by adding offset_seconds."""
    def replace_match(match):
        timestamp_str = match.group(1)
        parts = list(map(int, timestamp_str.split(':')))
        
        if len(parts) == 2:
            minutes, seconds = parts
            hours = 0
        elif len(parts) == 3:
            hours, minutes, seconds = parts
        else:
            return match.group(0) # Should not happen given regex
            
        total_seconds = hours * 3600 + minutes * 60 + seconds
        total_seconds += offset_seconds
        
        new_hours = int(total_seconds // 3600)
        new_minutes = int((total_seconds % 3600) // 60)
        new_seconds = int(total_seconds % 60)
        
        if new_hours > 0:
            return f"[{new_hours:02d}:{new_minutes:02d}:{new_seconds:02d}]"
        else:
            return f"[{new_minutes:02d}:{new_seconds:02d}]"

    # Regex to match [MM:SS] or [HH:MM:SS]
    # We look for square brackets containing digits and colons
    return re.sub(r'\[(\d{1,2}:\d{2}(?::\d{2})?)\]', replace_match, text)


def transcribe_audio(podcast_path, speakers_list, model_name, output_path, prompt_key="transcription_podcast"):
    """Uploads an audio file and generates a transcript. Handles splitting for long files."""
    print(f"--- Starting Transcription for {podcast_path} (Key: {prompt_key}) ---")
    
    try:
        audio = AudioSegment.from_file(podcast_path)
    except Exception as e:
        print(f"Error loading audio file: {e}")
        raise

    duration_ms = len(audio)
    # Threshold: 50 minutes to be safe (Gemini 2.5 limit is around 1 hour)
    CHUNK_LENGTH_MS = 50 * 60 * 1000 
    
    transcript_parts = []
    
    if duration_ms > 60 * 60 * 1000: # If > 1 hour
        print(f"Audio is {duration_ms/1000/60:.2f} minutes long. Splitting into chunks...")
        
        num_chunks = math.ceil(duration_ms / CHUNK_LENGTH_MS)
        
        for i in range(num_chunks):
            start_ms = i * CHUNK_LENGTH_MS
            end_ms = min((i + 1) * CHUNK_LENGTH_MS, duration_ms)
            
            chunk = audio[start_ms:end_ms]
            # Determine the Transcriptions directory from the output_path
            transcriptions_dir = os.path.dirname(output_path)
            base_filename = os.path.splitext(os.path.basename(podcast_path))[0]
            chunk_filename = os.path.join(transcriptions_dir, f"{base_filename}_part{i+1}.mp3")
            print(f"Exporting chunk {i+1}/{num_chunks}: {chunk_filename}...")
            chunk.export(chunk_filename, format="mp3")
            
            print(f"Transcribing chunk {i+1}/{num_chunks}...")
            part_text = _transcribe_segment(chunk_filename, speakers_list, model_name, prompt_key=prompt_key)
            
            # Adjust timestamps for chunks after the first one
            # (Actually, we can run it for all, with offset 0 for the first one, but let's be explicit)
            offset_seconds = int(start_ms / 1000)
            if offset_seconds > 0:
                print(f"Adjusting timestamps by {offset_seconds} seconds...")
                part_text = adjust_timestamps(part_text, offset_seconds)
            
            transcript_parts.append(part_text)
            
    else:
        print("Audio is under 1 hour. Transcribing directly...")
        text = _transcribe_segment(podcast_path, speakers_list, model_name, prompt_key=prompt_key)
        transcript_parts.append(text)

    full_transcript = "\\n".join(transcript_parts)
    
    # Remove intermediate [END] tags if present, keeping only the last one if desired.
    # For now, we'll just join them. The user can edit if needed.
    
    print(f"RAW RESPONSE (Merged): {full_transcript[:500]}...") # Print start of merged text
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_transcript)

    print(f"Transcription saved to {output_path}")
    return output_path


def generate_linkedin_post(transcript_path, model_name, output_path):
    """Generates a LinkedIn post based on a transcript file."""
    print(f"--- Generating LinkedIn Post from {transcript_path} ---")
    
    transcript_file =  client.files.upload(file=transcript_path)

    default_prompt = """אתה כותב עבור פודקאסט בשם "נקודה למחשבה" בהנחיית אדי שמיטנקה.
הפודקאסט פונה לאנשים רציונליים, סקרנים, בעלי צורך בהתפתחות אישית ובחשיבה עצמאית. רובם מגיעים מעולמות לוגיים או אנליטיים (כמו הייטק, מדעים, הנדסה, עיתונאות), צורכים הרבה ידע (פודקאסטים, ספרים, סרטונים) אך לא תמיד מיישמים, וחווים תחושות של עומס, בלבול או חוסר מימוש.
הם מעריכים גישה פרקטית, שיחה בגובה העיניים, ונרתעים משיח קלישאתי או "רוחני מדי".
מטרת הפודקאסט:
לעורר נקודות מחשבה שמטלטלות בעדינות, פותחות זווית חדשה על נושאים מוכרים, ומניעות את המאזינים לשנות משהו בתפיסה או בהרגלים.
סגנון הכתיבה הרצוי (מבוסס על הפוסטים הקיימים בלינקדאין):
הוק חזק ומסקרן – שורה או שתיים ראשונות שגורמות לקורא לעצור. לרוב שאלה פרובוקטיבית או הצגת תופעה/פרדוקס שמחוברת לנושא הפרק.
שפה ישירה ואותנטית – כתיבה בגובה העיניים, בלי קלישאות מוטיבציה, לפעמים עם נגיעה של הומור.
פירוט תמציתי של הנושא – הצגת הבעיה, הרעיון המרכזי של הפרק, ודוגמאות או שאלות שהפרק עוסק בהן. לא לשקוע בפרטים מיותרים.
פנייה אישית להאזנה – להזמין את הקורא להקשיב, לרוב עם שורה פשוטה (“קישור בתגובה הראשונה” או “להאזנה לפרק >>”).
שמירה על אורך פוסט של כ־150–200 מילים, קריא ומזמין.
הנחיות נוספות:
להשתמש במבנה של פסקאות קצרות עם שורות ריקות ביניהן, כדי שהפוסט יהיה קריא בסריקה מהירה בלינקדאין.
להדגיש את הייחוד של הפרק הזה ביחס לנושא – מה מפתיע, שונה או מאתגר בו.
אפשר להוסיף אימוג’ים נקודתיים כדי לשבור טקסט, אבל לא בצורה מוגזמת (רק אם זה מרגיש טבעי).
המטרה היא שהקורא ירגיש שהפוסט מדבר אליו אישית ושהוא חייב ללחוץ ולהאזין.
המשימה שלך:
קבל את תמליל הפרק המלא, קרא והבין את המסרים המרכזיים, ואז כתוב פוסט לינקדאין מלא לפי ההנחיות לעיל – בסגנון שתואם לפוסטים הקיימים של הפודקאסט. הפוסט צריך להציג את הרעיון המרכזי בצורה מסקרנת, להבליט את הערך שהמאזין יקבל, ולגרום לו לרצות להאזין.
צירפתי קובץ של התמלול של הפרק שעליו נעשה את פוסט הלינדקאין.
בנוסף צירפתי קובץ של תמלול פרק אחר שכבר עשיתי עליו פוסט לדוגמה
וצירפתי קובץ של הפוסט שעשיתי בלינדקאין, כדי שתהיה לך דוגמה לסגנון בהתאמה לפרק."""

    linkedin_prompt = get_prompt("linkedin", default_prompt)

    print("Generating LinkedIn post...")

    response = client.models.generate_content(
        model=model_name,
        contents=[linkedin_prompt, transcript_file],
    )

    text = _extract_text_from_response(response)
    if not text:
        raise RuntimeError("Empty text from model response for LinkedIn post.")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
        
    print(f"LinkedIn post saved to {output_path}")


def generate_description(transcript_path, speakers_list, model_name, output_path):
    """Generates an episode description based on a transcript file."""
    print(f"--- Generating Episode Description from {transcript_path} ---")
    
    transcript_file =  client.files.upload(file=transcript_path)

    default_prompt = f"""Here's the full transcript of an episode from my podcast 'נקודה למחשבה' – a show that sparks new ways of thinking about everyday life. The audience is mostly logical, analytical individuals, often from fields like tech, who appreciate thought-provoking content that challenges assumptions and helps them reflect on how to live more intentionally. Please write a compelling episode description that meets the following criteria:
The description should be in Hebrew. Only use characters from the Hebrew alphabet, unless you genuinely believe foreign characters are correct.
Opens with a strong, curiosity-driven hook that encourages people to listen
Short and concise (9-10 sentences max), with no fluff or repetition
Includes relevant keywords and themes from the episode that appeal to the target audience.
Clearly communicates what the listener will gain or think about differently after the episode
Add a bulleted list of key discussion points with timestamps. Base the timestamps on the questions {{ speakers_list[1] }} asks {{ speakers_list[0] }} I've attached the full transcript
The timestamps should in a format like "00:00 - Intro" - with no "**" for bold text, and should be in the same order as they appear in the transcript.
"""
    
    prompt_str = get_prompt("description", default_prompt)
    
    # We use Jinja2 here ONLY if the prompt string contains {{ }}, which it likely does for speakers list
    # The default prompt logic above had an f-string which interpolated variables.
    # To support external config, we should treat it as a Jinja2 template.
    # The user config should contain Jinja2 placeholders like {{ speakers_list[0] }}
    
    prompt_template = Template(prompt_str)
    descpt_prompt = prompt_template.render(speakers_list=speakers_list)

    print("Generating episode description...")
    
    response = client.models.generate_content(
        model=model_name,
        contents=[descpt_prompt, transcript_file],
    )

    text = _extract_text_from_response(response)
    if not text:
        raise RuntimeError("Empty text from model response for episode description.")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
        
    print(f"Episode description saved to {output_path}")

def generate_summary(transcript_path, speakers_list, model_name, output_path):
    """Generates an transcript summary based on a transcript file."""
    print(f"--- Generating Trasnscript Summary from {transcript_path} ---")
    
    transcript_file =  client.files.upload(file=transcript_path)

    default_prompt = """Here's the full transcript of an conversation. Please write a summary that includes the key talking points, things to remember, important notes.
The summary should be in Hebrew. Only use characters from the Hebrew alphabet, unless you genuinely believe foreign characters are correct.
Since the conversation was conducted in zoom and might have included visuals, include timestamps where you deem relevant.
"""
    
    descpt_prompt = get_prompt("summary", default_prompt)

    print("Generating transcript summary...")
    
    response = client.models.generate_content(
        model=model_name,
        contents=[descpt_prompt, transcript_file],
    )

    text = _extract_text_from_response(response)
    if not text:
        raise RuntimeError("Empty text from model response for transcript summary.")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
        
    print(f"Transcript summary saved to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process podcast audio files.")
    parser.add_argument("--file", required=True, help="Path to the input audio file")
    # Remove strict choices to allow custom config modes (e.g. "Draft", "Guest") which fallback to PODCAST defaults
    parser.add_argument("--mode", default="PODCAST", help="Processing mode")
    parser.add_argument("--speakers", nargs="+", default=[], help="List of speakers")
    parser.add_argument("--transcribe-only", action="store_true", help="Only transcribe the audio, skip generation tasks (Deprecated, use --actions)")
    parser.add_argument("--actions", nargs="+", default=["transcribe_podcast", "summary", "linkedin", "description"], help="List of actions to perform")
    
    args = parser.parse_args()
    
    # Configuration derived from arguments
    PODCAST_FILE_PATH = args.file
    MODE = args.mode
    SPEAKERS = args.speakers
    # Convert actions to lower case to handle potential case issues
    ACTIONS = [a.lower() for a in args.actions]
    
    # Backward compatibility for transcribe-only
    if args.transcribe_only:
        ACTIONS = ["transcribe_podcast"]
    
    # Model
    MODEL = "gemini-3-flash-preview"
    
    # Output paths derived from input filename
    directory = os.path.dirname(PODCAST_FILE_PATH)
    filename_no_ext = os.path.splitext(os.path.basename(PODCAST_FILE_PATH))[0]
    
    transcriptions_dir = os.path.join(directory, "Transcriptions")
    os.makedirs(transcriptions_dir, exist_ok=True)
    
    base_name = os.path.join(transcriptions_dir, filename_no_ext)
    TRANSCRIPT_FILE_PATH = f"{base_name}_Transcription.txt"
    LINKEDIN_POST_PATH = f"{base_name}_Linkedin.txt"
    DESCRIPTION_PATH = f"{base_name}_Description.txt"
    SUMMARY_PATH = f"{base_name}_Summary.txt"

    # 1. Transcribe the audio file
    transcript_path = None
    
    # Determine transcription type
    if "transcribe_podcast" in ACTIONS:
        transcript_path = transcribe_audio(PODCAST_FILE_PATH, SPEAKERS, MODEL, TRANSCRIPT_FILE_PATH, prompt_key="transcription_podcast")
    elif "transcribe_workshop" in ACTIONS:
        transcript_path = transcribe_audio(PODCAST_FILE_PATH, SPEAKERS, MODEL, TRANSCRIPT_FILE_PATH, prompt_key="transcription_workshop")
    elif os.path.exists(TRANSCRIPT_FILE_PATH):
        # reuse existing if we are just re-running other steps
        print(f"Skipping transcription, using existing file: {TRANSCRIPT_FILE_PATH}")
        transcript_path = TRANSCRIPT_FILE_PATH
    else:
        print("No transcription action selected and no existing transcript found. Cannot proceed with other steps.")
        sys.exit(1)

    if transcript_path:
        # 2. Generate LinkedIn post
        if "linkedin" in ACTIONS:
            generate_linkedin_post(transcript_path, MODEL, LINKEDIN_POST_PATH)
        
        # 3. Generate episode description
        if "description" in ACTIONS:
            # Ensure we have at least 2 speakers for the description prompt logic if needed, or handle gracefully
            if len(SPEAKERS) >= 2:
                 generate_description(transcript_path, SPEAKERS, MODEL, DESCRIPTION_PATH)
            else:
                 if len(SPEAKERS) == 1:
                     generate_description(transcript_path, [SPEAKERS[0], "Audience"], MODEL, DESCRIPTION_PATH)
                 else:
                     generate_description(transcript_path, ["Host", "Guest"], MODEL, DESCRIPTION_PATH)

        # 4. Generate transcript summary
        if "summary" in ACTIONS:
            generate_summary(transcript_path, SPEAKERS, MODEL, SUMMARY_PATH)
        
        print("--- All requested tasks completed. ---")
