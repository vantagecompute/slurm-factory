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
slurm-{version}-gcc{compiler}-software.tar.gz
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
│       └── {version}-gcc{compiler}.lua  # Modulefile for this build
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

Spack buildcache packages are organized by component:

### Compiler Buildcache

```text
s3://slurm-factory-spack-buildcache-4b670/compilers/{version}/buildcache/
├── build_cache/                   # Compiled binary packages
│   ├── linux-ubuntu24.04-x86_64_v3/
│   │   ├── gcc-13.4.0/
│   │   │   ├── gcc-13.4.0-*.spack              # GCC compiler package
│   │   │   ├── gcc-runtime-13.4.0-*.spack      # Runtime libraries
│   │   │   ├── binutils-2.43.1-*.spack         # Binary tools
│   │   │   ├── gmp-6.3.0-*.spack               # Math library
│   │   │   ├── mpfr-4.2.1-*.spack              # Floating-point library
│   │   │   └── mpc-1.3.1-*.spack               # Complex math library
├── _pgp/                          # GPG public keys
│   └── *.pub
└── index.json                     # Package index

```

### Slurm Buildcache

```text
s3://slurm-factory-spack-buildcache-4b670/slurm/{slurm_version}/{compiler_version}/buildcache/
├── build_cache/                   # Compiled binary packages
│   ├── linux-ubuntu24.04-x86_64_v3/
│   │   ├── gcc-13.4.0/
│   │   │   ├── slurm-25.11.0-*.spack           # Slurm package
│   │   │   ├── openmpi-5.0.6-*.spack           # OpenMPI
│   │   │   ├── pmix-5.0.3-*.spack              # PMIx
│   │   │   ├── munge-0.5.16-*.spack            # Authentication
│   │   │   ├── openssl-3.4.0-*.spack           # TLS/SSL
│   │   │   ├── hdf5-1.14.5-*.spack             # Data format
│   │   │   ├── hwloc-2.11.2-*.spack            # Hardware locality
│   │   │   ├── ucx-1.17.0-*.spack              # Communications
│   │   │   └── ... (40+ more packages)
├── _pgp/                          # GPG public keys
│   └── *.pub
└── index.json                     # Package index
```

**Package Benefits**:
- ✅ **GPG Signed** - Verify package integrity
- ✅ **Compressed** - zstd compression for smaller downloads
- ✅ **Metadata** - Full dependency information included
- ✅ **Relocatable** - RPATH configured for any prefix

## Distribution

Tarballs follow this naming pattern:

```text
slurm-{slurm_version}-gcc{compiler_version}-software.tar.gz
```

**Examples:**

- `slurm-25.11-gcc13.4.0-software.tar.gz` - Slurm 25.11 with GCC 13.4.0 (default)
- `slurm-24.11-gcc11.5.0-software.tar.gz` - Slurm 24.11 with GCC 11.5.0
- `slurm-23.11-gcc7.5.0-software.tar.gz` - Slurm 23.11 with GCC 7.5.0 (RHEL 7)

## Distribution

### Tarball Naming Convention

Tarballs follow this naming pattern:

```text
slurm-{slurm_version}-gcc{compiler_version}-software.tar.gz
```

**Examples:**

- `slurm-25.11-gcc13.4.0-software.tar.gz` - Slurm 25.11 with GCC 13.4.0 (default)
- `slurm-24.11-gcc11.5.0-software.tar.gz` - Slurm 24.11 with GCC 11.5.0
- `slurm-23.11-gcc7.5.0-software.tar.gz` - Slurm 23.11 with GCC 7.5.0 (RHEL 7)

### S3 Distribution

**Tarballs**: Stored in public S3 bucket for direct download

```text
s3://vantage-public-assets/slurm-factory/{slurm_version}/{compiler_version}/
└── slurm-{version}-gcc{compiler}-software.tar.gz
```

**Buildcache**: Stored in dedicated buildcache bucket

