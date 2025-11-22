# Slurm Factory Spack Build Cache

The Slurm Factory Spack Build Cache is a public, **GPG-signed** binary package repository hosted on AWS that provides pre-compiled Slurm packages and GCC compiler toolchains. This dramatically reduces build times from 45-90 minutes to 5-15 minutes by eliminating the need for compilation.

## Overview

The build cache is a **CloudFront-distributed S3 bucket** with a **three-tier mirror architecture**:

- **GCC Compiler Toolchains** (versions 7.5.0 through 15.2.0) - **9 versions**
- **Slurm Dependencies** - Pre-built dependencies for each compiler version
- **Slurm Packages** (versions 23.11, 24.11, 25.11) - **3 versions**
- **Total: 27 Slurm combinations** (3 Slurm × 9 GCC versions)

All packages are:

- 🔐 **GPG-Signed** - Cryptographically signed for security and integrity
- ✅ **Pre-compiled** - Ready to install in minutes
- 📦 **Relocatable** - Deploy to any filesystem path
- 🎯 **Optimized** - CPU-specific compilation (x86_64_v3)
- ✅ **Tested** - Validated via GitHub Actions CI/CD

## Public Access

The build cache is publicly accessible via CloudFront CDN:

```text
https://slurm-factory-spack-binary-cache.vantagecompute.ai
```

No AWS credentials are required for read access.

## Directory Structure

The buildcache uses a three-tier architecture for optimal caching:

```text
slurm-factory-spack-binary-cache.vantagecompute.ai/
├── compilers/
│   ├── 15.2.0/                  # GCC 15.2.0 build toolchain (GPG-signed)
│   ├── 14.2.0/                  # GCC 14.2.0 build toolchain (GPG-signed)
│   ├── 13.4.0/                  # GCC 13.4.0 build toolchain (default, GPG-signed)
│   ├── 12.5.0/                  # GCC 12.5.0 build toolchain (GPG-signed)
│   ├── 11.5.0/                  # GCC 11.5.0 build toolchain (Ubuntu 22.04, GPG-signed)
│   ├── 10.5.0/                  # GCC 10.5.0 build toolchain (RHEL 8/Ubuntu 20.04, GPG-signed)
│   ├── 9.5.0/                   # GCC 9.5.0 build toolchain (GPG-signed)
│   ├── 8.5.0/                   # GCC 8.5.0 build toolchain (RHEL 8, GPG-signed)
│   └── 7.5.0/                   # GCC 7.5.0 build toolchain (RHEL 7, max compatibility, GPG-signed)
├── deps/
│   ├── 15.2.0/                  # Slurm dependencies built with GCC 15.2.0 (GPG-signed)
│   ├── 14.2.0/                  # Slurm dependencies built with GCC 14.2.0 (GPG-signed)
│   ├── 13.4.0/                  # Slurm dependencies built with GCC 13.4.0 (GPG-signed)
│   └── ...                      # All GCC versions (GPG-signed)
├── slurm/
│   ├── 25.11/                   # Slurm 25.11 (latest)
│   │   ├── 15.2.0/              # Slurm 25.11 built with GCC 15.2.0 (GPG-signed)
│   │   ├── 14.2.0/              # Slurm 25.11 built with GCC 14.2.0 (GPG-signed)
│   │   ├── 13.4.0/              # Slurm 25.11 built with GCC 13.4.0 (GPG-signed)
│   │   └── ...                  # All 9 GCC versions (GPG-signed)
│   ├── 24.11/                   # Slurm 24.11 (LTS) - All GCC versions
│   └── 23.11/                   # Slurm 23.11 (stable) - All GCC versions
└── builds/
    ├── 25.11/
    │   ├── 15.2.0/
    │   │   ├── slurm-25.11-gcc15.2.0-software.tar.gz      # Complete tarball
    │   │   └── slurm-25.11-gcc15.2.0-software.tar.gz.asc  # GPG signature
    │   ├── 14.2.0/
    │   │   ├── slurm-25.11-gcc14.2.0-software.tar.gz
    │   │   └── slurm-25.11-gcc14.2.0-software.tar.gz.asc
    │   └── ...                  # All GCC versions
    ├── 24.11/
    │   └── ...                  # All GCC versions with tarballs + signatures
    └── 23.11/
        └── ...                  # All GCC versions with tarballs + signatures
```

