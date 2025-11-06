---
title: "Slurm Factory - Modern HPC Package Builder"
description: "Build and deploy optimized Slurm packages using public buildcache or custom Docker builds"
slug: /
---

# Slurm Factory

**Slurm Factory** is a modern Python CLI tool that builds and deploys **relocatable** Slurm workload manager packages for HPC environments. It leverages a **public binary cache** for instant installations or creates custom Docker builds with Spack for specific requirements.

## Key Features

- 🚀 **Public Binary Cache**: Pre-built packages at `slurm-factory-spack-binary-cache.vantagecompute.ai`
- ⚡ **Instant Deployment**: Install from cache in minutes instead of hours of compilation
- 📦 **Relocatable Packages**: Deploy to any filesystem path without recompilation
- 🔧 **Two Simple Commands**: `build` for Slurm packages, `build-compiler` for GCC toolchains
- 🏗️ **Modern Architecture**: Built with Python, Typer CLI, comprehensive test coverage
- 🎮 **GPU Support**: CUDA-enabled builds for GPU-accelerated HPC workloads
- 🔄 **Automated CI/CD**: GitHub Actions workflows maintain the public buildcache
- 📊 **Module System**: Lmod modules for easy environment management

## Support Matrix

Slurm Factory supports multiple Slurm and GCC compiler combinations. All combinations are pre-built and available in the public buildcache:

### Slurm Versions

- **25.11** (Latest)
- **24.11** (LTS)
- **23.11** (Stable)
- **23.02** (Legacy)

### GCC Compiler Versions

- **14.2.0** (Latest)
- **13.4.0** (Recommended)
- **12.5.0**
- **11.5.0**
- **10.5.0**
- **9.5.0**
- **8.5.0**
- **7.5.0**

### Recommended Combinations

| Slurm Version | GCC Version | Build Type | Use Case |
|---------------|-------------|------------|----------|
| 25.11 | 13.4.0 | GPU | Latest features with GPU support |
| 24.11 | 13.4.0 | Default | Long-term support production |
| 25.11 | 14.2.0 | Default | Bleeding edge |
| 23.11 | 12.5.0 | Default | Conservative production |

All version combinations are available in the buildcache at:

```text
https://slurm-factory-spack-binary-cache.vantagecompute.ai/slurm/<VERSION>/<COMPILER>/buildcache
```

## Quick Start

### Method 1: Using the Public Buildcache (Recommended)

The fastest way to deploy Slurm is using pre-built binaries from our public buildcache:

```bash
# Install slurm-factory
pip install slurm-factory

# Install Spack v1.0.0
git clone --depth 1 --branch v1.0.0 https://github.com/spack/spack.git
source spack/share/spack/setup-env.sh

# Add compiler and Slurm buildcache mirrors
spack mirror add slurm-factory-compilers \
  https://slurm-factory-spack-binary-cache.vantagecompute.ai/compilers/13.4.0/buildcache

spack mirror add slurm-factory-slurm \
  https://slurm-factory-spack-binary-cache.vantagecompute.ai/slurm/25.11/13.4.0/buildcache

# Install Slurm from cache (takes minutes!)
spack install --no-check-signature slurm@25.11%gcc@13.4.0

# Load and verify
spack load slurm@25.11
sinfo --version
# Output: slurm 25.11.0
```

### Method 2: Building Locally

For custom configurations or when you need specific build options:

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER && newgrp docker

# Install slurm-factory
pip install slurm-factory

# Build a compiler toolchain (one-time, ~15-20 minutes)
slurm-factory build-compiler --compiler-version 13.4.0

# Build Slurm with that compiler (~35-45 minutes)
slurm-factory build --slurm-version 25.11 --compiler-version 13.4.0

# Extract the tarball
sudo tar -xzf ~/.slurm-factory/builds/slurm-25.11-gcc13.4.0-software.tar.gz -C /opt/

# Run installation script
cd /opt && sudo ./data/slurm_assets/slurm_install.sh --full-init

# Load the module
module load slurm/25.11
```

## Two Primary Commands

### `build-compiler`

Build GCC compiler toolchains for use with Slurm builds:

```bash
# Build GCC 13.4.0 (default recommended version)
slurm-factory build-compiler

# Build specific version
slurm-factory build-compiler --compiler-version 14.2.0

# Build and publish to buildcache (requires AWS credentials)
slurm-factory build-compiler --compiler-version 13.4.0 --publish
```

**Supported Versions**: 14.2.0, 13.4.0, 12.5.0, 11.5.0, 10.5.0, 9.5.0, 8.5.0, 7.5.0

**Output**: Docker image and optional buildcache upload to S3

### `build`

Build complete Slurm packages with all dependencies:

```bash
# Standard build (CPU-optimized, ~2-5GB)
slurm-factory build --slurm-version 25.11

# GPU support (includes CUDA/ROCm, ~15-25GB)
slurm-factory build --slurm-version 25.11 --gpu

# Minimal build (no OpenMPI/extras, ~1-2GB)
slurm-factory build --slurm-version 25.11 --minimal

# Use specific compiler version
slurm-factory build --slurm-version 25.11 --compiler-version 14.2.0

