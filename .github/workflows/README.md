# GitHub Actions Workflows for Buildcache Publishing

This directory contains GitHub Actions workflows for building and publishing Slurm and compiler packages to S3 buildcache.

## Available Workflows

### 1. Build and Publish Compiler Buildcache
**File:** `build-and-publish-compiler-buildcache.yml`

Builds and publishes GCC compiler binaries to S3 buildcache for reuse across builds.

**Inputs:**
- `compiler_versions`: Compiler versions to build (comma-separated or "all")
  - Default: `all`
  - Example: `"13.4.0,11.5.0"` or `"all"`

**Supported Compiler Versions:**
- 14.2.0, 13.4.0, 12.5.0, 11.5.0, 10.5.0, 9.5.0, 8.5.0, 7.5.0

**Build Command:**
```bash
slurm-factory build-compiler --compiler-version <version> --publish
```

**Buildcache Location:**
- S3: `s3://slurm-factory-spack-buildcache-4b670/compilers/<version>/buildcache`
- CloudFront: `https://slurm-factory-spack-binary-cache.vantagecompute.ai/compilers/<version>/buildcache`

---

### 2. Build and Publish Slurm Dependencies for All Compilers
**File:** `build-and-publish-slurm-deps-all-compilers.yml`

Builds and publishes **only** Slurm dependencies (excluding Slurm itself) to S3 buildcache. This creates a matrix build across Slurm versions and compiler versions.

**Inputs:**
- `slurm_versions`: Slurm versions to build dependencies for (comma-separated or "all")
  - Default: `all`
  - Example: `"25.05,24.11"` or `"all"`
- `compiler_versions`: Compiler versions to use (comma-separated or "all")
  - Default: `all`
  - Example: `"13.4.0,11.5.0"` or `"all"`

**Supported Slurm Versions:**
- 25.05, 24.11, 23.11, 23.02

**Build Command:**
```bash
slurm-factory build \
  --slurm-version <slurm_version> \
  --compiler-version <compiler_version> \
  --publish=deps
```

**Buildcache Location:**
- S3: `s3://slurm-factory-spack-buildcache-4b670/slurm/<slurm_version>/<compiler_version>/buildcache`
- CloudFront: `https://slurm-factory-spack-binary-cache.vantagecompute.ai/slurm/<slurm_version>/<compiler_version>/buildcache`

**Use Case:**
- Pre-build dependencies for faster Slurm builds
- Share common dependencies across multiple builds
- Reduce build times by caching heavy dependencies like OpenMPI, OpenSSL, etc.

---

### 3. Build and Publish All Slurm Packages (Slurm + Dependencies)
**File:** `build-and-publish-all-packages.yml`

Builds and publishes **both** Slurm and all its dependencies to S3 buildcache. This creates a complete buildcache that can be used for binary installations.

**Inputs:**
- `slurm_versions`: Slurm versions to build (comma-separated or "all")
  - Default: `25.05`
  - Example: `"25.05,24.11"` or `"all"`
- `compiler_versions`: Compiler versions to use (comma-separated or "all")
  - Default: `13.4.0`
  - Example: `"13.4.0,11.5.0"` or `"all"`
- `build_type`: Build type
  - Default: `default`
  - Options: `default`, `gpu`, `minimal`

**Build Command:**
```bash
slurm-factory build \
  --slurm-version <slurm_version> \
  --compiler-version <compiler_version> \
  [--gpu | --minimal] \
  --publish=all
```

**Buildcache Location:**
- S3: `s3://slurm-factory-spack-buildcache-4b670/slurm/<slurm_version>/<compiler_version>/buildcache`
- CloudFront: `https://slurm-factory-spack-binary-cache.vantagecompute.ai/slurm/<slurm_version>/<compiler_version>/buildcache`

**Use Case:**
- Create complete binary distributions
- Enable fast binary installations of Slurm
- Support air-gapped or network-constrained environments

---

## Workflow Execution Strategy

All workflows use **matrix builds** to parallelize builds across different versions:

- **Compiler workflow**: Builds multiple compiler versions in parallel
- **Dependencies workflow**: Builds a matrix of (Slurm version × Compiler version)
- **All packages workflow**: Builds a matrix of (Slurm version × Compiler version)

The workflows use `fail-fast: false` to ensure all combinations are attempted even if some fail.

## Build Timeouts

- Compiler builds: 360 minutes (6 hours)
- Slurm dependencies: 480 minutes (8 hours)
- All packages: 480 minutes (8 hours)

## Environment Requirements

All workflows require:
- **Runner**: `self-hosted` (for performance and disk space)
- **Environment**: `release` (for secrets and protection rules)
- **Permissions**:
  - `contents: read` - Read repository contents
  - `id-token: write` - AWS OIDC authentication

## AWS Integration

Workflows use AWS OIDC authentication via:
```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
    aws-region: us-east-1
```

AWS credentials are passed to Docker containers for `spack buildcache push` operations.

## Testing

Each workflow includes:
1. **Build verification**: Checks that build completed successfully
2. **Buildcache upload verification**: Lists S3 contents to verify upload
3. **Installation test**: Attempts to install from buildcache to verify functionality
4. **Summary**: Generates GitHub Actions summary with build details and usage instructions

## Usage Examples

### Running Workflows Manually

#### Build all compilers:
```bash
# Via GitHub UI: Actions → "Build and Publish Compiler Buildcache to S3" → Run workflow
# Input: compiler_versions = "all"
```

#### Build dependencies for specific versions:
```bash
# Via GitHub UI: Actions → "Build and Publish Slurm Dependencies for All Compilers" → Run workflow
# Input: slurm_versions = "25.05,24.11"
# Input: compiler_versions = "13.4.0,11.5.0"
```

#### Build complete packages:
```bash
# Via GitHub UI: Actions → "Build and Publish All Slurm Packages" → Run workflow
# Input: slurm_versions = "25.05"
# Input: compiler_versions = "13.4.0"
# Input: build_type = "default"
```

### Using Published Buildcaches

After workflows complete, use buildcaches in Spack:

```bash
# Add compiler buildcache
spack mirror add compiler-buildcache \
  https://slurm-factory-spack-binary-cache.vantagecompute.ai/compilers/13.4.0/buildcache

# Add Slurm buildcache
spack mirror add slurm-buildcache \
  https://slurm-factory-spack-binary-cache.vantagecompute.ai/slurm/25.05/13.4.0/buildcache

# Install from buildcache
spack install --no-check-signature gcc@13.4.0
spack install --no-check-signature slurm@25.05
```

## Monitoring

Each workflow provides:
- Real-time build logs in GitHub Actions UI
- Build summaries with buildcache locations
- S3 bucket listings to verify uploads
- Installation tests to verify buildcache functionality
