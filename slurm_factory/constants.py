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

CENTOS_7_SETUP_SCRIPT = """
# CentOS 7 setup script for Slurm Factory
# Install EPEL repository
yum install -y epel-release
yum install -y \
    gcc \
    gcc-c++ \
    gcc-gfortran \
    make \
    wget \
    tar \
    git \
    Lmod \
    python3 \
    python3-pip \
    which \
    patch \
    lbzip2 \
    xz \
    kernel-headers && \
    python3 -m pip install boto3 pyyaml
"""

ROCKY_8_SETUP_SCRIPT = """
# Rocky 8 setup script for Slurm Factory
# Install EPEL repository
yum install -y epel-release
yum install -y \
    gcc \
    gcc-c++ \
    gcc-gfortran \
    make \
    wget \
    tar \
    git \
    Lmod \
    python3 \
    python3-pip \
    which \
    patch \
    lbzip2 \
    xz \
    kernel-headers && \
    python3 -m pip install boto3 pyyaml
"""

ROCKY_9_SETUP_SCRIPT = """
# Rocky 9 setup script for Slurm Factory
# Install EPEL repository
yum install -y epel-release
yum install -y \
    gcc \
    gcc-c++ \
    gcc-gfortran \
    make \
    wget \
    tar \
    git \
    Lmod \
    python3 \
    python3-pip \
    which \
    patch \
    lbzip2 \
    xz \
    kernel-headers && \
    python3 -m pip install boto3 pyyaml
"""

UBUNTU_22_04_SETUP_SCRIPT = """
# Ubuntu 22.04 setup script for Slurm Factory
apt-get update
apt-get install -y \
    build-essential \
    wget \
    tar \
    git \
    gcc \
    g++ \
    gfortran \
    lmod \
    ca-certificates \
    python3 \
    python3-pip \
    patch && \
    python3 -m pip install --break-system-packages boto3 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
"""

UBUNTU_24_04_SETUP_SCRIPT = """
# Ubuntu 24.04 setup script for Slurm Factory
apt-get update
apt-get install -y \
    build-essential \
    wget \
    tar \
    git \
    gcc \
    g++ \
    gfortran \
    lmod \
    ca-certificates \
    python3 \
    python3-pip \
    patch && \
    python3 -m pip install --break-system-packages boto3 pyyaml && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
"""

UBUNTU_26_04_SETUP_SCRIPT = """
# Ubuntu 26.04 setup script for Slurm Factory
apt-get update
apt-get install -y \
    build-essential \
    wget \
    tar \
    git \
    gcc \
    g++ \
    gfortran \
    lmod \
    ca-certificates \
    python3 \
    python3-pip \
    patch && \
    python3 -m pip install --break-system-packages boto3 pyyaml && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
"""


# Supported OS-based compiler toolchains for building
# Key: toolchain identifier, Value: (os_name, gcc_version, glibc_version, docker_image, setup_script)
# We use OS-provided compilers instead of building custom GCC toolchains
# This ensures compatibility with target deployment environments
COMPILER_TOOLCHAINS = {
    "centos7": ("CentOS 7", "4.8.5", "2.17", "centos:7", CENTOS_7_SETUP_SCRIPT),
    "rockylinux8": ("Rocky Linux 8", "8.5.0", "2.28", "rockylinux:8", ROCKY_8_SETUP_SCRIPT),
    "rockylinux9": ("Rocky Linux 9", "11.5.0", "2.34", "rockylinux:9", ROCKY_9_SETUP_SCRIPT),
    "jammy": ("Ubuntu 22.04 (Jammy)", "11.2.0", "2.35", "ubuntu:jammy", UBUNTU_22_04_SETUP_SCRIPT),
    "noble": ("Ubuntu 24.04 (Noble)", "13.3.0", "2.39", "ubuntu:noble", UBUNTU_24_04_SETUP_SCRIPT),
    "resolute": ("Ubuntu 26.04 (Resolute)", "15.2.0", "2.42", "ubuntu:resolute", UBUNTU_26_04_SETUP_SCRIPT),
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
BUILD_TIMEOUT = 14400  # 4 hours for full source build
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
