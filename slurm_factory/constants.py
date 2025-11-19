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

"""Constants of slurm-factory."""

from enum import Enum

# Mapping of user-facing version strings to Spack package versions
SLURM_VERSIONS = {
    "25.11": "25-11-0-1",
    "24.11": "24-11-6-1",
    "23.11": "23-11-11-1",
}

# Supported compiler versions for building
# Key: user-facing version, Value: (gcc_version, glibc_version, description)
# Latest stable minor versions for each major GCC version from Spack v1.0.0
COMPILER_TOOLCHAINS = {
    "15.2.0": ("15.2.0", "2.40", "GCC 15.2 (latest in Spack v1.0.0) - glibc 2.40"),
    "14.2.0": ("14.2.0", "2.39", "GCC 14.2 (latest stable) - glibc 2.39"),
    "13.4.0": ("13.4.0", "2.39", "GCC 13.4 / Ubuntu 24.04 (default) - glibc 2.39"),
    "12.5.0": ("12.5.0", "2.35", "GCC 12.5 (latest stable) - glibc 2.35"),
    "11.5.0": ("11.5.0", "2.35", "GCC 11.5 / Ubuntu 22.04 - glibc 2.35"),
    "10.5.0": ("10.5.0", "2.31", "GCC 10.5 / RHEL 8 / Ubuntu 20.04 - glibc 2.31"),
    "9.5.0": ("9.5.0", "2.28", "GCC 9.5 (latest stable) - glibc 2.28"),
    "8.5.0": ("8.5.0", "2.28", "GCC 8.5 / RHEL 8 minimum - glibc 2.28"),
    "7.5.0": ("7.5.0", "2.17", "GCC 7.5 / RHEL 7 compatible - glibc 2.17"),
}


class SlurmVersion(str, Enum):
    """Available Slurm versions for building."""

    v25_11 = "25.11"
    v24_11 = "24.11"
    v23_11 = "23.11"


class BuildType(str, Enum):
    """Build type options for Slurm."""

    cpu = "cpu"
    gpu = "gpu"


# Docker configuration
INSTANCE_NAME_PREFIX = "slurm-factory"

# Timeouts (in seconds)
BUILD_TIMEOUT = 3600  # 1 hour for full build
DOCKER_BUILD_TIMEOUT = 600  # 10 minutes for image build

# Spack buildcache configuration
SLURM_FACTORY_SPACK_CACHE_BASE_URL = "https://slurm-factory-spack-binary-cache.vantagecompute.ai"
SLURM_FACTORY_GPG_PUBLIC_KEY_URL = f"{SLURM_FACTORY_SPACK_CACHE_BASE_URL}/keys/vantage-slurm-factory.pub"

# S3 bucket for Spack buildcache
S3_BUILDCACHE_BUCKET = "s3://slurm-factory-spack-buildcache-4b670"

# Spack repository paths
SPACK_SETUP_SCRIPT = "/opt/spack/share/spack/setup-env.sh"

# Container paths
CONTAINER_CACHE_DIR = "/opt/slurm-factory-cache"
CONTAINER_SPACK_TEMPLATES_DIR = "/opt/spack/share/spack/templates"
CONTAINER_SPACK_PROJECT_DIR = "/root/spack-project"
CONTAINER_SLURM_DIR = "/opt/slurm"
CONTAINER_BUILD_OUTPUT_DIR = f"{CONTAINER_SLURM_DIR}/build_output"
CONTAINER_ROOT_DIR = "/root"
# NOTE: We do NOT create/use SPACK_CACHE_DIR to avoid cross-build contamination
# Each container build should start fresh without cached compiler metadata

# Shell script templates
BASH_HEADER = ["bash", "-c"]
