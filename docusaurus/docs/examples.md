# Examples

Practical examples for building and deploying Slurm packages with different versions and configurations.

## Supported Versions

**Slurm Versions:** 25.11, 24.11, 23.11

**GCC Compilers:** 14.2.0, 13.4.0 (default), 12.5.0, 11.5.0, 10.5.0, 9.5.0, 8.5.0, 7.5.0

See [Build Artifacts](build-artifacts.md) for pre-built S3 packages covering all version combinations.

## Basic Build Examples

```bash
# Standard build with default compiler (GCC 13.4.0)
slurm-factory build --slurm-version 25.11

# Build specific version with default compiler
slurm-factory build --slurm-version 24.11

# GPU support (~15-25GB)
slurm-factory build --slurm-version 25.11 --gpu

# Minimal (~1-2GB, no OpenMPI)
slurm-factory build --slurm-version 25.11 --minimal

# Verbose output
slurm-factory --verbose build --slurm-version 25.11

# Custom project name
slurm-factory --project-name prod build --slurm-version 25.11
```

## Compiler Version Examples

Build with different GCC compiler versions for cross-distribution compatibility:

```bash
# Latest compiler (Ubuntu 24.10+, Fedora 40+)
slurm-factory build --slurm-version 25.11 --compiler-version 14.2.0

# Default (Ubuntu 24.04, Debian 13+)
slurm-factory build --slurm-version 25.11 --compiler-version 13.4.0

# Ubuntu 22.04, Debian 12+
slurm-factory build --slurm-version 24.11 --compiler-version 11.5.0

# RHEL 8, Ubuntu 20.04, Debian 11+
slurm-factory build --slurm-version 23.11 --compiler-version 10.5.0

# Combine with GPU support
slurm-factory build --slurm-version 25.11 --compiler-version 10.5.0 --gpu
```

**Compiler Selection Guide:**

| Version | Compatible Distros | glibc | Use Case |
|---------|-------------------|-------|----------|
| 14.2.0 | Ubuntu 24.10+, Fedora 40+ | 2.40+ | Latest features |
| 13.4.0 | Ubuntu 24.04+, Debian 13+ | 2.39 | **Default** |
| 12.5.0 | Ubuntu 23.10+, Debian 12+ | 2.38 | Wide compatibility |
| 11.5.0 | Ubuntu 22.04+, Debian 12+ | 2.35 | LTS distributions |
| 10.5.0 | RHEL 8+, Ubuntu 20.04+ | 2.31 | Enterprise Linux |
| 9.5.0 | RHEL 8+, CentOS 8+ | 2.28 | RHEL 8 compatibility |
| 8.5.0 | RHEL 8+, CentOS 8+ | 2.28 | RHEL 8 minimal |
| 7.5.0 | RHEL 7+, CentOS 7+ | 2.17 | Legacy systems |

## Deployment Examples

```bash
# Standard deployment with default compiler
sudo tar -xzf ~/.slurm-factory/builds/slurm-25.11-gcc13.4.0-software.tar.gz -C /opt/
cd /opt && sudo ./data/slurm_assets/slurm_install.sh --full-init
module load slurm/25.11-gcc13.4.0

# Deploy RHEL 8 compatible build
sudo tar -xzf ~/.slurm-factory/builds/slurm-24.11-gcc10.5.0-software.tar.gz -C /opt/
cd /opt && sudo ./data/slurm_assets/slurm_install.sh --full-init
module load slurm/24.11-gcc10.5.0

# Deploy from S3
aws s3 cp s3://vantagecompute-slurm-builds/slurm-25.11-gcc13.4.0-software.tar.gz /tmp/
sudo tar -xzf /tmp/slurm-25.11-gcc13.4.0-software.tar.gz -C /opt/
cd /opt && sudo ./data/slurm_assets/slurm_install.sh --full-init
module load slurm/25.11-gcc13.4.0

# Custom path
export SLURM_INSTALL_PREFIX=/shared/apps/slurm
module load slurm/25.11-gcc13.4.0

# Multi-version deployment
sudo tar -xzf slurm-25.11-gcc13.4.0-software.tar.gz -C /opt/slurm-25.11/
sudo tar -xzf slurm-24.11-gcc11.5.0-software.tar.gz -C /opt/slurm-24.11/
cd /opt/slurm-25.11 && sudo ./data/slurm_assets/slurm_install.sh
cd /opt/slurm-24.11 && sudo ./data/slurm_assets/slurm_install.sh
module load slurm/25.11-gcc13.4.0  # or slurm/24.11-gcc11.5.0
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
          slurm-factory build --slurm-version 25.11 --compiler-version 13.4.0
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
    - slurm-factory build --slurm-version 25.11 --compiler-version 13.4.0
  artifacts:
    paths:
      - ~/.slurm-factory/builds/
```

## Python API

```python
from slurm_factory.builder import build
from slurm_factory.config import Settings

# Basic build
build(slurm_version="25.11", gpu=False, minimal=False)

# GPU build
build(slurm_version="25.11", gpu=True, minimal=False)

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
slurm-factory build --slurm-version 25.11
```
