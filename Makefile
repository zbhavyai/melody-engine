CONTAINER_ENGINE := $(shell if command -v podman >/dev/null 2>&1; then echo podman; else echo docker; fi)
LAST_TAG := $(shell git describe --tags --abbrev=0 --match "v*.*.*" 2>/dev/null || echo "v0.0.0")
REVISION := $(shell git rev-parse --short HEAD)

.PHONY: init format lint dev run build clean container-build container-run container-stop container-logs container-destroy help

init:
	@ln -sf $(CURDIR)/.hooks/pre-commit.sh .git/hooks/pre-commit
	@mkdir -p outputs
	@uv sync

format:
	@uv run ruff format --force-exclude -- app

lint:
	@uv run ruff check --quiet --force-exclude -- app
	@uv run mypy --pretty -- app

dev:
	@SETUPTOOLS_SCM_PRETEND_VERSION=$(LAST_TAG)+$(REVISION) uv run fastapi dev app/main.py --host 0.0.0.0 --port 8080

run:
	@SETUPTOOLS_SCM_PRETEND_VERSION=$(LAST_TAG)+$(REVISION) uv run fastapi run app/main.py --host 0.0.0.0 --port 8080

build: clean
	@SETUPTOOLS_SCM_PRETEND_VERSION=$(LAST_TAG)+$(REVISION) uv run python -m build --outdir dist

clean:
	@rm -rf build/ dist/ *.egg-info/ .venv/ .mypy_cache/ .ruff_cache/

container-build:
	@REVISION=$(LAST_TAG)+$(REVISION) $(CONTAINER_ENGINE) compose build

container-run:
	@REVISION=$(LAST_TAG)+$(REVISION) $(CONTAINER_ENGINE) compose up --detach

container-stop:
	@REVISION=$(LAST_TAG)+$(REVISION) $(CONTAINER_ENGINE) compose down

container-logs:
	@REVISION=$(LAST_TAG)+$(REVISION) $(CONTAINER_ENGINE) compose logs --follow

container-destroy:
	@REVISION=$(LAST_TAG)+$(REVISION) $(CONTAINER_ENGINE) compose down --volumes --rmi local

help:
	@echo "Available targets:"
	@echo "  init               - Set up environment and install dependencies"
	@echo "  format             - Run format on all python files"
	@echo "  lint               - Run lint on all python files"
	@echo "  dev                - Run the app in development mode"
	@echo "  run                - Run the app"
	@echo "  build              - Build the app package"
	@echo "  clean              - Clean build artifacts"
	@echo "  container-build	- Build the container image"
	@echo "  container-run      - Run the container"
	@echo "  container-stop     - Stop the container"
	@echo "  container-logs     - Show container logs"
	@echo "  container-destroy  - Destroy the container and remove volumes and images"
	@echo "  help               - Show this help message"
