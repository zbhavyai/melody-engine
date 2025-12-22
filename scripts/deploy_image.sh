#!/usr/bin/env bash
#
# Builds container image using make container-build and pushes to Docker Hub.
# Manual alternative to .github/workflows/container.yml workflow, because of disk space restraints.

set -euo pipefail

IMAGE_BASE="docker.io/zbhavyai/melody-engine"
LOCAL_IMAGE_BASE="localhost/melody-engine"

# -----------------------------------------------------------------------------
# ensure HEAD is exactly on a semver tag
# -----------------------------------------------------------------------------
git fetch --tags

if ! TAG="$(git describe --tags --abbrev=0 --exact-match --match 'v*.*.*' 2>/dev/null)"; then
    echo "ERROR: HEAD is not exactly on a semver tag (vX.Y.Z)"
    exit 1
fi

# -----------------------------------------------------------------------------
# validate semver format
# -----------------------------------------------------------------------------
if ! [[ "${TAG}" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "ERROR: Tag '${TAG}' is not valid semver (vX.Y.Z)"
    exit 1
fi

VERSION="${TAG#v}"
MAJOR="${VERSION%%.*}"
MINOR="$(cut -d. -f1,2 <<<"${VERSION}")"

echo "Git tag      : ${TAG}"
echo "Image Semver : ${VERSION}"
echo "Image Major  : ${MAJOR}"
echo "Image Minor  : ${MINOR}"

# -----------------------------------------------------------------------------
# determine latest tag
# -----------------------------------------------------------------------------
LATEST_TAG="$(git tag -l 'v*.*.*' | sort -V | tail -n 1)"

IS_LATEST="false"
if [[ "${TAG}" == "${LATEST_TAG}" ]]; then
    IS_LATEST="true"
fi

echo "Latest tag in repository: ${LATEST_TAG}"
echo "Is latest: ${IS_LATEST}"

# -----------------------------------------------------------------------------
# build image via make target
# -----------------------------------------------------------------------------
echo "Building container image"

make container-build

LOCAL_IMAGE="${LOCAL_IMAGE_BASE}:${VERSION}"

# -----------------------------------------------------------------------------
# ensure local image exists
# -----------------------------------------------------------------------------
if ! podman image exists "${LOCAL_IMAGE}"; then
    echo "ERROR: Expected local image '${LOCAL_IMAGE}' does not exist"
    exit 1
fi

# -----------------------------------------------------------------------------
# build tag list
# -----------------------------------------------------------------------------
TAGS=(
    "${VERSION}"
    "${MINOR}"
    "${MAJOR}"
)

if [[ "${IS_LATEST}" == "true" ]]; then
    TAGS+=("latest")
fi

# -----------------------------------------------------------------------------
# tag and push
# -----------------------------------------------------------------------------
for IMAGE_TAG in "${TAGS[@]}"; do
    TARGET_IMAGE="${IMAGE_BASE}:${IMAGE_TAG}"

    echo "Tagging ${LOCAL_IMAGE} -> ${TARGET_IMAGE}"
    podman image tag "${LOCAL_IMAGE}" "${TARGET_IMAGE}"

    echo "Pushing ${TARGET_IMAGE}"
    podman image push "${TARGET_IMAGE}"
done

echo "Done."