```text
s3://slurm-factory-spack-buildcache-4b670/
├── compilers/{version}/buildcache/
└── slurm/{slurm_version}/{compiler_version}/buildcache/
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

| Compiler | Target OS | Public URL |
|----------|-----------|------------|
| GCC 15.2.0 | Latest (experimental) | `https://vantage-public-assets.s3.amazonaws.com/slurm-factory/25.11/15.2.0/slurm-25.11-gcc15.2.0-software.tar.gz` |
| GCC 14.2.0 | Latest | `https://vantage-public-assets.s3.amazonaws.com/slurm-factory/25.11/14.2.0/slurm-25.11-gcc14.2.0-software.tar.gz` |
| GCC 13.4.0 | Ubuntu 24.04 **(recommended)** | `https://vantage-public-assets.s3.amazonaws.com/slurm-factory/25.11/13.4.0/slurm-25.11-gcc13.4.0-software.tar.gz` |
| GCC 12.5.0 | Ubuntu 22.04 | `https://vantage-public-assets.s3.amazonaws.com/slurm-factory/25.11/12.5.0/slurm-25.11-gcc12.5.0-software.tar.gz` |
| GCC 11.5.0 | Ubuntu 22.04 | `https://vantage-public-assets.s3.amazonaws.com/slurm-factory/25.11/11.5.0/slurm-25.11-gcc11.5.0-software.tar.gz` |
| GCC 10.5.0 | RHEL 8/Ubuntu 20.04 | `https://vantage-public-assets.s3.amazonaws.com/slurm-factory/25.11/10.5.0/slurm-25.11-gcc10.5.0-software.tar.gz` |
| GCC 9.5.0 | RHEL 8 | `https://vantage-public-assets.s3.amazonaws.com/slurm-factory/25.11/9.5.0/slurm-25.11-gcc9.5.0-software.tar.gz` |
| GCC 8.5.0 | RHEL 8 | `https://vantage-public-assets.s3.amazonaws.com/slurm-factory/25.11/8.5.0/slurm-25.11-gcc8.5.0-software.tar.gz` |
| GCC 7.5.0 | RHEL 7 | `https://vantage-public-assets.s3.amazonaws.com/slurm-factory/25.11/7.5.0/slurm-25.11-gcc7.5.0-software.tar.gz` |

#### Slurm 24.11 (LTS)

Similar URLs for Slurm 24.11 with all compiler versions.

#### Slurm 23.11 (Stable) and 23.02 (Legacy)

Similar URLs for older Slurm versions with all compiler versions.

### Buildcache

All buildcache packages are available via CloudFront:

**Compiler Buildcache URLs**:
```
https://slurm-factory-spack-binary-cache.vantagecompute.ai/compilers/{version}/buildcache
```

**Slurm Buildcache URLs**:
```
https://slurm-factory-spack-binary-cache.vantagecompute.ai/slurm/{slurm_version}/{compiler_version}/buildcache
```

See [Slurm Factory Spack Build Cache](./slurm-factory-spack-build-cache.md) for complete buildcache documentation.

## Downloading Artifacts

### Using Tarballs

#### AWS CLI

```bash
# Download a specific build
aws s3 cp s3://vantage-public-assets/slurm-factory/25.11/13.4.0/slurm-25.11-gcc13.4.0-software.tar.gz .

# List all available builds
aws s3 ls s3://vantage-public-assets/slurm-factory/ --recursive

# Download all builds for a specific Slurm version
aws s3 sync s3://vantage-public-assets/slurm-factory/25.11/ ./slurm-25.11/
```

#### wget (Public Access)

```bash
# Download via HTTPS
wget https://vantage-public-assets.s3.amazonaws.com/slurm-factory/25.11/13.4.0/slurm-25.11-gcc13.4.0-software.tar.gz
```

#### curl

