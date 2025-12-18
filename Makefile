CONTAINER_ENGINE := $(shell if command -v podman >/dev/null 2>&1; then echo podman; else echo docker; fi)
REVISION := $(shell git rev-parse --short HEAD)

.PHONY: init format lint build clean run help

define CHECK_DEPENDENCY
	@for cmd in $(1); do \
		if ! command -v $$cmd >/dev/null 2>&1; then \
			echo "Couldn't find $$cmd!"; \
			exit 1; \
		fi; \
	done
endef

.deps:
	$(call CHECK_DEPENDENCY, $(CONTAINER_ENGINE) uv)

init: .deps
	@ln -sf $(CURDIR)/.hooks/pre-commit.sh .git/hooks/pre-commit
	@uv sync
	@$(CONTAINER_ENGINE) image pull us-docker.pkg.dev/brain-magenta/magenta-rt/magenta-rt:gpu

format:
	@uv run ruff format --force-exclude -- app

lint:
	@uv run ruff check --quiet --force-exclude -- app
	@uv run mypy --pretty -- app

build: clean
	@SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0+$(REVISION) uv run python -m build --outdir dist

clean:
	@rm -rf build/ dist/ *.egg-info/

run:
	@SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0+$(REVISION) uv run python -m app.cli

help:
	@echo "Available targets:"
	@echo "  init       - Set up uv environment and install requirements"
	@echo "  format     - Run format on all python files"
	@echo "  lint       - Run lint on all python files"
	@echo "  build      - Build the app package"
	@echo "  clean      - Clean build artifacts"
	@echo "  run        - Run the app"
	@echo "  help       - Show this help message"
