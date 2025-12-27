import os
import requests
import json
import re
import asyncio
from typing import List, Dict, Any

# Load the PROMPT from prompt.md
PROMPT_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompt.md")

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
            message = result['choices'][0]['message']
            content = message.get('content') or ""
            
            # Check finish reason
            finish_reason = result['choices'][0].get('finish_reason')
            
            if not content and finish_reason == 'length':
                 raise Exception("Context limit exceeded. The transcript was too long for this model.")
                 
            if finish_reason == 'length':
                print("WARNING: AI Output truncated due to token limit.")
            
            # Parse JSON
            clean_json = clean_json_string(content)
            return json.loads(clean_json)
            
        except (json.JSONDecodeError, Exception) as e:
            print(f"Failed to parse AI response as JSON: {e}")
            # Log bad response for debugging
            try:
                with open("debug_llm_failure.txt", "w", encoding="utf-8") as f:
                    f.write(f"Error: {str(e)}\n")
                    f.write(f"Finish Reason: {result['choices'][0].get('finish_reason')}\n")
                    f.write(f"Content Length: {len(content)}\n")
                    f.write("-" * 20 + " CONTENT " + "-" * 20 + "\n")
                    f.write(content)
                    f.write("\n" + "-" * 20 + " END CONTENT " + "-" * 20 + "\n")
            except: pass
            
            return {"error": "JSON Parse Error. Check debug_llm_failure.txt for raw output.", "raw": content}
        except Exception as e:
            print(f"AI Request Failed: {e}")
            return {"error": str(e)}

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, sync_call)

