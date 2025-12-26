FROM us-docker.pkg.dev/brain-magenta/magenta-rt/magenta-rt:gpu
ARG REVISION
LABEL org.opencontainers.image.title="Melody Engine"
LABEL org.opencontainers.image.description="Prompt based instrumental music generation"
LABEL org.opencontainers.image.source="https://github.com/zbhavyai/melody-engine"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.authors="Bhavyai Gupta <https://zbhavyai.github.io>"
LABEL org.opencontainers.image.version="${REVISION}"
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
RUN uv export --quiet --frozen --no-emit-project --no-group dev --format requirements.txt -o requirements.txt
RUN uv pip install -r requirements.txt
COPY app/ ./app/
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--no-access-log"]
