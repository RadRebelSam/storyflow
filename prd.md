
# PRD: StoryFlow - Long-form Podcast Analysis Engine

|**Document Version**|**1.0**|
|---|---|
|**Status**|Draft|
|**Target Audience**|Podcast Hosts, Storytelling Students, Content Creators|
|**Core Value**|Decode the "Black Box" of great conversations by analyzing structure, host techniques, and guest storytelling mechanics.|

## 1. User Flow (用户流程)

1. **Input:** User pastes a YouTube link or Apple/Spotify Podcast link into the search bar.
    
2. **Processing (Loading State):**
    
    - System checks if analysis already exists in the database (Cache Hit).
        
    - If not, System downloads audio -> Transcribes (Speaker Diarization) -> AI Processing (Chunking).
        
    - User sees a progress bar: "Transcribing... Analyzing Flow... Extracting Insights..."
        
3. **Result Dashboard:**
    
    - User sees an interactive player synced with a transcript.
        
    - User sees a "Narrative Arc" timeline (Intro -> Climax -> Outro).
        
    - User sees "Learning Moments" marked on the timeline.
        
4. **Deep Dive:** User clicks a marker -> Player jumps to that timestamp -> Sidebar shows the AI analysis card (Technique + Why it worked).
    

## 2. Functional Requirements (功能需求)

### 2.1 Audio Ingestion & Transcription

- **Support:** YouTube Links (Priority 1), RSS Feeds/Audio Files (Priority 2).
    
- **Engine:** `yt-dlp` for downloading.
    
- **Transcription:**
    
    - Must use a provider supporting **Speaker Diarization** (Deepgram or AssemblyAI).
        
    - Output must serve formatted text with clear `Speaker A`, `Speaker B` labels.
        

### 2.2 AI Analysis Core (The Brain)

- **Model:** Claude 3.5 Sonnet (Recommended) or GPT-4o.
    
- **Configuration:**
    
    - **Temperature:** 0.3 (Strict adherence to JSON format).
        
    - **Prompt Strategy:** See "Master Storyteller Prompt".
        
- **Processing Logic:**
    
    - **Macro Analysis:** Analyze full text for `Summary` and `Narrative Arc`.
        
    - **Micro Analysis:** Split transcript into 15-minute chunks (with overlap) to extract `Learning Moments`.
        
- **Output Validation:** Backend must validate that the AI output is valid JSON before sending to Frontend. If JSON is broken, trigger a retry.
    

### 2.3 Frontend Interface (The Learning Experience)

- **Split View:**
    
    - **Left:** Audio/Video Player (Sticky).
        
    - **Right:** Scrollable Transcript.
        
- **The Timeline (Visualizer):**
    
    - A waveform or horizontal bar representing the episode duration.
        
    - **Color-coded Zones:** Indicate the "Narrative Arc" (e.g., Blue for Intro, Red for Climax).
        
    - **Pins/Markers:** clickable dots representing "Learning Moments".
        
- **Insight Cards:**
    
    - When a pin is clicked, display the structured data:
        
        - **Tag:** (e.g., "The Mirror") - _Ideally with a tooltip explaining the term._
            
        - **Analysis:** (The "Why").
            
        - **Takeaway:** (The actionable advice).
            

## 3. Data Structure (API Response)

Frontend expects this JSON format from Backend:

JSON

```
{
  "meta": {
    "title": "Episode Title",
    "duration_seconds": 3600
  },
  "analysis": {
    "summary": "String...",
    "narrative_arc": [
      {"phase": "Deep Dive", "start_time": "12:30", "description": "..."}
    ],
    "learning_moments": [
      {
        "timestamp_start": "14:20",
        "category": "Host Technique",
        "technique_name": "The Silence",
        "quote": "...",
        "analysis": "...",
        "takeaway": "..."
      }
    ]
  },
  "transcript": [
    {"speaker": "Host", "time": "00:01", "text": "Welcome back..."},
    {"speaker": "Guest", "time": "00:05", "text": "Thanks for having me..."}
  ]
}
```

## 4. Data Processing Specifications (Chunking Logic)
This section defines how the backend must handle long transcripts to stay within LLM context limits while preserving narrative continuity.

4.1 The "Map-Reduce" Strategy
The system shall use a two-pass approach:

Pass A (Macro): Feeds the entire transcript (or a token-reduced version) to generate the Narrative Arc.

Pass B (Micro): Feeds segmented parts to generate Learning Moments.

4.2 Segmentation Rules (Critical)
Chunk Duration: 15 minutes (approx. 2,000 - 2,500 words).

Overlap Window: 2 minutes.

Reasoning: If a "Host Technique" happens at minute 14:55, a hard cut at 15:00 might break the context. Overlap ensures the AI sees the full setup and reaction.

Boundary Detection: Cuts must occur at the nearest paragraph break or speaker change within the cut window, strictly avoiding mid-sentence cuts.

4.3 Deduplication Logic (The Merge Step)
Since chunks overlap, the AI might identify the same "Learning Moment" in both Chunk 1 and Chunk 2. The backend must de-duplicate based on:

Fuzzy Matching: If two moments have timestamp_start within 30 seconds of each other AND the quote similarity is > 80%, treat them as duplicates.

Selection: Keep the version with the longer/more detailed analysis.

## 5. Technical Constraints & Non-Functional Requirements

- **Latency:** Full analysis of a 1-hour episode should ideally complete under 3 minutes. (Async processing is mandatory).
    
- **Cost Management:**
    
    - Cache results! If User A analyzes "Joe Rogan #2000", save the JSON. If User B asks for it, serve from DB immediately (Cost = $0).
        
- **Scalability:** Use a Task Queue (e.g., Celery/BullMQ + Redis) to handle AI requests so the web server doesn't timeout.
    

## 6. MVP Scope (Phase 1)

- **In Scope:**
    
    - Only YouTube Links.
        
    - English Podcasts Only.
        
    - No user accounts (Guest mode).
        
    - Limit to videos < 60 mins (to control API costs during testing).
        
- **Out of Scope:**
    
    - PDF Export.
        
    - Chat with Transcript.
        
    - Multi-language support.