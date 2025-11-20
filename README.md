<div align="center">
<a href="https://www.vantagecompute.ai/">
  <img src="https://vantage-compute-public-assets.s3.us-east-1.amazonaws.com/branding/vantage-logo-text-black-horz.png" alt="Vantage Compute Logo" width="100"/>
</a>

# Slurm Factory

[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![PyPI](https://img.shields.io/pypi/v/slurm-factory.svg)](https://pypi.org/project/slurm-factory/)
[![Docker](https://img.shields.io/badge/Docker-24.0+-blue.svg)](https://docker.com)

Build relocatable, **GPG-signed** Slurm packages using Docker and Spack.

[Documentation](https://vantagecompute.github.io/slurm-factory) | [Buildcache](https://slurm-factory-spack-binary-cache.vantagecompute.ai)

</div>

## Quick Start

### Option 1: Install Pre-built Slurm from Buildcache (Fastest!)

Use Spack to install GPG-signed pre-built binaries (**no slurm-factory tool needed**):

```bash
# Install Spack
git clone --depth 1 --branch v1.0.0 https://github.com/spack/spack.git
source spack/share/spack/setup-env.sh

# Add mirrors for compilers, dependencies, and Slurm
SLURM_VERSION=25.11
COMPILER_VERSION=15.2.0
CLOUDFRONT_URL=https://slurm-factory-spack-binary-cache.vantagecompute.ai

spack mirror add slurm-factory-build-toolchain "${CLOUDFRONT_URL}/compilers/${COMPILER_VERSION}"
spack mirror add slurm-factory-slurm-deps "${CLOUDFRONT_URL}/deps/${COMPILER_VERSION}"
spack mirror add slurm-factory-slurm "${CLOUDFRONT_URL}/slurm/${SLURM_VERSION}/${COMPILER_VERSION}"

# Import GPG keys and install Slurm (5-15 min!)
spack buildcache keys --install --trust
spack install slurm@${SLURM_VERSION}%gcc@${COMPILER_VERSION}
```

**→ Full guide:** [Installing Slurm from Buildcache](https://vantagecompute.github.io/slurm-factory/installing-slurm-from-buildcache)

### Option 2: Build Custom Slurm with slurm-factory Tool

Install the slurm-factory tool to build custom packages:

```bash
# Install Docker and the slurm-factory build tool
pip install slurm-factory

# Build Slurm with default compiler (GCC 13.4.0)
slurm-factory build-slurm --slurm-version 25.11
```

**→ Full guide:** [Installing slurm-factory Tool](https://vantagecompute.github.io/slurm-factory/installation)

## Supported Versions

### Slurm × Operating System Matrix

All combinations use **OS-provided compilers** and are available in the public buildcache:

| Slurm Version | Status      | Supported Operating Systems                                 |
|---------------|-------------|-------------------------------------------------------------|
| **25.11**     | Latest      | CentOS 7, Rocky 8, Rocky 9, **Ubuntu 24.04**, Ubuntu 22.04, Ubuntu 25.04 |
| **24.11**     | LTS         | CentOS 7, Rocky 8, Rocky 9, **Ubuntu 24.04**, Ubuntu 22.04, Ubuntu 25.04 |
| **23.11**     | Stable      | CentOS 7, Rocky 8, Rocky 9, **Ubuntu 24.04**, Ubuntu 22.04, Ubuntu 25.04 |

**Default**: Ubuntu 24.04 (Noble) - recommended for most users

### Operating System Compiler Toolchains

Slurm is built using the default system compiler from each OS distribution:

| OS | Codename | GCC Version | GLIBC | Use Case |
|----|----------|-------------|-------|----------|
| **Ubuntu 24.04** | **Noble** | **13.2.0** | **2.39** | **Recommended - Modern stable** |
| Ubuntu 25.04 | Resolute | 15.2.0 | 2.42 | Latest features (development) |
| Ubuntu 22.04 | Jammy | 11.2.0 | 2.35 | LTS - Wide compatibility |
| Rocky Linux 9 | - | 11.4.1 | 2.34 | RHEL 9 compatible |
| Rocky Linux 8 | - | 8.5.0 | 2.28 | RHEL 8 compatible |
| CentOS 7 | - | 4.8.5 | 2.17 | Maximum backward compatibility |

## GPG Package Signing

All packages are **cryptographically signed with GPG** for security and integrity.

### Why GPG Signing?

- ✅ **Authenticity**: Verify packages were built by Vantage Compute
- ✅ **Integrity**: Detect tampering or corruption during download
- ✅ **Security**: Prevent man-in-the-middle attacks
- ✅ **Trust Chain**: Establish provenance for production deployments

### GPG Key Information

```text
Key ID: DFB92630BCA5AB71
Owner: Vantage Compute Corporation (Slurm Factory Spack Cache Signing Key)
Email: info@vantagecompute.ai
```

### Importing GPG Keys

Keys are automatically imported when using the buildcache:

```bash
# Automatic import and trust
spack buildcache keys --install --trust

# Packages are verified during installation
spack install slurm@25.11%gcc@13.4.0
```

## Features

- **🔐 GPG-Signed Packages** - All Slurm packages cryptographically signed
- **⚡ 10-15x Faster** - Pre-built packages install in 5-15 minutes vs 45-90 minutes
- **📦 Relocatable** - Deploy to any path, no host dependencies
- **🌍 CDN Distribution** - CloudFront-distributed buildcache for fast global access
- **🐧 6 OS Platforms** - CentOS 7, Rocky Linux 8/9, Ubuntu 22.04/24.04/25.04
- **🎯 3 Slurm Versions** - 25.11, 24.11, 23.11
- **🏭 OS-Native Compilers** - Uses system-provided GCC for maximum compatibility
- **🚀 Optimized** - Architecture-specific compilation (x86_64_v3)
- **🐳 Clean Builds** - Docker isolation, no system pollution

## Build Options

### Build from Source with slurm-factory

```bash
# Default build (CPU-only, Ubuntu 24.04 toolchain)
slurm-factory build-slurm --slurm-version 25.11

# GPU support (CUDA/ROCm)
slurm-factory build-slurm --slurm-version 25.11 --gpu

# Different OS toolchain
slurm-factory build-slurm --slurm-version 25.11 --toolchain jammy

# Build and publish to buildcache with GPG signing
slurm-factory build-slurm --slurm-version 25.11 --publish \
  --signing-key $GPG_KEY_ID \
  --gpg-private-key "$GPG_PRIVATE_KEY" \
  --gpg-passphrase "$GPG_PASSPHRASE"
```

### Install Pre-built from Buildcache (Fastest!)

```bash
# Install Spack
git clone --depth 1 --branch v1.0.0 https://github.com/spack/spack.git
source spack/share/spack/setup-env.sh

# Configure mirrors for buildcache
SLURM_VERSION=25.11
TOOLCHAIN=noble  # or: jammy, rockylinux9, etc.
CLOUDFRONT_URL=https://slurm-factory-spack-binary-cache.vantagecompute.ai

spack mirror add slurm-factory-slurm-deps "${CLOUDFRONT_URL}/deps/${TOOLCHAIN}"
spack mirror add slurm-factory-slurm "${CLOUDFRONT_URL}/slurm/${SLURM_VERSION}/${TOOLCHAIN}"

# Import GPG signing keys and trust
spack buildcache keys --install --trust

# Install signed package (5-15 minutes!)
spack install slurm@${SLURM_VERSION} target=x86_64_v3

# Deploy
spack load slurm@${SLURM_VERSION}
```

### Download Pre-built Tarball (Alternative)

Download complete Slurm installation as a tarball with GPG signature verification:

```bash
# Set versions
SLURM_VERSION=25.11
TOOLCHAIN=noble  # or: jammy, rockylinux9, etc.
CLOUDFRONT_URL=https://slurm-factory-spack-binary-cache.vantagecompute.ai

# Download tarball and signature
wget "${CLOUDFRONT_URL}/builds/${SLURM_VERSION}/${TOOLCHAIN}/slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz"
wget "${CLOUDFRONT_URL}/builds/${SLURM_VERSION}/${TOOLCHAIN}/slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz.asc"

# Import GPG key
gpg --keyserver keyserver.ubuntu.com --recv-keys DFB92630BCA5AB71

# Verify signature
gpg --verify slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz.asc \
             slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz

# Extract and install
sudo tar -xzf slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz -C /opt/
cd /opt && sudo ./data/slurm_assets/slurm_install.sh --full-init
```

## Package Structure

All builds produce GPG-signed relocatable tarballs:

```text
slurm-25.11-noble-software.tar.gz
├── view/                    # Slurm binaries & libraries
├── modules/slurm/25.11.lua  # Lmod module (relocatable)
└── data/slurm_assets/       # Config templates & install script
```

## Deployment

```bash
# Extract (from tarball build)
sudo tar -xzf slurm-25.11-noble-software.tar.gz -C /opt/

# Install (creates users, configs, services)
cd /opt && sudo ./data/slurm_assets/slurm_install.sh --full-init

# Use
module load slurm/25.11
```

## Buildcache Structure

The public buildcache is organized by OS toolchain for optimal performance:

```text
https://slurm-factory-spack-binary-cache.vantagecompute.ai/
├── deps/
│   ├── centos7/         # Slurm dependencies for CentOS 7 (GPG-signed)
│   ├── rockylinux8/     # Slurm dependencies for Rocky Linux 8 (GPG-signed)
│   ├── rockylinux9/     # Slurm dependencies for Rocky Linux 9 (GPG-signed)
│   ├── jammy/           # Slurm dependencies for Ubuntu 22.04 (GPG-signed)
│   ├── noble/           # Slurm dependencies for Ubuntu 24.04 (GPG-signed)
│   └── resolute/        # Slurm dependencies for Ubuntu 25.04 (GPG-signed)
├── slurm/
│   ├── 25.11/
│   │   ├── centos7/     # Slurm 25.11 for CentOS 7 (GPG-signed)
│   │   ├── rockylinux8/ # Slurm 25.11 for Rocky Linux 8 (GPG-signed)
│   │   ├── rockylinux9/ # Slurm 25.11 for Rocky Linux 9 (GPG-signed)
│   │   ├── jammy/       # Slurm 25.11 for Ubuntu 22.04 (GPG-signed)
│   │   ├── noble/       # Slurm 25.11 for Ubuntu 24.04 (GPG-signed)
│   │   └── resolute/    # Slurm 25.11 for Ubuntu 25.04 (GPG-signed)
│   ├── 24.11/
│   │   └── ...          # All OS toolchains (GPG-signed)
│   └── 23.11/
│       └── ...          # All OS toolchains (GPG-signed)
└── builds/
    ├── 25.11/
    │   ├── centos7/
    │   │   ├── slurm-25.11-centos7-software.tar.gz      # Complete tarball
    │   │   └── slurm-25.11-centos7-software.tar.gz.asc  # GPG signature
    │   ├── noble/
    │   │   ├── slurm-25.11-noble-software.tar.gz
    │   │   └── slurm-25.11-noble-software.tar.gz.asc
    │   └── ...          # All OS toolchains
    ├── 24.11/
    │   └── ...
    └── 23.11/
        └── ...
```

### Mirror Architecture

The buildcache uses a **two-tier mirror structure** for efficient caching and dependency resolution:

1. **`deps/`** - Slurm runtime dependencies (OpenMPI, PMIx, Munge, etc.) per OS toolchain
2. **`slurm/`** - Slurm packages compiled with OS-native compilers

This separation allows:

- ✅ **Better caching** - Dependencies shared across Slurm versions
- ✅ **Reduced storage** - No duplication of common packages
- ✅ **Parallel downloads** - Spack can fetch from multiple mirrors simultaneously
- ✅ **OS compatibility** - Packages built with native system compilers

## Requirements

- Python 3.12+
- Docker 24.0+ (for building from source)
- 50GB disk space
- 4+ CPU cores (8+ recommended)
- 16GB RAM (32GB+ recommended)

For buildcache installs: only Spack required (no Docker needed)

## Documentation

**[vantagecompute.github.io/slurm-factory](https://vantagecompute.github.io/slurm-factory)**

- [Overview](https://vantagecompute.github.io/slurm-factory/overview) - Architecture and features
- [Installation](https://vantagecompute.github.io/slurm-factory/installation) - Setup and quick start
- [Examples](https://vantagecompute.github.io/slurm-factory/examples) - Common use cases
- [Buildcache Guide](https://vantagecompute.github.io/slurm-factory/slurm-factory-spack-build-cache) - GPG signing and distribution
- [API Reference](https://vantagecompute.github.io/slurm-factory/api-reference) - Python API

## Development

```bash
# Install from source
git clone https://github.com/vantagecompute/slurm-factory.git
cd slurm-factory
pip install -e .

# Run tests
pytest

# Build docs
cd docusaurus && npm run build
```

## License

Apache License 2.0 - See [LICENSE](LICENSE) file.

## Support

- Issues: [github.com/vantagecompute/slurm-factory/issues](https://github.com/vantagecompute/slurm-factory/issues)
- Docs: [vantagecompute.github.io/slurm-factory](https://vantagecompute.github.io/slurm-factory)
- Website: [vantagecompute.ai](https://www.vantagecompute.ai)

---

Built with ❤️ by [Vantage Compute](https://www.vantagecompute.ai)
