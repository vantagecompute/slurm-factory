# Slurm Factory Spack Build Cache

The Slurm Factory Spack Build Cache is a public binary package repository hosted on AWS that provides pre-compiled Slurm packages and GCC compiler toolchains. This dramatically reduces build times from hours to minutes by eliminating the need for compilation.

## Overview

The build cache is a **CloudFront-distributed S3 bucket** containing:

- **GCC Compiler Toolchains** (versions 7.5.0 through 15.2.0)
- **Slurm Packages** (versions 23.02, 23.11, 24.11, 25.11)
- **All Dependencies** (OpenMPI, PMIx, Munge, HDF5, CUDA, etc.)

All packages are:
- ✅ **Pre-compiled and signed** with GPG
- ✅ **Relocatable** - deploy to any filesystem path
- ✅ **Optimized** - CPU-specific compilation (x86_64_v3)
- ✅ **Tested** - validated via GitHub Actions CI/CD

## Public Access

The build cache is publicly accessible via CloudFront CDN:

```
https://slurm-factory-spack-binary-cache.vantagecompute.ai
```

No AWS credentials are required for read access.

## Directory Structure

```text
slurm-factory-spack-binary-cache.vantagecompute.ai/
├── compilers/
│   ├── 15.2.0/
│   │   └── buildcache/          # GCC 15.2.0 compiler packages
│   ├── 14.2.0/
│   │   └── buildcache/          # GCC 14.2.0 compiler packages
│   ├── 13.4.0/
│   │   └── buildcache/          # GCC 13.4.0 compiler packages (default)
│   ├── 12.5.0/
│   │   └── buildcache/
│   ├── 11.5.0/
│   │   └── buildcache/
│   ├── 10.5.0/
│   │   └── buildcache/
│   ├── 9.5.0/
│   │   └── buildcache/
│   ├── 8.5.0/
│   │   └── buildcache/
│   └── 7.5.0/
│       └── buildcache/
└── slurm/
    ├── 25.11/                   # Slurm 25.11 (latest)
    │   ├── 15.2.0/
    │   │   └── buildcache/      # Slurm 25.11 + deps built with GCC 15.2.0
    │   ├── 14.2.0/
    │   │   └── buildcache/      # Slurm 25.11 + deps built with GCC 14.2.0
    │   ├── 13.4.0/
    │   │   └── buildcache/      # Slurm 25.11 + deps built with GCC 13.4.0
    │   └── ...
    ├── 24.11/                   # Slurm 24.11 (LTS)
    │   └── ...
    ├── 23.11/                   # Slurm 23.11 (stable)
    │   └── ...
    └── 23.02/                   # Slurm 23.02 (legacy)
        └── ...
```

## Using the Build Cache

### Quick Start with Spack

Install Slurm from the build cache in minutes:

```bash
# 1. Install Spack v1.0.0
git clone --depth 1 --branch v1.0.0 https://github.com/spack/spack.git
source spack/share/spack/setup-env.sh

# 2. Add compiler buildcache mirror
spack mirror add slurm-factory-compilers \
  https://slurm-factory-spack-binary-cache.vantagecompute.ai/compilers/13.4.0/buildcache

# 3. Add Slurm buildcache mirror
spack mirror add slurm-factory-slurm \
  https://slurm-factory-spack-binary-cache.vantagecompute.ai/slurm/25.11/13.4.0/buildcache

# 4. Install Slurm from cache (takes 5-15 minutes!)
spack install --no-check-signature slurm@25.11%gcc@13.4.0

# 5. Load and verify
spack load slurm@25.11
sinfo --version
# Output: slurm 25.11.0
```

### Using with slurm-factory CLI

The `slurm-factory` CLI can leverage the build cache automatically:

```bash
# Install from PyPI
pip install slurm-factory

# Build uses buildcache by default for dependencies
slurm-factory build --slurm-version 25.11 --compiler-version 13.4.0
```

