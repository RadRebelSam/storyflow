
from services.transcription_factory import get_transcription_provider, YouTubeCaptionsProvider, DeepgramProvider

def test_get_id_youtube():
    p = YouTubeCaptionsProvider()
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert p._get_video_id(url) == "dQw4w9WgXcQ"

def test_get_id_generic():
    p = DeepgramProvider("fake-key")
    url = "https://example.com/audio.mp3"
    assert p._get_video_id(url).startswith("url_")

def test_youtube_provider_rejects_mp3():
    p = YouTubeCaptionsProvider()
    url = "https://example.com/audio.mp3"
    try:
        p.fetch(url)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "restricted to YouTube" in str(e)

if __name__ == "__main__":
    print("Running manual tests...")
    test_get_id_youtube()
    test_get_id_generic()
    test_youtube_provider_rejects_mp3()
    print("All tests passed.")
