# Installing Slurm from Buildcache

This guide shows how to install pre-built, GPG-signed Slurm binaries directly from the public buildcache using **only Spack**. No `slurm-factory` tool installation is required.

## Overview

The slurm-factory buildcache provides pre-compiled, GPG-signed Slurm packages that install in **5-15 minutes** instead of 45-90 minutes from source. All packages are signed with GPG key `DFB92630BCA5AB71` for security verification.

The buildcache uses a **three-tier mirror architecture**:
- **`compilers/`** - GCC compiler toolchains
- **`deps/`** - Slurm runtime dependencies (OpenMPI, PMIx, Munge, etc.)
- **`slurm/`** - Slurm packages

**Use this method when:**
- ✅ You want the fastest installation (5-15 minutes)
- ✅ You don't need custom build configurations
- ✅ You want GPG-verified, trusted binaries
- ✅ You want to avoid Docker/compilation complexity

**Use slurm-factory tool instead when:**
- ❌ You need custom build options or patches
- ❌ You're building for unsupported OS/architecture
- ❌ You want to create your own buildcache

## Prerequisites

Only Spack is required - no Docker, no Python packages, no build tools:

- **OS**: Ubuntu 20.04+ or RHEL 8+ compatible Linux
- **Spack**: v1.0.0 (installed below)
- **Internet**: Access to download ~2-5GB of binaries

## Quick Start

### 1. Install Spack

```bash
# Clone Spack v1.0.0
git clone --depth 1 --branch v1.0.0 https://github.com/spack/spack.git ~/spack

# Activate Spack in your shell
source ~/spack/share/spack/setup-env.sh

# Add to your shell profile for persistence
echo 'source ~/spack/share/spack/setup-env.sh' >> ~/.bashrc
```

### 2. Configure Buildcache Mirrors

The buildcache uses three separate mirrors for optimal caching:

```bash
# Set versions
SLURM_VERSION=25.11
TOOLCHAIN=noble
CLOUDFRONT_URL=https://slurm-factory-spack-binary-cache.vantagecompute.ai

# Add three-tier mirror structure
spack mirror add slurm-factory-build-toolchain "${CLOUDFRONT_URL}/compilers/${TOOLCHAIN}"
spack mirror add slurm-factory-slurm-deps "${CLOUDFRONT_URL}/deps/${TOOLCHAIN}"
spack mirror add slurm-factory-slurm "${CLOUDFRONT_URL}/slurm/${SLURM_VERSION}/${TOOLCHAIN}"
```

### 3. Import GPG Signing Keys

```bash
# Import and trust the GPG key (enables automatic signature verification)
spack buildcache keys --install --trust

# Verify the key was imported
gpg --list-keys DFB92630BCA5AB71
```

### 4. Install Slurm

```bash
# Install Slurm with automatic signature verification (5-15 minutes)
spack install slurm@${SLURM_VERSION} target=x86_64_v3

# Load Slurm into your environment
spack load slurm@${SLURM_VERSION}

# Verify installation
sinfo --version
# Output: slurm 25.11.4
```

## Supported Versions

All 27 combinations of Slurm × GCC are available in the buildcache:

### Slurm Versions

| Version | Status | Description |
|---------|--------|-------------|
| **25.11** | Latest | Most recent features and improvements |
| **24.11** | LTS | Long-term support, production recommended |
| **23.11** | Stable | Previous stable release |

### Toolchains

| Toolchain | OS/Distribution | System GCC | Glibc |
|-----------|-----------------|------------|-------|
| **noble** | Ubuntu 24.04 (Noble) | 13.2.0 | 2.39 |
| **jammy** | Ubuntu 22.04 (Jammy) | 11.4.0 | 2.35 |
| **focal** | Ubuntu 20.04 (Focal) | 9.4.0 | 2.31 |
| **rockylinux9** | Rocky Linux 9 / RHEL 9 | 11.4.0 | 2.34 |
| **rockylinux8** | Rocky Linux 8 / RHEL 8 | 8.5.0 | 2.28 |
| **centos7** | CentOS 7 / RHEL 7 | 4.8.5 | 2.17 |

## Installation Examples

### Example 1: Latest Slurm (Recommended)

