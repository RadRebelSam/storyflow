
from deepgram import DeepgramClient
import inspect

def inspect_deepgram():
    try:
        dg = DeepgramClient(api_key="fake_key")
        print("DeepgramClient created.")
        
        # Try to find where transcribe_file lives
        if hasattr(dg, 'listen'):
            listen = dg.listen
            if hasattr(listen, 'v1'):
                 print("dg.listen.v1 exists")
                 v1 = listen.v1
                 print(f"Dir v1: {dir(v1)}")
            
                
                 if hasattr(v1, 'media'):
                     print("dg.listen.v1.media exists")
                     media = v1.media
                     if hasattr(media, 'transcribe_file'):
                         print("transcribe_file exists")
                         sig = inspect.signature(media.transcribe_file)
                         print(f"Signature: {sig}")
            
            # Check v1 method
            if hasattr(listen, 'rest'):
                 print("dg.listen.rest exists")
                 rest = listen.rest
                 if hasattr(rest, 'v'):
                     v1 = rest.v("1")
                     print("dg.listen.rest.v('1') exists")
                     if hasattr(v1, 'transcribe_file'):
                         print("dg.listen.rest.v('1').transcribe_file exists")
                         sig = inspect.signature(v1.transcribe_file)
                         print(f"Signature: {sig}")
            
            # Check for prerecorded
            if hasattr(listen, 'prerecorded'):
                 print("dg.listen.prerecorded exists")
                 pre = listen.prerecorded
                 if hasattr(pre, 'v'):
                     v1 = pre.v("1")
                     if hasattr(v1, 'transcribe_file'):
                         print("dg.listen.prerecorded.v('1').transcribe_file exists")
                         sig = inspect.signature(v1.transcribe_file)
                         print(f"Signature: {sig}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_deepgram()
