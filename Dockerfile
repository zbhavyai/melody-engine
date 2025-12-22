FROM us-docker.pkg.dev/brain-magenta/magenta-rt/magenta-rt:gpu
ARG REVISION
ENV SETUPTOOLS_SCM_PRETEND_VERSION=${REVISION} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1 \
    UV_BREAK_SYSTEM_PACKAGES=1
ENV TF_GPU_ALLOCATOR=cuda_malloc_async
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /opt/app
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml uv.lock ./
RUN apt-get update && apt-get install -y ffmpeg
RUN uv pip install --system -r pyproject.toml
COPY app/ ./app/
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
