# Build Artifacts

Slurm Factory produces two types of artifacts: **relocatable tarballs** for direct deployment and **Spack buildcache packages** for fast installation. Both are published to Amazon S3 for global distribution.

## Artifact Types

### 1. Relocatable Tarballs

**Purpose**: Complete, self-contained Slurm installations ready to extract and deploy

**Location**: `s3://vantage-public-assets/slurm-factory/`

**Format**: Single tarball containing Slurm binaries, modules, and installation scripts

**Use Cases**:
- Quick deployment on any Linux system
- Air-gapped installations (download once, deploy offline)
- Container base images
- Infrastructure automation (Ansible, Terraform)

### 2. Spack Buildcache Packages

**Purpose**: Binary package cache for Spack to enable fast installations

**Location**: `s3://slurm-factory-spack-buildcache-4b670/`

**Format**: Spack buildcache directory with GPG-signed packages

**Use Cases**:
- Fast Spack-based installations (5-15 minutes)
- Custom Slurm builds with modified dependencies
- Development and testing environments
- CI/CD pipelines

## Tarball Structure

## Tarball Structure

Each build produces **one tarball** containing:

```text
slurm-{version}-{toolchain}-software.tar.gz
├── view/                          # Slurm installation (unified prefix)
│   ├── bin/                       # Slurm binaries (srun, sbatch, squeue, etc.)
│   ├── sbin/                      # Daemons (slurmd, slurmctld, slurmdbd)
│   ├── lib/                       # Shared libraries
│   │   ├── libslurm.so            # Core Slurm library
│   │   ├── libslurmdb.so          # Database library
│   │   └── slurm/                 # Slurm plugins (auth, select, etc.)
│   ├── lib64/                     # 64-bit libraries
│   ├── include/                   # Header files
│   │   └── slurm/                 # Slurm development headers
│   ├── share/                     # Documentation, man pages
│   │   ├── man/                   # Man pages (man1, man5, man8)
│   │   ├── doc/slurm/             # HTML documentation
│   │   └── licenses/              # License files
│   └── etc/                       # Configuration templates
│       └── slurm/                 # Sample configs
├── modules/                       # Lmod modulefile
│   └── slurm/
│       └── {version}-{toolchain}.lua  # Modulefile for this build
└── data/slurm_assets/             # Installation scripts and configs
    ├── slurm_install.sh           # Automated installation script
    ├── defaults/                  # Systemd unit files
    │   ├── slurmd.service
    │   ├── slurmctld.service
    │   └── slurmdbd.service
    ├── slurm/                     # Configuration templates
    │   ├── slurm.conf.template
    │   ├── slurmdbd.conf.template
    │   ├── cgroup.conf.template
    │   └── topology.conf.template
    └── mysql/                     # Database setup
        └── slurm_acct_db.sql      # Database schema
```

## Buildcache Structure

Spack buildcache packages are organized by OS toolchain:

### Dependencies Buildcache

```text
s3://slurm-factory-spack-buildcache-4b670/{toolchain}/slurm/deps/buildcache/
├── build_cache/                   # Compiled binary packages
│   ├── linux-ubuntu24.04-x86_64_v3/  # For noble toolchain
│   │   ├── gcc-13.3.0/
│   │   │   ├── openmpi-5.0.6-*.spack           # MPI implementation
│   │   │   ├── pmix-5.0.5-*.spack              # Process Management Interface
│   │   │   ├── munge-0.5.16-*.spack            # Authentication service
│   │   │   ├── hwloc-2.11.2-*.spack            # Hardware locality
│   │   │   └── libevent-2.1.12-*.spack         # Event notification
├── _pgp/                          # GPG public keys
│   └── *.pub
└── index.json                     # Package index

```

### Slurm Buildcache

```text
s3://slurm-factory-spack-buildcache-4b670/{toolchain}/slurm/{slurm_version}/buildcache/
├── build_cache/                   # Compiled binary packages
│   ├── linux-ubuntu24.04-x86_64_v3/  # For noble toolchain
│   │   ├── gcc-13.3.0/             # Built with OS-provided GCC
│   │   │   ├── slurm-25.11.0-*.spack           # Slurm package
│   │   │   ├── openmpi-5.0.6-*.spack           # OpenMPI
│   │   │   ├── pmix-5.0.5-*.spack              # PMIx
│   │   │   ├── munge-0.5.16-*.spack            # Authentication
│   │   │   ├── openssl-3.4.0-*.spack           # TLS/SSL
│   │   │   ├── hdf5-1.14.5-*.spack             # Data format
│   │   │   ├── hwloc-2.11.2-*.spack            # Hardware locality
│   │   │   ├── ucx-1.17.0-*.spack              # Communications
│   │   │   └── ... (40+ more packages)
├── _pgp/                          # GPG public keys for signature verification
│   └── *.pub                      # Public keys automatically imported by Spack
└── index.json                     # Package index
```

**Package Benefits**:
- ✅ **GPG Signed** - Cryptographically signed for security and integrity
- ✅ **Compressed** - zstd compression for smaller downloads
- ✅ **Metadata** - Full dependency information included
- ✅ **Relocatable** - RPATH configured for any prefix

