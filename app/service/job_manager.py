from __future__ import annotations

import asyncio
import contextlib
import logging
import re
import uuid
from pathlib import Path
from uuid import UUID

from app.core.settings import settings
from app.models.job_model import Job
from app.schemas.job_schema import JobStatus, JobSubmitRequest
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

        logger.info("Starting background worker...")
        await asyncio.to_thread(self.engine.load_magentart_in_memory)
        self.worker_task = asyncio.create_task(self._worker())
        logger.info("Background worker started.")

    async def stop_worker(self) -> None:
        """
        Stops the background worker.
        """

        if self.worker_task:
            self.worker_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.worker_task

    async def submit_job(self, request: JobSubmitRequest) -> Job:
        """
        Submits a job.
        Raises asyncio.QueueFull if queue is full.
        """

        job = Job(id=uuid.uuid4(), request=request)
        logger.info(f"Create job with id={job.id}")

        # this raises QueueFull immediately if the queue is full
        self.queue.put_nowait(job.id)

        self.jobs[job.id] = job
        logger.info(f"Job submitted {job.id}")

        return job

    def get_job(self, job_id: UUID) -> Job | None:
        """
        Retrieves a job by its ID.
        """

        return self.jobs.get(job_id)

    def get_file_path(self, filename: str) -> Path:
        """
        Retrieves the file path for a given filename.
        """

        return Path(settings.output_dir) / filename

    async def _worker(self) -> None:
        """
        Infinite loop processing jobs from the queue.
        """

        logger.info("Starting worker loop...")
        while True:
            try:
                job_id = await self.queue.get()
                job = self.jobs[job_id]

                job.status = JobStatus.PROCESSING
                logger.info(f"Processing job {job_id}")

                try:
                    # prepare output path
                    slug = self._slugify(job.request.prompt)

                    # use string representation of UUID for filename
                    filename = f"{slug}_{str(job_id)[:8]}.{job.request.format}"
                    out_path = Path(settings.output_dir) / filename

                    # run blocking engine in a separate thread
                    await asyncio.to_thread(
                        self.engine.generate_music,
                        prompt=job.request.prompt,
                        duration_ms=int(job.request.duration_s * 1000),
                        out_path=str(out_path),
                        fmt=job.request.format,
                        gain_db=job.request.gain_db,
                    )

                    job.filename = filename
                    job.status = JobStatus.COMPLETED
                    logger.info(f"Job {job_id} COMPLETED")

                except Exception as e:
                    logger.error(f"Job {job_id} FAILED: {e}")
                    job.status = JobStatus.FAILED
                    job.error = str(e)
                finally:
                    self.queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Unexpected worker error: {e}")
                await asyncio.sleep(5)

    def _slugify(self, text: str) -> str:
        """
        Creates a URL-friendly slug of max length 50 from the given text.
        """

        text = text.lower()
        text = re.sub(r"[^a-z0-9]+", "-", text)
        return text.strip("-")[:50]
