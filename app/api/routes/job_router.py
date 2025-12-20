import logging
from uuid import UUID

from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.schemas.job_schema import JobInfo, JobSubmitRequest, JobSubmitResponse
from app.service.job_manager import JobManager

logger = logging.getLogger(__name__)
router = APIRouter()
job_manager = JobManager()


@router.post(
    "/generate",
    response_model=JobSubmitResponse,
)
async def request_generation(request: JobSubmitRequest) -> JobSubmitResponse:
    logger.debug("request_generation")

    job = await job_manager.submit_job(request)
    return JobSubmitResponse(
        id=job.id,
        status=job.status,
        message="Job submitted successfully",
    )


@router.get(
    "/status/{job_id}",
    response_model=JobInfo,
)
async def get_job_status(job_id: UUID) -> JobInfo:
    logger.debug("get_job_status")

    job = job_manager.get_job(job_id)
    return JobInfo.model_validate(job)


@router.get(
    "/download/{filename}",
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