```bash
# Set versions
SLURM_VERSION=25.11
TOOLCHAIN=noble
CLOUDFRONT_URL=https://slurm-factory-spack-binary-cache.vantagecompute.ai

# Add three-tier mirrors
spack mirror add slurm-factory-build-toolchain "${CLOUDFRONT_URL}/compilers/${TOOLCHAIN}"
spack mirror add slurm-factory-slurm-deps "${CLOUDFRONT_URL}/deps/${TOOLCHAIN}"
spack mirror add slurm-factory-slurm "${CLOUDFRONT_URL}/slurm/${SLURM_VERSION}/${TOOLCHAIN}"

# Import GPG keys
spack buildcache keys --install --trust

# Install latest Slurm with system compiler
spack install slurm@${SLURM_VERSION} target=x86_64_v3

# Load and verify
spack load slurm@${SLURM_VERSION}
sinfo --version
```

### Example 2: LTS Version for Production

```bash
# Set versions for LTS
SLURM_VERSION=24.11
TOOLCHAIN=jammy
CLOUDFRONT_URL=https://slurm-factory-spack-binary-cache.vantagecompute.ai

# Add mirrors
spack mirror add slurm-factory-build-toolchain "${CLOUDFRONT_URL}/compilers/${TOOLCHAIN}"
spack mirror add slurm-factory-slurm-deps "${CLOUDFRONT_URL}/deps/${TOOLCHAIN}"
spack mirror add slurm-factory-slurm "${CLOUDFRONT_URL}/slurm/${SLURM_VERSION}/${COMPILER_VERSION}"

# Import GPG keys
spack buildcache keys --install --trust

# Install LTS Slurm
spack install slurm@${SLURM_VERSION}%gcc@${COMPILER_VERSION} target=x86_64_v3

# Load and verify
spack load slurm@${SLURM_VERSION}
sinfo --version
```

### Example 3: RHEL 8 / Ubuntu 20.04 Compatible

```bash
# Use GCC 10.5.0 for RHEL 8 / Ubuntu 20.04 compatibility
SLURM_VERSION=25.11
COMPILER_VERSION=10.5.0
CLOUDFRONT_URL=https://slurm-factory-spack-binary-cache.vantagecompute.ai

# Add mirrors
spack mirror add slurm-factory-build-toolchain "${CLOUDFRONT_URL}/compilers/${COMPILER_VERSION}"
spack mirror add slurm-factory-slurm-deps "${CLOUDFRONT_URL}/deps/${COMPILER_VERSION}"
spack mirror add slurm-factory-slurm "${CLOUDFRONT_URL}/slurm/${SLURM_VERSION}/${COMPILER_VERSION}"

# Import GPG keys
spack buildcache keys --install --trust

# Install with compatible compiler
spack install slurm@${SLURM_VERSION}%gcc@${COMPILER_VERSION} target=x86_64_v3

# Load and verify
spack load slurm@${SLURM_VERSION}
sinfo --version
```

### Example 4: RHEL 7 Legacy Systems

```bash
# Use GCC 7.5.0 for RHEL 7 / older systems
SLURM_VERSION=23.11
COMPILER_VERSION=7.5.0
CLOUDFRONT_URL=https://slurm-factory-spack-binary-cache.vantagecompute.ai

# Add mirrors
spack mirror add slurm-factory-build-toolchain "${CLOUDFRONT_URL}/compilers/${COMPILER_VERSION}"
spack mirror add slurm-factory-slurm-deps "${CLOUDFRONT_URL}/deps/${COMPILER_VERSION}"
spack mirror add slurm-factory-slurm "${CLOUDFRONT_URL}/slurm/${SLURM_VERSION}/${COMPILER_VERSION}"

# Import GPG keys
spack buildcache keys --install --trust

# Install with legacy compiler
spack install slurm@${SLURM_VERSION}%gcc@${COMPILER_VERSION} target=x86_64_v3

# Load and verify
spack load slurm@${SLURM_VERSION}
sinfo --version
```

## Buildcache Structure

The buildcache uses a three-tier mirror architecture for optimal caching and dependency resolution:

```text
https://slurm-factory-spack-binary-cache.vantagecompute.ai/
├── compilers/
│   ├── 15.2.0/                  # GCC 15.2.0 build toolchain
│   ├── 14.2.0/                  # GCC 14.2.0 build toolchain
│   ├── 13.4.0/                  # GCC 13.4.0 build toolchain (default)
│   └── ...                      # All 9 GCC versions
├── deps/
│   ├── 15.2.0/                  # Slurm dependencies built with GCC 15.2.0
│   ├── 14.2.0/                  # Slurm dependencies built with GCC 14.2.0
│   ├── 13.4.0/                  # Slurm dependencies built with GCC 13.4.0
│   └── ...                      # For all GCC versions
├── slurm/
│   ├── 25.11/                   # Slurm 25.11 (latest)
│   │   ├── 15.2.0/              # Built with GCC 15.2.0
│   │   ├── 14.2.0/              # Built with GCC 14.2.0
│   │   ├── 13.4.0/              # Built with GCC 13.4.0
│   │   └── ...                  # All 9 GCC versions
│   ├── 24.11/                   # Slurm 24.11 (LTS)
│   └── 23.11/                   # Slurm 23.11 (stable)
└── builds/
    ├── 25.11/
    │   ├── 15.2.0/
    │   │   ├── slurm-25.11-gcc15.2.0-software.tar.gz      # Complete tarball
    │   │   └── slurm-25.11-gcc15.2.0-software.tar.gz.asc  # GPG signature
    │   └── ...
    ├── 24.11/
    └── 23.11/
```