```bash
# Download with curl
curl -O https://vantage-public-assets.s3.amazonaws.com/slurm-factory/25.11/13.4.0/slurm-25.11-gcc13.4.0-software.tar.gz
```

### Using Buildcache

#### With Spack

```bash
# 1. Install Spack
git clone --depth 1 --branch v1.0.0 https://github.com/spack/spack.git
source spack/share/spack/setup-env.sh

# 2. Add buildcache mirrors
spack mirror add slurm-factory-compilers \
  https://slurm-factory-spack-binary-cache.vantagecompute.ai/compilers/13.4.0/buildcache

spack mirror add slurm-factory-slurm \
  https://slurm-factory-spack-binary-cache.vantagecompute.ai/slurm/25.11/13.4.0/buildcache

# 3. Install from buildcache
spack install --no-check-signature slurm@25.11%gcc@13.4.0

# 4. Load and use
spack load slurm@25.11
sinfo --version
```

#### With slurm-factory CLI

```bash
# The CLI uses buildcache automatically
pip install slurm-factory

# Build will use buildcache for dependencies
slurm-factory build --slurm-version 25.11 --compiler-version 13.4.0
```

## Artifact Verification

Each tarball includes verification information:

```bash
# Extract and verify contents
tar -tzf slurm-25.11-gcc13.4.0-software.tar.gz | head -20

# Check modulefile
tar -xzf slurm-25.11-gcc13.4.0-software.tar.gz modules/slurm/25.11-gcc13.4.0.lua
cat modules/slurm/25.11-gcc13.4.0.lua
```

## Installation from Artifacts

### From Tarball

Complete installation example:

```bash
# 1. Download the tarball
wget https://vantage-public-assets.s3.amazonaws.com/slurm-factory/25.11/13.4.0/slurm-25.11-gcc13.4.0-software.tar.gz

# 2. Extract to target location
sudo mkdir -p /opt
sudo tar -xzf slurm-25.11-gcc13.4.0-software.tar.gz -C /opt/

# 3. Run installation script
cd /opt && sudo ./data/slurm_assets/slurm_install.sh --full-init --cluster-name mycluster

# 4. Configure Lmod to find modules
export MODULEPATH=/opt/modules:$MODULEPATH

# 5. Load the module
module load slurm/25.11-gcc13.4.0

# 6. Verify installation
sinfo --version
# Output: slurm 25.11.0
```

### From Buildcache

Install Slurm directly with Spack:

```bash
# 1. Add buildcache mirrors
spack mirror add slurm-factory-compilers \
  https://slurm-factory-spack-binary-cache.vantagecompute.ai/compilers/13.4.0/buildcache

spack mirror add slurm-factory-slurm \
  https://slurm-factory-spack-binary-cache.vantagecompute.ai/slurm/25.11/13.4.0/buildcache

# 2. Install from cache (5-15 minutes!)
spack install --no-check-signature slurm@25.11%gcc@13.4.0

# 3. Load and verify
spack load slurm@25.11
sinfo --version
```

## Package Sizes

Typical package sizes by type:

| Type | Size Range | Description |
|------|------------|-------------|
| **Default** | 2-5 GB | Full build with OpenMPI, PMIx, HDF5 |
| **Minimal** | 1-2 GB | Basic Slurm only, no OpenMPI |
| **GPU** | 15-25 GB | Includes CUDA/ROCm support |

## Build Metadata

Each build is tagged with metadata:

- **Build Date**: When the package was created
- **Slurm Version**: e.g., 25.11, 24.11
- **Compiler**: e.g., gcc@13.4.0
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
        object: slurm-25.11-gcc13.4.0-software.tar.gz
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
      "aws s3 cp s3://vantagecompute-slurm-builds/slurm-25.11-gcc13.4.0-software.tar.gz /tmp/",
      "sudo mkdir -p /opt/slurm",
      "sudo tar -xzf /tmp/slurm-25.11-gcc13.4.0-software.tar.gz -C /opt/slurm",
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
