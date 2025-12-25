from __future__ import annotations

import asyncio
import contextlib
import logging
import re
import uuid
from pathlib import Path
from uuid import UUID

from app.core.settings import settings
from app.schemas.job_schema import Job, JobAcknowledgment, JobRequest, JobStatus
from app.service.engine import AudioEngine

logger = logging.getLogger(__name__)


class JobManager:
    _instance: JobManager | None = None

    def __new__(cls) -> JobManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self) -> None:
        self.jobs: dict[UUID, Job] = {}
        self.queue: asyncio.Queue[UUID] = asyncio.Queue(maxsize=settings.max_queue_size)
        self.engine = AudioEngine()
        self.worker_task: asyncio.Task | None = None

    async def start_worker(self) -> None:
        """
        Starts the background worker.
        """
        logger.info("Starting background worker")

        await asyncio.to_thread(self.engine.load_magenta_rt_in_memory)
        self.worker_task = asyncio.create_task(self._worker())
        logger.info("Background worker started.")

    async def stop_worker(self) -> None:
        """
        Stops the background worker.
        """
        logger.info("Stopping background worker")

        if self.worker_task:
            self.worker_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.worker_task

    async def submit_job(self, request: JobRequest) -> JobAcknowledgment:
        """
        Submits a job.
        Raises asyncio.QueueFull if queue is full.
        """
        job = Job.from_request(job_id=uuid.uuid4(), request=request)
        logger.info("Creating job with id=%s", job.id)
        logger.info("Job details: %s", job)

        # this raises QueueFull immediately if the queue is full
        self.queue.put_nowait(job.id)

        self.jobs[job.id] = job
        logger.info("Job submitted with id=%s", job.id)
        return job.to_acknowledgment()

    def get_job(self, job_id: UUID) -> Job | None:
        """
        Retrieves a job by ID.
        """
        logger.info("Get job by id=%s", job_id)

        return self.jobs.get(job_id)

    def get_file_path_for_job(self, job_id: UUID) -> Path:
        """
        Retrieves the file path for a given job.
        """

        job = self.get_job(job_id)

        if job is None:
            logger.error("Job not found with id=%s", job_id)
            raise KeyError("Job not found")
        if job.status != JobStatus.COMPLETED:
            logger.error("Job with id=%s isn't completed yet", job_id)
            raise ValueError("Job isn't completed yet")
        if not job.output_name:
            logger.error("No output file found for job id=%s", job_id)
            raise FileNotFoundError(f"No output file found for job id={job_id}")

        path = Path(settings.output_dir) / job.output_name
        logger.info(f"Retrieve file path for job id={job_id}: {path}")
        return path

    def cancel_job(self, job_id: UUID) -> None:
        """
        Cancel a job by its ID.
        """
        logger.info("Cancel job by id=%s", job_id)

        job = self.get_job(job_id)

        if job is None:
            raise KeyError("Job not found")

        if job.status == JobStatus.PROCESSING:
            raise ValueError("Cannot cancel a processing job")

        # best-effort artifact cleanup
        if job.output_name:
            path = Path(settings.output_dir) / job.output_name
            if path.exists():
                path.unlink()

        del self.jobs[job_id]
        logger.info("Cancelled and removed job id=%s", job_id)

    def clear_jobs(self, status: JobStatus | None = None) -> int:
        """
        Clear jobs by status.
        """
        logger.info("Clearing jobs with status=%s", status)

        removed = 0

        for job_id, job in list(self.jobs.items()):
            if job.status == JobStatus.PROCESSING:
                # skip processing jobs
                continue

            if status is None or job.status == status:
                # best-effort artifact cleanup
                if job.output_name:
                    path = Path(settings.output_dir) / job.output_name
                    if path.exists():
                        path.unlink()

                del self.jobs[job_id]
                removed += 1

        logger.warning("Removed %d jobs", removed)
        return removed

    async def _worker(self) -> None:
        """
        Infinite loop processing jobs from the queue.
        """

        logger.info("Starting worker loop")
        while True:
            try:
                job_id = await self.queue.get()
                job = self.jobs.get(job_id)

                if job is None:
                    logger.info("Skipping cancelled job id=%s", job_id)
                    self.queue.task_done()
                    continue

                job.status = JobStatus.PROCESSING
                logger.info("Processing job with id=%s", job_id)

                try:
                    # prepare output path
                    slug = self._slugify(job.prompt)

                    # use string representation of UUID for filename
                    filename = f"{slug}-{str(job_id)[:8]}.{job.format}"
                    out_path = Path(settings.output_dir) / filename

                    # update the job with output path
                    job.output_name = filename

                    # run blocking engine in a separate thread
                    await asyncio.to_thread(
                        self.engine.generate_music,
                        prompt=job.prompt.strip(),
                        duration_ms=int(job.duration_s * 1000),
                        out_path=str(out_path),
                        fmt=job.format,
                        gain_db=job.gain_db,
                    )

                    job.output_name = filename
                    job.status = JobStatus.COMPLETED
                    logger.info("Job with id=%s COMPLETED", job_id)

                except Exception as e:
                    logger.error("Job with id=%s FAILED: %s", job_id, e)
                    job.status = JobStatus.FAILED
                    job.message = str(e)
                finally:
                    self.queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Unexpected worker error: {e}")
                await asyncio.sleep(5)

    @staticmethod
    def _slugify(text: str) -> str:
        """
        Creates a URL-friendly slug of max length 50 from the given text.
        """

        text = text.lower()
        text = re.sub(r"[^a-z0-9]+", "-", text)
        max_len = settings.filename_trim_length
        return text.strip("-")[:max_len]
