# Slurm Factory Spack Build Cache

The Slurm Factory Spack Build Cache is a public, **GPG-signed** binary package repository hosted on AWS that provides pre-compiled Slurm packages built with OS-native compilers. This dramatically reduces build times from 45-90 minutes to 5-15 minutes by eliminating the need for compilation.

## Overview

The build cache is a **CloudFront-distributed S3 bucket** with a **toolchain-based architecture**:

- **OS Toolchains** - Ubuntu (noble, jammy, resolute) and Rocky Linux (8, 9, 10)
- **Slurm Dependencies** - Pre-built dependencies for each toolchain
- **Slurm Packages** (versions 23.11, 24.11, 25.11) - **3 versions**
- **Total: 18 Slurm combinations** (3 Slurm × 6 OS toolchains)

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

The buildcache uses a toolchain-first architecture organized by OS:

```text
slurm-factory-spack-binary-cache.vantagecompute.ai/
├── noble/                       # Ubuntu 24.04 (recommended)
│   └── slurm/
│       ├── deps/                # Slurm dependencies (GPG-signed)
│       ├── 25.11/               # Slurm 25.11 packages (GPG-signed)
│       ├── 24.11/               # Slurm 24.11 packages (GPG-signed)
│       └── 23.11/               # Slurm 23.11 packages (GPG-signed)
├── jammy/                       # Ubuntu 22.04
│   └── slurm/
│       ├── deps/
│       ├── 25.11/
│       ├── 24.11/
│       └── 23.11/
├── resolute/                    # Ubuntu 25.04
│   └── slurm/
│       └── ...
├── rockylinux10/                # Rocky Linux 10 / RHEL 10
│   └── slurm/
│       └── ...
├── rockylinux9/                 # Rocky Linux 9 / RHEL 9
│   └── slurm/
│       └── ...
├── rockylinux8/                 # Rocky Linux 8 / RHEL 8
│   └── slurm/
│       └── ...
└── builds/
    ├── 25.11/
    │   ├── noble/
    │   │   ├── slurm-25.11-noble-software.tar.gz      # Complete tarball
    │   │   └── slurm-25.11-noble-software.tar.gz.asc  # GPG signature
    │   ├── jammy/
    │   │   ├── slurm-25.11-jammy-software.tar.gz
    │   │   └── slurm-25.11-jammy-software.tar.gz.asc
    │   └── ...                  # All OS toolchains
    ├── 24.11/
    │   └── ...                  # All toolchains with tarballs + signatures
    └── 23.11/
        └── ...                  # All toolchains with tarballs + signatures
```

**All 18 combinations are GPG-signed and ready to install.**

### Toolchain-Based Architecture Benefits

The organization by OS toolchain provides:

- ✅ **OS Compatibility** - Packages built with native system compilers
- ✅ **Better caching** - Dependencies shared across Slurm versions within each toolchain
- ✅ **Reduced storage** - No duplication of common packages per OS
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
  https://slurm-factory-spack-binary-cache.vantagecompute.ai/noble/slurm/25.11/

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
spack install slurm@25.11

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
TOOLCHAIN=noble  # or: jammy, resolute, rockylinux9, rockylinux10, rockylinux8
CLOUDFRONT_URL=https://slurm-factory-spack-binary-cache.vantagecompute.ai

# 3. Add two-tier mirrors (organized by toolchain)
spack mirror add slurm-factory-deps "${CLOUDFRONT_URL}/${TOOLCHAIN}/slurm/deps/"
spack mirror add slurm-factory-slurm "${CLOUDFRONT_URL}/${TOOLCHAIN}/slurm/${SLURM_VERSION}/"

# 4. Import and trust GPG signing keys (enables automatic signature verification)
spack buildcache keys --install --trust

# 5. Install GPG-signed Slurm from buildcache (5-15 minutes!)
spack install slurm@${SLURM_VERSION} target=x86_64_v3

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
TOOLCHAIN=noble  # or: jammy, resolute, rockylinux9, rockylinux10, rockylinux8
CLOUDFRONT_URL=https://slurm-factory-spack-binary-cache.vantagecompute.ai

# Download tarball and GPG signature
wget "${CLOUDFRONT_URL}/${TOOLCHAIN}/${SLURM_VERSION}/slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz"
wget "${CLOUDFRONT_URL}/${TOOLCHAIN}/${SLURM_VERSION}/slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz.asc"

# Import GPG key
gpg --keyserver keyserver.ubuntu.com --recv-keys DFB92630BCA5AB71

# Verify signature (REQUIRED - do not skip!)
gpg --verify slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz.asc \
             slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz

# Expected output:
# gpg: Good signature from "Vantage Compute Corporation (Slurm Factory Spack Cache Signing Key) <info@vantagecompute.ai>"

