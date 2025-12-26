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
        # 1. Try YouTube patterns
        patterns = [r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})']
        for p in patterns:
            match = re.search(p, url)
            if match: return match.group(1)
        
        # 2. Generic URL Support (return hash)
        if url.startswith("http"):
            import hashlib
            return f"url_{hashlib.md5(url.encode()).hexdigest()[:8]}"

        raise ValueError("Invalid URL")

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
        # Restrict to YouTube
        if not ("youtube.com" in url or "youtu.be" in url) and not ("mock" in url or "test_video" in url):
             raise ValueError("Free transcription (Captions) is restricted to YouTube. Please use Deepgram or Whisper for direct audio/video files.")

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
                try:
                    info = ydl.extract_info(url, download=True)
                    title = info.get('title', f"Video {video_id}")
                    duration = info.get('duration', 0)
                except Exception as dl_err:
                    # Fallback: if yt-dlp fails on generic URL but it IS a file, maybe wget/requests?
                    # For now, rely on yt-dlp specific error
                    raise Exception(f"Download Validation Failed: {str(dl_err)}")
                
            # Check file existence (yt-dlp might produce temp_id.mp3)
            if not os.path.exists(final_audio_path):
                 raise Exception("Audio download failed or file not found.")

            # 2. Call Deepgram
            print("Sending to Deepgram...")
            from deepgram import DeepgramClient
            
            deepgram = DeepgramClient(api_key=self.api_key)
            
            with open(final_audio_path, "rb") as audio:
                # Deepgram v3: transcribe_file takes keyword arguments only
                response = deepgram.listen.v1.media.transcribe_file(
                    request=audio, # File object acts as iterator
                    model="nova-2",
                    smart_format=True,
                    diarize=True,
                    punctuate=True
                )
                
            # 3. Parse Response
            # Deepgram SDK v3 returns objects, not dicts. Use attribute access.
            
            try:
                # Accessing via attributes
                # structure: response.results.channels[0].alternatives[0]
                res = response.results
                channel = res.channels[0]
                alt = channel.alternatives[0]
                words = alt.words
                
                # Group words into sentences/segments by speaker
                segments = []
                
                # Try to use paragraphs if available
                # Note: 'paragraphs' might be inside alt.paragraphs.paragraphs or just alt.paragraphs
                # SDK structure usually mirrors JSON: alt.paragraphs.paragraphs
                
                data_paragraphs = []
                if hasattr(alt, 'paragraphs') and alt.paragraphs:
                    if hasattr(alt.paragraphs, 'paragraphs'):
                         data_paragraphs = alt.paragraphs.paragraphs
                    else:
                         data_paragraphs = alt.paragraphs # Fallback
                
                if data_paragraphs:
                    for p in data_paragraphs:
                        # p is likely an object too
                        speaker = f"Speaker {p.speaker}"
                        
                        # sentences in p
                        p_sentences = p.sentences
                        text_parts = [s.text for s in p_sentences]
                        text = " ".join(text_parts)
                        
                        start = p.start
                        segments.append({
                            "speaker": speaker,
                            "time": self._format_timestamp(start),
                            "start_seconds": start,
                            "text": text
                        })
                else:
                    # Fallback to word-by-word
                    # words is a list of objects too
                    segments.append({"speaker": "Unknown", "time": "00:00", "start_seconds": 0, "text": "Raw words (diarization paragraphing unavailable)."})

            except Exception as parse_err:
                 print(f"Deepgram Response Parsing Failed: {parse_err}")
                 # Fallback debug print
                 print(f"Response dir: {dir(response)}")
                 raise parse_err

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





import subprocess
import glob

