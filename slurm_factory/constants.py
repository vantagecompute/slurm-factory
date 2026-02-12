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
    "25.11": "25-11-2-1",
    "24.11": "24-11-6-1",
    "23.11": "23-11-11-1",
}

RHEL8_SETUP_SCRIPT = """
# RHEL 8 / Rocky Linux 8 setup script for Slurm Factory
# Rocky 8 uses 'powertools' repository (not 'crb' like Rocky 9+)
# Install EPEL repository
yum install -y epel-release
# Enable PowerTools repository for EPEL dependencies (Rocky 8 specific)
# On Rocky Linux 8, this is required for lua-filesystem and lua-posix (Lmod dependencies)
dnf config-manager --set-enabled powertools || exit 1
# Update system packages AND install build tools in one transaction
# This ensures glibc and gcc versions are compatible
# Note: python39 is required because re2c needs Python 3.7+, and Rocky 8 defaults to Python 3.6
yum update -y && yum install -y \
    gcc \
    gcc-c++ \
    gcc-gfortran \
    glibc-devel \
    make \
    wget \
    tar \
    git \
    lua \
    lua-filesystem \
    lua-posix \
    Lmod \
    python39 \
    python39-pip \
    which \
    patch \
    xz \
    unzip \
    findutils \
    diffutils \
    kernel-headers \
    lbzip2 \
    sssd-client
# Set python3.9 as the default python3 (re2c and other tools need Python 3.7+)
alternatives --set python3 /usr/bin/python3.9
yum clean all && rm -rf /var/cache/yum
PIP_BREAK_SYSTEM_PACKAGES=1 pip3 install boto3
"""

RHEL9_SETUP_SCRIPT = """
# RHEL 9 / Rocky Linux 9 setup script for Slurm Factory
# Rocky 9 uses 'crb' (CodeReady Builder) repository
# Install EPEL repository
yum install -y epel-release
# Enable CRB (CodeReady Builder) repository for EPEL dependencies
# On Rocky Linux 9, this is required for lua-filesystem and lua-posix (Lmod dependencies)
dnf config-manager --set-enabled crb || exit 1
# Update system packages AND install build tools in one transaction
# This ensures glibc and gcc versions are compatible
yum update -y && yum install -y \
    gcc \
    gcc-c++ \
    gcc-gfortran \
    glibc-devel \
    make \
    wget \
    tar \
    git \
    lua \
    lua-filesystem \
    lua-posix \
    Lmod \
    python3 \
    python3-pip \
    which \
    patch \
    xz \
    unzip \
    findutils \
    diffutils \
    kernel-headers \
    lbzip2 \
    sssd-client
yum clean all && rm -rf /var/cache/yum
PIP_BREAK_SYSTEM_PACKAGES=1 pip3 install boto3
"""

RHEL10_SETUP_SCRIPT = """
# Rocky Linux 10 / RHEL 10 setup script for Slurm Factory
# Rocky 10 has different package names and repository structure
# Install EPEL repository
yum install -y epel-release
# Enable CRB (CodeReady Builder) repository for EPEL dependencies
/usr/bin/crb enable
# Update system packages AND install build tools in one transaction
# This ensures glibc and gcc versions are compatible
yum update -y && yum install -y \
    gcc \
    gcc-c++ \
    gcc-gfortran \
    libgfortran \
    libstdc++-devel \
    glibc-devel \
    gnupg2 \
    make \
    wget \
    tar \
    git \
    lua \
    lua-filesystem \
    lua-posix \
    Lmod \
    python3 \
    python3-pip \
    which \
    patch \
    xz \
    unzip \
    findutils \
    diffutils \
    kernel-headers \
    bzip2 \
    bzip2-libs \
    sssd-client
yum clean all && rm -rf /var/cache/yum
PIP_BREAK_SYSTEM_PACKAGES=1 pip3 install boto3
"""

