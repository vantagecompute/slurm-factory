# Examples

Practical examples for building and deploying Slurm packages with different versions and configurations.

## Supported Versions

**Slurm Versions:** 25.11, 24.11, 23.11

**Toolchains:** resolute, noble (default), jammy, rockylinux10, rockylinux9, rockylinux8

See [Build Artifacts](build-artifacts.md) for pre-built packages covering all version combinations.

## Basic Build Examples

```bash
# Standard build with default toolchain (noble)
slurm-factory build-slurm --slurm-version 25.11

# Build specific version with default toolchain
slurm-factory build-slurm --slurm-version 24.11

# GPU support (~15-25GB)
slurm-factory build-slurm --slurm-version 25.11 --gpu

# Verbose output
slurm-factory --verbose build-slurm --slurm-version 25.11

# Custom project name
slurm-factory --project-name prod build-slurm --slurm-version 25.11
```

## Toolchain Examples

Build for different operating systems:

```bash
# Ubuntu 25.04 (latest)
slurm-factory build-slurm --slurm-version 25.11 --toolchain resolute

# Ubuntu 24.04 (default, recommended)
slurm-factory build-slurm --slurm-version 25.11 --toolchain noble

# Ubuntu 22.04 LTS
slurm-factory build-slurm --slurm-version 24.11 --toolchain jammy

# Rocky Linux 10 / RHEL 10
slurm-factory build-slurm --slurm-version 25.11 --toolchain rockylinux10

# Rocky Linux 9 / RHEL 9
slurm-factory build-slurm --slurm-version 23.11 --toolchain rockylinux9

# Rocky Linux 8 / RHEL 8
slurm-factory build-slurm --slurm-version 23.11 --toolchain rockylinux8

# Combine with GPU support
slurm-factory build-slurm --slurm-version 25.11 --toolchain rockylinux9 --gpu
```

**Toolchain Selection Guide:**

| Toolchain | Target OS | GCC Version | glibc | Use Case |
|-----------|-----------|-------------|-------|----------|
| resolute | Ubuntu 25.04 | 15.x | 2.41+ | Latest features |
| noble | Ubuntu 24.04 | 13.x | 2.39 | **Default** |
| jammy | Ubuntu 22.04 | 11.x | 2.35 | LTS distributions |
| rockylinux10 | Rocky 10 / RHEL 10 | 14.x | 2.39+ | Latest Enterprise Linux |
| rockylinux9 | Rocky 9 / RHEL 9 | 11.x | 2.34 | Enterprise Linux |
| rockylinux8 | Rocky 8 / RHEL 8 | 8.x | 2.28 | Legacy Enterprise |

## Deployment Examples

```bash
# Standard deployment for Ubuntu 24.04
sudo tar -xzf ~/.slurm-factory/builds/slurm-25.11-noble-software.tar.gz -C /opt/
cd /opt && sudo ./data/slurm_assets/slurm_install.sh --full-init
module load slurm/25.11-noble

# Deploy Rocky Linux 9 compatible build
sudo tar -xzf ~/.slurm-factory/builds/slurm-24.11-rockylinux9-software.tar.gz -C /opt/
cd /opt && sudo ./data/slurm_assets/slurm_install.sh --full-init
module load slurm/24.11-rockylinux9

# Download from CDN
wget https://vantage-public-assets.s3.amazonaws.com/slurm-factory/25.11/noble/slurm-25.11-noble-software.tar.gz
sudo tar -xzf slurm-25.11-noble-software.tar.gz -C /opt/
cd /opt && sudo ./data/slurm_assets/slurm_install.sh --full-init
module load slurm/25.11-noble

# Custom path
export SLURM_INSTALL_PREFIX=/shared/apps/slurm
module load slurm/25.11-noble

# Multi-version deployment
sudo tar -xzf slurm-25.11-noble-software.tar.gz -C /opt/slurm-25.11/
sudo tar -xzf slurm-24.11-jammy-software.tar.gz -C /opt/slurm-24.11/
cd /opt/slurm-25.11 && sudo ./data/slurm_assets/slurm_install.sh
cd /opt/slurm-24.11 && sudo ./data/slurm_assets/slurm_install.sh
module load slurm/25.11-noble  # or slurm/24.11-jammy
```

## CI/CD Integration

**GitHub Actions:**

```yaml
name: Build Slurm
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build
        run: |
          pipx install slurm-factory
          slurm-factory build-slurm --slurm-version 25.11 --toolchain noble
      - uses: actions/upload-artifact@v4
        with:
          name: slurm-package
          path: ~/.slurm-factory/builds/
```

**GitLab CI:**

```yaml
build:
  image: ubuntu:24.04
  script:
    - apt-get update && apt-get install -y pipx docker.io
    - pipx install slurm-factory
    - slurm-factory build-slurm --slurm-version 25.11 --toolchain noble
  artifacts:
    paths:
      - ~/.slurm-factory/builds/
```

## Python API

```python
from slurm_factory.builder import build
from slurm_factory.config import Settings

# Basic build
build(slurm_version="25.11", gpu=False)

# GPU build
build(slurm_version="25.11", gpu=True)

# With custom settings
settings = Settings(project_name="custom")
build(slurm_version="25.11", settings=settings)
```

## Maintenance

```bash
# Clean build containers (keep caches)
slurm-factory clean

# Full cleanup (slower next build)
slurm-factory clean --full

# Check cache size
du -sh ~/.slurm-factory/

# Rebuild from scratch
slurm-factory clean --full
slurm-factory build-slurm --slurm-version 25.11
```
