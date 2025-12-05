# Deployment Guide

Deploy relocatable Slurm packages to HPC clusters. Packages can be built locally or downloaded from S3.

## Quick Start

### Option 1: Build Locally

```bash
# Build package for Ubuntu 24.04 (Noble)
slurm-factory build-slurm --slurm-version 25.11 --toolchain noble

# Build for Ubuntu 22.04 (Jammy)
slurm-factory build-slurm --slurm-version 25.11 --toolchain jammy

# Build for Rocky Linux 9
slurm-factory build-slurm --slurm-version 25.11 --toolchain rockylinux9

# Deploy
sudo tar -xzf ~/.slurm-factory/builds/slurm-25.11-noble-software.tar.gz -C /opt/
cd /opt && sudo ./data/slurm_assets/slurm_install.sh --full-init --cluster-name mycluster

# Load module
module load slurm/25.11-noble
```

### Option 2: Download Pre-Built Package from S3

```bash
# Download from S3 (Ubuntu 24.04)
wget https://vantage-public-assets.s3.amazonaws.com/slurm-factory/25.11/noble/slurm-25.11-noble-software.tar.gz

# Deploy
sudo tar -xzf slurm-25.11-noble-software.tar.gz -C /opt/
cd /opt && sudo ./data/slurm_assets/slurm_install.sh --full-init --cluster-name mycluster

# Load module
module load slurm/25.11-noble
```

See [Build Artifacts](build-artifacts.md) for all available packages.

## Toolchain Compatibility

Use `--toolchain` to build packages for your target distribution:

| Toolchain | Target OS | GCC Version | glibc |
|-----------|-----------|-------------|-------|
| resolute | Ubuntu 25.04 | 15.x | 2.41+ |
| noble | Ubuntu 24.04 | 13.x | 2.39 |
| jammy | Ubuntu 22.04 | 11.x | 2.35 |
| rockylinux10 | Rocky Linux 10 / RHEL 10 | 14.x | 2.39+ |
| rockylinux9 | Rocky Linux 9 / RHEL 9 | 11.x | 2.34 |
| rockylinux8 | Rocky Linux 8 / RHEL 8 | 8.x | 2.28 |

**Note**: Each toolchain uses the OS-provided compiler for maximum binary compatibility.

## Installation Script Options

- `--full-init` - Complete installation (users, dirs, configs, services)
- `--head-node-init` - Install MySQL, InfluxDB, SSSD dependencies
- `--start-services` - Start Slurm daemons
- `--cluster-name NAME` - Set cluster name
- `--org-id ID` - Organization ID for LDAP
- `--sssd-binder-password PW` - SSSD password
- `--ldap-uri URI` - LDAP server URI

**Examples:**

```bash
# Head node
sudo ./slurm_install.sh --head-node-init --full-init --start-services --cluster-name prod

# Compute node
sudo ./slurm_install.sh --full-init --start-services --cluster-name prod

# With LDAP
sudo ./slurm_install.sh --full-init --org-id myorg --ldap-uri ldap://ldap.example.com
```

## Package Structure

Each tarball contains:

```text
slurm-{version}-{toolchain}-software.tar.gz
├── data/slurm_assets/          # Configuration templates & install script
├── modules/slurm/              # Lmod modulefiles
│   └── {version}-{toolchain}.lua
└── view/                       # Slurm installation
    ├── bin/                    # srun, sbatch, squeue, sinfo
    ├── sbin/                   # slurmd, slurmctld, slurmdbd
    └── lib/                    # Libraries & plugins
```

## Relocatable Deployment

```bash
# Custom path deployment
export SLURM_INSTALL_PREFIX=/shared/apps/slurm
module load slurm/25.11-noble

# Verify
which srun
echo $SLURM_ROOT
```

## Multi-Version Deployment

```bash
# Deploy multiple versions
sudo tar -xzf slurm-25.11-noble-software.tar.gz -C /opt/slurm-25.11/
sudo tar -xzf slurm-24.11-jammy-software.tar.gz -C /opt/slurm-24.11/

cd /opt/slurm-25.11 && sudo ./data/slurm_assets/slurm_install.sh
cd /opt/slurm-24.11 && sudo ./data/slurm_assets/slurm_install.sh

# Switch versions
module load slurm/25.11-noble  # or slurm/24.11-jammy
```

## Basic Configuration

```bash
# Create slurm.conf
sudo tee /etc/slurm/slurm.conf << 'EOF'
ClusterName=mycluster
ControlMachine=head01
SlurmUser=slurm
AuthType=auth/munge
StateSaveLocation=/var/spool/slurm/ctld

NodeName=node[01-04] CPUs=8 RealMemory=32000 State=UNKNOWN
PartitionName=compute Nodes=node[01-04] Default=YES State=UP
EOF

# Start services
sudo systemctl start slurmctld  # head node
sudo systemctl start slurmd     # compute nodes
```

## Troubleshooting

**Module not found:**

```bash
module avail
echo $MODULEPATH
```

**Library errors:**

```bash
ldd $(which srun)
export LD_LIBRARY_PATH=/opt/slurm/view/lib:$LD_LIBRARY_PATH
```

**Permission errors:**

```bash
sudo chmod 755 /opt/slurm/view/bin/*
sudo chmod 755 /opt/slurm/view/sbin/*
```
