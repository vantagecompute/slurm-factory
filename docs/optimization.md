---
layout: page
title: Optimization Guide
description: Performance optimization guide for slurm-factory builds and deployments
permalink: /optimization/
---

# Optimization Guide

Comprehensive guide for optimizing build performance and package sizing with slurm-factory.

## Build Performance Optimization

### 1. Container Configuration

#### CPU Resources
```bash
# Check current LXD profile
lxc profile show default

# Optimize for faster builds
lxc profile edit default
```

**Recommended settings**:
```yaml
config:
  limits.cpu: "8"          # Use all available cores
  limits.memory: "16GB"    # Ensure adequate memory
  limits.memory.swap: "false"
resources:
  disk:
    pool: default
    type: disk
```

#### Storage Performance
```bash
# Use ZFS for better performance (if available)
lxc storage create fast zfs size=100GB

# Or btrfs as alternative
lxc storage create fast btrfs size=100GB

# Create optimized profile
lxc profile create fast-build
lxc profile edit fast-build
```

### 2. Spack Build Optimization

#### Parallel Compilation
Builds automatically use available CPU cores via:
- Spack's `build_jobs` configuration (auto-detected)
- Make's `-j$(nproc)` parallelization
- Ninja builds when available

#### Build Cache Utilization
```bash
# Pre-populate build cache with common dependencies
uv run slurm-factory build --slurm-version 25.05  # First build caches deps

# Subsequent builds reuse cached dependencies
uv run slurm-factory build --slurm-version 24.11  # Much faster
```

#### Dependency Management
```bash
# View dependency tree
spack spec slurm

# Minimize variants for faster builds
# CPU-only build (default) vs GPU build
uv run slurm-factory build --slurm-version 25.05          # ~45 minutes
uv run slurm-factory build --slurm-version 25.05 --gpu    # ~90 minutes
```

### 3. System-Level Optimization

#### Disk I/O
```bash
# Use tmpfs for build directory (if enough RAM)
sudo mount -t tmpfs -o size=32G tmpfs /tmp/slurm-build

# Or use fast SSD storage
export TMPDIR=/fast-ssd/tmp
```

#### Network
```bash
# Use local package mirrors for faster downloads
# Add to spack configuration
mkdir -p ~/.spack
cat > ~/.spack/mirrors.yaml << 'EOF'
mirrors:
  local: file:///opt/spack-mirror
EOF
```

## Package Size Optimization

### Build Variants Comparison

| Build Type | Dependencies | Size | Use Case |
|------------|-------------|------|----------|
| **CPU-only** | ~45 packages | ~2-5GB | Production clusters |
| **GPU-enabled** | ~180 packages | ~15-25GB | GPU clusters |
| **Minimal** | ~25 packages | ~1GB | Development/testing |

### 1. CPU-Only Builds (Recommended)

**Default configuration optimized for size**:
```yaml
# Automatically used with:
uv run slurm-factory build --slurm-version 25.05
```

**Dependencies included**:
- Core libraries: glibc, gcc runtime
- Network: PMIx, UCX (optimized)
- Essential tools: hwloc, numactl
- Authentication: munge, PAM

**Size breakdown**:
- Slurm binaries: ~200MB
- Core dependencies: ~1.5GB  
- Build tools overhead: ~500MB
- **Total: ~2-3GB**

### 2. Minimal Builds

For development or testing environments:
```bash
# Edit constants.py to reduce dependencies
# Modify SPACK_PROJECT_SETUP_SCRIPT template:

# Minimal package list
spack.yaml:
  packages:
    slurm:
      variants: ~cuda ~nvml ~x11 ~gtk
```

### 3. Optimized GPU Builds

When GPU support is required:
```bash
uv run slurm-factory build --slurm-version 25.05 --gpu
```

**Additional dependencies**:
- CUDA toolkit: ~8-12GB
- NVIDIA drivers: ~2-3GB
- GPU monitoring: NVML, nvidia-ml-py

**Optimization strategies**:
- Use CUDA containers instead of full GPU builds
- Deploy CPU build + CUDA runtime separately
- Use shared filesystems for CUDA installations

## Build Time Optimization

### Expected Build Times

