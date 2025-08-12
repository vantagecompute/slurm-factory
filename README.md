<div align="center">

 <a href="https://www.vantagecompute.ai/">
  <img src="https://vantage-compute-public-assets.s3.us-east-1.amazonaws.com/branding/vantage-logo-text-black-horz.png" alt="Vantage Compute Logo" width="100" style="margin-bottom: 0.5em;"/>
</a>

# Slurm Factory

[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![PyPI](https://img.shields.io/pypi/v/slurm-factory.svg)](https://pypi.org/project/slurm-factory/)
[![LXD](https://img.shields.io/badge/LXD-5.0+-orange.svg)](https://linuxcontainers.org/lxd)

![Build Status](https://img.shields.io/github/actions/workflow/status/vantagecompute/slurm-factory/ci.yaml?branch=main&label=build&logo=github&style=plastic)
![GitHub Issues](https://img.shields.io/github/issues/vantagecompute/slurm-factory?label=issues&logo=github&style=plastic)
![Pull Requests](https://img.shields.io/github/issues-pr/vantagecompute/slurm-factory?label=pull-requests&logo=github&style=plastic)
![GitHub Contributors](https://img.shields.io/github/contributors/vantagecompute/slurm-factory?logo=github&style=plastic)

</div>

A modern Python CLI tool that automates building optimized, portable Slurm workload manager packages using LXD containers and the Spack package manager.

## 🚀 Quick Start

### Option 1: Install from PyPI (Recommended)

```bash
# Install LXD
sudo snap install lxd && sudo lxd init

# Install slurm-factory from PyPI
pip install slurm-factory

# Build latest Slurm
slurm-factory build
```

### Option 2: Install from Source

```bash
# Install LXD and UV
sudo snap install lxd && sudo lxd init
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone https://github.com/vantagecompute/slurm-factory.git
cd slurm-factory && uv sync

# Build latest Slurm
uv run slurm-factory build
```

Extract and deploy packages on your HPC cluster!

## ✨ Key Features

- **Automated Build Process**: One-command Slurm package creation
- **Portable Packages**: Self-contained software and module packages  
- **Performance Optimized**: CPU-specific optimizations using Spack
- **Multi-Version Support**: Support for Slurm 25.05, 24.11, 23.11, 23.02
- **Container Isolation**: Reproducible builds in LXD containers
- **Intelligent Caching**: Ultra-fast rebuilds with build and source caching

## 📋 Supported Versions

| Version | Status | Package Size (CPU) | Package Size (GPU) |
|---------|---------|--------------------|--------------------|
| 25.05   | ✅ Latest | ~2-5GB | ~15-25GB |
| 24.11   | ✅ LTS | ~2-5GB | ~15-25GB |
| 23.11   | ✅ Stable | ~2-5GB | ~15-25GB |
| 23.02   | ✅ Legacy | ~2-5GB | ~15-25GB |

## 📚 Documentation

Visit our comprehensive documentation site:
**[vantagecompute.github.io/slurm-factory](https://vantagecompute.github.io/slurm-factory)**

- **[Installation Guide](https://vantagecompute.github.io/slurm-factory/installation/)**: Detailed setup instructions
- **[Architecture Overview](https://vantagecompute.github.io/slurm-factory/architecture/)**: How slurm-factory works
- **[Deployment Guide](https://vantagecompute.github.io/slurm-factory/deployment/)**: Production deployment workflows
- **[API Reference](https://vantagecompute.github.io/slurm-factory/api-reference/)**: Complete CLI documentation
- **[Troubleshooting](https://vantagecompute.github.io/slurm-factory/troubleshooting/)**: Common issues and solutions

## 🛠️ Basic Usage

### Building Packages

```bash
# Build latest Slurm (CPU-optimized)
uv run slurm-factory build

# Build specific version with GPU support
uv run slurm-factory build --slurm-version 24.11 --gpu

# Build minimal Slurm (no OpenMPI, smaller size)
uv run slurm-factory build --minimal

# Build with verbose output
uv run slurm-factory --verbose build
```

**Note**: All builds now automatically generate self-contained Lmod modules that include proper environment variables for dependencies, eliminating the need for separate dependency modules.

### Deploying Packages

```bash
# Extract software package on target system
sudo mkdir -p /opt/slurm
sudo tar -xzf ~/.slurm-factory/builds/slurm-25.05-software.tar.gz -C /opt/

# Extract module files (use updated version if available)
sudo mkdir -p /usr/share/lmod/lmod/modulefiles/slurm
sudo tar -xzf ~/.slurm-factory/builds/slurm-25.05-module-updated.tar.gz -C /usr/share/lmod/lmod/modulefiles/slurm
# OR use original if not updated:
# sudo tar -xzf ~/.slurm-factory/builds/slurm-25.05-module.tar.gz -C /usr/share/lmod/lmod/modulefiles/slurm

# Load the module
module load slurm/25.05
```

## 🏗️ Architecture

### Build Process

```
1. Container Creation
   ├── Launch Ubuntu 24.04 LXD container
   ├── Install build dependencies
   └── Set up isolated environment

2. Spack Installation
   ├── Bootstrap Spack package manager
   ├── Configure optimized compiler toolchain
   └── Set up package repositories

3. Slurm Build
   ├── Compile Slurm with optimizations
   ├── Install runtime dependencies
   └── Package software stack

4. Module Generation
   ├── Create Environment Module files
   ├── Set up module hierarchy
   └── Configure Lmod integration

5. Package Creation
   ├── Create portable software archive
   ├── Bundle module files
   └── Generate deployment scripts
```

### Output Structure

```
~/.slurm-factory/
├── builds/                 # Build outputs
│   ├── 25.05/
│   │   ├── slurm-25.05-software.tar.gz
│   │   └── slurm-25.05-module.tar.gz
│   └── 24.11/
├── spack-buildcache/       # Binary package cache
└── spack-sourcecache/      # Source download cache
```

## 🎯 Use Cases

- **Research Computing Centers**: Standardized Slurm deployments across clusters
- **Cloud HPC Providers**: Rapid cluster provisioning with consistent software stacks
- **Educational Institutions**: Teaching HPC concepts with reproducible environments
- **Industry HPC**: Compliance-ready deployments with audit trails

## 🤝 Contributing

We welcome contributions! See our [Contributing Guide](https://vantagecompute.github.io/slurm-factory/contributing/) for details on:

- Setting up development environment
- Code style guidelines  
- Submitting pull requests
- Reporting issues

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/vantagecompute/slurm-factory/issues)
- **Discussions**: [GitHub Discussions](https://github.com/vantagecompute/slurm-factory/discussions)
- **Email**: [james@vantagecompute.ai](mailto:james@vantagecompute.ai)

---

**Made with ❤️ by [Vantage Compute](https://vantagecompute.ai)**
