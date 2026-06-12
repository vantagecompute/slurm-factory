#!/bin/bash
# Test script to validate Slurm tarballs produced by the build system
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

set -e

# Default values
SLURM_VERSION="${SLURM_VERSION:-25.11}"
TOOLCHAIN="${TOOLCHAIN:-resolute}"
ARCHITECTURE="${ARCHITECTURE:-amd64}"
LOCAL_TARBALL_PATH="${LOCAL_TARBALL_PATH:-}"
TEST_IMAGE_TAG="${TEST_IMAGE_TAG:-slurm-tarball-test:${SLURM_VERSION}-${TOOLCHAIN}-${ARCHITECTURE}}"
CLEANUP="${CLEANUP:-false}"
VERBOSE="${VERBOSE:-false}"
QUIET="${QUIET:-false}"
TIMEOUT="${TIMEOUT:-3600}"

# Supported toolchains based on COMPILER_TOOLCHAINS in slurm_factory/constants.py
SUPPORTED_TOOLCHAINS=("jammy" "noble" "resolute" "rockylinux8" "rockylinux9" "rockylinux10")

# Help text
show_help() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Test script to validate Slurm tarballs produced by the build system.

OPTIONS:
    -h, --help                  Show this help message and exit
    -s, --slurm-version VERSION Set Slurm version (default: ${SLURM_VERSION})
    -t, --toolchain TOOLCHAIN   Set toolchain (default: ${TOOLCHAIN})
    -a, --architecture ARCH     Set CPU architecture (default: ${ARCHITECTURE})
    -l, --local-tarball PATH    Local tarball to test
    -c, --cleanup               Remove Docker images after test completion
    -v, --verbose               Enable verbose output
    -q, --quiet                 Suppress non-error output
    --timeout SECONDS           Set timeout for Docker operations in seconds (default: ${TIMEOUT})

ENVIRONMENT VARIABLES:
    SLURM_VERSION    Slurm version to test (can be overridden by --slurm-version)
    TOOLCHAIN        Toolchain to use (can be overridden by --toolchain)
    ARCHITECTURE     CPU architecture (can be overridden by --architecture)
    LOCAL_TARBALL_PATH  Path to local tarball (can be overridden by --local-tarball)
    CLEANUP          Set to 'true' to enable cleanup (can be overridden by --cleanup)
    VERBOSE          Set to 'true' to enable verbose output (can be overridden by --verbose)
    QUIET            Set to 'true' to enable quiet mode (can be overridden by --quiet)
    TIMEOUT          Timeout for Docker operations in seconds (can be overridden by --timeout)

SUPPORTED TOOLCHAINS:
    jammy, noble, resolute, rockylinux8, rockylinux9, rockylinux10

EXAMPLES:
    # Test a local tarball
    $(basename "$0") --local-tarball ./slurm-26.05-rockylinux9-arm64-software.tar.gz \
        --slurm-version 26.05 --toolchain rockylinux9 --architecture arm64

    # Test with cleanup
    $(basename "$0") --local-tarball ./slurm-26.05-rockylinux9-arm64-software.tar.gz --cleanup

    # Test with environment variables
    LOCAL_TARBALL_PATH=./slurm-24.11-noble-amd64-software.tar.gz \
        SLURM_VERSION=24.11 TOOLCHAIN=noble $(basename "$0")

    # Test with custom timeout
    $(basename "$0") --timeout 7200
EOF
}

# Logging functions
log_info() {
    if [[ "${QUIET}" != "true" ]]; then
        echo "$@"
    fi
}

log_verbose() {
    if [[ "${VERBOSE}" == "true" ]]; then
        echo "[VERBOSE] $*"
    fi
}

log_error() {
    echo "[ERROR] $*" >&2
}

# Error handler with cleanup
cleanup_on_error() {
    local exit_code=$?
    log_error "Script failed with exit code ${exit_code}"
    
    # If cleanup is enabled, remove Docker images even on failure
    if [[ "${CLEANUP}" == "true" ]]; then
        log_info "Cleaning up Docker images due to error..."
        cleanup_docker_images
    fi
    
    exit "${exit_code}"
}

