#!/usr/bin/env bash
set -euo pipefail

function block() {
    echo -e "\n\n"
    echo "$@"
    echo "[ERROR] Commit blocked."
    exit 1
}

function py_lint() {
    mapfile -d '' -t staged_py < <(git diff --cached --name-only -z --diff-filter=ACMR -- '*.py' || true)

    if ((${#staged_py[@]} == 0)); then
        return 0
    fi

    if ! uv run ruff format --check --quiet --force-exclude -- "${staged_py[@]}"; then
        block "[ERROR] ruff format failed"
    fi

    if ! uv run ruff check --quiet --force-exclude -- "${staged_py[@]}"; then
        block "[ERROR] ruff check failed"
    fi

    if ! uv run mypy --pretty -- "${staged_py[@]}"; then
        block "[ERROR] mypy failed"
    fi
}

(py_lint) || exit $?
