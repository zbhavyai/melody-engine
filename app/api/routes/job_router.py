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
        job_ack = await job_manager.submit_job(request)
        return JobAcknowledgment.model_validate(job_ack)
    except asyncio.QueueFull:
        logger.error("Job queue is full")
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Queue is full")


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


@router.get(
    "/{job_id}/download",
    response_class=FileResponse,
)
async def download_file(job_id: UUID) -> FileResponse:
    logger.debug("download_file")

    try:
        path = job_manager.get_file_path_for_job(job_id)

        if not path.exists():
            raise FileNotFoundError(f"No output file found for job id={job_id}")

        return FileResponse(
            path=path,
            media_type=f"audio/{path.suffix.lstrip('.')}",
            filename=path.name,
        )
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.args[0])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.args[0])
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.args[0])
    except Exception as e:
        logger.error("Unexpected error while retrieving file for job id=%s: %s", job_id, str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