# Cleanup Docker images
cleanup_docker_images() {
    local image_name="${TEST_IMAGE_TAG}"
    
    if docker images -q "${image_name}" 2>/dev/null | grep -q .; then
        log_verbose "Removing Docker image: ${image_name}"
        if docker rmi -f "${image_name}" >/dev/null 2>&1; then
            log_info "✓ Cleaned up Docker image: ${image_name}"
        else
            log_error "Failed to remove Docker image: ${image_name}"
        fi
    else
        log_verbose "Docker image not found, skipping cleanup: ${image_name}"
    fi
}

# Set up error trap
trap cleanup_on_error ERR

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -s|--slurm-version)
            SLURM_VERSION="$2"
            shift 2
            ;;
        -t|--toolchain)
            TOOLCHAIN="$2"
            shift 2
            ;;
        -a|--architecture)
            ARCHITECTURE="$2"
            shift 2
            ;;
        -l|--local-tarball)
            LOCAL_TARBALL_PATH="$2"
            shift 2
            ;;
        -c|--cleanup)
            CLEANUP="true"
            shift
            ;;
        -v|--verbose)
            VERBOSE="true"
            shift
            ;;
        -q|--quiet)
            QUIET="true"
            shift
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

if [ -z "${LOCAL_TARBALL_PATH}" ]; then
    log_error "LOCAL_TARBALL_PATH is required; use --local-tarball PATH"
    exit 1
fi

if [ ! -f "${LOCAL_TARBALL_PATH}" ]; then
    log_error "Local tarball not found: ${LOCAL_TARBALL_PATH}"
    exit 1
fi

# Input validation: Check Docker is installed
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed or not in PATH"
    log_error "Please install Docker from https://docs.docker.com/get-docker/"
    exit 1
fi

# Input validation: Check Docker daemon is running
if ! docker info &> /dev/null; then
    log_error "Docker daemon is not running"
    log_error "Please start Docker and try again"
    exit 1
fi

log_verbose "Docker is available and running"

# Input validation: Validate toolchain
toolchain_valid=false
for tc in "${SUPPORTED_TOOLCHAINS[@]}"; do
    if [[ "${tc}" == "${TOOLCHAIN}" ]]; then
        toolchain_valid=true
        break
    fi
done

if [[ "${toolchain_valid}" == "false" ]]; then
    log_error "Invalid toolchain: ${TOOLCHAIN}"
    log_error "Supported toolchains: ${SUPPORTED_TOOLCHAINS[*]}"
    exit 1
fi

log_verbose "Toolchain validation passed: ${TOOLCHAIN}"

# Input validation: Validate timeout is a positive number
if ! [[ "${TIMEOUT}" =~ ^[0-9]+$ ]] || [[ "${TIMEOUT}" -le 0 ]]; then
    log_error "Invalid timeout: ${TIMEOUT}"
    log_error "Timeout must be a positive integer (seconds)"
    exit 1
fi

log_verbose "Timeout validation passed: ${TIMEOUT}s"

# Display configuration
log_info "========================================="
log_info "Slurm Tarball Validation Test"
log_info "========================================="
log_info "Slurm Version: ${SLURM_VERSION}"
log_info "Toolchain: ${TOOLCHAIN}"
log_info "Source: local (${LOCAL_TARBALL_PATH})"
log_info "Test Image Tag: ${TEST_IMAGE_TAG}"
log_info "Cleanup: ${CLEANUP}"
log_info "Verbose: ${VERBOSE}"
log_info "Quiet: ${QUIET}"
log_info "Timeout: ${TIMEOUT}s"
log_info "========================================="

# Determine Docker image base
DOCKER_IMAGE_BASE="rocky"
BASE_IMAGE=""

if [[ "${TOOLCHAIN}" == "jammy" || "${TOOLCHAIN}" == "noble" || "${TOOLCHAIN}" == "resolute" ]]; then
    DOCKER_IMAGE_BASE="ubuntu"
    BASE_IMAGE="ubuntu:${TOOLCHAIN}"
elif [[ "${TOOLCHAIN}" == "rockylinux8" ]]; then
    BASE_IMAGE="rockylinux/rockylinux:8"