# Extract and install
sudo tar -xzf slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz -C /opt/
cd /opt && sudo ./data/slurm_assets/slurm_install.sh --full-init
```

### Using with slurm-factory CLI

The `slurm-factory` CLI can leverage the build cache automatically:

```bash
# Install from PyPI
pip install slurm-factory

# Build uses buildcache by default for dependencies
slurm-factory build-slurm --slurm-version 25.11 --toolchain noble
```

The CLI will:

1. Pull the compiler from the buildcache (if available)
2. Pull all Slurm dependencies from the buildcache
3. Only compile Slurm itself from source
4. Package everything into a relocatable tarball

## Available Packages

### OS Toolchains

All OS toolchains use the system GCC and glibc from the base OS:

| Toolchain | OS/Distribution | System GCC | Glibc | Use Case |
|-----------|-----------------|------------|-------|----------|
| **noble** | Ubuntu 24.04 | 13.2.0 | 2.39 | **Recommended** - Modern stable |
| resolute | Ubuntu 25.04 | 15.2.0 | 2.42 | Latest features |
| jammy | Ubuntu 22.04 | 11.4.0 | 2.35 | LTS - Wide compatibility |
| rockylinux10 | Rocky Linux 10 / RHEL 10 | 14.3.1 | 2.40 | RHEL 10 compatible |
| rockylinux9 | Rocky Linux 9 / RHEL 9 | 11.4.1 | 2.34 | RHEL 9 compatible |
| rockylinux8 | Rocky Linux 8 / RHEL 8 | 8.5.0 | 2.28 | RHEL 8 compatible |

### Slurm Packages

All combinations of Slurm version × OS toolchain are available:

| Slurm Version | Status | Available Toolchains | Buildcache URL Pattern |
|---------------|--------|---------------------|------------------------|
| 25.11 | Latest | All 6 toolchains | `{toolchain}/slurm/25.11/` |
| 24.11 | LTS | All 6 toolchains | `{toolchain}/slurm/24.11/` |
| 23.11 | Stable | All 6 toolchains | `{toolchain}/slurm/23.11/` |

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
# Set toolchain and version
TOOLCHAIN=noble
SLURM_VERSION=25.11
CLOUDFRONT_URL=https://slurm-factory-spack-binary-cache.vantagecompute.ai

# Add mirrors for deps and slurm
spack mirror add slurm-factory-deps "${CLOUDFRONT_URL}/${TOOLCHAIN}/slurm/deps/"
spack mirror add slurm-factory-slurm "${CLOUDFRONT_URL}/${TOOLCHAIN}/slurm/${SLURM_VERSION}/"

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

### Use Multiple Mirrors for Different Toolchains

```bash
# Set CloudFront URL
CLOUDFRONT_URL=https://slurm-factory-spack-binary-cache.vantagecompute.ai

# Add mirrors for Ubuntu 24.04 (noble) - Slurm 25.11
spack mirror add noble-deps "${CLOUDFRONT_URL}/noble/slurm/deps/"
spack mirror add noble-slurm "${CLOUDFRONT_URL}/noble/slurm/25.11/"

# Add mirrors for Rocky Linux 9 - Slurm 24.11
spack mirror add rocky9-deps "${CLOUDFRONT_URL}/rockylinux9/slurm/deps/"
spack mirror add rocky9-slurm "${CLOUDFRONT_URL}/rockylinux9/slurm/24.11/"

# Add mirrors for Ubuntu 22.04 (jammy) - Slurm 23.11
spack mirror add jammy-deps "${CLOUDFRONT_URL}/jammy/slurm/deps/"
spack mirror add jammy-slurm "${CLOUDFRONT_URL}/jammy/slurm/23.11/"

# Import GPG signing keys from all mirrors
spack buildcache keys --install --trust

# Install with verified signatures
spack install slurm@25.11  # Uses noble mirrors if that's configured
spack install slurm@24.11  # Uses rocky9 mirrors if that's configured
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

Six workflows keep the buildcache current across all toolchains:

| Workflow | Purpose |
|----------|---------|
| `publish-slurm-buildcache-deps.yml` | Builds and publishes Slurm dependencies for a single toolchain |
| `publish-slurm-buildcache-version.yml` | Builds and publishes a specific Slurm version for a single toolchain |
| `publish-slurm-all-deps.yml` | Matrix workflow - builds deps across all 6 toolchains |
| `publish-slurm-all-versions.yml` | Matrix workflow - builds all Slurm versions across all 6 toolchains |
| `build-and-publish-slurm-tarball.yml` | Builds relocatable Slurm tarballs |
| `slurm-docker-image.yml` | Builds Docker images with Slurm pre-installed |

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
# Replace {toolchain} with: noble, jammy, resolute, rockylinux9, etc.
spack mirror add s3-direct \
  https://slurm-factory-spack-buildcache-4b670.s3.amazonaws.com/noble/slurm/25.11/
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