The CLI will:
1. Pull the compiler from the buildcache (if available)
2. Pull all Slurm dependencies from the buildcache
3. Only compile Slurm itself from source
4. Package everything into a relocatable tarball

## Available Packages

### Compiler Toolchains

All GCC versions are available with full dependency chains:

| GCC Version | glibc | Target Distro | Buildcache URL |
|-------------|-------|---------------|----------------|
| 15.2.0 | 2.40 | Latest (experimental) | `compilers/15.2.0/buildcache` |
| 14.2.0 | 2.39 | Latest stable | `compilers/14.2.0/buildcache` |
| 13.4.0 | 2.39 | Ubuntu 24.04 **(default)** | `compilers/13.4.0/buildcache` |
| 12.5.0 | 2.35 | Ubuntu 22.04 | `compilers/12.5.0/buildcache` |
| 11.5.0 | 2.35 | Ubuntu 22.04 | `compilers/11.5.0/buildcache` |
| 10.5.0 | 2.31 | RHEL 8 / Ubuntu 20.04 | `compilers/10.5.0/buildcache` |
| 9.5.0 | 2.28 | RHEL 8 | `compilers/9.5.0/buildcache` |
| 8.5.0 | 2.28 | RHEL 8 | `compilers/8.5.0/buildcache` |
| 7.5.0 | 2.17 | RHEL 7 | `compilers/7.5.0/buildcache` |

Each compiler buildcache includes:
- `gcc` - Full GCC compiler suite (C, C++, Fortran)
- `gcc-runtime` - Runtime libraries (libgcc, libstdc++, libgfortran)
- `binutils` - Assembler, linker, and binary tools
- `gmp`, `mpfr`, `mpc` - Math libraries
- `zlib-ng`, `zstd` - Compression libraries

### Slurm Packages

All combinations of Slurm version × GCC compiler version are available:

| Slurm Version | Status | Available Compilers | Buildcache URL Pattern |
|---------------|--------|---------------------|------------------------|
| 25.11 | Latest | All (7.5.0-15.2.0) | `slurm/25.11/{compiler}/buildcache` |
| 24.11 | LTS | All (7.5.0-14.2.0) | `slurm/24.11/{compiler}/buildcache` |
| 23.11 | Stable | All (7.5.0-14.2.0) | `slurm/23.11/{compiler}/buildcache` |
| 23.02 | Legacy | All (7.5.0-14.2.0) | `slurm/23.02/{compiler}/buildcache` |

Each Slurm buildcache includes:
- **Slurm** - Complete workload manager with all plugins
- **OpenMPI** - MPI implementation (unless minimal build)
- **PMIx** - Process Management Interface for Exascale
- **Munge** - Authentication service
- **OpenSSL** - TLS/SSL support
- **HDF5** - High-performance data format
- **hwloc** - Hardware locality
- **libevent** - Event notification
- **UCX** - Unified Communication X
- And 40+ more dependencies

GPU builds additionally include:
- **CUDA** - NVIDIA CUDA toolkit (11.8+, 12.x)
- **ROCm** - AMD ROCm platform (5.7+, 6.x for select builds)

## Build Cache Benefits

### Speed Comparison

| Build Type | From Source | From Buildcache | Speedup |
|------------|-------------|-----------------|---------|
| Compiler Only | 30-60 min | 2-5 min | **10-15x** |
| Slurm (CPU) | 45-90 min | 5-15 min | **10-15x** |
| Slurm (GPU) | 90-180 min | 15-25 min | **6-10x** |

### Storage Savings

| Build Type | Local Build | Buildcache | Savings |
|------------|-------------|------------|---------|
| Compiler | 50 GB disk | 5 GB download | **90%** |
| Slurm (CPU) | 50 GB disk | 10 GB download | **80%** |
| Slurm (GPU) | 100 GB disk | 25 GB download | **75%** |

### Additional Benefits

