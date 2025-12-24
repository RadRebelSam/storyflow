from typing import Dict, Any, Optional
import uuid
from enum import Enum
from datetime import datetime

class JobStatus(Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class JobManager:
    _instance = None
    _jobs: Dict[str, Dict[str, Any]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(JobManager, cls).__new__(cls)
        return cls._instance

    def create_job(self) -> str:
        """Creates a new job and returns its ID."""
        job_id = str(uuid.uuid4())
        self._jobs[job_id] = {
            "id": job_id,
            "status": JobStatus.QUEUED.value,
            "progress": 0,
            "message": "Queued...",
            "created_at": datetime.now().isoformat(),
            "result": None,
            "error": None
        }
        return job_id

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self._jobs.get(job_id)

    def update_progress(self, job_id: str, progress: int, message: str):
        if job_id in self._jobs:
            self._jobs[job_id]["status"] = JobStatus.PROCESSING.value
            self._jobs[job_id]["progress"] = progress
            self._jobs[job_id]["message"] = message

    def complete_job(self, job_id: str, result: Any):
        if job_id in self._jobs:
            self._jobs[job_id]["status"] = JobStatus.COMPLETED.value
            self._jobs[job_id]["progress"] = 100
            self._jobs[job_id]["message"] = "Analysis Complete"
            self._jobs[job_id]["result"] = result

    def fail_job(self, job_id: str, error: str):
        if job_id in self._jobs:
            self._jobs[job_id]["status"] = JobStatus.FAILED.value
            self._jobs[job_id]["error"] = error
            self._jobs[job_id]["message"] = f"Failed: {error}"

# Global instance
job_manager = JobManager()