**All 27 combinations are GPG-signed and ready to install.**

### Three-Tier Architecture Benefits

The separation of compiler toolchain, dependencies, and Slurm packages provides:

- ✅ **Faster builds** - Compiler toolchain cached across all Slurm versions
- ✅ **Better caching** - Dependencies shared across Slurm versions
- ✅ **Reduced storage** - No duplication of common packages
- ✅ **Parallel downloads** - Spack fetches from multiple mirrors simultaneously
- ✅ **Easier updates** - Update dependencies independently of Slurm versions

## GPG Package Signing

All packages in the build cache are **cryptographically signed with GPG** for security and integrity verification.

### Key Information

**Signing Key Details:**

- **Key ID**: `DFB92630BCA5AB71`
- **Owner**: Vantage Compute Corporation (Slurm Factory Spack Cache Signing Key)
- **Email**: `info@vantagecompute.ai`
- **Type**: RSA 4096-bit

### Automatic Key Import

The easiest way to import the signing keys is to let Spack fetch them automatically from the buildcache:

```bash
# Add a mirror first
spack mirror add slurm-factory \
  https://slurm-factory-spack-binary-cache.vantagecompute.ai/slurm/25.11/13.4.0/

# Import and trust all GPG keys from the buildcache
spack buildcache keys --install --trust
```

This command:

1. Downloads all GPG public keys from the `_pgp/` directory in the buildcache
2. Imports them into Spack's GPG keyring
3. Marks them as trusted for package verification

### Manual Key Verification

For additional security in production environments, you can verify the key fingerprint:

```bash
# List imported keys
spack gpg list

# Expected output shows the Slurm Factory signing key:
# pub   rsa4096/DFB92630BCA5AB71 2025-XX-XX
#       Fingerprint: 9C4E 8B2F 3A1D 5E6C 7F8A  9B0D DFB9 2630 BCA5 AB71
```

### Signature Verification

Once keys are imported, Spack **automatically verifies package signatures** during installation:

```bash
# Install with automatic signature verification
spack install slurm@25.11%gcc@13.4.0

# Spack will verify GPG signatures before installing packages
# Any signature mismatch will abort the installation

# Check a specific package signature manually
spack buildcache check slurm@25.11
```

### Why GPG Signing Matters

- 🔒 **Integrity**: Ensures packages haven't been tampered with during transit
- ✅ **Authenticity**: Confirms packages came from Vantage Compute
- 🛡️ **Security**: Protects against man-in-the-middle attacks
- 📋 **Compliance**: Meets security requirements for production systems
- 🔍 **Provenance**: Establishes trust chain for audit trails

## Using the Build Cache

### Quick Start with Spack

Install GPG-signed Slurm from the build cache in 5-15 minutes:

```bash
# 1. Install Spack v1.0.0
git clone --depth 1 --branch v1.0.0 https://github.com/spack/spack.git
source spack/share/spack/setup-env.sh

# 2. Set versions
SLURM_VERSION=25.11
COMPILER_VERSION=15.2.0
CLOUDFRONT_URL=https://slurm-factory-spack-binary-cache.vantagecompute.ai

# 3. Add three-tier mirrors
spack mirror add slurm-factory-build-toolchain "${CLOUDFRONT_URL}/compilers/${COMPILER_VERSION}"
spack mirror add slurm-factory-slurm-deps "${CLOUDFRONT_URL}/deps/${COMPILER_VERSION}"
spack mirror add slurm-factory-slurm "${CLOUDFRONT_URL}/slurm/${SLURM_VERSION}/${COMPILER_VERSION}"

# 4. Import and trust GPG signing keys (enables automatic signature verification)
spack buildcache keys --install --trust

# 5. Install GPG-signed Slurm from buildcache (5-15 minutes!)
spack install slurm@${SLURM_VERSION}%gcc@${COMPILER_VERSION} target=x86_64_v3

# 6. Load and verify
spack load slurm@${SLURM_VERSION}
sinfo --version
# Output: slurm 25.11.4
```

