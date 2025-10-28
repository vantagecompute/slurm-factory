# Optimization

Performance tuning for faster builds and efficient deployments.

## Build Optimization

**Cache Reuse:**
```bash
# Caches persist across builds
~/.slurm-factory/spack-buildcache/   # Binary packages
~/.slurm-factory/spack-sourcecache/  # Downloaded sources

# Performance impact:
# - First build: 45-90 minutes
# - Cached build: 5-15 minutes (>10x speedup)
```

**Docker Resources:**
```bash
# Allocate more resources for faster builds
docker run --cpus=8 --memory=16g ...

# Monitor resource usage
docker stats
```

**Parallel Builds:**
```bash
# Spack uses 4 parallel jobs by default
# Increase via SPACK_JOBS environment variable
export SPACK_JOBS=8
slurm-factory build --slurm-version 25.05
```

## Deployment Optimization

**Fast Extraction:**
```bash
# Extract to target
tar -xzf slurm-25.05-software.tar.gz -C /opt/

# Parallel deployment across nodes
parallel-ssh -h nodes "tar -xzf /shared/slurm-25.05-software.tar.gz -C /opt/"
```

**Library Caching:**
```bash
# Update library cache for faster loading
echo '/opt/slurm/view/lib' | sudo tee /etc/ld.so.conf.d/slurm.conf
sudo ldconfig
```

## Storage Optimization

```bash
# Check cache sizes
du -sh ~/.slurm-factory/*

# Clean old builds
rm ~/.slurm-factory/builds/slurm-24.*

# Compress packages
xz ~/.slurm-factory/builds/*.tar.gz  # Better compression

# Clean build containers (keep caches)
slurm-factory clean
```

## Network Optimization

**Download Mirrors:**
```bash
# Spack uses mirrors automatically
# Configure custom mirror via spack.yaml
```

**Local Mirror:**
```bash
# Create local source mirror
spack mirror create -d /shared/mirror --all
```

## Troubleshooting Performance

**Slow builds:**
- Check Docker resources: `docker stats`
- Verify cache mounts: `docker inspect <container>`
- Clear corrupted cache: `slurm-factory clean --full`

**Large packages:**
- Use `--minimal` for smaller builds
- Exclude GPU support if not needed
- Clean old versions from cache
