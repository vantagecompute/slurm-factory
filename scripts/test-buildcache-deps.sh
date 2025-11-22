#!/bin/bash
# Test script for buildcache-based dependency installation
set -e

SLURM_VERSION="${SLURM_VERSION:-25.11}"
COMPILER_VERSION="${COMPILER_VERSION:-13.4.0}"
BASE_URL="${BASE_URL:-https://slurm-factory-spack-binary-cache.vantagecompute.ai}"

echo "========================================="
echo "Buildcache Dependency Installation Test"
echo "========================================="
echo "Slurm Version: $SLURM_VERSION"
echo "Compiler Version: GCC $COMPILER_VERSION"
echo "Base URL: $BASE_URL"
echo "========================================="
echo ""

echo "==> Building test Docker image..."
docker build \
  --build-arg SLURM_VERSION="$SLURM_VERSION" \
  --build-arg COMPILER_VERSION="$COMPILER_VERSION" \
  --build-arg BASE_URL="$BASE_URL" \
  -f tests/Dockerfile.test-buildcache-deps \
  -t slurm-buildcache-deps-test:${SLURM_VERSION}-gcc${COMPILER_VERSION} \
  .

echo ""
echo "==> Running buildcache dependency test..."
docker run --rm \
  -e SLURM_VERSION="$SLURM_VERSION" \
  -e COMPILER_VERSION="$COMPILER_VERSION" \
  -e BASE_URL="$BASE_URL" \
  slurm-buildcache-deps-test:${SLURM_VERSION}-gcc${COMPILER_VERSION}

echo ""
echo "========================================="
echo "✓ Buildcache dependency test PASSED!"
echo "========================================="
