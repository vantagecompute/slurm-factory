# API Reference

Complete CLI commands and Python API documentation for slurm-factory.

## CLI Commands

### slurm-factory

Main application command with global options.

```bash
slurm-factory [OPTIONS] COMMAND [ARGS]...
```

**Global Options:**

- `--project-name TEXT` - LXD project name for resource creation (env: `IF_PROJECT_NAME`) [default: slurm-factory]
- `--verbose, -v` - Enable verbose output
- `--install-completion` - Install shell completion
- `--show-completion` - Show shell completion script
- `--help` - Show help message and exit

**Available Commands:**

- `build` - Build a specific Slurm version
- `build-compiler` - Build a GCC compiler toolchain
- `clean` - Clean up Docker containers and images

---

### build-slurm

Build a specific Slurm version with relocatable packages.

```bash
slurm-factory build-slurm [OPTIONS]
```

**Description:**

Builds Slurm packages using Docker containers and Spack. Supports multiple OS toolchains, GPU acceleration, and buildcache publishing with GPG signing.

**Options:**

- `--slurm-version [25.11|24.11|23.11]` - Slurm version to build [default: 25.11]
- `--toolchain TEXT` - OS toolchain to use (noble, jammy, resolute, rockylinux10, rockylinux9, rockylinux8) [default: noble]
- `--gpu` - Enable GPU support (CUDA/ROCm) - creates larger packages
- `--verify` - Enable relocatability verification (for CI/testing)
- `--no-cache` - Force a fresh build without using Docker cache
- `--buildcache TEXT` - Use buildcache: none (default), all (dependencies + Slurm), deps (only dependencies) [default: none]
- `--publish TEXT` - Publish to buildcache: none (default), slurm (only Slurm), deps (only dependencies) [default: none]
- `--enable-hierarchy` - Enable Core/Compiler/MPI module hierarchy
- `--signing-key TEXT` - GPG key ID for signing buildcache packages (e.g., '0xKEYID')
- `--gpg-private-key TEXT` - Base64-encoded GPG private key to import into Docker container for signing
- `--gpg-passphrase TEXT` - Passphrase for the GPG private key (if encrypted)
- `--help` - Show help message and exit

**OS Toolchains:**

Each toolchain uses the OS-provided compiler for maximum binary compatibility:

- **resolute**: Ubuntu 25.04, GCC 15.x, glibc 2.41 (latest)
- **noble** (default): Ubuntu 24.04, GCC 13.x, glibc 2.39
- **jammy**: Ubuntu 22.04, GCC 11.x, glibc 2.35
- **rockylinux10**: Rocky Linux 10 / RHEL 10, GCC 14.x, glibc 2.39
- **rockylinux9**: Rocky Linux 9 / RHEL 9, GCC 11.x, glibc 2.34
- **rockylinux8**: Rocky Linux 8 / RHEL 8, GCC 8.x, glibc 2.28

**Build Types:**

- **Default**: ~2-5GB, CPU-only with OpenMPI and standard features
- **--gpu**: ~15-25GB, includes CUDA/ROCm support for GPU workloads
- **--verify**: Enable relocatability verification for CI/testing
- **--no-cache**: Force a fresh build without using Docker layer cache

**Examples:**

```bash
# Build default CPU version (25.11, noble)
slurm-factory build-slurm

# Build specific version
slurm-factory build-slurm --slurm-version 24.11

# Build for Ubuntu 22.04
slurm-factory build-slurm --toolchain jammy

# Build for Rocky Linux 9 / RHEL 9
slurm-factory build-slurm --toolchain rockylinux9

# Build for Rocky Linux 8 / RHEL 8
slurm-factory build-slurm --toolchain rockylinux8

# Build with GPU support
slurm-factory build-slurm --gpu

# Build with verification (CI)
slurm-factory build-slurm --verify

# Build without Docker cache
slurm-factory build-slurm --no-cache

# Build with module hierarchy
slurm-factory build-slurm --enable-hierarchy

# Build using remote buildcache for dependencies
slurm-factory build-slurm --buildcache=deps

# Build and publish to buildcache
slurm-factory build-slurm --publish=slurm

# Build and publish only dependencies
slurm-factory build-slurm --publish=deps

# Build and publish with GPG signing
slurm-factory build-slurm --publish=all --signing-key 0xDFB92630BCA5AB71

# Use local compiler tarball (advanced)
slurm-factory build-slurm --use-local-buildcache
```

