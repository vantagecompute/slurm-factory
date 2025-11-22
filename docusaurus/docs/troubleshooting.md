# Troubleshooting

Common issues and solutions.

## Build Issues

**Docker not running:**
```bash
sudo systemctl start docker
sudo usermod -aG docker $USER
newgrp docker
```

**Build fails with cache errors:**
```bash
slurm-factory clean --full
slurm-factory build-slurm --slurm-version 25.11
```

**Out of disk space:**
```bash
# Check usage
df -h ~/.slurm-factory
du -sh ~/.slurm-factory/*

# Clean up
slurm-factory clean --full
docker system prune -a
```

**Permission denied:**
```bash
# Fix cache permissions
sudo chown -R $USER:$USER ~/.slurm-factory
chmod -R u+rw ~/.slurm-factory
```

## Deployment Issues

**Module not found:**
```bash
# Check module path
module avail
echo $MODULEPATH

# Verify installation
ls /usr/share/lmod/lmod/modulefiles/slurm/
```

**Commands not found:**
```bash
# Check module loaded
module list

# Load module
module load slurm/25.11

# Verify paths
which srun
echo $PATH
```

**Library errors:**
```bash
# Check library path
ldd $(which srun)

# Fix if needed
export LD_LIBRARY_PATH=/opt/slurm/view/lib:$LD_LIBRARY_PATH
```

**Permission errors:**
```bash
# Fix permissions
sudo chmod 755 /opt/slurm/view/bin/*
sudo chmod 755 /opt/slurm/view/sbin/*
```

## Runtime Issues

**Slurm not starting:**
```bash
# Check logs
journalctl -u slurmctld -n 50
journalctl -u slurmd -n 50

# Test config
slurmctld -t
slurmd -t

# Check munge
systemctl status munge
```

**Communication errors:**
```bash
# Verify munge key same on all nodes
md5sum /etc/munge/munge.key

# Restart munge
sudo systemctl restart munge
```

## Performance Issues

**Slow builds:**
```bash
# Check Docker resources
docker stats

# Increase resources
export DOCKER_BUILDKIT=1
```

**Large package sizes:**
```bash
# Skip GPU if not needed (builds are 2-5GB instead of 15-25GB)
slurm-factory build-slurm --slurm-version 25.11  # no --gpu
```

## Getting Help

```bash
# Verbose mode for debugging
slurm-factory --verbose build-slurm --slurm-version 25.11

# Check build logs
docker logs <container-id>

# System information
docker version
slurm-factory --version
uname -a
```

**Report Issues:**
- GitHub: https://github.com/vantagecompute/slurm-factory/issues
- Include: verbose output, Docker version, OS details
