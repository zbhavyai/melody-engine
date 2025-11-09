CONTAINER_ENGINE := $(shell if command -v podman >/dev/null 2>&1; then echo podman; else echo docker; fi)
REVISION := $(shell git rev-parse --short HEAD)
VENV_DIR := .venv/PY-VENV

.PHONY: init format lint build run help

define CHECK_DEPENDENCY
	@for cmd in $(1); do \
		if ! command -v $$cmd &>/dev/null; then \
			echo "Couldn't find $$cmd!"; \
			exit 1; \
		fi; \
	done
endef

.deps-container:
	$(call CHECK_DEPENDENCY, $(CONTAINER_ENGINE))

init:
	@ln -sf $(CURDIR)/.hooks/pre-commit.sh .git/hooks/pre-commit
	@if [ ! -d "$(VENV_DIR)" ]; then \
		python3 -m venv $(VENV_DIR); \
	fi
	@. $(VENV_DIR)/bin/activate && pip install --upgrade pip && pip install .
	@$(CONTAINER_ENGINE) image pull us-docker.pkg.dev/brain-magenta/magenta-rt/magenta-rt:gpu

format:
	@. $(VENV_DIR)/bin/activate && \
	ruff format --force-exclude -- app

lint:
	@. $(VENV_DIR)/bin/activate && \
	ruff check --force-exclude -- app && \
	mypy --pretty -- app

build:
	@. $(VENV_DIR)/bin/activate && \
	SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0+$(REVISION) python -m build --outdir dist

run:
	@. $(VENV_DIR)/bin/activate && \
	SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0+$(REVISION) python -m app.cli

help:
	@echo "Available targets:"
	@echo "  init		- Set up py venv and install requirements"
	@echo "  format     - Run format on all python files"
	@echo "  lint       - Run lint on all python files"
	@echo "  build      - Build the app package"
	@echo "  run        - Run the app"
	@echo "  help       - Show this help message"