UBUNTU_SETUP_SCRIPT = """
# Ubuntu setup script for Slurm Factory
apt-get update
apt-get install -y \
    build-essential \
    wget \
    file \
    tar \
    git \
    gcc \
    g++ \
    gfortran \
    lmod \
    ca-certificates \
    python3 \
    python3-pip \
    patch \
    unzip \
    bzip2 \
    gzip \
    xz-utils \
    diffutils \
    libnss-sss && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
    PIP_BREAK_SYSTEM_PACKAGES=1 pip3 install boto3
"""

UBUNTU_RESOLUTE_SETUP_SCRIPT = """
# Ubuntu 26.04 (Resolute) setup script with CUDA workarounds
# Resolute uses uutils coreutils (Rust) which is incompatible with CUDA installers
# Workaround: Install GNU coreutils and libxml2-16 for CUDA installer
# Note: Ubuntu 26.04 renamed libxml2 to libxml2-16 (SONAME 16)

apt-get update
apt-get install -y \
    build-essential \
    wget \
    file \
    tar \
    git \
    gcc \
    g++ \
    gfortran \
    lmod \
    ca-certificates \
    python3 \
    python3-pip \
    patch \
    unzip \
    bzip2 \
    gzip \
    xz-utils \
    diffutils \
    gnu-coreutils \
    libxml2-16 \
    libnss-sss

# Replace uutils dd with GNU dd (required for CUDA installer compatibility)
rm -f /usr/bin/dd && ln -s /usr/bin/gnudd /usr/bin/dd

# Create libxml2.so.2 symlink for CUDA installer compatibility
# CUDA installer is built against libxml2.so.2, but Ubuntu 26.04 has libxml2.so.16
ln -sf /usr/lib/x86_64-linux-gnu/libxml2.so.16 /usr/lib/x86_64-linux-gnu/libxml2.so.2

apt-get clean && rm -rf /var/lib/apt/lists/*
PIP_BREAK_SYSTEM_PACKAGES=1 pip3 install boto3
"""

# Supported OS-based compiler toolchains for building
# Key: toolchain identifier, Value: (os_name, gcc_version, glibc_version, docker_image, setup_script)
# We use OS-provided compilers instead of building custom GCC toolchains
# This ensures compatibility with target deployment environments
COMPILER_TOOLCHAINS = {
    "rockylinux8": (
        "Rocky Linux 8",
        "8.5.0",
        "2.28",
        "rockylinux/rockylinux:8",
        RHEL8_SETUP_SCRIPT,
    ),
    "rockylinux9": (
        "Rocky Linux 9",
        "11.5.0",
        "2.34",
        "rockylinux/rockylinux:9",
        RHEL9_SETUP_SCRIPT,
    ),
    "rockylinux10": (
        "Rocky Linux 10",
        "14.3.1",
        "2.39",
        "rockylinux/rockylinux:10",
        RHEL10_SETUP_SCRIPT,
    ),
    "jammy": (
        "Ubuntu 22.04 (Jammy)",
        "11.4.0",
        "2.35",
        "ubuntu:jammy",
        UBUNTU_SETUP_SCRIPT,
    ),
    "noble": (
        "Ubuntu 24.04 (Noble)",
        "13.3.0",
        "2.39",
        "ubuntu:noble",
        UBUNTU_SETUP_SCRIPT,
    ),
    "resolute": (
        "Ubuntu 26.04 (Resolute)",
        "15.2.0",
        "2.42",
        "ubuntu:resolute",
        UBUNTU_RESOLUTE_SETUP_SCRIPT,
    ),
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
DOCKER_COMMIT_TIMEOUT = 1800  # 30 minutes for container commit (large GPU images)

# Spack buildcache configuration
SLURM_FACTORY_SPACK_CACHE_BASE_URL = "https://slurm-factory-spack-binary-cache.vantagecompute.ai"

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
CONTAINER_SPACK_STAGE_DIR = "/opt/spack-stage"