| System Configuration | CPU Build | GPU Build |
|---------------------|-----------|-----------|
| 4 cores, 8GB RAM | ~60 minutes | ~120 minutes |
| 8 cores, 16GB RAM | ~35 minutes | ~75 minutes |
| 16 cores, 32GB RAM | ~20 minutes | ~45 minutes |

### Optimization Strategies

#### 1. Incremental Builds
```bash
# Build multiple versions efficiently
uv run slurm-factory build --slurm-version 24.11  # Caches dependencies
uv run slurm-factory build --slurm-version 25.05  # Reuses 90% of deps
```

#### 2. Parallel Dependency Builds
```bash
# Spack automatically parallelizes dependency builds
# Configure via ~/.spack/config.yaml:
config:
  build_jobs: 8              # Parallel package builds
  build_stage: /fast-disk    # Use fast storage
```

#### 3. Build Cache Management
```bash
# Monitor cache size
du -sh ~/.slurm-factory/spack-cache/

# Clean old builds if space is limited
rm -rf ~/.slurm-factory/builds/old-version/

# Spack garbage collection
spack gc -y
```

## Memory Optimization

### Container Memory Limits

#### Minimum Requirements
- **CPU builds**: 4GB RAM minimum, 8GB recommended
- **GPU builds**: 8GB RAM minimum, 16GB recommended
- **Parallel builds**: 2GB per build job

#### Memory-Constrained Systems
```bash
# Limit parallel jobs if memory is constrained
export SPACK_BUILD_JOBS=2

# Or edit build configuration
lxc profile set build-container limits.memory 4GB
```

### Swap Configuration
```bash
# Disable swap in containers for performance
lxc profile set build-container limits.memory.swap false

# Or configure host swap appropriately
sudo swapon --summary
```

## Network Optimization

### Download Acceleration
```bash
# Use package mirrors closest to your location
# Check slurm-factory's mirror configuration
grep -r "github\|releases" slurm_factory/

# Use corporate mirrors if available
export SPACK_MIRROR_URL=https://company-mirror.example.com
```

### Bandwidth Management
```bash
# Parallel downloads are automatic
# Limit if bandwidth is constrained:
export SPACK_CURL_TIMEOUT=30
export SPACK_CURL_RETRIES=3
```

## Storage Optimization

### Disk Space Management

#### Minimum Space Requirements
- **Build process**: 50GB free space
- **Final packages**: 5-30GB depending on variant
- **Spack cache**: 20-100GB (grows over time)

#### Space-Saving Strategies
```bash
# Build on separate filesystem
export SLURM_FACTORY_BUILD_DIR=/large-disk/builds

# Compress packages after build
gzip ~/.slurm-factory/builds/*/slurm-*-software.tar

# Clean intermediate files
rm -rf ~/.slurm-factory/builds/*/build-*
```

### File System Recommendations

| Filesystem | Build Performance | Storage Efficiency | Notes |
|------------|------------------|-------------------|-------|
| **ZFS** | Excellent | Excellent | Best overall choice |
| **Btrfs** | Good | Good | Good compression |
| **XFS** | Excellent | Fair | Best for large files |
| **Ext4** | Good | Fair | Most compatible |

## Deployment Optimization

### Module System Performance

#### Module Loading Optimization
```bash
# Pre-compile module files for faster loading
# Add to deployment script:
module load slurm/25.05
module unload slurm/25.05

# Cache module information
modulecmd bash avail 2>&1 | grep slurm
```

#### Path Optimization
```bash
# For frequently used systems, add to system PATH
echo 'export PATH=/opt/slurm/software/bin:$PATH' | sudo tee -a /etc/profile.d/slurm.sh

# Update library cache
echo '/opt/slurm/software/lib' | sudo tee -a /etc/ld.so.conf.d/slurm.conf
sudo ldconfig
```

### Package Deployment Optimization

#### Parallel Extraction
```bash
# Extract packages in parallel for faster deployment
tar -xzf slurm-25.05-software.tar.gz -C /opt/slurm/ &
tar -xzf slurm-25.05-module.tar.gz -C /opt/modules/ &
wait
```

#### Network Deployment
```bash
# For multiple nodes, use parallel deployment
parallel-ssh -h hostlist "tar -xzf /shared/packages/slurm-25.05-software.tar.gz -C /opt/slurm/"
```

## Troubleshooting Performance Issues

### Build Performance Issues

#### Build Hanging/Slow

