#!/bin/bash
# Test script to validate Slurm tarballs produced by the build system

set -e

# Default values
SLURM_VERSION="${SLURM_VERSION:-25.11}"
TOOLCHAIN="${TOOLCHAIN:-resolute}"
BASE_URL="${BASE_URL:-https://slurm-factory-spack-binary-cache.vantagecompute.ai}"

echo "========================================="
echo "Slurm Tarball Validation Test"
echo "========================================="
echo "Slurm Version: ${SLURM_VERSION}"
echo "Toolchain: ${TOOLCHAIN}"
echo "Base URL: ${BASE_URL}"
echo "========================================="

# Build the Docker image
echo ""
echo "==> Building test Docker image..."

DOCKER_IMAGE_BASE="rocky"

if [[ "${TOOLCHAIN}" == "jammy" || "${TOOLCHAIN}" == "noble" || "${TOOLCHAIN}" == "resolute" ]]; then
    DOCKER_IMAGE_BASE="ubuntu"
fi

docker build \
    --build-arg SLURM_VERSION="${SLURM_VERSION}" \
    --build-arg TOOLCHAIN="${TOOLCHAIN}" \
    -f tests/dockerfiles/Dockerfile.tarball-${DOCKER_IMAGE_BASE} \
    -t slurm-tarball-test:${SLURM_VERSION}-${TOOLCHAIN} \
    .

echo ""
echo "==> Running tarball validation test..."
docker run --rm slurm-tarball-test:${SLURM_VERSION}-${TOOLCHAIN}

echo ""
echo "========================================="
echo "✓ Tarball validation test PASSED!"
echo "========================================="
