import os
import math
import logging
from pydub import AudioSegment

class AudioChunker:
    def __init__(self):
        self.TARGET_BITRATE = "150k"
        self.CHUNK_LENGTH_MS = 50 * 60 * 1000  # 50 minutes

    def process_audio(self, file_path: str, output_dir: str) -> list[str]:
        """
        Processes audio file:
        1. Checks bitrate -> compresses if > 160k
        2. Checks duration -> splits if > 1 hour
        Returns list of file paths to transcribe.
        """
        logging.info(f"Processing audio: {file_path}")
        
        try:
            audio = AudioSegment.from_file(file_path)
        except Exception as e:
            logging.error(f"Error loading audio file {file_path}: {e}")
            raise

        duration_ms = len(audio)
        file_size = os.path.getsize(file_path)
        bitrate_bps = (file_size * 8) / (duration_ms / 1000) if duration_ms > 0 else 0
        
        base_filename = os.path.splitext(os.path.basename(file_path))[0]
        os.makedirs(output_dir, exist_ok=True)
        
        final_files = []

        # Logic 1: Splitting
        if duration_ms > 60 * 60 * 1000: # > 1 hour
            logging.info(f"Audio is long ({duration_ms/1000/60:.2f} min). Splitting...")
            num_chunks = math.ceil(duration_ms / self.CHUNK_LENGTH_MS)
            
            for i in range(num_chunks):
                start_ms = i * self.CHUNK_LENGTH_MS
                end_ms = min((i + 1) * self.CHUNK_LENGTH_MS, duration_ms)
                
                chunk = audio[start_ms:end_ms]
                chunk_filename = os.path.join(output_dir, f"{base_filename}_part{i+1}.mp3")
                
                logging.info(f"Exporting chunk {i+1}/{num_chunks}: {chunk_filename}")
                self._export(chunk, chunk_filename)
                final_files.append(chunk_filename)
                
        else:
            # Logic 2: Compression (only if small enough to not split)
            if bitrate_bps > 160000:
                logging.info(f"Compressing high bitrate file ({int(bitrate_bps/1000)}kbps)...")
                compressed_path = os.path.join(output_dir, f"{base_filename}_compressed.mp3")
                self._export(audio, compressed_path)
                final_files.append(compressed_path)
            else:
                # No change needed, just use original
                final_files.append(file_path)
                
        return final_files

    def _export(self, audio_segment, path):
        audio_segment.export(path, format="mp3", bitrate=self.TARGET_BITRATE)
