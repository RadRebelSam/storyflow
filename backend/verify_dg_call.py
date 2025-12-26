
from deepgram import DeepgramClient
import io

def verify_call():
    try:
        dg = DeepgramClient(api_key="fake_key")
        # Create dummy in-memory file
        dummy_audio = io.BytesIO(b"fake audio data")
        
        print("Attempting transcribe_file with kwargs...")
        try:
            # We expect an API error (Unauthorized), NOT a TypeError about arguments
            dg.listen.v1.media.transcribe_file(
                request=dummy_audio,
                model="nova-2",
                smart_format=True,
                diarize=True,
                punctuate=True
            )
        except TypeError as e:
            print(f"FAILED: TypeError: {e}")
        except Exception as e:
            print(f"SUCCESS: Call passed syntax check (failed later with: {type(e).__name__} - {e})")

    except Exception as e:
        print(f"Setup Error: {e}")

if __name__ == "__main__":
    verify_call()