1. **Check container resources**:
   ```bash
   lxc info build-container
   htop  # Check CPU/memory usage
   iotop # Check disk I/O
   ```

2. **Network connectivity**:
   ```bash
   # Test download speed
   wget -O /dev/null https://github.com/SchedMD/slurm/archive/refs/tags/slurm-25-05.tar.gz
   ```

3. **Spack debugging**:
   ```bash
   # Enable verbose output
   spack -d install slurm
   
   # Check build logs
   spack build-env slurm -- bash
   ```

#### Memory Issues

1. **Out of memory errors**:
   ```bash
   # Reduce parallel jobs
   export SPACK_BUILD_JOBS=1
   
   # Increase container memory
   lxc config set build-container limits.memory 32GB
   ```

2. **Swap thrashing**:
   ```bash
   # Disable swap in container
   lxc config set build-container limits.memory.swap false
   
   # Monitor memory usage
   watch -n 1 'free -h && echo "---" && lxc info build-container'
   ```

#### Disk Space Issues

1. **No space left**:
   ```bash
   # Check space usage
   df -h ~/.slurm-factory/
   lxc storage list
   
   # Clean old builds
   rm -rf ~/.slurm-factory/builds/old-*/
   
   # Clean spack cache
   spack clean --all
   ```

2. **I/O bottlenecks**:
   ```bash
   # Monitor I/O
   iostat -x 1
   
   # Use faster storage
   lxc storage create nvme dir source=/fast-nvme
   lxc profile device set default root pool nvme
   ```

## Advanced Optimization Techniques

### Container Optimization

#### Pre-built Base Images
```bash
# Create optimized base container
lxc launch ubuntu:22.04 slurm-base
lxc exec slurm-base -- apt update
lxc exec slurm-base -- apt install -y build-essential git python3-pip

# Snapshot for reuse
lxc snapshot slurm-base clean-base
lxc publish slurm-base/clean-base --alias slurm-factory-base

# Use optimized base
lxc launch slurm-factory-base build-container
```

#### Container Networking
```bash
# Use host networking for better performance
lxc config set build-container security.privileged true
lxc config device add build-container eth0 nic nictype=bridged parent=lxdbr0
```

### Build Parallelization

#### Multiple Concurrent Builds
```bash
# Build different versions in parallel (if resources allow)
uv run slurm-factory build --slurm-version 25.05 &
uv run slurm-factory build --slurm-version 24.11 &
wait
```

#### Resource Isolation
```bash
# Create separate profiles for concurrent builds
lxc profile create build-profile-1
lxc profile create build-profile-2

# Configure different resource limits
lxc profile set build-profile-1 limits.cpu 4
lxc profile set build-profile-2 limits.cpu 4
```

### Spack Optimization

#### Custom Spack Configuration
```bash
# Create optimized spack configuration
mkdir -p ~/.spack
cat > ~/.spack/config.yaml << 'EOF'
config:
  build_stage: /tmp/spack-build
  source_cache: ~/.spack/cache
  build_jobs: 8
  ccache: true
  install_tree:
    root: ~/.spack/opt/spack
    projections:
      all: ${ARCHITECTURE}/${COMPILERNAME}-${COMPILERVER}/${PACKAGE}-${VERSION}-${HASH}
EOF
```

#### Compiler Optimization
```bash
# Use newer compilers for better optimization
spack install gcc@11.3.0
spack compiler find
spack config edit compilers
```

### Monitoring and Profiling

#### Build Monitoring
```bash
# Monitor build progress
watch -n 5 'lxc exec build-container -- ps aux | grep -E "(make|ninja|gcc)"'

# Monitor resource usage
watch -n 1 'lxc info build-container | grep -A5 "Memory\|CPU"'
```

#### Performance Profiling
```bash
# Profile build performance
time uv run slurm-factory build --slurm-version 25.05

# Detailed timing
strace -T -e trace=file uv run slurm-factory build --slurm-version 25.05 2>&1 | grep -E 'open|write|read'
```

This optimization guide provides comprehensive strategies for improving both build and deployment performance of slurm-factory packages across different environments and constraints.

---

**Next Steps**: 
- Apply optimizations to your [deployment](/slurm-factory/deployment/)
- Learn about [troubleshooting](/slurm-factory/troubleshooting/) specific issues
- Explore [contributing](/slurm-factory/contributing/) for custom optimizations