# Publish to buildcache (requires AWS credentials)
slurm-factory build --slurm-version 25.11 --publish=all
```

**Supported Versions**: 25.11, 24.11, 23.11, 23.02

**Output**: Tarball at `~/.slurm-factory/builds/slurm-{version}-gcc{compiler}-software.tar.gz`

## Public Buildcache

Pre-built packages are available at `slurm-factory-spack-binary-cache.vantagecompute.ai` via global CloudFront CDN.

### Available Packages

#### Compilers

- **URL**: `https://slurm-factory-spack-binary-cache.vantagecompute.ai/compilers/{version}/buildcache`
- **Versions**: GCC 7.5.0 through 14.2.0
- **Includes**: gcc, gcc-runtime, binutils, gmp, mpfr, mpc, zlib-ng, zstd

#### Slurm Packages

- **URL**: `https://slurm-factory-spack-binary-cache.vantagecompute.ai/slurm/{slurm_version}/{compiler_version}/buildcache`
- **Slurm Versions**: 25.11, 24.11, 23.11, 23.02
- **Compiler Combinations**: Each Slurm version × each GCC version
- **Includes**: All dependencies (OpenMPI, OpenSSL, Munge, PMIx, HDF5, etc.)

### Benefits

- ⚡ **10x Faster**: Install in 5-15 minutes vs 45-90 minutes building from source
- 🔒 **Verified Builds**: All packages built and tested via GitHub Actions CI/CD
- 🌐 **Global CDN**: CloudFront distribution for fast worldwide access
- 🔄 **Always Current**: Automated workflows keep packages up-to-date
- 💾 **Storage Efficient**: Download only what you need (2-25GB vs 50GB build requirements)

### Usage Examples

```bash
# Install latest Slurm with recommended compiler
spack mirror add slurm-factory \
  https://slurm-factory-spack-binary-cache.vantagecompute.ai/slurm/25.11/13.4.0/buildcache
spack install --no-check-signature slurm@25.11

# Install legacy Slurm with older compiler
spack mirror add slurm-factory \
  https://slurm-factory-spack-binary-cache.vantagecompute.ai/slurm/23.11/11.5.0/buildcache
spack install --no-check-signature slurm@23.11

# Install just the compiler
spack mirror add gcc-buildcache \
  https://slurm-factory-spack-binary-cache.vantagecompute.ai/compilers/13.4.0/buildcache
spack install --no-check-signature gcc@13.4.0
```

## Build Types Comparison

| Build Type | Dependencies | Size | Build Time | Buildcache Time | Use Case |
|------------|-------------|------|------------|-----------------|----------|
| **CPU-only** | ~45 packages | 2-5GB | 35-45 min | 5-10 min | Production clusters |
| **GPU-enabled** | ~180 packages | 15-25GB | 75-90 min | 15-20 min | GPU/CUDA clusters |
| **Minimal** | ~20 packages | 1-2GB | 15-20 min | 3-5 min | Development/testing |

## Requirements

### For Using Buildcache

- Python 3.12+ (for slurm-factory tool - optional, can use Spack directly)
- Spack v1.0.0+
- 10-25GB disk space (depending on build type)
- Internet connection for buildcache download

### For Local Builds

- Python 3.12+
- Docker 24.0+
- 50GB disk space
- 4+ CPU cores, 16GB RAM recommended
- Internet connection for initial Docker image pull

## GitHub Actions CI/CD

Slurm Factory uses three GitHub Actions workflows to maintain the public buildcache:

1. **build-and-publish-compiler-buildcache.yml**: Builds and publishes GCC compiler toolchains
2. **build-and-publish-slurm-deps-all-compilers.yml**: Builds Slurm dependencies for all compiler combinations
3. **build-and-publish-all-packages.yml**: Builds complete Slurm packages (Slurm + dependencies)

All workflows use:

- AWS OIDC authentication for secure S3 access
- Self-hosted runners for faster builds
- Matrix builds for parallel execution
- Automated testing of buildcache installations

See [Contributing Guide](./contributing.md) for details on setting up CI/CD workflows.

## Use Cases

- **HPC Cluster Deployment**: Standardized Slurm installations across heterogeneous clusters
- **Development Environments**: Quick Slurm setup for testing without lengthy compilation
- **Multi-Version Support**: Running different Slurm versions side-by-side with module system
- **Performance Testing**: Optimized builds for specific hardware configurations  
- **Container Deployment**: Portable packages for containerized HPC environments
- **Air-Gapped Installations**: Download buildcache once, deploy offline

## Next Steps

- **[Installation Guide](./installation.md)**: Detailed setup instructions
- **[API Reference](./api-reference.md)**: Complete documentation of `build` and `build-compiler` commands
- **[Build Artifacts](./build-artifacts.md)**: Understanding the buildcache and tarball outputs
- **[Architecture](./architecture.md)**: Understanding the build system internals
- **[Examples](./examples.md)**: Real-world usage scenarios
- **[Contributing](./contributing.md)**: Development workflow and submitting changes

---

**Built with ❤️ by [Vantage Compute](https://vantagecompute.ai)**