### Download Pre-built Tarball

Alternatively, download a complete Slurm installation as a signed tarball:

```bash
# Set versions
SLURM_VERSION=25.11
COMPILER_VERSION=15.2.0
CLOUDFRONT_URL=https://slurm-factory-spack-binary-cache.vantagecompute.ai

# Download tarball and GPG signature
wget "${CLOUDFRONT_URL}/builds/${SLURM_VERSION}/${COMPILER_VERSION}/slurm-${SLURM_VERSION}-gcc${COMPILER_VERSION}-software.tar.gz"
wget "${CLOUDFRONT_URL}/builds/${SLURM_VERSION}/${COMPILER_VERSION}/slurm-${SLURM_VERSION}-gcc${COMPILER_VERSION}-software.tar.gz.asc"

# Import GPG key
gpg --keyserver keyserver.ubuntu.com --recv-keys DFB92630BCA5AB71

# Verify signature (REQUIRED - do not skip!)
gpg --verify slurm-${SLURM_VERSION}-gcc${COMPILER_VERSION}-software.tar.gz.asc \
             slurm-${SLURM_VERSION}-gcc${COMPILER_VERSION}-software.tar.gz

# Expected output:
# gpg: Good signature from "Vantage Compute Corporation (Slurm Factory Spack Cache Signing Key) <info@vantagecompute.ai>"

# Extract and install
sudo tar -xzf slurm-${SLURM_VERSION}-gcc${COMPILER_VERSION}-software.tar.gz -C /opt/
cd /opt && sudo ./data/slurm_assets/slurm_install.sh --full-init
```

### Using with slurm-factory CLI

The `slurm-factory` CLI can leverage the build cache automatically:

```bash
# Install from PyPI
pip install slurm-factory

# Build uses buildcache by default for dependencies
slurm-factory build-slurm --slurm-version 25.11 --compiler-version 15.2.0
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
| 15.2.0 | 2.40 | Latest (experimental) | `compilers/15.2.0/` |
| 14.2.0 | 2.39 | Latest stable | `compilers/14.2.0/` |
| 13.4.0 | 2.39 | Ubuntu 24.04 **(default)** | `compilers/13.4.0/` |
| 12.5.0 | 2.35 | Ubuntu 22.04 | `compilers/12.5.0/` |
| 11.5.0 | 2.35 | Ubuntu 22.04 | `compilers/11.5.0/` |
| 10.5.0 | 2.31 | RHEL 8 / Ubuntu 20.04 | `compilers/10.5.0/` |
| 9.5.0 | 2.28 | RHEL 8 | `compilers/9.5.0/` |
| 8.5.0 | 2.28 | RHEL 8 | `compilers/8.5.0/` |
| 7.5.0 | 2.17 | RHEL 7 | `compilers/7.5.0/` |

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
| 25.11 | Latest | All (7.5.0-15.2.0) | `slurm/25.11/{compiler}/` |
| 24.11 | LTS | All (7.5.0-14.2.0) | `slurm/24.11/{compiler}/` |
| 23.11 | Stable | All (7.5.0-14.2.0) | `slurm/23.11/{compiler}/` |

Each Slurm buildcache includes:
- **Slurm** - Complete workload manager with all plugins
- **OpenMPI** - MPI implementation
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
  https://slurm-factory-spack-binary-cache.vantagecompute.ai/slurm/25.11/13.4.0/

# Import GPG signing keys
spack buildcache keys --install --trust

# List all packages in buildcache
spack buildcache list --allarch
```

