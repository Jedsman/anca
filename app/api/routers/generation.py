"""
Content Generation Routes
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException, status
import logging

from app.schemas.models import GenerateRequest, JobResponse, ErrorResponse
from app.services.job_service import job_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Content Generation"])


@router.post(
    "/generate",
    response_model=JobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate content for a topic",
    responses={
        202: {"description": "Job created successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request"}
    }
)
async def generate_content(
    request: GenerateRequest,
    background_tasks: BackgroundTasks
):
    """
    Start content generation for a given topic.
    
    The job runs asynchronously in the background.
    Use the returned job_id to track progress via /status/{job_id}.
    """
    try:
        job = job_service.create_job(
            topic=request.topic,
            affiliate=request.affiliate,
            niche=request.niche,
            discover_mode=request.discover_mode,
            provider=request.provider,
            model=request.model
        )
        background_tasks.add_task(job_service.run_job, job.job_id)
        logger.info(f"Created job {job.job_id} for topic: {request.topic}")
        return job
    except Exception as e:
        logger.error(f"Error creating job: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job: {str(e)}"
        )


@router.get(
    "/status/{job_id}",
    response_model=JobResponse,
    summary="Get job status",
    responses={
        200: {"description": "Job status retrieved"},
        404: {"model": ErrorResponse, "description": "Job not found"}
    }
)
async def get_job_status(job_id: str):
    """Get the status of a content generation job"""
    try:
        return job_service.get_job(job_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/jobs",
    response_model=list[JobResponse],
    summary="List all jobs"
)
async def list_jobs():
    """List all content generation jobs"""
    return job_service.list_jobs()