**Security Workflow**:

1. All packages built in isolated Docker containers
2. Packages signed with GPG private key during CI/CD
3. Public keys stored in `_pgp/` directory of buildcache
4. Users import keys with `spack buildcache keys --install --trust`
5. Spack verifies signatures automatically during installation

## Distribution

Tarballs follow this naming pattern:

```text
slurm-{slurm_version}-{toolchain}-software.tar.gz
```

**Examples:**

- `slurm-25.11-noble-software.tar.gz` - Slurm 25.11 for Ubuntu 24.04 (Noble)
- `slurm-24.11-jammy-software.tar.gz` - Slurm 24.11 for Ubuntu 22.04 (Jammy)
- `slurm-23.11-rockylinux9-software.tar.gz` - Slurm 23.11 for Rocky Linux 9

## Distribution

### S3 Distribution

**Tarballs**: Stored in public S3 bucket for direct download

```text
s3://vantage-public-assets/slurm-factory/{slurm_version}/{toolchain}/
└── slurm-{version}-{toolchain}-software.tar.gz
```

**Buildcache**: Stored in dedicated buildcache bucket organized by OS toolchain

```text
s3://slurm-factory-spack-buildcache-4b670/
├── {toolchain}/slurm/deps/buildcache/
└── {toolchain}/slurm/{slurm_version}/buildcache/
```

Example for noble (Ubuntu 24.04):
```text
s3://slurm-factory-spack-buildcache-4b670/
├── noble/slurm/deps/buildcache/
└── noble/slurm/25.11/buildcache/
```

### CloudFront CDN

Both S3 buckets are distributed via CloudFront for fast global access:

**Buildcache CDN**:
```
https://slurm-factory-spack-binary-cache.vantagecompute.ai
```

**Tarball CDN** (planned):
```
https://vantage-public-assets.s3.amazonaws.com/slurm-factory/
```

## Available Builds

## Available Builds

### Tarballs

All Slurm × Compiler combinations are pre-built and available:

#### Slurm 25.11 (Latest)

| Toolchain | Target OS | Public URL |
|-----------|-----------|------------|
| noble | Ubuntu 24.04 **(recommended)** | `https://vantage-public-assets.s3.amazonaws.com/slurm-factory/25.11/noble/slurm-25.11-noble-software.tar.gz` |
| jammy | Ubuntu 22.04 | `https://vantage-public-assets.s3.amazonaws.com/slurm-factory/25.11/jammy/slurm-25.11-jammy-software.tar.gz` |
| focal | Ubuntu 20.04 | `https://vantage-public-assets.s3.amazonaws.com/slurm-factory/25.11/focal/slurm-25.11-focal-software.tar.gz` |
| rockylinux10 | Rocky Linux 10 / RHEL 10 | `https://vantage-public-assets.s3.amazonaws.com/slurm-factory/25.11/rockylinux10/slurm-25.11-rockylinux10-software.tar.gz` |
| rockylinux9 | Rocky Linux 9 / RHEL 9 | `https://vantage-public-assets.s3.amazonaws.com/slurm-factory/25.11/rockylinux9/slurm-25.11-rockylinux9-software.tar.gz` |
| rockylinux8 | Rocky Linux 8 / RHEL 8 | `https://vantage-public-assets.s3.amazonaws.com/slurm-factory/25.11/rockylinux8/slurm-25.11-rockylinux8-software.tar.gz` |

#### Slurm 24.11 (LTS)

Similar URLs for Slurm 24.11 with all compiler versions.

#### Slurm 23.11 (Stable)

Similar URLs for Slurm 23.11 with all compiler versions.

### Buildcache

All buildcache packages are available via CloudFront:

**Dependencies Buildcache URLs**:
```
https://slurm-factory-spack-binary-cache.vantagecompute.ai/{toolchain}/slurm/deps/
```

**Slurm Buildcache URLs**:
```
https://slurm-factory-spack-binary-cache.vantagecompute.ai/{toolchain}/slurm/{slurm_version}/
```

See [Slurm Factory Spack Build Cache](./slurm-factory-spack-build-cache.md) for complete buildcache documentation.

## Downloading Artifacts

### Using Tarballs

#### AWS CLI

```bash
# Download a specific build
aws s3 cp s3://vantage-public-assets/slurm-factory/25.11/noble/slurm-25.11-noble-software.tar.gz .

# List all available builds
aws s3 ls s3://vantage-public-assets/slurm-factory/ --recursive

# Download all builds for a specific Slurm version
aws s3 sync s3://vantage-public-assets/slurm-factory/25.11/ ./slurm-25.11/
```

#### wget (Public Access)

```bash
# Download via HTTPS
wget https://vantage-public-assets.s3.amazonaws.com/slurm-factory/25.11/noble/slurm-25.11-noble-software.tar.gz
```

#### curl

```bash
# Download with curl
curl -O https://vantage-public-assets.s3.amazonaws.com/slurm-factory/25.11/noble/slurm-25.11-noble-software.tar.gz
```

