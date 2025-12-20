from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from app.schemas.job_schema import JobStatus, JobSubmitRequest


@dataclass
class Job:
    id: UUID
    request: JobSubmitRequest
    status: JobStatus = JobStatus.QUEUED
    created_at: datetime = field(default_factory=datetime.now)
    filename: str | None = None
    error: str | None = None
