import asyncio
import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from app.schemas.job_schema import Job, JobAcknowledgment, JobRequest
from app.service.job_manager import JobManager

logger = logging.getLogger(__name__)
router = APIRouter()
job_manager = JobManager()


@router.post(
    "",
    response_model=JobAcknowledgment,
)
async def request_generation(request: JobRequest) -> JobAcknowledgment:
    logger.debug("request_generation")

    try:
        jobAck = await job_manager.submit_job(request)
        return JobAcknowledgment.model_validate(jobAck)
    except asyncio.QueueFull:
        logger.error("Job queue is full")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Queue is full")


@router.get(
    "/{job_id}",
    response_model=Job,
)
async def get_job_status(job_id: UUID) -> Job:
    logger.debug("get_job_status")

    job = job_manager.get_job(job_id)

    if job is None:
        logger.error("Job not found with id=%s", job_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    return Job.model_validate(job)


@router.post(
    "{job_id}",
    response_class=FileResponse,
)
async def download_file(filename: str) -> FileResponse:
    logger.debug("download_file")

    path = job_manager.get_file_path(filename)
    return FileResponse(
        path=path,
        media_type=f"audio/{path.suffix.lstrip('.')}",
        filename=filename,
    )
