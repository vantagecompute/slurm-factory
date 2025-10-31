# Build Artifacts

Slurm Factory produces relocatable Slurm packages that are published to Amazon S3 for easy distribution. Each build creates a single tarball containing both the Slurm installation and its corresponding Lmod modulefile.

## Package Structure

Each build produces **one tarball** containing:

```text
slurm-{version}-gcc{compiler}-software.tar.gz
├── view/                          # Slurm installation
│   ├── bin/                       # Slurm binaries (srun, sbatch, etc.)
│   ├── lib/                       # Shared libraries
│   ├── lib64/                     # 64-bit libraries
│   ├── include/                   # Header files
│   ├── share/                     # Documentation, man pages
│   └── etc/                       # Configuration templates
└── modules/                       # Lmod modulefile
    └── slurm/
        └── {version}-gcc{compiler}.lua  # Modulefile for this build
```

## Package Naming Convention

Tarballs follow this naming pattern:

```text
slurm-{slurm_version}-gcc{compiler_version}-software.tar.gz
```

**Examples:**

- `slurm-25.05-gcc13.4.0-software.tar.gz` - Slurm 25.05 with GCC 13.4.0 (default)
- `slurm-24.11-gcc11.5.0-software.tar.gz` - Slurm 24.11 with GCC 11.5.0
- `slurm-23.11-gcc7.5.0-software.tar.gz` - Slurm 23.11 with GCC 7.5.0 (RHEL 7)

## S3 Build Artifacts

All pre-built packages are available in our S3 bucket. You can download them directly or use them in your deployment automation.

### S3 Bucket Location

```text
s3://vantagecompute-slurm-builds/
```

### Available Builds

#### Slurm 25.05

| Compiler | Target OS | S3 URL |
|----------|-----------|--------|
| GCC 14.2.0 | Latest | `s3://vantagecompute-slurm-builds/slurm-25.05-gcc14.2.0-software.tar.gz` |
| GCC 13.4.0 | Ubuntu 24.04 | `s3://vantagecompute-slurm-builds/slurm-25.05-gcc13.4.0-software.tar.gz` |
| GCC 12.5.0 | Ubuntu 22.04 | `s3://vantagecompute-slurm-builds/slurm-25.05-gcc12.5.0-software.tar.gz` |
| GCC 11.5.0 | Ubuntu 22.04 | `s3://vantagecompute-slurm-builds/slurm-25.05-gcc11.5.0-software.tar.gz` |
| GCC 10.5.0 | RHEL 8/Ubuntu 20.04 | `s3://vantagecompute-slurm-builds/slurm-25.05-gcc10.5.0-software.tar.gz` |
| GCC 9.5.0 | RHEL 8 | `s3://vantagecompute-slurm-builds/slurm-25.05-gcc9.5.0-software.tar.gz` |
| GCC 8.5.0 | RHEL 8 | `s3://vantagecompute-slurm-builds/slurm-25.05-gcc8.5.0-software.tar.gz` |
| GCC 7.5.0 | RHEL 7 | `s3://vantagecompute-slurm-builds/slurm-25.05-gcc7.5.0-software.tar.gz` |

#### Slurm 24.11

| Compiler | Target OS | S3 URL |
|----------|-----------|--------|
| GCC 14.2.0 | Latest | `s3://vantagecompute-slurm-builds/slurm-24.11-gcc14.2.0-software.tar.gz` |
| GCC 13.4.0 | Ubuntu 24.04 | `s3://vantagecompute-slurm-builds/slurm-24.11-gcc13.4.0-software.tar.gz` |
| GCC 12.5.0 | Ubuntu 22.04 | `s3://vantagecompute-slurm-builds/slurm-24.11-gcc12.5.0-software.tar.gz` |
| GCC 11.5.0 | Ubuntu 22.04 | `s3://vantagecompute-slurm-builds/slurm-24.11-gcc11.5.0-software.tar.gz` |
| GCC 10.5.0 | RHEL 8/Ubuntu 20.04 | `s3://vantagecompute-slurm-builds/slurm-24.11-gcc10.5.0-software.tar.gz` |
| GCC 9.5.0 | RHEL 8 | `s3://vantagecompute-slurm-builds/slurm-24.11-gcc9.5.0-software.tar.gz` |
| GCC 8.5.0 | RHEL 8 | `s3://vantagecompute-slurm-builds/slurm-24.11-gcc8.5.0-software.tar.gz` |
| GCC 7.5.0 | RHEL 7 | `s3://vantagecompute-slurm-builds/slurm-24.11-gcc7.5.0-software.tar.gz` |

#### Slurm 23.11