async def analyze_transcript(transcript_data: Dict, model_id: str, job_id: str = None, provider_config: Dict = None):
    """
    Orchestrates the Map-Reduce analysis with Progress Tracking.
    """
    try:
        provider_config = provider_config or {}
        
        segments = transcript_data.get('segments', [])
        if not segments:
            if job_id: job_manager.fail_job(job_id, "No segments found")
            return {"error": "No segments found"}

        system_prompt_base = load_prompt()
        
        # --- Handle Output Language ---
        # Default Constraint (Match Audio)
        constraint_text = """- **CRITICAL**: The output language for the *values* (summary, descriptions, quotes, analysis) MUST match the **majority language** spoken in the transcript.
- **IMPORTANT**: The **JSON KEYS** (e.g., "narrative_arc", "learning_moments") MUST remain in **ENGLISH**. Do NOT translate the keys.
- **Recall**: Use Single Quotes (') or Chinese Quotes (「」) for internal text. NEVER use double quotes (") inside the values.
- If the audio is mixed (e.g., Spanglish), write in the dominant language."""

        output_language = provider_config.get("output_language")
        if output_language and output_language.lower() not in ["auto", "audio", "same as audio"]:
            print(f"Applying Output Language Constraint: {output_language}")
            constraint_text = f"""- **CRITICAL**: You MUST write the content (summary, analysis, takeaways) in **{output_language}**.
- **IMPORTANT**: The **JSON KEYS** (e.g., "narrative_arc", "learning_moments") MUST remain in **ENGLISH**. Do NOT translate the keys.
- **Recall**: Use Single Quotes (') or Chinese Quotes (「」) for internal text. NEVER use double quotes (") inside the values."""

        # Apply to Prompt
        if "{{LANGUAGE_CONSTRAINT}}" in system_prompt_base:
            system_prompt_base = system_prompt_base.replace("{{LANGUAGE_CONSTRAINT}}", constraint_text)
        else:
            # Fallback: Append if placeholder is missing in prompt.md
            system_prompt_base += f"\n\n# Language Constraint\n{constraint_text}"
        if job_id: job_manager.update_progress(job_id, 10, "Analyzing Narrative Arc (Macro Pass)...")
        print("Starting Macro Analysis...")
        print("Starting Macro Analysis...")
        full_text = "\n".join([f"[{s['time']}] {s.get('speaker', 'Speaker')}: {s['text']}" for s in segments])
        
        # Truncate to valid context limit (approx 37k tokens)
        if len(full_text) > 150000:
            print(f"⚠️ Truncating transcript from {len(full_text)} chars to 150,000 chars for Macro Analysis.")
            full_text = full_text[:150000] + "\n...(truncated)"
        
        macro_system_prompt = system_prompt_base + "\n\nTASK: Focus ONLY on generating the 'summary' and 'narrative_arc'. return empty list for 'learning_moments'. You MUST output valid JSON ONLY. No Introduction. No Conclusion. If the transcript is short or incomplete, analyze what you have. DO NOT REFUSE. DO NOT ASK FOR MORE CONTEXT."
        
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
        # --- Step 2: Micro Analysis (The Moments) ---
        if job_id: job_manager.update_progress(job_id, 30, "Chunking Transcript...")
        print("Starting Micro Analysis (Chunking)...")
        # Reduce chunk size to 5 mins (300s) to prevent context overflow
        chunks = chunk_transcript(segments, chunk_duration_sec=300, overlap_sec=60)
        all_learning_moments = []
        
        micro_system_prompt = system_prompt_base + """

TASK: Find specific 'learning_moments' in this segment.
REQUIRED JSON STRUCTURE:
{
  "learning_moments": [
    {
      "timestamp_start": "MM:SS",
      "timestamp_end": "MM:SS",
      "category": "Host Technique" or "Guest Storytelling",
      "technique_name": "Name of technique",
      "quote": "Direct quote",
      "analysis": "Why it worked",
      "takeaway": "Actionable advice"
    }
  ]
}
You MUST output valid JSON ONLY. No Introduction. No Conclusion. DO NOT REFUSE.
"""
        
        total_chunks = len(chunks)
        print(f"Total chunks to analyze: {total_chunks}")
        
        for i, chunk in enumerate(chunks):
            current_chunk_num = i + 1
            pct = 30 + int((current_chunk_num / total_chunks) * 60) # 30% to 90%
            if job_id: job_manager.update_progress(job_id, pct, f"Analyzing Chunk {current_chunk_num}/{total_chunks}...")
            
            print(f"Analyzing Chunk {current_chunk_num}/{total_chunks}...")
            
            chunk_text = chunk['text']
            if len(chunk_text) > 30000:
                print(f"⚠️ Truncating Chunk {current_chunk_num} from {len(chunk_text)} chars to 30,000.")
                chunk_text = chunk_text[:30000] + "\n...(truncated)"

            micro_messages = [
                {"role": "system", "content": micro_system_prompt},
                {"role": "user", "content": f"Analyze this segment ({chunk['start']}s to {chunk['end']}s) for learning moments:\n\n{chunk_text}"}
            ]
            
            micro_result = await call_ai_api(micro_messages, model_id, provider_config)

            # Debug Log for Micro Analysis
            try:
                with open("debug_micro_response.txt", "a", encoding="utf-8") as f:
                     f.write(f"\n--- Chunk {i+1} ---\n{json.dumps(micro_result, ensure_ascii=False, indent=2)}\n")
            except: pass
            
            moments = micro_result.get('learning_moments', [])
            if isinstance(moments, list):
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

    except Exception as e:
        import traceback
        traceback.print_exc()
        if job_id: job_manager.fail_job(job_id, f"Internal Analysis Error: {str(e)}")
        return {"error": str(e)}

def deduplicate_moments(moments: List[Dict]) -> List[Dict]:
    """
    Simple deduplication based on timestamps/content. 
    (MVP: Just pass through for now, or basic exact match check)
    """
    # TODO: Implement fuzzy matching as per PRD
    return moments

def clean_json_string(s):
    """
    Robustly extracts JSON object from a string.
    1. Tries to find markdown code blocks (```json ... ```).
    2. Fallback: Finds the first open brace '{' and the last closing brace '}'.
    """
    if not isinstance(s, str): return ""
    
    # 1. Try Markdown Code Blocks
    pattern = r"```json\s*(.*?)\s*```"
    match = re.search(pattern, s, re.DOTALL)
    if match: return match.group(1)
    
    pattern_generic = r"```\s*(.*?)\s*```"
    match_generic = re.search(pattern_generic, s, re.DOTALL)
    if match_generic: return match_generic.group(1)
        
    # 2. Fallback: Find outermost {}
    # This handles cases where models chat before/after the JSON without code blocks
    start = s.find('{')
    end = s.rfind('}')
    
    if start != -1 and end != -1 and end > start:
        return s[start:end+1]
        
    return s
