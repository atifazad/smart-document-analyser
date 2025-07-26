from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.services.progress_service import progress_tracker

router = APIRouter()

class JobStatusResponse(BaseModel):
    id: str
    filename: str
    total_pages: int
    processed_pages: int
    status: str
    progress_percentage: float
    current_page: int
    errors: list
    duration: Optional[float] = None

@router.get("/{job_id}")
async def get_job_status(job_id: str):
    """Get the status of a processing job"""
    job = progress_tracker.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JSONResponse({
        "id": job["id"],
        "filename": job["filename"],
        "total_pages": job["total_pages"],
        "processed_pages": job["processed_pages"],
        "status": job["status"],
        "progress_percentage": job["progress_percentage"],
        "current_page": job["current_page"],
        "errors": job["errors"],
        "duration": job.get("duration"),
        "start_time": job["start_time"],
        "end_time": job.get("end_time")
    })

@router.get("/")
async def list_jobs():
    """List all jobs (for admin/debugging)"""
    jobs = progress_tracker.get_all_jobs()
    return JSONResponse({
        "jobs": list(jobs.values()),
        "total_jobs": len(jobs),
        "active_jobs": len([j for j in jobs.values() if j["status"] == "processing"])
    })

@router.delete("/{job_id}")
async def delete_job(job_id: str):
    """Delete a job (for cleanup)"""
    job = progress_tracker.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Remove the job
    if job_id in progress_tracker.jobs:
        del progress_tracker.jobs[job_id]
    
    return JSONResponse({"message": "Job deleted successfully"})

@router.post("/cleanup")
async def cleanup_old_jobs():
    """Clean up old completed/failed jobs"""
    before_count = len(progress_tracker.jobs)
    progress_tracker.cleanup_old_jobs()
    after_count = len(progress_tracker.jobs)
    
    return JSONResponse({
        "message": "Cleanup completed",
        "jobs_removed": before_count - after_count,
        "remaining_jobs": after_count
    }) 