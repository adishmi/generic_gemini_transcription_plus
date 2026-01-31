import os
import re
import logging
from google import genai
from jinja2 import Template

class GeminiProcessor:
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)

    def upload_file(self, file_path):
        logging.info(f"Uploading file for Gemini: {file_path}")
        return self.client.files.upload(file=file_path)

    def generate_content(self, model_name, contents):
        logging.info(f"Sending request to Gemini model: {model_name}")
        response = self.client.models.generate_content(
            model=model_name,
            contents=contents
        )
        return self._extract_text(response)

    def _extract_text(self, response):
        try:
            if getattr(response, "text", None):
                return response.text
            parts = []
            for candidate in getattr(response, "candidates", []) or []:
                content = getattr(candidate, "content", None)
                for part in getattr(content, "parts", []) or []:
                    text = getattr(part, "text", None)
                    if text:
                        parts.append(text)
            return "\n".join(parts)
        except Exception as e:
            logging.error(f"Error extracting text: {e}")
            return ""

    def render_prompt(self, prompt_template_str, **kwargs):
        """Renders a Jinja2 prompt template."""
        if not prompt_template_str:
            return ""
        template = Template(prompt_template_str)
        return template.render(**kwargs)

    def adjust_timestamps(self, text, offset_seconds):
        """Adjusts timestamps in the text by adding offset_seconds."""
        if offset_seconds <= 0:
            return text

        def replace_match(match):
            timestamp_str = match.group(1)
            parts = list(map(int, timestamp_str.split(':')))
            
            if len(parts) == 2:
                minutes, seconds = parts
                hours = 0
            elif len(parts) == 3:
                hours, minutes, seconds = parts
            else:
                return match.group(0)
                
            total_seconds = hours * 3600 + minutes * 60 + seconds
            total_seconds += offset_seconds
            
            new_hours = int(total_seconds // 3600)
            new_minutes = int((total_seconds % 3600) // 60)
            new_seconds = int(total_seconds % 60)
            
            if new_hours > 0:
                return f"[{new_hours:02d}:{new_minutes:02d}:{new_seconds:02d}]"
            else:
                return f"[{new_minutes:02d}:{new_seconds:02d}]"

        return re.sub(r'\[(\d{1,2}:\d{2}(?::\d{2})?)\]', replace_match, text)
