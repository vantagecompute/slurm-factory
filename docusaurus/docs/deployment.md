# Deployment Guide

Deploy relocatable Slurm packages to HPC clusters.

## Quick Start

```bash
# Build package (default: Ubuntu 24.04 compatible)
slurm-factory build --slurm-version 25.05

# Build for RHEL 8 / Ubuntu 20.04 compatibility
slurm-factory build --slurm-version 25.05 --compiler-version 10.5.0

# Build for RHEL 7 compatibility
slurm-factory build --slurm-version 25.05 --compiler-version 7.5.0

# Deploy
sudo tar -xzf ~/.slurm-factory/builds/slurm-25.05-software.tar.gz -C /opt/
cd /opt && sudo ./data/slurm_assets/slurm_install.sh --full-init --cluster-name mycluster

# Load module
module load slurm/25.05
```

## Cross-Distro Compatibility

Use `--compiler-version` to build packages compatible with older distributions:

| Compiler Version | Compatible Distros                    | glibc |
|------------------|---------------------------------------|-------|
| 13.3.0 (default) | Ubuntu 24.04+, Debian 13+             | 2.39  |
| 11.4.0           | Ubuntu 22.04+, Debian 12+             | 2.35  |
| 10.5.0           | RHEL 8+, Ubuntu 20.04+, Debian 11+    | 2.31  |
| 8.5.0            | RHEL 8+, CentOS 8+                    | 2.28  |
| 7.5.0            | RHEL 7+, CentOS 7+                    | 2.17  |

**Build time**: Older compilers add 30-60 minutes for toolchain bootstrap on first build.

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

```
data/slurm_assets/       # Configuration templates & install script
modules/slurm/25.05.lua  # Lmod module
view/                    # Slurm binaries & libraries
├── bin/                 # srun, sbatch, squeue, sinfo
├── sbin/                # slurmd, slurmctld, slurmdbd
└── lib/                 # Libraries & plugins
```

## Relocatable Deployment

```bash
# Custom path deployment
export SLURM_INSTALL_PREFIX=/shared/apps/slurm
module load slurm/25.05

# Verify
which srun
echo $SLURM_ROOT
```

## Multi-Version Deployment

```bash
# Deploy multiple versions
sudo tar -xzf slurm-25.05-software.tar.gz -C /opt/slurm-25.05/
sudo tar -xzf slurm-24.11-software.tar.gz -C /opt/slurm-24.11/

cd /opt/slurm-25.05 && sudo ./data/slurm_assets/slurm_install.sh
cd /opt/slurm-24.11 && sudo ./data/slurm_assets/slurm_install.sh

# Switch versions
module load slurm/25.05  # or slurm/24.11
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
