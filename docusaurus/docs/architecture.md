# Architecture

Docker-based build system for creating relocatable Slurm packages using Spack.

## System Overview

```text
┌─────────────────────────────────────────────┐
│     Python CLI (Typer + Pydantic)           │
├─────────────────────────────────────────────┤
│  Docker Build  │ Volume Mounts │ Spack      │
├─────────────────────────────────────────────┤
│  Integrated TAR │ Modules │ Install Script  │
└─────────────────────────────────────────────┘
```

## Module Structure

```text
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

```text
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

Dynamic module paths using environment variable fallback:

```lua
-- Dynamic prefix with fallback
local prefix = os.getenv("SLURM_INSTALL_PREFIX") or "/opt/slurm/view"
prepend_path("PATH", pathJoin(prefix, "bin"))
prepend_path("LD_LIBRARY_PATH", pathJoin(prefix, "lib"))
setenv("SLURM_ROOT", prefix)
```

**Usage:**

```bash
# Default location
module load slurm/25.05-gcc13.4.0

# Custom location
export SLURM_INSTALL_PREFIX=/shared/apps/slurm
module load slurm/25.05-gcc13.4.0
```

## Package Structure

Single tarball output containing everything needed:

```text
slurm-{version}-gcc{compiler}-software.tar.gz (2-25GB depending on options)
├── view/                                  # Slurm installation
│   ├── bin/                               # Slurm binaries (srun, sbatch, etc.)
│   ├── sbin/                              # Daemons (slurmd, slurmctld, slurmdbd)
│   ├── lib/                               # Shared libraries and plugins
│   ├── lib64/                             # 64-bit libraries
│   ├── include/                           # Header files
│   └── share/                             # Documentation, man pages
├── modules/slurm/                         # Lmod modulefiles
│   └── {version}-gcc{compiler}.lua        # Modulefile for this build
└── data/slurm_assets/                     # Configuration and scripts
    ├── slurm_install.sh                   # Installation script
    ├── defaults/                          # Systemd unit files
    ├── slurm/                             # Configuration templates
    └── mysql/                             # Database configs
```

**Package naming examples:**

- `slurm-25.05-gcc13.4.0-software.tar.gz` - Slurm 25.05 with GCC 13.4.0
- `slurm-24.11-gcc10.5.0-software.tar.gz` - Slurm 24.11 with GCC 10.5.0  
- `slurm-23.11-gcc7.5.0-software.tar.gz` - Slurm 23.11 with GCC 7.5.0

## Compiler Toolchain

Builds support 8 different GCC versions for cross-distribution compatibility:

| Compiler | Compatible Distros | glibc | Bootstrap Time |
|----------|-------------------|-------|----------------|
| GCC 14.2.0 | Ubuntu 24.10+, Fedora 40+ | 2.40+ | +60 min |
| GCC 13.4.0 | Ubuntu 24.04+, Debian 13+ | 2.39 | Default |
| GCC 12.5.0 | Ubuntu 23.10+, Debian 12+ | 2.38 | +45 min |
| GCC 11.5.0 | Ubuntu 22.04+, Debian 12+ | 2.35 | +45 min |
| GCC 10.5.0 | RHEL 8+, Ubuntu 20.04+ | 2.31 | +50 min |
| GCC 9.5.0 | RHEL 8+, CentOS 8+ | 2.28 | +50 min |
| GCC 8.5.0 | RHEL 8+, CentOS 8+ | 2.28 | +55 min |
| GCC 7.5.0 | RHEL 7+, CentOS 7+ | 2.17 | +60 min |

Older compilers add build time for initial toolchain bootstrap, but use cached binaries on subsequent builds.

## Build Options

```bash
# CPU-optimized with default compiler (recommended)
slurm-factory build --slurm-version 25.05

# Specific compiler for RHEL 8 compatibility
slurm-factory build --slurm-version 25.05 --compiler-version 10.5.0

# With GPU support (CUDA/ROCm)
slurm-factory build --slurm-version 25.05 --gpu

# Minimal (Slurm only, no OpenMPI)
slurm-factory build --slurm-version 25.05 --minimal

# Combined: RHEL 8 with GPU support
slurm-factory build --slurm-version 25.05 --compiler-version 10.5.0 --gpu
```

## Docker Integration

**Volume Mounts:**

```text
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