| Compiler | Target OS | S3 URL |
|----------|-----------|--------|
| GCC 14.2.0 | Latest | `s3://vantagecompute-slurm-builds/slurm-23.11-gcc14.2.0-software.tar.gz` |
| GCC 13.4.0 | Ubuntu 24.04 | `s3://vantagecompute-slurm-builds/slurm-23.11-gcc13.4.0-software.tar.gz` |
| GCC 12.5.0 | Ubuntu 22.04 | `s3://vantagecompute-slurm-builds/slurm-23.11-gcc12.5.0-software.tar.gz` |
| GCC 11.5.0 | Ubuntu 22.04 | `s3://vantagecompute-slurm-builds/slurm-23.11-gcc11.5.0-software.tar.gz` |
| GCC 10.5.0 | RHEL 8/Ubuntu 20.04 | `s3://vantagecompute-slurm-builds/slurm-23.11-gcc10.5.0-software.tar.gz` |
| GCC 9.5.0 | RHEL 8 | `s3://vantagecompute-slurm-builds/slurm-23.11-gcc9.5.0-software.tar.gz` |
| GCC 8.5.0 | RHEL 8 | `s3://vantagecompute-slurm-builds/slurm-23.11-gcc8.5.0-software.tar.gz` |
| GCC 7.5.0 | RHEL 7 | `s3://vantagecompute-slurm-builds/slurm-23.11-gcc7.5.0-software.tar.gz` |

#### Slurm 23.02

| Compiler | Target OS | S3 URL |
|----------|-----------|--------|
| GCC 14.2.0 | Latest | `s3://vantagecompute-slurm-builds/slurm-23.02-gcc14.2.0-software.tar.gz` |
| GCC 13.4.0 | Ubuntu 24.04 | `s3://vantagecompute-slurm-builds/slurm-23.02-gcc13.4.0-software.tar.gz` |
| GCC 12.5.0 | Ubuntu 22.04 | `s3://vantagecompute-slurm-builds/slurm-23.02-gcc12.5.0-software.tar.gz` |
| GCC 11.5.0 | Ubuntu 22.04 | `s3://vantagecompute-slurm-builds/slurm-23.02-gcc11.5.0-software.tar.gz` |
| GCC 10.5.0 | RHEL 8/Ubuntu 20.04 | `s3://vantagecompute-slurm-builds/slurm-23.02-gcc10.5.0-software.tar.gz` |
| GCC 9.5.0 | RHEL 8 | `s3://vantagecompute-slurm-builds/slurm-23.02-gcc9.5.0-software.tar.gz` |
| GCC 8.5.0 | RHEL 8 | `s3://vantagecompute-slurm-builds/slurm-23.02-gcc8.5.0-software.tar.gz` |
| GCC 7.5.0 | RHEL 7 | `s3://vantagecompute-slurm-builds/slurm-23.02-gcc7.5.0-software.tar.gz` |

## Downloading Artifacts

### Using AWS CLI

```bash
# Download a specific build
aws s3 cp s3://vantagecompute-slurm-builds/slurm-25.05-gcc13.4.0-software.tar.gz .

# List all available builds
aws s3 ls s3://vantagecompute-slurm-builds/

# Download all builds for a specific Slurm version
aws s3 sync s3://vantagecompute-slurm-builds/ . --exclude "*" --include "slurm-25.05-*"
```

### Using wget (Public Access)

```bash
# Download via HTTPS (if bucket has public read access)
wget https://vantagecompute-slurm-builds.s3.amazonaws.com/slurm-25.05-gcc13.4.0-software.tar.gz
```

### Using curl

```bash
# Download with curl
curl -O https://vantagecompute-slurm-builds.s3.amazonaws.com/slurm-25.05-gcc13.4.0-software.tar.gz
```

## Artifact Verification

Each tarball includes verification information:

```bash
# Extract and verify contents
tar -tzf slurm-25.05-gcc13.4.0-software.tar.gz | head -20

# Check modulefile
tar -xzf slurm-25.05-gcc13.4.0-software.tar.gz modules/slurm/25.05-gcc13.4.0.lua
cat modules/slurm/25.05-gcc13.4.0.lua
```

## Installation from S3

Complete installation example:

```bash
# 1. Download the tarball
aws s3 cp s3://vantagecompute-slurm-builds/slurm-25.05-gcc13.4.0-software.tar.gz /tmp/

# 2. Extract to target location
sudo mkdir -p /opt/slurm
sudo tar -xzf /tmp/slurm-25.05-gcc13.4.0-software.tar.gz -C /opt/slurm

# 3. Set up module system
sudo mkdir -p /opt/modulefiles
sudo cp -r /opt/slurm/modules/slurm /opt/modulefiles/

# 4. Configure Lmod to find modules
export MODULEPATH=/opt/modulefiles:$MODULEPATH

# 5. Load the module
module load slurm/25.05-gcc13.4.0

# 6. Verify installation
srun --version
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
- **Slurm Version**: e.g., 25.05, 24.11
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
        object: slurm-25.05-gcc13.4.0-software.tar.gz
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
      "aws s3 cp s3://vantagecompute-slurm-builds/slurm-25.05-gcc13.4.0-software.tar.gz /tmp/",
      "sudo mkdir -p /opt/slurm",
      "sudo tar -xzf /tmp/slurm-25.05-gcc13.4.0-software.tar.gz -C /opt/slurm",
      "sudo cp -r /opt/slurm/modules/slurm /opt/modulefiles/"
    ]
  }
}
```

## See Also

- [Deployment Guide](/slurm-factory/deployment/) - Detailed deployment instructions
- [Architecture](/slurm-factory/architecture/) - How packages are built
- [Examples](/slurm-factory/examples/) - Usage examples and patterns