### Mirror Architecture Benefits

The three-tier structure provides:

- ✅ **Faster builds** - Compiler toolchain cached across all Slurm versions
- ✅ **Better caching** - Dependencies shared across Slurm versions
- ✅ **Reduced storage** - No duplication of common packages
- ✅ **Parallel downloads** - Spack fetches from multiple mirrors simultaneously

## Alternative: Download Pre-built Tarball

Instead of using Spack buildcache, you can download a complete Slurm installation as a tarball. This is ideal for air-gapped environments or simple deployments.

### 1. Download Tarball and Signature

```bash
# Set versions
SLURM_VERSION=25.11
COMPILER_VERSION=15.2.0
CLOUDFRONT_URL=https://slurm-factory-spack-binary-cache.vantagecompute.ai

# Download tarball
wget "${CLOUDFRONT_URL}/builds/${SLURM_VERSION}/${COMPILER_VERSION}/slurm-${SLURM_VERSION}-gcc${COMPILER_VERSION}-software.tar.gz"

# Download GPG signature
wget "${CLOUDFRONT_URL}/builds/${SLURM_VERSION}/${COMPILER_VERSION}/slurm-${SLURM_VERSION}-gcc${COMPILER_VERSION}-software.tar.gz.asc"
```

### 2. Verify GPG Signature

```bash
# Import the public GPG key
gpg --keyserver keyserver.ubuntu.com --recv-keys DFB92630BCA5AB71

# Verify the tarball signature
gpg --verify slurm-${SLURM_VERSION}-gcc${COMPILER_VERSION}-software.tar.gz.asc \
             slurm-${SLURM_VERSION}-gcc${COMPILER_VERSION}-software.tar.gz
```

**Expected output:**

```text
gpg: Signature made [DATE]
gpg:                using RSA key DFB92630BCA5AB71
gpg: Good signature from "Vantage Compute Corporation (Slurm Factory Spack Cache Signing Key) <info@vantagecompute.ai>"
```

If you see `BAD signature` or the signature doesn't match, **do not use the tarball** - it may have been tampered with.

### 3. Trust the GPG Key (Optional)

To avoid "untrusted signature" warnings in the future:

```bash
# Start GPG key editor
gpg --edit-key DFB92630BCA5AB71

# In the GPG prompt, type:
trust
# Choose: 5 (I trust ultimately)
quit
```

### 4. Extract and Install

```bash
# Extract to /opt (or your preferred location)
sudo tar -xzf slurm-${SLURM_VERSION}-gcc${COMPILER_VERSION}-software.tar.gz -C /opt/

# Run the installation script
cd /opt
sudo ./data/slurm_assets/slurm_install.sh --full-init

# Verify installation
module load slurm/${SLURM_VERSION}
sinfo --version
```

### Tarball Contents

Each tarball contains:

```text
slurm-25.11-gcc15.2.0-software.tar.gz
├── view/                      # Slurm binaries & libraries
├── modules/slurm/25.11.lua    # Lmod module (relocatable)
└── data/slurm_assets/         # Config templates & install script
    ├── slurm_install.sh       # Installation script
    ├── defaults/              # Default configuration files
    ├── systemd/               # Systemd service units
    └── ...
```

## GPG Signature Verification

All packages are signed with GPG for security:

**Key Information:**
- **Key ID**: `DFB92630BCA5AB71`
- **Owner**: Vantage Compute Corporation (Slurm Factory Spack Cache Signing Key)
- **Email**: info@vantagecompute.ai

### Manual Verification

```bash
# Import the GPG key
spack buildcache keys --install --trust

# List imported keys
gpg --list-keys DFB92630BCA5AB71

# View key details
spack gpg list

# Packages are automatically verified during installation
spack install slurm@25.11%gcc@13.4.0
# ✓ All packages verified with GPG signatures
```

### Security Benefits

- **Authenticity**: Verifies packages come from Vantage Compute
- **Integrity**: Ensures no tampering or corruption
- **Supply Chain Security**: Trusted build provenance
- **Automatic**: Verification happens transparently during install