### Using Buildcache

#### With Spack

```bash
# 1. Install Spack
git clone --depth 1 --branch v1.0.0 https://github.com/spack/spack.git
source spack/share/spack/setup-env.sh

# 2. Add buildcache mirrors (organized by OS toolchain)
spack mirror add slurm-factory-slurm-deps \
  https://slurm-factory-spack-binary-cache.vantagecompute.ai/noble/slurm/deps/

spack mirror add slurm-factory-slurm \
  https://slurm-factory-spack-binary-cache.vantagecompute.ai/noble/slurm/25.11/

# 3. Import and trust GPG signing keys
spack buildcache keys --install --trust

# 4. Install from signed buildcache
spack install slurm@25.11

# 5. Load and use
spack load slurm@25.11
sinfo --version
```

#### With slurm-factory CLI

```bash
# The CLI uses buildcache automatically
pip install slurm-factory

# Build will use buildcache for dependencies
slurm-factory build-slurm --slurm-version 25.11 --toolchain noble
```

## Artifact Verification

Each tarball includes verification information:

```bash
# Extract and verify contents
tar -tzf slurm-25.11-noble-software.tar.gz | head -20

# Check modulefile
tar -xzf slurm-25.11-noble-software.tar.gz modules/slurm/25.11-noble.lua
cat modules/slurm/25.11-noble.lua
```

## Installation from Artifacts

### From Tarball

Complete installation example:

```bash
# 1. Download the tarball
wget https://vantage-public-assets.s3.amazonaws.com/slurm-factory/25.11/noble/slurm-25.11-noble-software.tar.gz

# 2. Extract to target location
sudo mkdir -p /opt
sudo tar -xzf slurm-25.11-noble-software.tar.gz -C /opt/

# 3. Run installation script
cd /opt && sudo ./data/slurm_assets/slurm_install.sh --full-init --cluster-name mycluster

# 4. Configure Lmod to find modules
export MODULEPATH=/opt/modules:$MODULEPATH

# 5. Load the module
module load slurm/25.11-noble

# 6. Verify installation
sinfo --version
# Output: slurm 25.11.0
```

### From Buildcache

Install Slurm directly with Spack:

```bash
# 1. Add buildcache mirrors
spack mirror add slurm-factory-deps \
  https://slurm-factory-spack-binary-cache.vantagecompute.ai/noble/slurm/deps/

spack mirror add slurm-factory-slurm \
  https://slurm-factory-spack-binary-cache.vantagecompute.ai/noble/slurm/25.11/

# 2. Import and trust GPG signing keys
spack buildcache keys --install --trust

# 3. Install from signed buildcache (5-15 minutes!)
spack install slurm@25.11

# 4. Load and verify
spack load slurm@25.11
sinfo --version
```

## Package Sizes

Typical package sizes by type:

| Type | Size Range | Description |
|------|------------|-------------|
| **Default** | 2-5 GB | Full build with OpenMPI, PMIx, HDF5 |
| **GPU** | 15-25 GB | Includes CUDA/ROCm support |

## Build Metadata

Each build is tagged with metadata:

- **Build Date**: When the package was created
- **Slurm Version**: e.g., 25.11, 24.11
- **Toolchain**: e.g., noble, jammy, rockylinux9
- **Architecture**: x86_64_v3 (optimized for modern CPUs)
- **Features**: OpenMPI version, GPU support, etc.

## Automation Integration

### Ansible Playbook Example

```yaml
- name: Deploy Slurm from S3
  hosts: cluster
  tasks:
    - name: Download Slurm tarball
      aws_s3:
        bucket: vantagecompute-slurm-builds
        object: slurm-25.11-noble-software.tar.gz
        dest: /tmp/slurm.tar.gz
        mode: get

    - name: Extract Slurm
      unarchive:
        src: /tmp/slurm.tar.gz
        dest: /opt/slurm
        remote_src: yes

    - name: Set up modules
      copy:
        src: /opt/slurm/modules/slurm/
        dest: /opt/modulefiles/slurm/
        remote_src: yes
```

### Terraform Example

```hcl
resource "null_resource" "deploy_slurm" {
  provisioner "remote-exec" {
    inline = [
      "aws s3 cp s3://vantagecompute-slurm-builds/slurm-25.11-noble-software.tar.gz /tmp/",
      "sudo mkdir -p /opt/slurm",
      "sudo tar -xzf /tmp/slurm-25.11-noble-software.tar.gz -C /opt/slurm",
      "sudo cp -r /opt/slurm/modules/slurm /opt/modulefiles/"
    ]
  }
}
```

## See Also

- [Slurm Factory Spack Build Cache](./slurm-factory-spack-build-cache.md) - Detailed buildcache documentation
- [Infrastructure](./infrastructure.md) - AWS infrastructure and CDN
- [GitHub Actions](./github-actions.md) - Automated build and publishing
- [Deployment Guide](./deployment.md) - Detailed deployment instructions
- [Architecture](./architecture.md) - How packages are built
- [Examples](./examples.md) - Usage examples and patterns
