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
- **Advanced Spack 1.x** - Enhanced compiler packaging and module hierarchy

## Advanced Features (Spack 1.x)

- **Enhanced Compiler Packaging** - GCC runtime libraries as separate package for better relocatability
- **Module Hierarchy** - Optional Core/Compiler/MPI 3-tier Lmod hierarchy
- **Binary Cache** - Fast rebuilds with buildcache support (5-10x speedup)
- **Improved RPATH** - Enhanced RPATH/RUNPATH for true relocatability
- **Professional Modules** - Advanced Jinja2 templates with autoloading and conflict resolution

## Requirements

- Docker 24.0+
- Python 3.12+
- 50GB disk space
- 4+ CPU cores (8+ recommended)
- 16GB RAM (32GB+ recommended)

## Build Options

```bash
# Standard (CPU-optimized, 2-5GB)
slurm-factory build --slurm-version 25.05

# GPU support (CUDA/ROCm, 15-25GB)
slurm-factory build --slurm-version 25.05 --gpu

# Minimal (no OpenMPI, 1-2GB)
slurm-factory build --slurm-version 25.05 --minimal

# Advanced Spack 1.x features
slurm-factory build --slurm-version 25.05 --enable-hierarchy  # Core/Compiler/MPI hierarchy
slurm-factory build --slurm-version 25.05 --enable-buildcache  # Binary cache for 5-10x faster rebuilds

# Cross-distro compatibility with older toolchains
slurm-factory build --compiler-version 10.5.0  # RHEL 8 / Ubuntu 20.04
slurm-factory build --compiler-version 7.5.0   # RHEL 7

# Latest compilers
slurm-factory build --compiler-version 15.2.0  # Latest GCC 15
slurm-factory build --compiler-version 14.3.0  # Latest GCC 14

# Combine multiple options
slurm-factory build --slurm-version 25.05 --enable-hierarchy --enable-buildcache

# Verbose
slurm-factory --verbose build --slurm-version 25.05
```

## Compiler Toolchains

All compiler toolchains are built by Spack for maximum relocatability and cross-distribution compatibility.

| Version | Target Distro        | glibc | Description                      |
|---------|----------------------|-------|----------------------------------|
| 15.2.0  | Latest               | 2.39  | Latest GCC 15, newest features   |
| 14.3.0  | Latest               | 2.39  | Latest GCC 14, modern features   |
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

## Spack 1.x Features

### Module Hierarchy (--enable-hierarchy)

The optional 3-tier Core/Compiler/MPI hierarchy provides better dependency management:

- **Core**: GCC runtime libraries (always available)
- **Compiler**: Packages compiled with specific GCC version (e.g., OpenMPI)
- **MPI**: Packages requiring both compiler and MPI (e.g., Slurm)

**Benefits:**
- Automatic dependency loading
- Prevents incompatible module combinations
- Professional HPC environment

**Usage:**
```bash
# Build with hierarchy
slurm-factory build --slurm-version 25.05 --enable-hierarchy

# After deployment
module avail           # Shows available Core modules
module load slurm      # Automatically loads required dependencies
```

### Binary Cache (--enable-buildcache)

Enable binary package caching for 5-10x faster rebuilds:

**Benefits:**
- Reuse compiled packages across builds
- Dramatically faster incremental builds (2-5 minutes vs 45-90 minutes)
- Efficient CI/CD workflows

**Usage:**
```bash
# First build with buildcache
slurm-factory build --slurm-version 25.05 --enable-buildcache

# Subsequent builds are much faster
slurm-factory build --slurm-version 25.05 --enable-buildcache
# Uses cached binaries, only rebuilds changed packages
```

### Enhanced Relocatability

All builds use Spack 1.x enhanced RPATH configuration:

- **RPATH/RUNPATH**: Binaries find libraries without LD_LIBRARY_PATH
- **Unbound paths**: RPATH not bound to absolute paths - allows relocation
- **GCC runtime**: Separate gcc-runtime package for clean ABI compatibility
- **Padded paths**: Optional padded install paths for binary caching

## Documentation

**[vantagecompute.github.io/slurm-factory](https://vantagecompute.github.io/slurm-factory)**

## How It Works

1. **Docker Container** - Ubuntu 24.04 with build tools
2. **Spack Bootstrap** - Install GCC compiler toolchain
3. **Build Slurm** - Compile with dependencies (cached)
4. **Package** - Create tarball with modules and install script
5. **Deploy** - Extract and run installation script

**Performance:**
- First build: 45-90 minutes
- Cached builds: 5-15 minutes (>10x speedup)
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
