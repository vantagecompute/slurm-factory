# Architecture

Docker-based build system for creating relocatable Slurm packages using Spack.

## System Overview

```
┌─────────────────────────────────────────────┐
│     Python CLI (Typer + Pydantic)           │
├─────────────────────────────────────────────┤
│  Docker Build  │ Volume Mounts │ Spack      │
├─────────────────────────────────────────────┤
│  Integrated TAR │ Modules │ Install Script  │
└─────────────────────────────────────────────┘
```

## Module Structure

```
slurm_factory/
├── main.py          # CLI interface
├── builder.py       # Build orchestration
├── config.py        # Settings & cache management
├── constants.py     # Build configuration & templates
├── spack_yaml.py    # Dynamic Spack config
├── utils.py         # Docker & package creation
└── exceptions.py    # Error handling
```

## Build Pipeline

1. **Docker Container** - Ubuntu 24.04 base with build tools
2. **Spack Bootstrap** - Install compiler toolchain
3. **Dependency Build** - Compile Slurm and dependencies
4. **Package Creation** - Tar view/, modules/, data/

## Caching Strategy

```
~/.slurm-factory/
├── builds/              # Final tarballs
├── spack-buildcache/    # Binary packages (>10x speedup)
├── spack-sourcecache/   # Downloaded sources
└── binary_index/        # Dependency cache
```

**Performance:**
- First build: 45-90 minutes
- Cached builds: 5-15 minutes
- Cache hit: 80-95%

## Dependency Classification

**External (Build-Only):**
- cmake, autoconf, automake, gcc, pkg-config
- Not included in final package

**Built Fresh (Runtime):**
- munge, json-c, curl, openssl, hwloc
- Architecture-optimized, security-critical

## Relocatable Modules

```lua
-- Dynamic prefix with fallback
prepend_path("PATH", "${SLURM_INSTALL_PREFIX:-/opt/slurm/view}/bin")
prepend_path("LD_LIBRARY_PATH", "${SLURM_INSTALL_PREFIX:-/opt/slurm/view}/lib")
setenv("SLURM_ROOT", "${SLURM_INSTALL_PREFIX:-/opt/slurm/view}")
```

**Usage:**
```bash
# Default location
module load slurm/25.05

# Custom location
export SLURM_INSTALL_PREFIX=/shared/apps/slurm
module load slurm/25.05
```

## Package Structure

```
slurm-25.05-software.tar.gz (2-25GB)
├── view/                  # Slurm binaries & libraries
├── modules/slurm/25.05.lua # Lmod module
└── data/slurm_assets/     # Configs & install script
```

## Build Options

```bash
# CPU-optimized (recommended)
slurm-factory build --slurm-version 25.05

# With GPU support  
slurm-factory build --slurm-version 25.05 --gpu

# Minimal (Slurm only, no OpenMPI)
slurm-factory build --slurm-version 25.05 --minimal
```

## Docker Integration

**Volume Mounts:**
```
~/.slurm-factory/spack-buildcache  → /opt/slurm-factory-cache/buildcache
~/.slurm-factory/spack-sourcecache → /opt/slurm-factory-cache/sourcecache
```

**Container Lifecycle:**
1. Create container with Ubuntu 24.04
2. Mount cache volumes
3. Install Spack and bootstrap compiler
4. Build Slurm with dependencies
5. Extract packages to host
6. Cleanup container

## Error Handling

Custom exception hierarchy:
- `SlurmFactoryError` - Base exception
- `DockerError` - Docker operation failures  
- `BuildError` - Build process failures
- `ConfigurationError` - Invalid configuration

## Optimization Features

- **Parallel compilation** - 4 jobs by default
- **ccache** - C/C++ object caching
- **Docker layer caching** - Faster image builds
- **Binary package cache** - Reuse compiled dependencies
- **Hardlinks** - Fast file operations

## Security

- Process isolation via Docker namespaces
- Resource limits (--cpus, --memory)
- Checksum validation for downloads
- User-specific cache directories
- No privileged container access
