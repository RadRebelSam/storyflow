from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import requests
from dotenv import load_dotenv


# Import services
from services.transcription import fetch_transcript
from services.analysis import analyze_transcript
from services.rss import parse_podcast_feed

load_dotenv()

app = FastAPI(title="StoryFlow API")

# CORS Configuration
origins = [
    "http://localhost:5173",  # React Dev Server
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.getenv("SUPER_MIND_API_KEY")
BASE_URL = os.getenv("BASE_URL", "https://space.ai-builders.com/backend/v1")

class AnalyzeRequest(BaseModel):
    url: Optional[str] = None
    transcript_text: Optional[str] = None
    model: str
    provider_config: Optional[dict] = None # { provider: 'openai', api_key: '...', base_url: '...' }
    transcription_config: Optional[dict] = None # { provider: 'deepgram', api_key: '...' }

@app.get("/")
def read_root():
    return {"message": "StoryFlow Backend is Running"}

import asyncio

# ... (imports)

@app.get("/models")
async def get_models():
    """Fetches available models.
       TODO: In multi-provider world, this might need to accept provider config to listing models.
       For now, we will return a static curated list of popular models across providers to simplify UI.
    """
    # Static list since fetching from all dynamic providers is complex without knowing the key first
    return {
        "data": [
            {"id": "gemini-2.5-pro", "description": "gemini-2.5-pro (Google Gemini)"},
            {"id": "gpt-4o", "description": "gpt-4o (OpenAI - Most Capable)"},
            {"id": "gpt-3.5-turbo", "description": "gpt-3.5-turbo (OpenAI - Fast & Cheap)"},
            {"id": "deepseek", "description": "deepseek (Fast & Cost Effective)"},
            {"id": "supermind-agent-v1", "description": "supermind-agent-v1 (Multi-tool Agent)"},
            {"id": "grok-2-1212", "description": "Grok 2 (X.AI)"},
        ]
    }

@app.post("/parse_file")
async def parse_file_endpoint(file: UploadFile = File(...)):
    """
    Parses a file and returns its text content.
    """
    from services.file_processing import parse_uploaded_file
    text = await parse_uploaded_file(file)
    text = await parse_uploaded_file(file)
    return {"text": text}

class RssFeedRequest(BaseModel):
    url: str

@app.post("/tools/rss-feed")
def get_rss_feed(request: RssFeedRequest):
    """Parses podcast RSS feed."""
    return parse_podcast_feed(request.url)

from fastapi import BackgroundTasks
from services.jobs import job_manager

@app.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    """Returns the status and result of a job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

from services.cache import cache_service

async def run_analysis_task(job_id: str, transcript_data: dict, model_id: str, provider_config: dict, cache_key_input: str = None):
    """Background task wrapper."""
    try:
        # Pass job_id to analyze_transcript so it can update progress
        result = await analyze_transcript(transcript_data, model_id, job_id=job_id, provider_config=provider_config)
        
        # Merge everything into a single cacheable object
        full_result = {
            "meta": {
                "video_id": transcript_data.get("video_id"),
                "title": transcript_data.get("title"),
                "duration": transcript_data.get("duration"),
                "url": provider_config.get("url") or "Uploaded File" # Or derived from request
            },
            "transcript": transcript_data.get("segments"),
            "analysis": result
        }

        # Cache the result if successful
        if cache_key_input:
            cache_service.set(cache_key_input, model_id, full_result)
            
    except Exception as e:
        print(f"Background Job Failed: {e}")
        job_manager.fail_job(job_id, str(e))

@app.get("/history")
def get_history():
    """Returns list of past analyses."""
    return {"history": cache_service.get_history_list()}

@app.get("/history/{key}")
def get_history_item(key: str):
    """Returns full analysis for a specific history item."""
    data = cache_service.get_analysis_by_key(key)
    if not data:
        raise HTTPException(status_code=404, detail="History item not found")
    return data

class DeleteHistoryRequest(BaseModel):
    keys: list[str]

@app.post("/history/delete")
def delete_history(request: DeleteHistoryRequest):
    """Deletes selected history items."""
    cache_service.delete_keys(request.keys)
    return {"message": "Deleted successfully", "count": len(request.keys)}

@app.post("/analyze")
async def analyze(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """
    Starts analysis in background and returns job_id.
    """
    print(f"Received analysis request using {request.model}")
    print(f"Provider: {request.provider_config.get('provider') if request.provider_config else 'Default'}")
    print(f"Transcription: {request.transcription_config.get('provider') if request.transcription_config else 'Default'}")
    
    # Check Cache First
    cache_input = request.url if request.url else request.transcript_text
    # We use a summarized version of transcript text for key if it's too long, 
    # but for correctness we should probably hash the whole thing. 
    # For now, let's just pass the full string to the cache service (it hashes it internally).
    
    cached_result = cache_service.get(cache_input, request.model)
    if cached_result:
        # Cache Hit! Create a job that is already done.
        job_id = job_manager.create_job()
        job_manager.update_progress(job_id, 100, "Result found in cache.")
        job_manager.complete_job(job_id, cached_result)
        
        return {
            "job_id": job_id,
            "status": "completed",
            "message": "Result found in cache.",
            "meta": cached_result.get("meta", {}),
            "transcript_preview": [] # Already done
        }

    # 1. Fetch/Process Transcript (Synchronous or lightweight async)
    try:
        if request.transcript_text:
            print("Using manual transcript text...")
            from services.transcription import process_manual_transcript
            transcript_data = process_manual_transcript(request.transcript_text)
            request_url = "Manual Input"
        elif request.url:
            print(f"Fetching from URL: {request.url}")
            transcript_data = fetch_transcript(request.url, request.transcription_config)
            request_url = request.url
        else:
            raise HTTPException(status_code=400, detail="Either 'url' or 'transcript_text' must be provided.")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Transcription failed: {str(e)}")
    
    # 2. Create Job
    job_id = job_manager.create_job()
    
    # 3. Start Background Task
    # Pass cache_key_input so the background task knows what to cache it as
    cache_key_to_save = request.url if request.url else request.transcript_text
    
    background_tasks.add_task(run_analysis_task, job_id, transcript_data, request.model, request.provider_config, cache_key_to_save)
    
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Analysis started. Poll /jobs/{job_id} for updates.",
        "meta": {
             "url": request_url,
             "video_id": transcript_data.get("video_id"),
             "title": transcript_data.get("title", "Unknown Title"),
             "duration": transcript_data.get("duration", 0)
        },
        "transcript_preview": transcript_data.get("segments", []) # Send transcript immediately so UI can show it
    }
