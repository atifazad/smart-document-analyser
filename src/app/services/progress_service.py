import asyncio
import time
from typing import Dict, Any, Optional
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)

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
            "status": "preparing",  # preparing, processing, completed, failed
            "start_time": time.time(),
            "current_page": 0,
            "progress_percentage": 0,
            "current_step": "uploading",
            "step_description": "Uploading and preparing document...",
            "errors": [],
            "results": []
        }
        return job_id
    
    def mark_preparing_complete(self, job_id: str):
        """Mark job as ready to start processing pages (after file conversion)"""
        if job_id not in self.jobs:
            return
        job = self.jobs[job_id]
        job["status"] = "processing"
        job["progress_percentage"] = 10
        job["current_step"] = "processing_pages"
        job["step_description"] = f"Processing page 1 of {job['total_pages']}..."
    
    def update_page_progress(self, job_id: str, page_index: int, result: Dict[str, Any]):
        """Update progress when a page is completed"""
        if job_id not in self.jobs:
            return
        
        job = self.jobs[job_id]
        job["processed_pages"] += 1
        job["current_page"] = page_index + 1
        
        # Calculate progress: 10% (preparation) + 70% (pages) + 20% (finalization)
        if job["total_pages"] == 1:
            # Single page: 10% prep + 70% processing + 20% finalization
            progress = 10 + 70
        else:
            # Multiple pages: 10% prep + (pages completed / total pages) * 70% + 20% finalization
            progress = 10 + (job["processed_pages"] / job["total_pages"]) * 70
        
        job["progress_percentage"] = min(80, progress)  # Cap at 80% until finalization
        job["step_description"] = f"Processing page {job['current_page']} of {job['total_pages']}..."
        
        # Store the result
        job["results"].append(result)
        
        # Check for errors
        if result.get("error"):
            job["errors"].append({
                "page": page_index + 1,
                "error": result["error"]
            })
    
    def update_step(self, job_id: str, step: str, description: str, progress: int):
        """Update the current step and progress"""
        if job_id not in self.jobs:
            return
        job = self.jobs[job_id]
        job["current_step"] = step
        job["step_description"] = description
        job["progress_percentage"] = progress
    
    def mark_vector_store_creation(self, job_id: str):
        """Mark that vector store creation has started"""
        if job_id not in self.jobs:
            return
        job = self.jobs[job_id]
        job["current_step"] = "vector_store"
        job["step_description"] = "Creating vector store for document..."
        job["progress_percentage"] = 80
    
    def mark_finalization(self, job_id: str):
        """Mark that finalization has started"""
        if job_id not in self.jobs:
            return
        job = self.jobs[job_id]
        job["current_step"] = "finalizing"
        job["step_description"] = "Finalizing results..."
        job["progress_percentage"] = 90
    
    def update_substep_progress(self, job_id: str, page_index: int, substep: int, total_substeps: int):
        """Update progress for a substep within a page (for granular progress)"""
        if job_id not in self.jobs:
            return
        job = self.jobs[job_id]
        # Calculate progress: preparation (5%) + (pages completed + substeps completed) / (total_pages * total_substeps) * 95%
        completed_pages = job["processed_pages"]
        total_pages = job["total_pages"]
        # Each page has total_substeps, so total steps = total_pages * total_substeps
        # Progress for completed pages:
        progress = 5 + (completed_pages / total_pages) * 95
        # Progress for current page's substeps:
        progress += (substep / total_substeps) * (95 / total_pages)
        job["progress_percentage"] = min(99, progress)  # Don't hit 100 until complete
        job["current_page"] = page_index + 1
    
    def complete_job(self, job_id: str, final_results: list):
        """Mark job as completed"""
        if job_id not in self.jobs:
            logger.error(f"Job {job_id} not found in complete_job")
            return
        
        job = self.jobs[job_id]
        job["status"] = "completed"
        job["end_time"] = time.time()
        job["duration"] = job["end_time"] - job["start_time"]
        job["results"] = final_results
        job["progress_percentage"] = 100
        logger.info(f"Job {job_id} completed with {len(final_results)} results")
    
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