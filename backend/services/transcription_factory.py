import os
import shutil
import re
from typing import Dict, Optional, List
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import JSONFormatter
import yt_dlp

class TranscriptionProvider:
    def fetch(self, url: str) -> Dict:
        raise NotImplementedError("Subclasses must implement fetch")

    def _get_video_id(self, url: str) -> str:
        patterns = [r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})']
        for p in patterns:
            match = re.search(p, url)
            if match: return match.group(1)
        raise ValueError("Invalid YouTube URL")

    def _format_timestamp(self, seconds):
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        if h > 0: return f"{int(h)}:{int(m):02d}:{int(s):02d}"
        return f"{int(m):02d}:{int(s):02d}"

class YouTubeCaptionsProvider(TranscriptionProvider):
    """
    Default free provider using community captions or auto-generated captions.
    Fast, free, but NO speaker labels (Diarization).
    """
    def fetch(self, url: str) -> Dict:
        video_id = self._get_video_id(url)
        
        # Mock Logic preserved
        if "mock" in url or "test_video" in url:
             return self._get_mock(video_id)

        print(f"Fetching YouTube Captions (via yt-dlp) for {video_id}...")
        import uuid
        temp_uuid = str(uuid.uuid4())
        base_filename = f"temp_subs_{temp_uuid}"
        
        try:
            # 1. Download Subtitles using yt-dlp
            ydl_opts = {
                'skip_download': True,
                'writeautomaticsub': True,
                'writesubtitles': True,
                'subtitleslangs': ['en'],
                'outtmpl': base_filename,
                'quiet': True,
                'no_warnings': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', f"YouTube Video ({video_id})")
                duration = info.get('duration', 0)

            # 2. Find the .vtt file
            vtt_path = f"{base_filename}.en.vtt"
            if not os.path.exists(vtt_path):
                # Try finding any vtt that starts with base_filename
                files = [f for f in os.listdir('.') if f.startswith(base_filename) and f.endswith('.vtt')]
                if files:
                    vtt_path = files[0]
                else:
                    raise Exception("No subtitles found for this video. (yt-dlp failed to download .vtt)")
            
            # 3. Parse VTT
            segments = self._parse_vtt(vtt_path)
            
            # Cleanup
            try:
                if os.path.exists(vtt_path): os.remove(vtt_path)
            except: pass

            return {
                "video_id": video_id,
                "title": title,
                "duration": duration,
                "segments": segments
            }
            
        except Exception as e:
            # Cleanup in case of error
            try:
                for f in os.listdir('.'):
                    if f.startswith(base_filename): os.remove(f)
            except: pass
            
            err = str(e)
            print(f"yt-dlp subs error: {err}")
            if "No subtitles found" in err:
                raise Exception("No English captions available for this video.")
            raise Exception(f"Failed to fetch captions: {err}")

    def _parse_vtt(self, vtt_path: str) -> List[Dict]:
        segments = []
        with open(vtt_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Simple VTT parser
        # Skip header
        current_start = 0.0
        current_text = []
        
        time_pattern = re.compile(r'(\d{2}:)?(\d{2}):(\d{2})\.(\d{3}) --> (\d{2}:)?(\d{2}):(\d{2})\.(\d{3})')
        
        for line in lines:
            line = line.strip()
            if not line: continue
            if "WEBVTT" in line: continue
            if "Language:" in line: continue
            if "Kind:" in line: continue
            
            match = time_pattern.search(line)
            if match:
                # If we have previous text, save it
                if current_text:
                    text = " ".join(current_text)
                    # Filter out purely metadata tags if any, simpler validation
                    text = re.sub(r'<[^>]+>', '', text) 
                    if text.strip():
                        segments.append({
                            "speaker": "Speaker",
                            "time": self._format_timestamp(current_start),
                            "start_seconds": current_start,
                            "text": text
                        })
                
                # Parse new start time
                # match groups: 1=h, 2=m, 3=s, 4=ms
                h = int(match.group(1).replace(':', '')) if match.group(1) else 0
                m = int(match.group(2))
                s = int(match.group(3))
                ms = int(match.group(4))
                current_start = h * 3600 + m * 60 + s + ms / 1000.0
                current_text = []
            else:
                 # It's text (or IDs), append if not just digits
                 if not line.isdigit():
                     current_text.append(line)
        
        # Append last
        if current_text:
            text = " ".join(current_text)
            text = re.sub(r'<[^>]+>', '', text)
            if text.strip():
                segments.append({
                    "speaker": "Speaker",
                    "time": self._format_timestamp(current_start),
                    "start_seconds": current_start,
                    "text": text
                })
        
        return segments

    def _get_mock(self, video_id):
        return {
            "video_id": "mock_video_id",
            "title": "MOCK VIDEO: Storytelling Masterclass",
            "duration": 450,
            "segments": [{"speaker": "Speaker", "time": "00:10", "start_seconds": 10.0, "text": "Mock transcript text."}]
        }


class DeepgramProvider(TranscriptionProvider):
    """
    Paid provider.
    1. Extracts Audio using yt-dlp (requires ffmpeg).
    2. Uploads to Deepgram for 'nova-2' model with 'diarize=true'.
    Returns Speaker 0, Speaker 1, etc.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key

    def fetch(self, url: str) -> Dict:
        # 0. Ensure FFmpeg is available
        if not shutil.which('ffmpeg'):
            # Fallback for Windows: Try standard install path
            possible_path = r"C:\ffmpeg\bin"
            if os.path.exists(possible_path):
                print(f"Adding {possible_path} to PATH for FFmpeg...")
                os.environ["PATH"] += os.pathsep + possible_path
            
            # Re-check
            if not shutil.which('ffmpeg'):
                raise Exception("FFmpeg is not installed or not found in PATH. Please install it to C:\\ffmpeg\\bin or add it to your system PATH.")
            
        video_id = self._get_video_id(url)
        print(f"Deepgram: extracting audio for {video_id}...")
        
        # 1. Download Audio
        import uuid
        temp_uuid = str(uuid.uuid4())
        audio_path_base = f"temp_{temp_uuid}"
        final_audio_path = f"{audio_path_base}.mp3"
        
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': audio_path_base, # yt-dlp adds extension
                'quiet': True,
                'no_warnings': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', f"Video {video_id}")
                duration = info.get('duration', 0)
                
            # Check file existence (yt-dlp might produce temp_id.mp3)
            if not os.path.exists(final_audio_path):
                 raise Exception("Audio download failed or file not found.")

            # 2. Call Deepgram
            print("Sending to Deepgram...")
            from deepgram import DeepgramClient
            
            deepgram = DeepgramClient(api_key=self.api_key)
            
            with open(final_audio_path, "rb") as audio:
                payload = {"buffer": audio}
                # Use simple dict for options
                options = {
                    "model": "nova-2",
                    "smart_format": "true", # Pass as string if dict? SDK usually handles it. 
                    "diarize": "true",
                    "punctuate": "true"
                }
                # v3.x syntax found via introspection: deepgram.listen.v1.media.transcribe_file
                response = deepgram.listen.v1.media.transcribe_file(payload, options)
                
            # 3. Parse Response
            segments = []
            words = response['results']['channels'][0]['alternatives'][0]['words']
            
            # Group words into sentences/segments by speaker
            current_speaker = None
            current_text = []
            segment_start = 0.0
            
            # Simple grouping heuristic
            # Real Deepgram response has 'paragraphs' too, but let's stick to word stream or use their paragraphs if available
            # Let's try to use 'paragraphs' for better chunking if available, otherwise word grouping
            
            data_paragraphs = response['results']['channels'][0]['alternatives'][0].get('paragraphs', {}).get('paragraphs', [])
            
            if data_paragraphs:
                for p in data_paragraphs:
                    speaker = f"Speaker {p['speaker']}"
                    text = " ".join([s['text'] for s in p['sentences']])
                    start = p['start']
                    segments.append({
                        "speaker": speaker,
                        "time": self._format_timestamp(start),
                        "start_seconds": start,
                        "text": text
                    })
            else:
                # Fallback to word-by-word (less clean)
                segments.append({"speaker": "Unknown", "time": "00:00", "start_seconds": 0, "text": "Raw words (diarization paragraphing unavailable)."})

            # Cleanup
            try:
                if os.path.exists(final_audio_path):
                    os.remove(final_audio_path)
            except PermissionError:
                print(f"Warning: Could not remove temp file {final_audio_path} (locked by process). It will remain until next cleanup.")
            except Exception as e:
                print(f"Warning: Error removing temp file: {e}")
            
            return {
                "video_id": video_id,
                "title": title,
                "duration": duration,
                "segments": segments
            }
            
        except Exception as e:
            print(f"Deepgram Error: {e}")
            # Try cleanup in error case too
            try:
                if 'final_audio_path' in locals() and os.path.exists(final_audio_path):
                     os.remove(final_audio_path)
            except: 
                pass
            raise e




def get_transcription_provider(provider_type: str, api_key: str = None) -> TranscriptionProvider:
    if provider_type == 'deepgram':
        if not api_key:
             raise ValueError("Deepgram API Key required")
        return DeepgramProvider(api_key)
    return YouTubeCaptionsProvider()
