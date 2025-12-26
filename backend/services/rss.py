
import feedparser
from typing import List, Dict, Optional

def parse_podcast_feed(url: str) -> Dict:
    """
    Parses a podcast RSS feed URL.
    Returns metadata and list of episodes with audio URLs.
    """
    try:
        feed = feedparser.parse(url)
        
        if feed.bozo:
            # feedparser sets bozo=1 if there's an error (XML generic) but often still parses content.
            # We log but continue unless empty.
            print(f"RSS Parse Warning (Bozo): {feed.bozo_exception}")
            
        if not feed.feed:
             return {"error": "Invalid or inaccessible feed URL."}

        podcast_title = feed.feed.get("title", "Unknown Podcast")
        podcast_image = ""
        if "image" in feed.feed:
            podcast_image = feed.feed.image.get("href", "")
        
        episodes = []
        for entry in feed.entries:
            # Find audio enclosure
            audio_url = None
            duration = None
            
            # 1. Check standard enclosures
            for link in entry.get("links", []):
                if link.get("rel") == "enclosure":
                    # Check type
                    mime = link.get("type", "")
                    if "audio" in mime:
                        audio_url = link.get("href")
                        break # Take first audio
            
            # 2. Skip if no audio
            if not audio_url:
                continue

            # 3. Extract metadata
            title = entry.get("title", "Untitled Episode")
            published = entry.get("published", "")
            
            # itunes:duration often exists
            # feedparser maps 'itunes_duration' -> 'itunes_duration' usually?
            # It puts it in entry keys directly mostly.
            itunes_duration = entry.get("itunes_duration", "")
            
            episodes.append({
                "title": title,
                "published": published,
                "audio_url": audio_url,
                "duration": itunes_duration
            })
            
        return {
            "title": podcast_title,
            "image": podcast_image,
            "episodes": episodes
        }

    except Exception as e:
        print(f"RSS Error: {e}")
        return {"error": str(e)}