- ✅ **No Docker required** - Install directly with Spack
- ✅ **Reproducible** - Same binaries every time
- ✅ **Verified** - All packages built and tested via CI/CD
- ✅ **Signed** - GPG signatures for package integrity
- ✅ **Global CDN** - Fast downloads worldwide via CloudFront
- ✅ **Bandwidth efficient** - Only download what you need

## Advanced Usage

### List Available Packages

```bash
# Add mirror
spack mirror add slurm-factory \
  https://slurm-factory-spack-binary-cache.vantagecompute.ai/slurm/25.11/13.4.0/buildcache

# List all packages in buildcache
spack buildcache list --allarch
```

### Install Specific Dependencies

```bash
# Install only OpenMPI from buildcache
spack install --no-check-signature --cache-only openmpi@5.0.6

# Install PMIx from buildcache
spack install --no-check-signature --cache-only pmix@5.0.3
```

### Use Multiple Mirrors

```bash
# Add multiple buildcache mirrors (Spack will try in order)
spack mirror add compilers \
  https://slurm-factory-spack-binary-cache.vantagecompute.ai/compilers/13.4.0/buildcache

spack mirror add slurm-deps \
  https://slurm-factory-spack-binary-cache.vantagecompute.ai/slurm/25.11/13.4.0/buildcache

# Install will use both mirrors
spack install --no-check-signature slurm@25.11
```

### Cache-Only Installation

Force Spack to only use buildcache (fail if package not in cache):

```bash
spack install --no-check-signature --cache-only slurm@25.11
```

### Verify Package Signatures

If you have the GPG public key, you can verify package signatures:

```bash
# Import GPG public key (if available)
spack gpg trust <key-file>

# Install with signature verification
spack install slurm@25.11  # Without --no-check-signature
```

## CI/CD Integration

The buildcache is automatically maintained by GitHub Actions workflows. See [GitHub Actions](./github-actions.md) for details.

### Automated Builds

Three workflows keep the buildcache current:

1. **build-and-publish-compiler-buildcache.yml** - Builds and publishes GCC compilers
2. **build-and-publish-slurm-all.yml** - Builds Slurm dependencies for all compiler combinations
3. **build-and-publish-slurm-tarball.yml** - Builds complete Slurm tarballs

All workflows:
- Run on self-hosted runners for performance
- Use AWS OIDC for secure S3 access
- Sign packages with GPG
- Test installations before publishing
- Generate deployment summaries

## Infrastructure

The buildcache is hosted on AWS infrastructure managed via CDK. See [Infrastructure](./infrastructure.md) for details.

### Components

- **S3 Bucket**: `slurm-factory-spack-buildcache-4b670`
- **CloudFront Distribution**: Global CDN for fast access
- **Route53**: DNS for `slurm-factory-spack-binary-cache.vantagecompute.ai`
- **IAM Roles**: GitHub OIDC for automated publishing

### Regions and Availability

- **Primary Region**: us-east-1
- **CDN**: CloudFront with global edge locations
- **Availability**: 99.9% SLA via AWS

## Troubleshooting

### Build Cache Not Found

If Spack can't find packages in buildcache:

```bash
# Verify mirror is configured
spack mirror list

# Check buildcache index
spack buildcache list --allarch

# Try updating buildcache index
spack buildcache update-index
```

### Network Issues

If downloads are slow or failing:

```bash
# Test CloudFront access
curl -I https://slurm-factory-spack-binary-cache.vantagecompute.ai/

# Try direct S3 access (if CloudFront is down)
spack mirror add s3-direct \
  https://slurm-factory-spack-buildcache-4b670.s3.amazonaws.com/slurm/25.11/13.4.0/buildcache
```

### Signature Verification Failures

If package signatures fail:

```bash
# Skip signature verification (use with caution)
spack install --no-check-signature slurm@25.11

# Or import the public key if available
spack gpg list  # Check if key is already imported
```

## See Also

- [Infrastructure](./infrastructure.md) - AWS infrastructure details
- [GitHub Actions](./github-actions.md) - CI/CD workflows
- [Architecture](./architecture.md) - Build system overview
- [Installation](./installation.md) - Getting started guide
