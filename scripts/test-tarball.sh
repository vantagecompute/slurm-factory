#!/bin/bash
# Test script to validate Slurm tarballs produced by the build system

set -e

# Default values
SLURM_VERSION="${SLURM_VERSION:-25.11}"
COMPILER_VERSION="${COMPILER_VERSION:-9.5.0}"
BASE_URL="${BASE_URL:-https://slurm-factory-spack-binary-cache.vantagecompute.ai}"

echo "========================================="
echo "Slurm Tarball Validation Test"
echo "========================================="
echo "Slurm Version: ${SLURM_VERSION}"
echo "Compiler Version: GCC ${COMPILER_VERSION}"
echo "Base URL: ${BASE_URL}"
echo "========================================="

# Build the Docker image
echo ""
echo "==> Building test Docker image..."
docker build \
    --build-arg SLURM_VERSION="${SLURM_VERSION}" \
    --build-arg COMPILER_VERSION="${COMPILER_VERSION}" \
    --build-arg TARBALL_URL="${BASE_URL}/builds/${SLURM_VERSION}/${COMPILER_VERSION}/slurm-${SLURM_VERSION}-gcc${COMPILER_VERSION}-software.tar.gz" \
    -f tests/Dockerfile.test-tarball \
    -t slurm-tarball-test:${SLURM_VERSION}-gcc${COMPILER_VERSION} \
    .

echo ""
echo "==> Running tarball validation test..."
docker run --rm slurm-tarball-test:${SLURM_VERSION}-gcc${COMPILER_VERSION}

echo ""
echo "========================================="
echo "✓ Tarball validation test PASSED!"
echo "========================================="
