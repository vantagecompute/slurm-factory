<div align="center">
<a href="https://www.vantagecompute.ai/">
  <img src="https://vantage-compute-public-assets.s3.us-east-1.amazonaws.com/branding/vantage-logo-text-black-horz.png" alt="Vantage Compute Logo" width="100"/>
</a>

# Slurm Factory

[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![PyPI](https://img.shields.io/pypi/v/slurm-factory.svg)](https://pypi.org/project/slurm-factory/)
[![Docker](https://img.shields.io/badge/Docker-24.0+-blue.svg)](https://docker.com)

Build relocatable, optimized Slurm packages using Docker and Spack.

</div>

## Quick Start

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER && newgrp docker

# Install slurm-factory
pip install slurm-factory

# Build Slurm
slurm-factory build --slurm-version 25.05

# Deploy
sudo tar -xzf ~/.slurm-factory/builds/slurm-25.05-software.tar.gz -C /opt/
cd /opt && sudo ./data/slurm_assets/slurm_install.sh --full-init
module load slurm/25.05
```

## Features

- **Relocatable** - Deploy to any path, no host dependencies
- **Fast** - Cached builds: 5-15 minutes (first build: 45-90 min)
- **Portable** - Runtime prefix override via environment variable
- **Optimized** - Architecture-specific compilation, parallel builds
- **Clean** - Docker isolation, no system pollution

## Requirements

- Docker 24.0+
- Python 3.12+
- 50GB disk space
- 4+ CPU cores (8+ recommended)
- 16GB RAM (32GB+ recommended)

## Build Options

### Compiler Toolchain Build

Build a GCC compiler toolchain separately for reuse across multiple builds:

```bash
# Build default compiler (GCC 13.4.0)
slurm-factory build-compiler

# Build specific compiler version
slurm-factory build-compiler --compiler-version 14.2.0

# Build and publish to buildcache
slurm-factory build-compiler --compiler-version 13.4.0 --publish

# Fresh build without Docker cache
slurm-factory build-compiler --no-cache
```

The compiler build produces:
- Relocatable GCC compiler tarball (for manual distribution)
- Spack buildcache binaries (for automated reuse)

### Slurm Package Build

```bash
# Standard (CPU-optimized, 2-5GB)
slurm-factory build --slurm-version 25.05

# GPU support (CUDA/ROCm, 15-25GB)
slurm-factory build --slurm-version 25.05 --gpu

# Minimal (no OpenMPI, 1-2GB)
slurm-factory build --slurm-version 25.05 --minimal

# Cross-distro compatibility with older toolchains
slurm-factory build --compiler-version 10.5.0  # RHEL 8 / Ubuntu 20.04
slurm-factory build --compiler-version 7.5.0   # RHEL 7

# Use pre-built compiler from buildcache (default)
slurm-factory build --slurm-version 25.05 --use-buildcache

# Build compiler from source (slower)
slurm-factory build --slurm-version 25.05 --no-use-buildcache

# Latest compilers
slurm-factory build --compiler-version 14.2.0  # Latest GCC 14
slurm-factory build --compiler-version 13.4.0  # GCC 13.4 (default)

# Verbose
slurm-factory --verbose build --slurm-version 25.05
```

## Compiler Toolchains

All compiler toolchains are built by Spack for maximum relocatability and cross-distribution compatibility. 

You can now build compiler toolchains separately using `slurm-factory build-compiler` and reuse them across multiple Slurm builds.

| Version | Target Distro        | glibc | Description                      |
|---------|----------------------|-------|----------------------------------|
| 14.2.0  | Latest               | 2.39  | Latest GCC 14, modern features   |
| 13.4.0  | Ubuntu 24.04         | 2.39  | **Default**, Ubuntu 24.04        |
| 12.5.0  | Latest               | 2.35  | Latest GCC 12                    |
| 11.5.0  | Ubuntu 22.04         | 2.35  | Good compatibility               |
| 10.5.0  | RHEL 8 / Ubuntu 20.04| 2.31  | Wide compatibility               |
| 9.5.0   | Latest               | 2.28  | Latest GCC 9                     |
| 8.5.0   | RHEL 8               | 2.28  | Older distros                    |
| 7.5.0   | RHEL 7               | 2.17  | Maximum compatibility            |

## Supported Versions

| Version | Status | Size (CPU) | Size (GPU) |
|---------|--------|------------|------------|
| 25.05   | Latest | 2-5GB      | 15-25GB    |
| 24.11   | LTS    | 2-5GB      | 15-25GB    |
| 23.11   | Stable | 2-5GB      | 15-25GB    |
| 23.02   | Legacy | 2-5GB      | 15-25GB    |

## Package Structure

```
slurm-25.05-software.tar.gz
├── view/                    # Slurm binaries & libraries
├── modules/slurm/25.05.lua  # Lmod module (relocatable)
└── data/slurm_assets/       # Config templates & install script
```

## Deployment

```bash
# Extract
sudo tar -xzf slurm-25.05-software.tar.gz -C /opt/

# Install (creates users, configs, services)
cd /opt && sudo ./data/slurm_assets/slurm_install.sh --full-init --cluster-name mycluster

# Use
module load slurm/25.05
```

**Relocatable:**
```bash
# Deploy to custom path
export SLURM_INSTALL_PREFIX=/shared/apps/slurm
module load slurm/25.05
```

## Documentation

**[vantagecompute.github.io/slurm-factory](https://vantagecompute.github.io/slurm-factory)**

## How It Works

### Two-Stage Build System

The build process is now split into two independent stages for better efficiency and reusability:

#### Stage 1: Compiler Toolchain Build (Optional, One-time)

1. **Docker Container** - Ubuntu 24.04 with build tools
2. **Spack Bootstrap** - Build custom GCC compiler with specific glibc
3. **Package Compiler** - Create tarball and populate buildcache
4. **Publish** - Store binaries for reuse across builds

```bash
slurm-factory build-compiler --compiler-version 13.4.0 --publish
```

**Output:**
- `~/.slurm-factory/compilers/13.4.0/gcc-13.4.0-compiler.tar.gz` - Relocatable compiler tarball
- `~/.slurm-factory/buildcache/` - Spack binary cache for reuse

#### Stage 2: Slurm Package Build

1. **Docker Container** - Ubuntu 24.04 with build tools
2. **Compiler Reuse** - Use pre-built compiler from buildcache (or build from source)
3. **Build Slurm** - Compile Slurm with dependencies using Spack
4. **Package** - Create tarball with modules and install script
5. **Deploy** - Extract and run installation script

```bash
slurm-factory build --slurm-version 25.05 --use-buildcache
```

**Output:**
- `~/.slurm-factory/25.05/13.4.0/slurm-25.05-gcc13.4.0-software.tar.gz`

### Build Cache Architecture

The build system uses Spack's buildcache to store and reuse binaries:

- **Source Cache** (`~/.slurm-factory/source/`) - Downloaded source tarballs
- **Build Cache** (`~/.slurm-factory/buildcache/`) - Compiled binary packages

These caches are mounted into Docker containers during builds, enabling:
- Faster rebuilds (reuse pre-built dependencies)
- Consistency across builds
- Publishable binary artifacts for sharing

**Performance:**
- First compiler build: 30-60 minutes
- First Slurm build (with compiler from buildcache): 30-60 minutes  
- First Slurm build (building compiler from source): 60-120 minutes
- Cached Slurm builds: 5-15 minutes (>10x speedup)
- Cache hit rate: 80-95%

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

- **Issues**: https://github.com/vantagecompute/slurm-factory/issues
- **Docs**: https://vantagecompute.github.io/slurm-factory
- **Website**: https://www.vantagecompute.ai

---

Built with ❤️ by [Vantage Compute](https://www.vantagecompute.ai)
