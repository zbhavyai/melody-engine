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

function sh_lint() {
    mapfile -d '' -t staged_sh < <(git diff --cached --name-only -z --diff-filter=ACMR -- '*.sh' || true)

    if ((${#staged_sh[@]} == 0)); then
        return 0
    fi

    for f in "${staged_sh[@]}"; do
        if [[ ! -f "$f" ]]; then
            continue
        fi

        if ! uv run shfmt --diff --indent 4 -- "$f"; then
            block "[ERROR] shfmt failed for $f"
        fi

        if ! uv run shellcheck --external-sources --exclude=SC2034 -- "$f"; then
            block "[ERROR] shellcheck failed for $f"
        fi
    done
}

CHECKS="py_lint sh_lint"

for CHECK in $CHECKS; do
    ($CHECK) || exit $?
done
