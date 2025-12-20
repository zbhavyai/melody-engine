from datetime import datetime
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


class JobInfo(_FromORM):
    id: UUID = Field(..., description="Job identifier")
    status: JobStatus = Field(..., description="Job status")
    prompt: str = Field(..., description="Prompt used for generation")
    created_at: datetime = Field(..., description="Timestamp when the job was created")
    filename: str | None = Field(None, description="Filename of the generated audio")
    error: str | None = Field(None, description="Error message if the job failed")


class JobSubmitRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Text prompt for music generation")
    duration_s: float = Field(..., gt=0, le=36000, description="Duration in seconds")
    gain_db: float = Field(default=0.0, description="Gain adjustment in dB")
    format: str = Field(default="mp3", pattern="^(wav|flac|mp3)$", description="Output audio format")


class JobSubmitResponse(BaseModel):
    id: UUID = Field(..., description="Job identifier")
    status: JobStatus = Field(..., description="Job status")
    message: str = Field(..., description="Job submission message")
