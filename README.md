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

### Slurm × GCC Matrix

All combinations are **GPG-signed** and available in the public buildcache:

| Slurm Version | Status      | GCC Versions                                                |
|---------------|-------------|-------------------------------------------------------------|
| **25.11**     | Latest      | 15.2.0, 14.2.0, **13.4.0**, 12.5.0, 11.5.0, 10.5.0, 9.5.0, 8.5.0, 7.5.0 |
| **24.11**     | LTS         | 15.2.0, 14.2.0, **13.4.0**, 12.5.0, 11.5.0, 10.5.0, 9.5.0, 8.5.0, 7.5.0 |
| **23.11**     | Stable      | 15.2.0, 14.2.0, **13.4.0**, 12.5.0, 11.5.0, 10.5.0, 9.5.0, 8.5.0, 7.5.0 |

**Default**: GCC 13.4.0 (recommended for most users)

### GCC Compiler Toolchains

| Version | Target Distribution  | glibc | Use Case                        |
|---------|---------------------|-------|---------------------------------|
| 15.2.0  | Latest              | 2.39  | Cutting-edge features           |
| 14.2.0  | Latest              | 2.39  | Modern features                 |
| **13.4.0** | **Ubuntu 24.04**  | **2.39** | **Recommended default**      |
| 12.5.0  | Latest              | 2.35  | Good compatibility              |
| 11.5.0  | Ubuntu 22.04        | 2.35  | Wide compatibility              |
| 10.5.0  | RHEL 8/Ubuntu 20.04 | 2.31  | Enterprise Linux 8              |
| 9.5.0   | Latest              | 2.28  | Older systems                   |
| 8.5.0   | RHEL 8              | 2.28  | Enterprise Linux 8              |
| 7.5.0   | RHEL 7              | 2.17  | Maximum backward compatibility  |

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

- **🔐 GPG-Signed Packages** - All compiler and Slurm packages cryptographically signed
- **⚡ 10-15x Faster** - Pre-built packages install in 5-15 minutes vs 45-90 minutes
- **📦 Relocatable** - Deploy to any path, no host dependencies
- **🌍 CDN Distribution** - CloudFront-distributed buildcache for fast global access
- **🔧 9 GCC Versions** - From GCC 7.5.0 (RHEL 7) to 15.2.0 (latest)
- **🎯 3 Slurm Versions** - 25.11, 24.11, 23.11
- **🚀 Optimized** - Architecture-specific compilation (x86_64_v3)
- **🐳 Clean Builds** - Docker isolation, no system pollution

## Build Options

### Build from Source with slurm-factory

```bash
# Default build (CPU-only, GCC 13.4.0)
slurm-factory build-slurm --slurm-version 25.11

# GPU support (CUDA/ROCm)
slurm-factory build-slurm --slurm-version 25.11 --gpu

# Different compiler version
slurm-factory build-slurm --slurm-version 25.11 --compiler-version 14.2.0

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

# Configure mirrors for three-tier buildcache
SLURM_VERSION=25.11
COMPILER_VERSION=15.2.0
CLOUDFRONT_URL=https://slurm-factory-spack-binary-cache.vantagecompute.ai

spack mirror add slurm-factory-build-toolchain "${CLOUDFRONT_URL}/compilers/${COMPILER_VERSION}"
spack mirror add slurm-factory-slurm-deps "${CLOUDFRONT_URL}/deps/${COMPILER_VERSION}"
spack mirror add slurm-factory-slurm "${CLOUDFRONT_URL}/slurm/${SLURM_VERSION}/${COMPILER_VERSION}"

# Import GPG signing keys and trust
spack buildcache keys --install --trust

# Install signed package (5-15 minutes!)
spack install slurm@${SLURM_VERSION}%gcc@${COMPILER_VERSION} target=x86_64_v3

# Deploy
spack load slurm@${SLURM_VERSION}
```

### Download Pre-built Tarball (Alternative)

Download complete Slurm installation as a tarball with GPG signature verification:

```bash
# Set versions
SLURM_VERSION=25.11
COMPILER_VERSION=15.2.0
CLOUDFRONT_URL=https://slurm-factory-spack-binary-cache.vantagecompute.ai

# Download tarball and signature
wget "${CLOUDFRONT_URL}/builds/${SLURM_VERSION}/${COMPILER_VERSION}/slurm-${SLURM_VERSION}-gcc${COMPILER_VERSION}-software.tar.gz"
wget "${CLOUDFRONT_URL}/builds/${SLURM_VERSION}/${COMPILER_VERSION}/slurm-${SLURM_VERSION}-gcc${COMPILER_VERSION}-software.tar.gz.asc"

# Import GPG key
gpg --keyserver keyserver.ubuntu.com --recv-keys DFB92630BCA5AB71

# Verify signature
gpg --verify slurm-${SLURM_VERSION}-gcc${COMPILER_VERSION}-software.tar.gz.asc \
             slurm-${SLURM_VERSION}-gcc${COMPILER_VERSION}-software.tar.gz

# Extract and install
sudo tar -xzf slurm-${SLURM_VERSION}-gcc${COMPILER_VERSION}-software.tar.gz -C /opt/
cd /opt && sudo ./data/slurm_assets/slurm_install.sh --full-init
```

