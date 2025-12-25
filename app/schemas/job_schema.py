from datetime import UTC, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class _FromORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class JobRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Text prompt for music generation")
    duration_s: float = Field(..., gt=0, le=36000, description="Duration in seconds")
    gain_db: float = Field(default=0.0, description="Gain adjustment in dB")
    format: str = Field(default="mp3", pattern="^(wav|flac|mp3)$", description="Output audio format")


class JobAcknowledgment(BaseModel):
    id: UUID = Field(..., description="Job identifier")
    status: JobStatus = Field(..., description="Job status")
    created_at: datetime = Field(..., description="Job submit timestamp")


class Job(_FromORM):
    id: UUID = Field(..., description="Job identifier")
    prompt: str = Field(..., description="Prompt used for generation")
    duration_s: float = Field(..., description="Duration in seconds")
    gain_db: float = Field(..., description="Gain adjustment in dB")
    format: str = Field(..., description="Output audio format")
    created_at: datetime = Field(..., description="Job submit timestamp")
    status: JobStatus = Field(..., description="Job status")
    output_name: str | None = Field(None, description="Filename of the generated audio")
    message: str | None = Field(None, description="Other details")

    @classmethod
    def from_request(
        cls,
        job_id: UUID,
        request: JobRequest,
        output_name: str = "",
        message: str = "",
    ) -> "Job":
        return cls(
            id=job_id,
            prompt=request.prompt,
            duration_s=request.duration_s,
            gain_db=request.gain_db,
            format=request.format,
            created_at=datetime.now(UTC),
            status=JobStatus.QUEUED,
            output_name=output_name,
            message=message,
        )

    def to_acknowledgment(self) -> JobAcknowledgment:
        return JobAcknowledgment(
            id=self.id,
            status=self.status,
            created_at=self.created_at,
        )