elif [[ "${TOOLCHAIN}" == "rockylinux9" ]]; then
    BASE_IMAGE="rockylinux/rockylinux:9"
elif [[ "${TOOLCHAIN}" == "rockylinux10" ]]; then
    BASE_IMAGE="rockylinux/rockylinux:10"
else
    log_error "Unknown toolchain: ${TOOLCHAIN}"
    exit 1
fi

log_verbose "Using Docker base: ${DOCKER_IMAGE_BASE}"
log_verbose "Using base image: ${BASE_IMAGE}"

# Build the Docker image
log_info ""
log_info "==> Building test Docker image..."

CONTEXT_DIR=$(mktemp -d)
LOCAL_CLEANUP_CONTEXT_DIR="${CONTEXT_DIR}"
mkdir -p "${CONTEXT_DIR}/tarball"
cp "${LOCAL_TARBALL_PATH}" "${CONTEXT_DIR}/tarball/"
cp "tests/dockerfiles/Dockerfile.tarball-${DOCKER_IMAGE_BASE}" "${CONTEXT_DIR}/"
DOCKERFILE_PATH="${CONTEXT_DIR}/Dockerfile.tarball-${DOCKER_IMAGE_BASE}"
BUILD_CONTEXT="${CONTEXT_DIR}"

BUILD_ARGS=(
    --build-arg "SLURM_VERSION=${SLURM_VERSION}"
    --build-arg "TOOLCHAIN=${TOOLCHAIN}"
    --build-arg "ARCHITECTURE=${ARCHITECTURE}"
    --build-arg "BASE_IMAGE=${BASE_IMAGE}"
    -f "${DOCKERFILE_PATH}"
    -t "${TEST_IMAGE_TAG}"
    "${BUILD_CONTEXT}"
)

log_verbose "Docker build command: docker build ${BUILD_ARGS[*]}"

# Run docker build with timeout
if [[ "${VERBOSE}" == "true" ]]; then
    timeout "${TIMEOUT}" docker build "${BUILD_ARGS[@]}"
    BUILD_EXIT_CODE=$?
else
    timeout "${TIMEOUT}" docker build "${BUILD_ARGS[@]}" > /dev/null
    BUILD_EXIT_CODE=$?
fi

# Clean up local build context if created
if [ -n "${LOCAL_CLEANUP_CONTEXT_DIR:-}" ]; then
    rm -rf "${LOCAL_CLEANUP_CONTEXT_DIR}"
fi

if [[ $BUILD_EXIT_CODE -eq 124 ]]; then
    log_error "Docker build timed out after ${TIMEOUT} seconds"
    exit 1
elif [[ $BUILD_EXIT_CODE -ne 0 ]]; then
    log_error "Docker build failed with exit code ${BUILD_EXIT_CODE}"
    exit 1
fi

log_info "✓ Docker image built successfully"

# Run tarball validation test
log_info ""
log_info "==> Running tarball validation test..."

log_verbose "Docker run command: docker run --rm ${TEST_IMAGE_TAG}"

# Run docker container with timeout
if [[ "${VERBOSE}" == "true" ]]; then
    timeout "${TIMEOUT}" docker run --rm "${TEST_IMAGE_TAG}"
    RUN_EXIT_CODE=$?
else
    timeout "${TIMEOUT}" docker run --rm "${TEST_IMAGE_TAG}" > /dev/null
    RUN_EXIT_CODE=$?
fi

if [[ $RUN_EXIT_CODE -eq 124 ]]; then
    log_error "Docker run timed out after ${TIMEOUT} seconds"
    exit 1
elif [[ $RUN_EXIT_CODE -ne 0 ]]; then
    log_error "Docker run failed with exit code ${RUN_EXIT_CODE}"
    exit 1
fi

log_info "✓ Tarball validation test completed successfully"

# Cleanup if requested
if [[ "${CLEANUP}" == "true" ]]; then
    log_info ""
    log_info "==> Cleaning up Docker images..."
    cleanup_docker_images
fi

log_info ""
log_info "========================================="
log_info "✓ Tarball validation test PASSED!"
log_info "========================================="
