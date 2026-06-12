#!/bin/bash
# Copyright 2025 Vantage Compute Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Test script to validate Slurm tarballs produced by the build system

set -e

# Default values
SLURM_VERSION="${SLURM_VERSION:-25.11}"
TOOLCHAIN="${TOOLCHAIN:-resolute}"
ARCHITECTURE="${ARCHITECTURE:-amd64}"
LOCAL_TARBALL_PATH="${LOCAL_TARBALL_PATH:-}"

echo "========================================="
echo "Slurm Tarball Validation Test"
echo "========================================="
echo "Slurm Version: ${SLURM_VERSION}"
echo "Toolchain: ${TOOLCHAIN}"
echo "Architecture: ${ARCHITECTURE}"
if [ -n "$LOCAL_TARBALL_PATH" ]; then
    echo "Source: local (${LOCAL_TARBALL_PATH})"
else
    echo "Source: local tarball required"
fi
echo "========================================="

# Build the Docker image
echo ""
echo "==> Building test Docker image..."

DOCKER_IMAGE_BASE="rocky"

if [[ "${TOOLCHAIN}" == "jammy" || "${TOOLCHAIN}" == "noble" || "${TOOLCHAIN}" == "resolute" ]]; then
    DOCKER_IMAGE_BASE="ubuntu"
fi

if [ -z "$LOCAL_TARBALL_PATH" ]; then
    echo "[ERROR] LOCAL_TARBALL_PATH is required" >&2
    exit 1
fi

if [ ! -f "$LOCAL_TARBALL_PATH" ]; then
    echo "[ERROR] Local tarball not found: $LOCAL_TARBALL_PATH" >&2
    exit 1
fi

CONTEXT_DIR=$(mktemp -d)
trap "rm -rf $CONTEXT_DIR" EXIT
mkdir -p "$CONTEXT_DIR/tarball"
cp "$LOCAL_TARBALL_PATH" "$CONTEXT_DIR/tarball/"
cp tests/dockerfiles/Dockerfile.tarball-${DOCKER_IMAGE_BASE} "$CONTEXT_DIR/"

docker build \
    --build-arg SLURM_VERSION="${SLURM_VERSION}" \
    --build-arg TOOLCHAIN="${TOOLCHAIN}" \
    --build-arg ARCHITECTURE="${ARCHITECTURE}" \
    -f "$CONTEXT_DIR/Dockerfile.tarball-${DOCKER_IMAGE_BASE}" \
    -t slurm-tarball-test:${SLURM_VERSION}-${TOOLCHAIN} \
    "$CONTEXT_DIR"

echo ""
echo "==> Running tarball validation test..."
docker run --rm slurm-tarball-test:${SLURM_VERSION}-${TOOLCHAIN}

echo ""
echo "========================================="
echo "✓ Tarball validation test PASSED!"
echo "========================================="
