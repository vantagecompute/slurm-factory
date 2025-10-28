# Installing Slurm from Buildcache

This guide shows how to install pre-built, GPG-signed Slurm binaries directly from the public buildcache using **only Spack**. No `slurm-factory` tool installation is required.

## Overview

The slurm-factory buildcache provides pre-compiled, GPG-signed Slurm packages that install in **5-15 minutes** instead of 45-90 minutes from source. All packages are signed with GPG key `DFB92630BCA5AB71` for security verification.

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

### 2. Configure Buildcache Mirror

```bash
# Add the buildcache mirror for Slurm 25.11 with GCC 13.4.0
spack mirror add slurm-factory \
  https://slurm-factory-spack-binary-cache.vantagecompute.ai/slurm/25.11/13.4.0
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
spack install slurm@25.11%gcc@13.4.0 target=x86_64_v3

# Load Slurm into your environment
spack load slurm@25.11

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

### GCC Versions

| GCC Version | Glibc | Compatible OS |
|-------------|-------|---------------|
| **15.2.0** | 2.40 | Ubuntu 24.04+ |
| **14.2.0** | 2.39 | Ubuntu 24.04+ |
| **13.4.0** | 2.39 | Ubuntu 24.04+ (default) |
| **12.5.0** | 2.35 | Ubuntu 22.04+ |
| **11.5.0** | 2.31 | Ubuntu 20.04+ |
| **10.5.0** | 2.31 | Ubuntu 20.04+, RHEL 8+ |
| **9.5.0** | 2.31 | Ubuntu 20.04+, RHEL 8+ |
| **8.5.0** | 2.28 | Ubuntu 18.04+, RHEL 7+ |
| **7.5.0** | 2.28 | Ubuntu 18.04+, RHEL 7+ |

## Installation Examples

### Example 1: Latest Slurm (Recommended)

```bash
# Add mirror
spack mirror add slurm-factory \
  https://slurm-factory-spack-binary-cache.vantagecompute.ai/slurm/25.11/13.4.0

# Import GPG keys
spack buildcache keys --install --trust

# Install latest Slurm with default compiler
spack install slurm@25.11%gcc@13.4.0 target=x86_64_v3

# Load and verify
spack load slurm@25.11
sinfo --version
```

### Example 2: LTS Version for Production

```bash
# Add mirror for LTS version
spack mirror add slurm-factory \
  https://slurm-factory-spack-binary-cache.vantagecompute.ai/slurm/24.11/13.4.0

# Import GPG keys
spack buildcache keys --install --trust

# Install LTS Slurm
spack install slurm@24.11%gcc@13.4.0 target=x86_64_v3

# Load and verify
spack load slurm@24.11
sinfo --version
```

### Example 3: RHEL 8 / Ubuntu 20.04 Compatible

```bash
# Use GCC 10.5.0 for RHEL 8 / Ubuntu 20.04 compatibility
spack mirror add slurm-factory \
  https://slurm-factory-spack-binary-cache.vantagecompute.ai/slurm/25.11/10.5.0

# Import GPG keys
spack buildcache keys --install --trust

# Install with compatible compiler
spack install slurm@25.11%gcc@10.5.0 target=x86_64_v3

# Load and verify
spack load slurm@25.11
sinfo --version
```

### Example 4: RHEL 7 Legacy Systems

```bash
# Use GCC 7.5.0 for RHEL 7 / older systems
spack mirror add slurm-factory \
  https://slurm-factory-spack-binary-cache.vantagecompute.ai/slurm/23.11/7.5.0

# Import GPG keys
spack buildcache keys --install --trust

# Install with legacy compiler
spack install slurm@23.11%gcc@7.5.0 target=x86_64_v3

# Load and verify
spack load slurm@23.11
sinfo --version
```

## Buildcache Structure

The buildcache is organized by Slurm version and compiler:

```
https://slurm-factory-spack-binary-cache.vantagecompute.ai/
├── compilers/
│   ├── 15.2.0/buildcache/     # GCC 15.2.0 compiler binaries
│   ├── 14.2.0/buildcache/     # GCC 14.2.0 compiler binaries
│   ├── 13.4.0/buildcache/     # GCC 13.4.0 compiler binaries (default)
│   ├── 12.5.0/buildcache/     # GCC 12.5.0 compiler binaries
│   ├── 11.5.0/buildcache/     # GCC 11.5.0 compiler binaries
│   ├── 10.5.0/buildcache/     # GCC 10.5.0 compiler binaries
│   ├── 9.5.0/buildcache/      # GCC 9.5.0 compiler binaries
│   ├── 8.5.0/buildcache/      # GCC 8.5.0 compiler binaries
│   └── 7.5.0/buildcache/      # GCC 7.5.0 compiler binaries
└── slurm/
    ├── 25.11/                 # Slurm 25.11 (latest)
    │   ├── 15.2.0/buildcache/ # Built with GCC 15.2.0
    │   ├── 14.2.0/buildcache/ # Built with GCC 14.2.0
    │   ├── 13.4.0/buildcache/ # Built with GCC 13.4.0 (default)
    │   ├── 12.5.0/buildcache/ # Built with GCC 12.5.0
    │   ├── 11.5.0/buildcache/ # Built with GCC 11.5.0
    │   ├── 10.5.0/buildcache/ # Built with GCC 10.5.0
    │   ├── 9.5.0/buildcache/  # Built with GCC 9.5.0
    │   ├── 8.5.0/buildcache/  # Built with GCC 8.5.0
    │   └── 7.5.0/buildcache/  # Built with GCC 7.5.0
    ├── 24.11/                 # Slurm 24.11 (LTS)
    │   └── [same structure]
    └── 23.11/                 # Slurm 23.11 (stable)
        └── [same structure]
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
# Add multiple mirrors
spack mirror add slurm-25.11-gcc13 \
  https://slurm-factory-spack-binary-cache.vantagecompute.ai/slurm/25.11/13.4.0

spack mirror add slurm-24.11-gcc10 \
  https://slurm-factory-spack-binary-cache.vantagecompute.ai/slurm/24.11/10.5.0

# List configured mirrors
spack mirror list

# Install from specific versions
spack install slurm@25.11%gcc@13.4.0  # Uses slurm-25.11-gcc13
spack install slurm@24.11%gcc@10.5.0  # Uses slurm-24.11-gcc10
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
  https://slurm-factory-spack-binary-cache.vantagecompute.ai/slurm/25.11/13.4.0
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