---

### clean

Clean up Docker containers and images from slurm-factory builds.

```bash
slurm-factory clean [OPTIONS]
```

**Description:**

Removes stopped containers by default. Use `--full` to remove both containers and images for complete cleanup.

**Options:**

- `--full` - Remove Docker images in addition to containers
- `--help` - Show help message and exit

**Examples:**

```bash
# Remove stopped containers
slurm-factory clean

# Remove containers and images
slurm-factory clean --full
```

---

## Python API

```python
from slurm_factory.builder import build
from slurm_factory.config import Settings

# Basic build with defaults (Slurm 25.11, noble toolchain)
build(slurm_version="25.11", toolchain="noble")

# GPU-enabled build
build(slurm_version="25.11", gpu=True)

# Build with specific compiler for RHEL 8
build(slurm_version="25.11", compiler_version="10.5.0")

# Build with verification
build(slurm_version="25.11", verify=True)

# Build without cache
build(slurm_version="25.11", no_cache=True)

# Build and publish to buildcache
build(
    slurm_version="25.11",
    publish="all",
    signing_key="0xDFB92630BCA5AB71",
    gpg_private_key="base64_encoded_key",
    gpg_passphrase="passphrase"
)

# Custom settings
settings = Settings(project_name="production")
build(slurm_version="25.11", settings=settings)
```

---

## Configuration

### Environment Variables

- `IF_PROJECT_NAME` - Default project name for Docker containers and resources [default: slurm-factory]
- `SPACK_JOBS` - Number of parallel build jobs (optional)

### Cache Directories

slurm-factory uses several cache directories under `~/.slurm-factory/`:

```
~/.slurm-factory/
├── builds/              # Final tarball packages
├── spack-buildcache/    # Binary package cache (compiled packages)
├── spack-sourcecache/   # Source archive downloads
├── binary_index/        # Dependency resolution cache
└── ccache/              # Compiler object cache
```

### Build Artifacts

Build outputs are stored in `~/.slurm-factory/builds/`:

```
~/.slurm-factory/builds/
├── slurm-25.11-noble-software.tar.gz          # Ubuntu 24.04 build
├── slurm-25.11-noble-gpu-software.tar.gz      # GPU build
├── slurm-25.11-jammy-software.tar.gz          # Ubuntu 22.04 build
├── slurm-25.11-rockylinux9-software.tar.gz    # Rocky Linux 9 / RHEL 9
└── slurm-24.11-rockylinux8-software.tar.gz    # Rocky Linux 8 / RHEL 8
```

---

## GPG Signing

All buildcache packages can be signed with GPG for security and integrity.

### Signing Options

When using `--publish`, you can sign packages with:

- `--signing-key TEXT` - GPG key ID (e.g., `0xDFB92630BCA5AB71`)
- `--gpg-private-key TEXT` - Base64-encoded private key
- `--gpg-passphrase TEXT` - Private key passphrase (if encrypted)

### Example with Signing

```bash
# Build and publish with GPG signing
slurm-factory build-slurm \
  --slurm-version 25.11 \
  --publish=all \
  --signing-key 0xDFB92630BCA5AB71 \
  --gpg-private-key "$(base64 -w0 < ~/.gnupg/private.key)" \
  --gpg-passphrase "your-passphrase"
```

### Verification

Packages signed with GPG can be verified by Spack:

```bash
# Import GPG keys
spack buildcache keys --install --trust

# Install with automatic signature verification
spack install slurm@25.11
```

---

## Exit Codes

- `0` - Success
- `1` - General error (build failed, validation error, etc.)
- `2` - Command-line usage error

---

## Additional Resources

- [Installation Guide](./installation.md) - Setup and prerequisites
- [Examples](./examples.md) - Real-world usage scenarios
- [Architecture](./architecture.md) - Build system internals
- [Deployment](./deployment.md) - Installing and configuring built packages

## Exceptions

- `SlurmFactoryError` - Base exception
- `DockerError` - Docker operation failures
- `BuildError` - Build failures
- `ConfigurationError` - Invalid configuration
