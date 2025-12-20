FROM us-docker.pkg.dev/brain-magenta/magenta-rt/magenta-rt:gpu
ARG REVISION
ENV SETUPTOOLS_SCM_PRETEND_VERSION=${REVISION} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /opt/app
COPY pyproject.toml uv.lock ./
RUN uv pip install --system --no-deps -r pyproject.toml
COPY app/ ./app/
EXPOSE 8080
CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8080"]
