from services.transcription_factory import get_transcription_provider

def fetch_transcript(url: str, provider_config: dict = None):
    """
    Fetches transcript using the configured provider.
    provider_config = { 'transcription_provider': 'youtube' | 'deepgram', 'deepgram_key': '...' }
    """
    provider_config = provider_config or {}
    provider_type = provider_config.get('transcription_provider', 'youtube')
    provider_type = provider_config.get('transcription_provider', 'youtube')
    
    # Extract appropriate key
    api_key = None
    if provider_type == 'deepgram':
        api_key = provider_config.get('deepgram_key')
    elif provider_type == 'openai_whisper':
        api_key = provider_config.get('openai_api_key')
    elif provider_type == 'uniscribe':
        api_key = provider_config.get('uniscribe_key')
    
    input_language = provider_config.get('input_language')
    
    provider = get_transcription_provider(provider_type, api_key)
    return provider.fetch(url, language=input_language)

def process_manual_transcript(text: str):
    """
    Converts raw text into a structure compatible with the analysis pipeline.
    Estimates timestamps assuming ~150 words per minute.
    """
    # Split by double newlines to find paragraphs, or single if sparse
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    
    segments = []
    current_time = 0.0
    words_per_minute = 150
    
    def format_timestamp(seconds):
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        if h > 0: return f"{int(h)}:{int(m):02d}:{int(s):02d}"
        return f"{int(m):02d}:{int(s):02d}"
    
    for i, para in enumerate(paragraphs):
        word_count = len(para.split())
        duration = (word_count / words_per_minute) * 60
        
        segments.append({
            "speaker": "Speaker", # Unknown in manual text
            "time": format_timestamp(current_time),
            "start_seconds": current_time,
            "text": para
        })
        
        current_time += duration
        
    return {
        "video_id": None, # No video for manual text
        "title": "Manual Transcript Analysis",
        "duration": current_time,
        "segments": segments
    }