### Install Specific Dependencies

```bash
# Import GPG keys (if not already done)
spack buildcache keys --install --trust

# Install only OpenMPI from signed buildcache
spack install --cache-only openmpi@5.0.6

# Install PMIx from signed buildcache
spack install --cache-only pmix@5.0.3
```

### Use Multiple Mirrors

```bash
# Set CloudFront URL
CLOUDFRONT_URL=https://slurm-factory-spack-binary-cache.vantagecompute.ai

# Add three-tier mirrors for multiple versions
# Slurm 25.11 with GCC 15.2.0
spack mirror add slurm-25-gcc15-toolchain "${CLOUDFRONT_URL}/compilers/15.2.0"
spack mirror add slurm-25-gcc15-deps "${CLOUDFRONT_URL}/deps/15.2.0"
spack mirror add slurm-25-gcc15 "${CLOUDFRONT_URL}/slurm/25.11/15.2.0"

# Slurm 24.11 with GCC 13.4.0
spack mirror add slurm-24-gcc13-toolchain "${CLOUDFRONT_URL}/compilers/13.4.0"
spack mirror add slurm-24-gcc13-deps "${CLOUDFRONT_URL}/deps/13.4.0"
spack mirror add slurm-24-gcc13 "${CLOUDFRONT_URL}/slurm/24.11/13.4.0"

# Import GPG signing keys from all mirrors
spack buildcache keys --install --trust

# Install with verified signatures
spack install slurm@25.11%gcc@15.2.0  # Uses slurm-25-gcc15 mirrors
spack install slurm@24.11%gcc@13.4.0  # Uses slurm-24-gcc13 mirrors
```

### Cache-Only Installation

Force Spack to only use buildcache (fail if package not in cache):

```bash
# Import GPG keys first
spack buildcache keys --install --trust

# Install only from buildcache with signature verification
spack install --cache-only slurm@25.11
```

### GPG Key Management

All packages in the buildcache are GPG-signed for security and integrity:

```bash
# Import and trust GPG keys from buildcache
spack buildcache keys --install --trust

# List trusted GPG keys
spack gpg list

# Verify a package signature manually
spack buildcache check <package-spec>
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

# Import GPG keys if not already done
spack buildcache keys --install --trust

# Check buildcache index
spack buildcache list --allarch

# Try updating buildcache index
spack buildcache update-index
```

### Signature Verification Issues

If you encounter GPG signature errors:

```bash
# Import and trust GPG keys from buildcache
spack buildcache keys --install --trust

# Verify keys are installed
spack gpg list

# Check package signature
spack buildcache check slurm@25.11
```

### Network Issues

If downloads are slow or failing:

```bash
# Test CloudFront access
curl -I https://slurm-factory-spack-binary-cache.vantagecompute.ai/

# Try direct S3 access (if CloudFront is down)
spack mirror add s3-direct \
  https://slurm-factory-spack-buildcache-4b670.s3.amazonaws.com/slurm/25.11/13.4.0/buildcache
spack buildcache keys --install --trust
```

### Signature Verification Failures

If package signatures fail, the issue is usually that GPG keys haven't been imported:

```bash
# Import GPG keys from the buildcache
spack buildcache keys --install --trust

# Verify keys are installed
spack gpg list

# Try installation again
spack install slurm@25.11
```

If you still encounter issues:

```bash
# Update buildcache index
spack buildcache update-index

# Verify the package signature manually
spack buildcache check slurm@25.11
```

## See Also

- [Infrastructure](./infrastructure.md) - AWS infrastructure details
- [GitHub Actions](./github-actions.md) - CI/CD workflows
- [Architecture](./architecture.md) - Build system overview
- [Installation](./installation.md) - Getting started guide
