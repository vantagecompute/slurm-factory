# API Reference

CLI commands and Python API.

## CLI Commands

### build

Build relocatable Slurm packages.

```bash
slurm-factory build [OPTIONS]
```

**Options:**
- `--slurm-version TEXT` - Slurm version (default: 25.11)
- `--compiler-version TEXT` - GCC compiler version (default: 13.4.0)
  - Available: 15.2.0, 14.3.0, 13.4.0, 12.5.0, 11.5.0, 10.5.0, 9.5.0, 8.5.0, 7.5.0
- `--gpu` - Include GPU support (CUDA/ROCm)
- `--minimal` - Minimal build (no OpenMPI)
- `--verify` - Verify relocatability
- `--no-cache` - Force fresh build without Docker cache

**Examples:**
```bash
# Standard build with default compiler (GCC 13.4.0)
slurm-factory build --slurm-version 25.11

# Build with specific compiler for cross-distro compatibility
slurm-factory build --compiler-version 10.5.0  # RHEL 8/Ubuntu 20.04
slurm-factory build --compiler-version 7.5.0   # RHEL 7

# Latest compiler versions
slurm-factory build --compiler-version 15.2.0  # Latest GCC 15

# Combine options
slurm-factory build --slurm-version 25.11 --compiler-version 11.5.0 --gpu
slurm-factory build --slurm-version 25.11 --minimal
```

### clean

Remove build containers and caches.

```bash
slurm-factory clean [OPTIONS]
```

**Options:**
- `--full` - Remove all containers and caches (slower next build)

**Examples:**
```bash
slurm-factory clean              # Keep caches
slurm-factory clean --full       # Full cleanup
```

## Global Options

- `--project-name TEXT` - Custom project name for containers
- `--verbose` - Enable verbose output
- `--help` - Show help message

**Examples:**
```bash
slurm-factory --project-name prod build --slurm-version 25.11
slurm-factory --verbose build --slurm-version 25.11
```

## Python API

```python
from slurm_factory.builder import build
from slurm_factory.config import Settings

# Basic build
build(slurm_version="25.11", gpu=False, minimal=False)

# GPU build
build(slurm_version="25.11", gpu=True, minimal=False)

# Custom settings
settings = Settings(project_name="custom")
build(slurm_version="25.11", settings=settings)
```

## Configuration

**Environment Variables:**
- `IF_PROJECT_NAME` - Default project name
- `SPACK_JOBS` - Parallel build jobs

**Cache Directories:**
```
~/.slurm-factory/
├── builds/              # Final packages
├── spack-buildcache/    # Binary cache
├── spack-sourcecache/   # Source downloads
└── binary_index/        # Dependency cache
```

## Exceptions

- `SlurmFactoryError` - Base exception
- `DockerError` - Docker operation failures
- `BuildError` - Build failures
- `ConfigurationError` - Invalid configuration
