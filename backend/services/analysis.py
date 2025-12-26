import os
import requests
import json
import re
import asyncio
from typing import List, Dict, Any

# Load the PROMPT from prompt.md
PROMPT_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "prompt.md")

def load_prompt():
    """Reads the prompt.md file."""
    try:
        with open(PROMPT_FILE_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: prompt.md not found at {PROMPT_FILE_PATH}")
        return "You are an expert storytelling coach..."

def chunk_transcript(segments: List[Dict], chunk_duration_sec: int = 900, overlap_sec: int = 120) -> List[Dict]:
    """
    Splits transcript segments into chunks based on duration.
    
    Args:
        segments: List of transcript segments [{'start_seconds': 0.0, 'text': '...'}]
        chunk_duration_sec: Target duration for each chunk (default 15 mins)
        overlap_sec: Overlap between chunks (default 2 mins)
        
    Returns:
        List of chunks, where each chunk is {'text': '...', 'start': 0.0, 'end': ...}
    """
    if not segments:
        return []
        
    total_duration = segments[-1]['start_seconds'] + 10 # Approx end
    chunks = []
    
    current_time = 0.0
    
    while current_time < total_duration:
        end_time = current_time + chunk_duration_sec
        
        # Filter segments that fall into this time window
        chunk_segments = [
            s for s in segments 
            if s['start_seconds'] >= current_time and s['start_seconds'] < end_time
        ]
        
        if chunk_segments:
            # Combine text
            chunk_text = "\n".join([f"[{s['time']}] {s.get('speaker', 'Speaker')}: {s['text']}" for s in chunk_segments])
            
            chunks.append({
                "index": len(chunks),
                "start": current_time,
                "end": end_time,
                "text": chunk_text
            })
            
        # Move forward, but account for overlap
        # If we are near the end, break to avoid infinite loops if step is small
        next_step = chunk_duration_sec - overlap_sec
        if next_step <= 0: next_step = chunk_duration_sec # Safety
        
        current_time += next_step
        
        # Break if the last chunk covered the end
        if chunk_segments and chunk_segments[-1]['start_seconds'] >= segments[-1]['start_seconds']:
            break
            
    return chunks

from services.jobs import job_manager

from services.jobs import job_manager
from services.llm_factory import get_llm_provider

# We no longer need call_ai_api_sync as a standalone, but the factory is sync.
# We will wrap the factory call in the async executor.

async def call_ai_api(messages: List[Dict], model_id: str, provider_config: Dict) -> Dict:
    """
    Async wrapper calling the LLM Factory.
    """
    api_key = provider_config.get("api_key") or os.getenv("SUPER_MIND_API_KEY")
    base_url = provider_config.get("base_url") or os.getenv("BASE_URL")
    provider_type = provider_config.get("provider", "openai")

    if not api_key:
        return {"error": "API Key missing. Please check settings."}

    def sync_call():
        try:
            provider = get_llm_provider(provider_type, api_key, base_url)
            result = provider.generate(messages, model=model_id)
            
            # Common parsing logic (OpenAI format is returned by all adapters)
            content = result['choices'][0]['message']['content']
            
            # Check finish reason
            finish_reason = result['choices'][0].get('finish_reason')
            if finish_reason == 'length':
                print("WARNING: AI Output truncated due to token limit.")
            
            # Parse JSON
            clean_json = clean_json_string(content)
            return json.loads(clean_json)
            
        except json.JSONDecodeError:
            print("Failed to parse AI response as JSON")
            return {"error": "JSON Parse Error", "raw": content}
        except Exception as e:
            print(f"AI Request Failed: {e}")
            return {"error": str(e)}

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, sync_call)

async def analyze_transcript(transcript_data: Dict, model_id: str, job_id: str = None, provider_config: Dict = None):
    """
    Orchestrates the Map-Reduce analysis with Progress Tracking.
    """
    provider_config = provider_config or {}
    
    segments = transcript_data.get('segments', [])
    if not segments:
        if job_id: job_manager.fail_job(job_id, "No segments found")
        return {"error": "No segments found"}

    system_prompt_base = load_prompt()
    
    # --- Step 1: Macro Analysis (The Arc) ---
    if job_id: job_manager.update_progress(job_id, 10, "Analyzing Narrative Arc (Macro Pass)...")
    print("Starting Macro Analysis...")
    full_text = "\n".join([f"[{s['time']}] {s.get('speaker', 'Speaker')}: {s['text']}" for s in segments])
    
    macro_system_prompt = system_prompt_base + "\n\nTASK: Focus ONLY on generating the 'summary' and 'narrative_arc'. return empty list for 'learning_moments'. You MUST output valid JSON."
    
    macro_messages = [
        {"role": "system", "content": macro_system_prompt},
        {"role": "user", "content": f"Analyze the following full transcript to find the Narrative Arc:\n\n{full_text}"}
    ]
    
    # Run Macro Analysis
    macro_result = await call_ai_api(macro_messages, model_id, provider_config)
    
    if "error" in macro_result:
        # If job_id exists, fail it
        if job_id:
             job_manager.fail_job(job_id, f"Macro analysis failed: {macro_result['error']}")
        return macro_result

    # --- Step 2: Micro Analysis (The Moments) ---
    if job_id: job_manager.update_progress(job_id, 30, "Chunking Transcript...")
    print("Starting Micro Analysis (Chunking)...")
    chunks = chunk_transcript(segments)
    all_learning_moments = []
    
    micro_system_prompt = system_prompt_base + "\n\nTASK: Focus ONLY on finding specific 'learning_moments' in this segment. Return empty values for summary and arc. You MUST output valid JSON."
    
    total_chunks = len(chunks)
    for i, chunk in enumerate(chunks):
        current_chunk_num = i + 1
        pct = 30 + int((current_chunk_num / total_chunks) * 60) # 30% to 90%
        if job_id: job_manager.update_progress(job_id, pct, f"Analyzing Chunk {current_chunk_num}/{total_chunks}...")
        
        print(f"Analyzing Chunk {current_chunk_num}/{total_chunks}...")
        
        micro_messages = [
            {"role": "system", "content": micro_system_prompt},
            {"role": "user", "content": f"Analyze this segment ({chunk['start']}s to {chunk['end']}s) for learning moments:\n\n{chunk['text']}"}
        ]
        
        micro_result = await call_ai_api(micro_messages, model_id, provider_config)
        
        moments = micro_result.get('learning_moments', [])
        if moments:
            all_learning_moments.extend(moments)

    # --- Step 3: Merge & Deduplicate ---
    if job_id: job_manager.update_progress(job_id, 95, "Finalizing Results...")
    final_result = {
        "summary": macro_result.get("summary", "Analysis failed to generate summary."),
        "narrative_arc": macro_result.get("narrative_arc", []),
        "learning_moments": deduplicate_moments(all_learning_moments)
    }
    
    if job_id: job_manager.complete_job(job_id, final_result)
    return final_result

def deduplicate_moments(moments: List[Dict]) -> List[Dict]:
    """
    Simple deduplication based on timestamps/content. 
    (MVP: Just pass through for now, or basic exact match check)
    """
    # TODO: Implement fuzzy matching as per PRD
    return moments

def clean_json_string(s):
    """Removes markdown code blocks if present."""
    if not isinstance(s, str): return ""
    pattern = r"```json\s*(.*?)\s*```"
    match = re.search(pattern, s, re.DOTALL)
    if match: return match.group(1)
    
    pattern_generic = r"```\s*(.*?)\s*```"
    match_generic = re.search(pattern_generic, s, re.DOTALL)
    if match_generic: return match_generic.group(1)
        
    return s
