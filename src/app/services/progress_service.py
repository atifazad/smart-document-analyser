import asyncio
import time
from typing import Dict, Any, Optional
from uuid import uuid4

class ProgressTracker:
    """Track processing progress for real-time updates"""
    
    def __init__(self):
        self.jobs: Dict[str, Dict[str, Any]] = {}
    
    def create_job(self, total_pages: int, filename: str) -> str:
        """Create a new processing job"""
        job_id = str(uuid4())
        self.jobs[job_id] = {
            "id": job_id,
            "filename": filename,
            "total_pages": total_pages,
            "processed_pages": 0,
            "status": "processing",  # processing, completed, failed
            "start_time": time.time(),
            "current_page": 0,
            "progress_percentage": 0,
            "errors": [],
            "results": []
        }
        return job_id
    
    def update_page_progress(self, job_id: str, page_index: int, result: Dict[str, Any]):
        """Update progress when a page is completed"""
        if job_id not in self.jobs:
            return
        
        job = self.jobs[job_id]
        job["processed_pages"] += 1
        job["current_page"] = page_index + 1
        job["progress_percentage"] = min(100, (job["processed_pages"] / job["total_pages"]) * 100)
        
        # Store the result
        job["results"].append(result)
        
        # Check for errors
        if result.get("error"):
            job["errors"].append({
                "page": page_index + 1,
                "error": result["error"]
            })
    
    def complete_job(self, job_id: str, final_results: list):
        """Mark job as completed"""
        if job_id not in self.jobs:
            return
        
        job = self.jobs[job_id]
        job["status"] = "completed"
        job["end_time"] = time.time()
        job["duration"] = job["end_time"] - job["start_time"]
        job["results"] = final_results
        job["progress_percentage"] = 100
    
    def fail_job(self, job_id: str, error: str):
        """Mark job as failed"""
        if job_id not in self.jobs:
            return
        
        job = self.jobs[job_id]
        job["status"] = "failed"
        job["end_time"] = time.time()
        job["duration"] = job["end_time"] - job["start_time"]
        job["error"] = error
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a job"""
        return self.jobs.get(job_id)
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Clean up old completed/failed jobs"""
        current_time = time.time()
        jobs_to_remove = []
        
        for job_id, job in self.jobs.items():
            if job["status"] in ["completed", "failed"]:
                age_hours = (current_time - job.get("end_time", job["start_time"])) / 3600
                if age_hours > max_age_hours:
                    jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del self.jobs[job_id]
    
    def get_all_jobs(self) -> Dict[str, Dict[str, Any]]:
        """Get all jobs (for admin/debugging)"""
        return self.jobs.copy()

# Global instance
progress_tracker = ProgressTracker() 