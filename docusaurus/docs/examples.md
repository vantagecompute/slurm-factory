# Examples

Practical examples for building and deploying Slurm packages.

## Build Examples

```bash
# Standard build (default GCC 13.4.0)
slurm-factory build --slurm-version 25.05

# GPU support (~15-25GB)
slurm-factory build --slurm-version 25.05 --gpu

# Minimal (~1-2GB, no OpenMPI)
slurm-factory build --slurm-version 25.05 --minimal

# Verbose output
slurm-factory --verbose build --slurm-version 25.05

# Custom project name
slurm-factory --project-name prod build --slurm-version 25.05
```

## Compiler Version Examples

Build with different GCC compiler versions for cross-distribution compatibility:

```bash
# Latest compilers
slurm-factory build --compiler-version 15.2.0  # Latest GCC 15, glibc 2.39
slurm-factory build --compiler-version 14.3.0  # Latest GCC 14, glibc 2.39

# Default (Ubuntu 24.04)
slurm-factory build --compiler-version 13.4.0  # Default, glibc 2.39

# Older distributions
slurm-factory build --compiler-version 11.5.0  # Ubuntu 22.04, glibc 2.35
slurm-factory build --compiler-version 10.5.0  # RHEL 8/Ubuntu 20.04, glibc 2.31
slurm-factory build --compiler-version 7.5.0   # RHEL 7, glibc 2.17

# Combine with GPU support
slurm-factory build --compiler-version 10.5.0 --gpu  # RHEL 8 with GPU
```

**Compiler Version Selection Guide:**
- **15.2.0/14.3.0**: Latest features, Ubuntu 24.04+
- **13.4.0**: Default, good balance of features and compatibility
- **11.5.0/10.5.0**: Wide compatibility, Ubuntu 22.04/20.04, RHEL 8
- **7.5.0**: Maximum compatibility, RHEL 7 and older systems

## Deployment Examples

```bash
# Standard
sudo tar -xzf ~/.slurm-factory/builds/slurm-25.05-software.tar.gz -C /opt/
cd /opt && sudo ./data/slurm_assets/slurm_install.sh --full-init
module load slurm/25.05

# Custom path
export SLURM_INSTALL_PREFIX=/shared/apps/slurm
module load slurm/25.05

# Multi-version
sudo tar -xzf slurm-25.05-software.tar.gz -C /opt/slurm-25.05/
sudo tar -xzf slurm-24.11-software.tar.gz -C /opt/slurm-24.11/
cd /opt/slurm-25.05 && sudo ./data/slurm_assets/slurm_install.sh
cd /opt/slurm-24.11 && sudo ./data/slurm_assets/slurm_install.sh
module load slurm/25.05  # or slurm/24.11
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
          slurm-factory build --slurm-version 25.05
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
    - slurm-factory build --slurm-version 25.05
  artifacts:
    paths:
      - ~/.slurm-factory/builds/
```

## Python API

```python
from slurm_factory.builder import build
from slurm_factory.config import Settings

# Basic build
build(slurm_version="25.05", gpu=False, minimal=False)

# GPU build
build(slurm_version="25.05", gpu=True, minimal=False)

# With custom settings
settings = Settings(project_name="custom")
build(slurm_version="25.05", settings=settings)
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
slurm-factory build --slurm-version 25.05
```
