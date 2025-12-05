# GitHub Actions CI/CD

Slurm Factory uses GitHub Actions for continuous integration, testing, and automated builds. The workflows maintain the public buildcache, publish releases, and ensure code quality.

## Overview

The CI/CD system consists of:

- **Slurm Dependencies Build** - Build and publish Slurm dependencies for each OS toolchain
- **Slurm Build** - Build and publish Slurm packages for each version × toolchain combination
- **Continuous Integration** - Run tests, linters, and type checking
- **Documentation** - Auto-deploy documentation to GitHub Pages

## Workflows

### 1. Slurm Dependencies Buildcache (`build-and-publish-slurm-dependencies.yml`)

**Purpose**: Build Slurm dependencies (OpenMPI, PMIx, Munge, etc.) and publish to Spack buildcache for all OS toolchains.

**Trigger**: Manual workflow dispatch

**Workflow Diagram**:

\`\`\`mermaid
flowchart TD
    Start([Workflow Dispatch]) --> PrepareMatrix[Prepare Toolchain Matrix]
    PrepareMatrix --> Matrix{Matrix Build<br/>6 Toolchains}
    
    Matrix -->|resolute| Build1[Build Deps - Ubuntu 25.04]
    Matrix -->|noble| Build2[Build Deps - Ubuntu 24.04]
    Matrix -->|jammy| Build3[Build Deps - Ubuntu 22.04]
    Matrix -->|rockylinux10| Build4[Build Deps - Rocky 10]
    Matrix -->|rockylinux9| Build5[Build Deps - Rocky 9]
    Matrix -->|rockylinux8| Build6[Build Deps - Rocky 8]
    
    Build1 --> Docker1[Docker Build<br/>Spack Container]
    Build2 --> Docker2[Docker Build<br/>Spack Container]
    Build3 --> Docker3[Docker Build<br/>Spack Container]
    Build4 --> Docker4[Docker Build<br/>Spack Container]
    Build5 --> Docker5[Docker Build<br/>Spack Container]
    Build6 --> Docker6[Docker Build<br/>Spack Container]
    
    Docker1 --> SpackBuild1[Spack Build<br/>All Dependencies]
    Docker2 --> SpackBuild2[Spack Build<br/>All Dependencies]
    Docker3 --> SpackBuild3[Spack Build<br/>All Dependencies]
    Docker4 --> SpackBuild4[Spack Build<br/>All Dependencies]
    Docker5 --> SpackBuild5[Spack Build<br/>All Dependencies]
    Docker6 --> SpackBuild6[Spack Build<br/>All Dependencies]
    
    SpackBuild1 --> Sign1[GPG Sign<br/>All Packages]
    SpackBuild2 --> Sign2[GPG Sign<br/>All Packages]
    SpackBuild3 --> Sign3[GPG Sign<br/>All Packages]
    SpackBuild4 --> Sign4[GPG Sign<br/>All Packages]
    SpackBuild5 --> Sign5[GPG Sign<br/>All Packages]
    SpackBuild6 --> Sign6[GPG Sign<br/>All Packages]
    
    Sign1 --> Upload1[Upload to S3<br/>resolute/slurm/deps/]
    Sign2 --> Upload2[Upload to S3<br/>noble/slurm/deps/]
    Sign3 --> Upload3[Upload to S3<br/>jammy/slurm/deps/]
    Sign4 --> Upload4[Upload to S3<br/>rockylinux10/slurm/deps/]
    Sign5 --> Upload5[Upload to S3<br/>rockylinux9/slurm/deps/]
    Sign6 --> Upload6[Upload to S3<br/>rockylinux8/slurm/deps/]
    
    Upload1 --> End1([Success])
    Upload2 --> End2([Success])
    Upload3 --> End3([Success])
    Upload4 --> End4([Success])
    Upload5 --> End5([Success])
    Upload6 --> End6([Success])
    
    style Start fill:#4CAF50
    style End1 fill:#2196F3
    style End2 fill:#2196F3
    style End3 fill:#2196F3
    style End4 fill:#2196F3
    style End5 fill:#2196F3
    style End6 fill:#2196F3
\`\`\`

**Configuration**:
\`\`\`yaml
name: Build and Publish Slurm Dependencies for All Toolchains

on:
  workflow_dispatch:
    inputs:
      toolchain_versions:
        description: 'Toolchain versions (comma-separated or "all")'
        required: true
        default: 'all'
        type: string

env:
  S3_BUCKET: slurm-factory-spack-buildcache-4b670
  CLOUDFRONT_URL: https://slurm-factory-spack-binary-cache.vantagecompute.ai
\`\`\`

**Toolchains**:

| Toolchain | OS/Distribution | System GCC | Use Case |
|-----------|-----------------|------------|----------|
| **resolute** | Ubuntu 25.04 | 15.2.0 | Latest features |
| **noble** | Ubuntu 24.04 | 13.2.0 | **Recommended** |
| **jammy** | Ubuntu 22.04 | 11.4.0 | LTS |
| **rockylinux10** | Rocky Linux 10 | 14.3.1 | RHEL 10 |
| **rockylinux9** | Rocky Linux 9 | 11.4.1 | RHEL 9 |
| **rockylinux8** | Rocky Linux 8 | 8.5.0 | RHEL 8 |

**Outputs**:
- Dependencies buildcache at: \`s3://slurm-factory-spack-buildcache-4b670/{toolchain}/slurm/deps/\`
- Accessible via: \`https://slurm-factory-spack-binary-cache.vantagecompute.ai/{toolchain}/slurm/deps/\`

### 2. Slurm Buildcache (`build-and-publish-slurm.yml`)

**Purpose**: Build Slurm packages for all version × toolchain combinations and publish to buildcache.

**Trigger**: Manual workflow dispatch

**Workflow Diagram**:

\`\`\`mermaid
flowchart TD
    Start([Workflow Dispatch]) --> PrepareMatrix[Prepare Matrix<br/>Slurm × Toolchain]
    
    PrepareMatrix --> Matrix{Matrix Build<br/>3 Slurm × 6 Toolchains = 18 combinations}
    
    Matrix --> Build1[Slurm 25.11 + noble]
    Matrix --> Build2[Slurm 25.11 + jammy]
    Matrix --> Build3[Slurm 24.11 + noble]
    Matrix --> BuildN[... 18 combinations ...]
    
    Build1 --> Docker1[Docker Build<br/>Spack Container]
    Build2 --> Docker2[Docker Build<br/>Spack Container]
    Build3 --> Docker3[Docker Build<br/>Spack Container]
    BuildN --> DockerN[Docker Build<br/>Spack Container]
    
    Docker1 --> DepsCache1[Pull Dependencies<br/>from Buildcache]
    Docker2 --> DepsCache2[Pull Dependencies<br/>from Buildcache]
    Docker3 --> DepsCache3[Pull Dependencies<br/>from Buildcache]
    DockerN --> DepsCacheN[Pull Dependencies<br/>from Buildcache]
    
    DepsCache1 --> SpackBuild1[Spack Build<br/>Slurm]
    DepsCache2 --> SpackBuild2[Spack Build<br/>Slurm]
    DepsCache3 --> SpackBuild3[Spack Build<br/>Slurm]
    DepsCacheN --> SpackBuildN[Spack Build<br/>Slurm]
    
    SpackBuild1 --> Sign1[GPG Sign<br/>Packages]
    SpackBuild2 --> Sign2[GPG Sign<br/>Packages]
    SpackBuild3 --> Sign3[GPG Sign<br/>Packages]
    SpackBuildN --> SignN[GPG Sign<br/>Packages]
    
    Sign1 --> Upload1[Upload to S3<br/>noble/slurm/25.11/]
    Sign2 --> Upload2[Upload to S3<br/>jammy/slurm/25.11/]
    Sign3 --> Upload3[Upload to S3<br/>noble/slurm/24.11/]
    SignN --> UploadN[Upload to S3<br/>{toolchain}/slurm/{version}/]
    
    Upload1 --> End1([Success])
    Upload2 --> End2([Success])
    Upload3 --> End3([Success])
    UploadN --> EndN([Success])
    
    style Start fill:#4CAF50
    style End1 fill:#2196F3
    style End2 fill:#2196F3
    style End3 fill:#2196F3
    style EndN fill:#2196F3
    style Matrix fill:#FF9800
\`\`\`

**Configuration**:
\`\`\`yaml
name: Build and Publish Slurm

on:
  workflow_dispatch:
    inputs:
      slurm_versions:
        description: 'Slurm versions (comma-separated or "all")'
        required: true
        default: 'all'
      toolchains:
        description: 'Toolchains (comma-separated or "all")'
        required: true
        default: 'all'

env:
  S3_BUCKET: slurm-factory-spack-buildcache-4b670
  CLOUDFRONT_URL: https://slurm-factory-spack-binary-cache.vantagecompute.ai
\`\`\`

**Matrix Strategy**:
- Cartesian product: Slurm versions × Toolchains
- Default: 3 Slurm versions × 6 toolchains = **18 parallel builds**
- Each combination runs independently
- Uses self-hosted runners for performance

**Slurm Versions**:
- \`25.11\` - Latest
- \`24.11\` - LTS
- \`23.11\` - Stable

**Outputs**:
- Buildcache at: \`s3://slurm-factory-spack-buildcache-4b670/{toolchain}/slurm/{version}/\`
- Accessible via: \`https://slurm-factory-spack-binary-cache.vantagecompute.ai/{toolchain}/slurm/{version}/\`
- Includes: Slurm, OpenMPI, PMIx, Munge, OpenSSL, HDF5, and all dependencies

### 3. CI Tests (`ci.yml`)

**Purpose**: Run linters, type checking, and unit tests on every pull request.

**Trigger**: Pull requests to \`main\` branch

**Jobs**:

1. **commitlint**: Validate commit messages follow Conventional Commits
2. **ci-tests**: Run linters, type checker, and unit tests

**Steps**:
\`\`\`yaml
- Checkout code
- Install just (task runner)
- Install uv (package manager)
- Run linters (ruff, codespell)
- Run type checker (pyright)
- Run unit tests (pytest)
\`\`\`

**Requirements**:
- All tests must pass before PR can be merged
- Commit messages must follow \`type(scope): message\` format
- Code coverage threshold: 80%

### 4. Documentation Deploy (`update-docs.yml`)

**Purpose**: Build and deploy Docusaurus documentation to GitHub Pages.

**Trigger**: Push to \`main\` branch or manual dispatch

**Steps**:
1. Checkout repository with full history
2. Setup Node.js LTS
3. Install Docusaurus dependencies
4. Build documentation
5. Deploy to GitHub Pages

**Output**: https://vantagecompute.github.io/slurm-factory

### 5. PyPI Publish (`publish.yml`)

**Purpose**: Publish slurm-factory package to PyPI on tagged releases.

**Trigger**: Push of version tags (e.g., \`v1.0.0\`)

**Steps**:
1. Checkout code
2. Setup Python and uv
3. Build package with \`uv build\`
4. Publish to PyPI

## Build Process Diagrams

### Slurm Build Process

\`\`\`mermaid
flowchart TB
    Start([slurm-factory build-slurm]) --> Docker[Create Docker<br/>Container]
    Docker --> Base[Base Image<br/>Ubuntu/Rocky]
    Base --> Spack[Install Spack<br/>v1.0.0]
    Spack --> CustomRepo[Add Custom<br/>Spack Repo]
    
    CustomRepo --> DepsCache{Dependencies<br/>in Buildcache?}
    
    DepsCache -->|Yes| PullDeps[Pull Dependencies<br/>from Buildcache]
    DepsCache -->|Partial| MixedBuild[Pull Some,<br/>Build Others]
    DepsCache -->|No| BuildDeps[Build All<br/>Dependencies]
    
    PullDeps --> BuildSlurm[Build Slurm<br/>from Source]
    MixedBuild --> BuildSlurm
    BuildDeps --> BuildSlurm
    
    BuildSlurm --> CreateView[Create Spack View<br/>Unified Tree]
    CreateView --> Modules[Generate Lmod<br/>Modulefile]
    Modules --> InstallScript[Add Install Script<br/>& Configs]
    InstallScript --> Tarball[Create Tarball<br/>view/ + modules/ + data/]
    
    Tarball --> PublishOpt{Publish<br/>Buildcache?}
    
    PublishOpt -->|all| SignAll[GPG Sign<br/>All Packages]
    PublishOpt -->|slurm-only| SignSlurm[GPG Sign<br/>Slurm Only]
    PublishOpt -->|no| NoSign[Skip Signing]
    
    SignAll --> UploadAll[Upload All to<br/>S3 Buildcache]
    SignSlurm --> UploadSlurm[Upload Slurm to<br/>S3 Buildcache]
    NoSign --> SkipUpload[No Upload]
    
    UploadAll --> Output[Output Tarball<br/>~/.slurm-factory/builds/]
    UploadSlurm --> Output
    SkipUpload --> Output
    
    Output --> Done([Complete])
    
    style Start fill:#4CAF50
    style Done fill:#2196F3
    style DepsCache fill:#FF9800
    style PublishOpt fill:#FF9800
\`\`\`

## Self-Hosted Runners

The build workflows use **self-hosted runners** for:

- **Performance**: Direct access to high-performance hardware
- **Cost**: No GitHub Actions minutes consumed
- **Docker**: Pre-installed Docker for builds
- **Storage**: Large disk space for build artifacts and caches
- **Network**: Fast network for S3 uploads

**Runner Specifications**:
- **CPU**: 16+ cores
- **RAM**: 32+ GB
- **Disk**: 500+ GB SSD
- **OS**: Ubuntu 24.04 LTS
- **Docker**: 24.0+

## Secrets and Variables

### Repository Secrets

| Secret | Purpose | Used By |
|--------|---------|---------|
| \`AWS_ROLE_ARN\` | GitHub Actions IAM role ARN | All build workflows |
| \`GPG_PRIVATE_KEY\` | GPG private key for signing | Slurm builds |
| \`GPG_KEY_ID\` | GPG key ID | Slurm builds |

### Environment Variables

| Variable | Value | Purpose |
|----------|-------|---------|
| \`S3_BUCKET\` | \`slurm-factory-spack-buildcache-4b670\` | Buildcache S3 bucket |
| \`CLOUDFRONT_URL\` | \`https://slurm-factory-spack-binary-cache.vantagecompute.ai\` | Public CDN URL |

## Buildcache URL Structure

The buildcache is organized by toolchain first, then by type:

\`\`\`
{CLOUDFRONT_URL}/
├── noble/                          # Ubuntu 24.04 toolchain
│   └── slurm/
│       ├── deps/                   # Shared dependencies
│       │   └── build_cache/        # Spack binary cache
│       ├── 25.11/                  # Slurm 25.11 packages
│       │   └── build_cache/
│       ├── 24.11/                  # Slurm 24.11 packages
│       │   └── build_cache/
│       └── 23.11/                  # Slurm 23.11 packages
│           └── build_cache/
├── jammy/                          # Ubuntu 22.04 toolchain
│   └── slurm/
│       ├── deps/
│       ├── 25.11/
│       ├── 24.11/
│       └── 23.11/
├── resolute/                       # Ubuntu 25.04 toolchain
│   └── slurm/...
├── rockylinux10/                   # Rocky Linux 10 toolchain
│   └── slurm/...
├── rockylinux9/                    # Rocky Linux 9 toolchain
│   └── slurm/...
└── rockylinux8/                    # Rocky Linux 8 toolchain
    └── slurm/...
\`\`\`

## Monitoring and Notifications

### Workflow Status

Monitor workflow runs at:
https://github.com/vantagecompute/slurm-factory/actions

### Notifications

Failed workflows generate:
- GitHub status checks on PRs
- Email notifications to repository admins

### Build Logs

All build logs are retained for:
- **90 days** for workflow runs
- **Indefinitely** for releases

## Troubleshooting

### Workflow Failures

Check the workflow run logs for:
1. **Build errors**: Look for compilation failures
2. **Upload errors**: Check AWS credentials and permissions
3. **Test failures**: Review test output for issues

### Re-running Failed Jobs

\`\`\`bash
# Re-run Slurm build for specific combination
gh workflow run build-and-publish-slurm.yml \\
  -f slurm_versions="25.11" \\
  -f toolchains="noble"

# Re-run dependencies build for specific toolchain
gh workflow run build-and-publish-slurm-dependencies.yml \\
  -f toolchain_versions="noble"

# Re-run entire workflow
gh run rerun <run-id>
\`\`\`

### Debugging Locally

Test workflows locally with [act](https://github.com/nektos/act):

\`\`\`bash
# Install act
brew install act  # macOS
# or
sudo snap install act  # Linux

# Run CI workflow locally
act pull_request
\`\`\`

## Best Practices

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

\`\`\`
feat: add new feature
fix: fix bug
docs: update documentation
chore: update dependencies
ci: update CI workflow
\`\`\`

### Pull Requests

1. Create feature branch
2. Make changes
3. Run \`just lint\` and \`just unit\`
4. Push and create PR
5. Wait for CI to pass
6. Request review
7. Merge after approval

### Release Process

1. Update version in \`pyproject.toml\`
2. Update \`CHANGELOG.md\`
3. Create git tag: \`git tag v1.0.0\`
4. Push tag: \`git push origin v1.0.0\`
5. GitHub Actions will create release
6. Publish to PyPI: \`uv build && uv publish\`

## See Also

- [Infrastructure](./infrastructure.md) - AWS infrastructure details
- [Slurm Factory Spack Build Cache](./slurm-factory-spack-build-cache.md) - Using the buildcache
- [Contributing](./contributing.md) - Development guide
- [Architecture](./architecture.md) - Build system overview