### Build Compiler Toolchain

Build GCC compiler toolchains separately for reuse:

```bash
# Build default compiler (GCC 13.4.0)
slurm-factory build-compiler

# Build specific version
slurm-factory build-compiler --compiler-version 15.2.0

# Build and publish to buildcache with GPG signing
slurm-factory build-compiler --compiler-version 13.4.0 \
  --publish=compiler \
  --signing-key $GPG_KEY_ID \
  --gpg-private-key "$GPG_PRIVATE_KEY" \
  --gpg-passphrase "$GPG_PASSPHRASE"
```

## Package Structure

All builds produce GPG-signed relocatable tarballs:

```text
slurm-25.11-gcc13.4.0-software.tar.gz
├── view/                    # Slurm binaries & libraries
├── modules/slurm/25.11.lua  # Lmod module (relocatable)
└── data/slurm_assets/       # Config templates & install script
```

## Deployment

```bash
# Extract (from tarball build)
sudo tar -xzf slurm-25.11-gcc13.4.0-software.tar.gz -C /opt/

# Install (creates users, configs, services)
cd /opt && sudo ./data/slurm_assets/slurm_install.sh --full-init

# Use
module load slurm/25.11
```

## Buildcache Structure

The public buildcache is organized with a three-tier mirror architecture for optimal performance:

```text
https://slurm-factory-spack-binary-cache.vantagecompute.ai/
├── compilers/
│   ├── 15.2.0/    # GCC 15.2.0 build toolchain (GPG-signed)
│   ├── 14.2.0/    # GCC 14.2.0 build toolchain (GPG-signed)
│   ├── 13.4.0/    # GCC 13.4.0 build toolchain (GPG-signed)
│   ├── 12.5.0/    # GCC 12.5.0 build toolchain (GPG-signed)
│   ├── 11.5.0/    # GCC 11.5.0 build toolchain (GPG-signed)
│   ├── 10.5.0/    # GCC 10.5.0 build toolchain (GPG-signed)
│   ├── 9.5.0/     # GCC 9.5.0 build toolchain (GPG-signed)
│   ├── 8.5.0/     # GCC 8.5.0 build toolchain (GPG-signed)
│   └── 7.5.0/     # GCC 7.5.0 build toolchain (GPG-signed)
├── deps/
│   ├── 15.2.0/    # Slurm dependencies built with GCC 15.2.0 (GPG-signed)
│   ├── 14.2.0/    # Slurm dependencies built with GCC 14.2.0 (GPG-signed)
│   ├── 13.4.0/    # Slurm dependencies built with GCC 13.4.0 (GPG-signed)
│   └── ...        # All GCC versions (GPG-signed)
├── slurm/
│   ├── 25.11/
│   │   ├── 15.2.0/    # Slurm 25.11 built with GCC 15.2.0 (GPG-signed)
│   │   ├── 14.2.0/    # Slurm 25.11 built with GCC 14.2.0 (GPG-signed)
│   │   ├── 13.4.0/    # Slurm 25.11 built with GCC 13.4.0 (GPG-signed)
│   │   └── ...
│   ├── 24.11/
│   │   └── ...        # All GCC versions (GPG-signed)
│   └── 23.11/
│       └── ...        # All GCC versions (GPG-signed)
└── builds/
    ├── 25.11/
    │   ├── 15.2.0/
    │   │   ├── slurm-25.11-gcc15.2.0-software.tar.gz      # Complete tarball
    │   │   └── slurm-25.11-gcc15.2.0-software.tar.gz.asc  # GPG signature
    │   └── ...
    ├── 24.11/
    │   └── ...
    └── 23.11/
        └── ...
```

### Mirror Architecture

The buildcache uses a **three-tier mirror structure** for efficient caching and dependency resolution:

1. **`compilers/`** - GCC compiler toolchains (bootstrap dependencies)
2. **`deps/`** - Slurm runtime dependencies (OpenMPI, PMIx, Munge, etc.)
3. **`slurm/`** - Slurm packages compiled with specific GCC versions

This separation allows:
- ✅ **Faster builds** - Compiler toolchain cached across all Slurm versions
- ✅ **Better caching** - Dependencies shared across Slurm versions
- ✅ **Reduced storage** - No duplication of common packages
- ✅ **Parallel downloads** - Spack can fetch from multiple mirrors simultaneously

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