class BaseWhisperProvider(TranscriptionProvider):
    """
    Base class for Whisper-based providers (OpenAI, Grok, etc.)
    Handles download, size check, chunking (if needed), and transcription loop.
    """
    CHUNK_SIZE_LIMIT_MB = 24
    SEGMENT_TIME_SEC = 900

    def __init__(self, api_key: str, base_url: str = None):
        self.api_key = api_key
        self.base_url = base_url

    def _get_client(self):
        raise NotImplementedError

    def _get_model_name(self):
        return "whisper-1"

    def _get_audio_duration(self, file_path: str) -> float:
        try:
            cmd = [
                "ffprobe", 
                "-v", "error", 
                "-show_entries", "format=duration", 
                "-of", "default=noprint_wrappers=1:nokey=1", 
                file_path
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return float(result.stdout.strip())
        except:
            return 0.0

    def fetch(self, url: str) -> Dict:
        video_id = self._get_video_id(url)
        print(f"{self.__class__.__name__}: extracting audio for {video_id}...")
        
        import uuid
        temp_uuid = str(uuid.uuid4())
        audio_path_base = f"temp_whisper_{temp_uuid}"
        final_audio_path = f"{audio_path_base}.mp3"
        chunk_pattern = f"{audio_path_base}_chunk_*.mp3"
        
        try:
            # 1. Download Audio
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '64', 
                }],
                'outtmpl': audio_path_base,
                'quiet': True,
                'no_warnings': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', f"Video {video_id}")
                duration = info.get('duration', 0)

            if not os.path.exists(final_audio_path):
                 raise Exception("Audio download failed.")

            # 2. Check Size
            file_size_mb = os.path.getsize(final_audio_path) / (1024 * 1024)
            chunks = [final_audio_path]
            is_chunked = False
            
            if file_size_mb > self.CHUNK_SIZE_LIMIT_MB: # Safety margin for 25MB limit
                print(f"File size {file_size_mb:.2f}MB > {self.CHUNK_SIZE_LIMIT_MB}MB. Chunking...")
                is_chunked = True
                # Chunk using ffmpeg
                split_cmd = [
                    "ffmpeg", "-i", final_audio_path,
                    "-f", "segment",
                    "-segment_time", str(self.SEGMENT_TIME_SEC),
                    "-c", "copy",
                    f"{audio_path_base}_chunk_%03d.mp3"
                ]
                subprocess.run(split_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                
                # Get chunks
                chunks = sorted(glob.glob(chunk_pattern))
                print(f"Split into {len(chunks)} chunks.")

            # 3. Transcribe Loop
            client = self._get_client()
            all_segments = []
            time_offset = 0.0
            
            for i, chunk_file in enumerate(chunks):
                print(f"Transcribing segment {i+1}/{len(chunks)}...")
                
                # Get duration BEFORE processing (for offset calculation of next chunk)
                # Getting precise duration of chunk is important if using -c copy
                chunk_duration = self._get_audio_duration(chunk_file) if is_chunked else duration
                
                # Retry logic for API
                transcript = None
                for attempt in range(2):
                    try:
                        with open(chunk_file, "rb") as audio_file:
                            transcript = client.audio.transcriptions.create(
                                model=self._get_model_name(), 
                                file=audio_file, 
                                response_format="verbose_json"
                            )
                        break
                    except Exception as e:
                        print(f"Error transcribing chunk {i+1} (Attempt {attempt+1}): {e}")
                        if attempt == 1: raise e
                
                if hasattr(transcript, 'segments'):
                    for s in transcript.segments:
                        start = s.start + time_offset
                        text = s.text.strip()
                        all_segments.append({
                            "speaker": "Speaker",
                            "time": self._format_timestamp(start),
                            "start_seconds": start,
                            "text": text
                        })
                else:
                     # Fallback
                     all_segments.append({
                         "speaker": "Speaker",
                         "time": self._format_timestamp(time_offset),
                         "start_seconds": time_offset,
                         "text": transcript.text
                     })
                
                time_offset += chunk_duration

            # Cleanup
            try:
                if os.path.exists(final_audio_path): os.remove(final_audio_path)
                for f in glob.glob(chunk_pattern): os.remove(f)
            except: pass

            return {
                "video_id": video_id,
                "title": title,
                "duration": duration,
                "segments": all_segments
            }
            
        except Exception as e:
            try:
                if 'final_audio_path' in locals() and os.path.exists(final_audio_path):
                     os.remove(final_audio_path)
                if 'chunk_pattern' in locals():
                    for f in glob.glob(chunk_pattern): os.remove(f)
            except: pass
            raise e


class OpenAIWhisperProvider(BaseWhisperProvider):
    def _get_client(self):
        from openai import OpenAI
        return OpenAI(api_key=self.api_key)

class GrokWhisperProvider(BaseWhisperProvider):
    def __init__(self, api_key: str):
        super().__init__(api_key, base_url="https://api.x.ai/v1")

    def _get_client(self):
        from openai import OpenAI
        return OpenAI(api_key=self.api_key, base_url=self.base_url)


def get_transcription_provider(provider_type: str, api_key: str = None) -> TranscriptionProvider:
    if provider_type == 'deepgram':
        if not api_key:
             raise ValueError("Deepgram API Key required")
        return DeepgramProvider(api_key)
    elif provider_type == 'openai_whisper':
        if not api_key:
             raise ValueError("OpenAI API Key required for Whisper")
        return OpenAIWhisperProvider(api_key)
    elif provider_type == 'grok_whisper':
        if not api_key:
             raise ValueError("Grok API Key required")
        return GrokWhisperProvider(api_key)
        
    return YouTubeCaptionsProvider()
