import logging
import os
import tomllib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler
from pathlib import Path

import setuptools_scm
from fastapi import FastAPI, staticfiles
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.settings import settings
from app.service.job_manager import JobManager


def configure_logging() -> None:
    level = getattr(logging, settings.log_level.upper())
    handlers: list[logging.Handler] = [logging.StreamHandler()]

    if settings.log_file:
        log_file = os.path.expandvars(str(settings.log_file))
        log_file = str(Path(log_file).expanduser())

        Path(log_file).parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=settings.log_file_max_size,
            backupCount=settings.log_file_backup_count,
        )
        handlers.append(file_handler)

    logging.basicConfig(
        level=level,
        format=settings.log_format,
        handlers=handlers,
        force=True,
    )


def get_project_metadata() -> dict[str, str]:
    pkg_version = setuptools_scm.get_version(root="..", relative_to=__file__)

    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    with pyproject_path.open("rb") as f:
        pyproject = tomllib.load(f)
    project = pyproject.get("project", {})
    return {
        "title": project.get("name", ""),
        "description": project.get("description", ""),
        "version": pkg_version,
        "docs_url": "/docs",
    }


metadata = get_project_metadata()
configure_logging()


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    logger = logging.getLogger("app.main")
    logger.info("--------------------------------------------------------------------------------")
    logger.info("Starting application")
    logger.info("--------------------------------------------------------------------------------")

    manager = JobManager()
    await manager.start_worker()

    yield

    await manager.stop_worker()

    logger.info("--------------------------------------------------------------------------------")
    logger.info("Shutting down application")
    logger.info("--------------------------------------------------------------------------------")


app = FastAPI(
    title=metadata["title"],
    description=metadata["description"],
    version=metadata["version"],
    docs_url=metadata["docs_url"],
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router=api_router, prefix="/api/v1")

app.mount(
    "/",
    staticfiles.StaticFiles(directory=str(Path(__file__).parent / "static"), html=True),
    name="static",
)
