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

### build

Build a specific Slurm version with relocatable packages.

```bash
slurm-factory build [OPTIONS]
```

**Description:**

Builds Slurm packages using Docker containers and Spack. Supports multiple GCC versions, GPU acceleration, and buildcache publishing with GPG signing.

**Options:**

- `--slurm-version [25.11|24.11|23.11]` - Slurm version to build [default: 25.11]
- `--compiler-version TEXT` - GCC compiler version (15.2.0, 14.2.0, 13.4.0, 12.5.0, 11.5.0, 10.5.0, 9.5.0, 8.5.0, 7.5.0) [default: 13.4.0]
- `--gpu` - Enable GPU support (CUDA/ROCm) - creates larger packages
- `--verify` - Enable relocatability verification (for CI/testing)
- `--no-cache` - Force a fresh build without using Docker cache
- `--use-local-buildcache` - Use locally cached compiler tarball instead of building from source
- `--publish-s3` - Upload binaries to S3 (s3://slurm-factory-spack-buildcache-4b670)
- `--publish TEXT` - Publish to buildcache: none (default), slurm (only Slurm), deps (only dependencies), all (Slurm + deps) [default: none]
- `--enable-hierarchy` - Enable Core/Compiler/MPI module hierarchy
- `--signing-key TEXT` - GPG key ID for signing buildcache packages (e.g., '0xKEYID')
- `--gpg-private-key TEXT` - Base64-encoded GPG private key to import into Docker container for signing
- `--gpg-passphrase TEXT` - Passphrase for the GPG private key (if encrypted)
- `--help` - Show help message and exit

**Compiler Toolchains:**

All compilers are built with Spack for relocatability:

- **15.2.0**: GCC 15.2, glibc 2.39, latest GCC 15
- **14.2.0**: GCC 14.2, glibc 2.39, latest stable
- **13.4.0** (default): GCC 13.4, glibc 2.39, Ubuntu 24.04 compatible
- **12.5.0**: GCC 12.5, glibc 2.35, Ubuntu 22.04 compatible
- **11.5.0**: GCC 11.5, glibc 2.35, good compatibility
- **10.5.0**: GCC 10.5, glibc 2.31, RHEL 8/Ubuntu 20.04 compatible
- **9.5.0**: GCC 9.5, glibc 2.28, wide compatibility
- **8.5.0**: GCC 8.5, glibc 2.28, RHEL 8 minimum
- **7.5.0**: GCC 7.5, glibc 2.17, RHEL 7 compatible (maximum compatibility)

**Build Types:**

- **Default**: ~2-5GB, CPU-only with OpenMPI and standard features
- **--gpu**: ~15-25GB, includes CUDA/ROCm support for GPU workloads
- **--verify**: Enable relocatability verification for CI/testing
- **--no-cache**: Force a fresh build without using Docker layer cache

**Examples:**

```bash
# Build default CPU version (25.11, gcc 13.4.0)
slurm-factory build

# Build specific version
slurm-factory build --slurm-version 24.11

# Build with specific compiler
slurm-factory build --compiler-version 14.2.0

# Build with gcc 12 - Ubuntu 22.04 compatibility
slurm-factory build --compiler-version 12.5.0

# Build with gcc 10.5 - RHEL 8 compatibility
slurm-factory build --compiler-version 10.5.0

# Build with gcc 7.5 - RHEL 7 compatibility
slurm-factory build --compiler-version 7.5.0

# Build with GPU support
slurm-factory build --gpu

# Build with verification (CI)
slurm-factory build --verify

# Build without Docker cache
slurm-factory build --no-cache

# Build with module hierarchy
slurm-factory build --enable-hierarchy

# Build and publish all to buildcache
slurm-factory build --publish=all

# Build and publish only Slurm
slurm-factory build --publish=slurm

# Build and publish only dependencies
slurm-factory build --publish=deps

# Build and publish with GPG signing
slurm-factory build --publish=all --signing-key 0xDFB92630BCA5AB71

# Use local compiler tarball (advanced)
slurm-factory build --use-local-buildcache
```

---

### build-compiler

Build a GCC compiler toolchain for use in Slurm builds.

```bash
slurm-factory build-compiler [OPTIONS]
```

**Description:**

Builds a relocatable GCC compiler toolchain using Spack and optionally publishes it to S3 buildcache for reuse across builds.

**Options:**

- `--compiler-version TEXT` - GCC compiler version to build (15.2.0, 14.2.0, 13.4.0, 12.5.0, 11.5.0, 10.5.0, 9.5.0, 8.5.0, 7.5.0) [default: 13.4.0]
- `--no-cache` - Force a fresh build without using Docker cache
- `--publish TEXT` - Publish to buildcache: none (default), compiler (publish compiler), all (same as compiler) [default: none]
- `--signing-key TEXT` - GPG key ID for signing buildcache packages (e.g., '0xKEYID')
- `--gpg-private-key TEXT` - Base64-encoded GPG private key to import into Docker container for signing
- `--gpg-passphrase TEXT` - GPG private key passphrase for signing packages
- `--help` - Show help message and exit

**Compiler Toolchains:**

All toolchains are built with Spack for relocatability:

- **15.2.0**: GCC 15.2, glibc 2.39, latest GCC 15
- **14.2.0**: GCC 14.2, glibc 2.39, latest stable
- **13.4.0** (default): GCC 13.4, glibc 2.39, Ubuntu 24.04 compatible
- **12.5.0**: GCC 12.5, glibc 2.35, Ubuntu 22.04 compatible
- **11.5.0**: GCC 11.5, glibc 2.35, good compatibility
- **10.5.0**: GCC 10.5, glibc 2.31, RHEL 8/Ubuntu 20.04 compatible
- **9.5.0**: GCC 9.5, glibc 2.28, wide compatibility
- **8.5.0**: GCC 8.5, glibc 2.28, RHEL 8 minimum
- **7.5.0**: GCC 7.5, glibc 2.17, RHEL 7 compatible (maximum compatibility)

**Examples:**

```bash
# Build default compiler (gcc 13.4.0)
slurm-factory build-compiler

# Build gcc 14.2
slurm-factory build-compiler --compiler-version 14.2.0

# Build gcc 10.5 for RHEL 8
slurm-factory build-compiler --compiler-version 10.5.0

# Build and publish to S3 buildcache
slurm-factory build-compiler --publish=compiler

# Build and publish with GPG signing
slurm-factory build-compiler --publish=all --signing-key 0xDFB92630BCA5AB71

# Build without Docker cache
slurm-factory build-compiler --no-cache
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

# Basic build with defaults (Slurm 25.11, GCC 13.4.0)
build(slurm_version="25.11", compiler_version="13.4.0")

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
├── slurm-25.11-gcc13.4.0-software.tar.gz       # Standard build
├── slurm-25.11-gcc13.4.0-gpu-software.tar.gz   # GPU build
├── slurm-25.11-gcc10.5.0-software.tar.gz       # RHEL 8 compatible
└── slurm-24.11-gcc7.5.0-software.tar.gz        # RHEL 7 compatible
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
slurm-factory build \
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
spack install slurm@25.11%gcc@13.4.0
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
