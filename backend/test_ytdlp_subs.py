import yt_dlp
import os

url = "https://www.youtube.com/watch?v=M7FIvfx5J10" # A video known to have captions

ydl_opts = {
    'skip_download': True,
    'writeautomaticsub': True,
    'writesubtitles': True,
    'subtitleslangs': ['en'],
    'outtmpl': 'test_subs',
    'quiet': False
}

try:
    if os.path.exists("test_subs.en.vtt"): os.remove("test_subs.en.vtt")
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        
    if os.path.exists("test_subs.en.vtt"):
        print("SUCCESS: Downloaded test_subs.en.vtt")
        with open("test_subs.en.vtt", "r", encoding="utf-8") as f:
            print("First 5 lines:")
            print("\n".join(f.readlines()[:5]))
    else:
        print("FAILURE: No subtitle file created.")

except Exception as e:
    print(f"Error: {e}")