## Advanced Usage

### Multiple Mirrors

You can configure multiple buildcache mirrors for different versions:

```bash
# Set CloudFront URL
CLOUDFRONT_URL=https://slurm-factory-spack-binary-cache.vantagecompute.ai

# Add mirrors for Slurm 25.11 with GCC 15.2.0
spack mirror add slurm-25-gcc15-toolchain "${CLOUDFRONT_URL}/compilers/15.2.0"
spack mirror add slurm-25-gcc15-deps "${CLOUDFRONT_URL}/deps/15.2.0"
spack mirror add slurm-25-gcc15 "${CLOUDFRONT_URL}/slurm/25.11/15.2.0"

# Add mirrors for Slurm 24.11 with GCC 13.4.0
spack mirror add slurm-24-gcc13-toolchain "${CLOUDFRONT_URL}/compilers/13.4.0"
spack mirror add slurm-24-gcc13-deps "${CLOUDFRONT_URL}/deps/13.4.0"
spack mirror add slurm-24-gcc13 "${CLOUDFRONT_URL}/slurm/24.11/13.4.0"

# List configured mirrors
spack mirror list

# Install from specific versions
spack install slurm@25.11%gcc@15.2.0  # Uses slurm-25-gcc15 mirrors
spack install slurm@24.11%gcc@13.4.0  # Uses slurm-24-gcc13 mirrors
```

### Specific Target Architecture

```bash
# Install for specific CPU microarchitecture
spack install slurm@25.11%gcc@13.4.0 target=x86_64_v3  # Recommended
spack install slurm@25.11%gcc@13.4.0 target=x86_64_v4  # Latest CPUs
spack install slurm@25.11%gcc@13.4.0 target=x86_64     # Maximum compatibility
```

### Verify Before Installing

```bash
# List available packages in buildcache
spack buildcache list

# Search for specific package
spack buildcache list slurm

# Get package info
spack info slurm
```

## Deployment

After installing from buildcache, deploy Slurm to your system. See the [Deployment Guide](deployment.md) for complete instructions.

### Quick Deployment Overview

```bash
# 1. Install from buildcache (as shown above)
spack install slurm@25.11%gcc@13.4.0 target=x86_64_v3

# 2. Find installation location
spack location -i slurm@25.11

# 3. Copy to system location (optional)
sudo cp -r $(spack location -i slurm@25.11) /opt/slurm

# 4. Configure and start services
# See deployment guide for detailed configuration steps
```

## Troubleshooting

### Mirror Connection Issues

```bash
# Test mirror connectivity
curl -I https://slurm-factory-spack-binary-cache.vantagecompute.ai/

# Remove and re-add mirror
spack mirror remove slurm-factory
spack mirror add slurm-factory \
  https://slurm-factory-spack-binary-cache.vantagecompute.ai/slurm/25.11/13.4.0/
```

### GPG Key Issues

```bash
# Re-import GPG keys
spack buildcache keys --install --trust

# List imported keys
spack gpg list

# If still failing, manually download and import
curl https://slurm-factory-spack-binary-cache.vantagecompute.ai/build_cache/_pgp/DFB92630BCA5AB71.pub | \
  spack gpg trust
```

### Package Not Found

```bash
# Update buildcache index
spack buildcache update-index slurm-factory

# List what's available
spack buildcache list --allarch

# Check you're using the right version combination
spack mirror list
```

### Slow Download

```bash
# The buildcache uses CloudFront CDN, but downloads can still be slow for large packages
# Monitor progress with verbose output
spack -d install slurm@25.11%gcc@13.4.0

# Or install specific dependencies first
spack install openssl@3:
spack install munge
spack install slurm@25.11%gcc@13.4.0
```

## Comparison: Buildcache vs Building

| Method | Time | Disk | Requirements | Customization |
|--------|------|------|--------------|---------------|
| **Buildcache** | 5-15 min | ~5GB | Spack only | None |
| **slurm-factory** | 45-90 min | ~50GB | Docker + Python | Full control |

## Next Steps

- **Deploy Slurm**: See [Deployment Guide](deployment.md)
- **Build Custom**: See [Installing slurm-factory Tool](installation.md)
- **Documentation**: Visit [slurm-factory docs](https://vantagecompute.github.io/slurm-factory)
- **Support**: Contact info@vantagecompute.ai

## Related Documentation

- [Buildcache Architecture](slurm-factory-spack-build-cache.md) - Technical details
- [Installation Guide](installation.md) - Installing the slurm-factory build tool
- [Deployment Guide](deployment.md) - Configuring and running Slurm
- [Examples](examples.md) - Common usage patterns
