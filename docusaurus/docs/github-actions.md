# GitHub Actions CI/CD

Slurm Factory uses GitHub Actions for continuous integration, testing, and automated builds. The workflows maintain the public buildcache, publish releases, and ensure code quality.

## Overview

The CI/CD system consists of:

- **Compiler Builds** - Build and publish GCC toolchains to buildcache
- **Slurm Builds** - Build and publish Slurm packages with all dependencies
- **Tarball Publishing** - Create relocatable tarballs and upload to S3
- **Continuous Integration** - Run tests, linters, and type checking
- **Documentation** - Auto-deploy documentation to GitHub Pages

## Workflows

### 1. Compiler Buildcache (`build-and-publish-compiler-buildcache.yml`)

**Purpose**: Build GCC compiler toolchains and publish to Spack buildcache

**Trigger**: Manual workflow dispatch

**Workflow Diagram**:

```mermaid
flowchart TD
    Start([Workflow Dispatch]) --> PrepareMatrix[Prepare Compiler Matrix]
    PrepareMatrix --> Matrix{Matrix Build}
    
    Matrix -->|GCC 15.2.0| Build1[Build Compiler 15.2.0]
    Matrix -->|GCC 14.2.0| Build2[Build Compiler 14.2.0]
    Matrix -->|GCC 13.4.0| Build3[Build Compiler 13.4.0]
    Matrix -->|GCC 12.5.0| Build4[Build Compiler 12.5.0]
    Matrix -->|GCC 11.5.0| Build5[Build Compiler 11.5.0]
    Matrix -->|GCC 10.5.0| Build6[Build Compiler 10.5.0]
    Matrix -->|GCC 9.5.0| Build7[Build Compiler 9.5.0]
    Matrix -->|GCC 8.5.0| Build8[Build Compiler 8.5.0]
    Matrix -->|GCC 7.5.0| Build9[Build Compiler 7.5.0]
    
    Build1 --> Steps1[Build Steps]
    Build2 --> Steps2[Build Steps]
    Build3 --> Steps3[Build Steps]
    Build4 --> Steps4[Build Steps]
    Build5 --> Steps5[Build Steps]
    Build6 --> Steps6[Build Steps]
    Build7 --> Steps7[Build Steps]
    Build8 --> Steps8[Build Steps]
    Build9 --> Steps9[Build Steps]
    
    Steps1 --> Checkout1[Checkout Code]
    Steps2 --> Checkout2[Checkout Code]
    Steps3 --> Checkout3[Checkout Code]
    Steps4 --> Checkout4[Checkout Code]
    Steps5 --> Checkout5[Checkout Code]
    Steps6 --> Checkout6[Checkout Code]
    Steps7 --> Checkout7[Checkout Code]
    Steps8 --> Checkout8[Checkout Code]
    Steps9 --> Checkout9[Checkout Code]
    
    Checkout1 --> SetupPython1[Setup Python]
    Checkout2 --> SetupPython2[Setup Python]
    Checkout3 --> SetupPython3[Setup Python]
    Checkout4 --> SetupPython4[Setup Python]
    Checkout5 --> SetupPython5[Setup Python]
    Checkout6 --> SetupPython6[Setup Python]
    Checkout7 --> SetupPython7[Setup Python]
    Checkout8 --> SetupPython8[Setup Python]
    Checkout9 --> SetupPython9[Setup Python]
    
    SetupPython1 --> OIDC1[AWS OIDC Auth]
    SetupPython2 --> OIDC2[AWS OIDC Auth]
    SetupPython3 --> OIDC3[AWS OIDC Auth]
    SetupPython4 --> OIDC4[AWS OIDC Auth]
    SetupPython5 --> OIDC5[AWS OIDC Auth]
    SetupPython6 --> OIDC6[AWS OIDC Auth]
    SetupPython7 --> OIDC7[AWS OIDC Auth]
    SetupPython8 --> OIDC8[AWS OIDC Auth]
    SetupPython9 --> OIDC9[AWS OIDC Auth]
    
    OIDC1 --> BuildCompiler1[slurm-factory build-compiler]
    OIDC2 --> BuildCompiler2[slurm-factory build-compiler]
    OIDC3 --> BuildCompiler3[slurm-factory build-compiler]
    OIDC4 --> BuildCompiler4[slurm-factory build-compiler]
    OIDC5 --> BuildCompiler5[slurm-factory build-compiler]
    OIDC6 --> BuildCompiler6[slurm-factory build-compiler]
    OIDC7 --> BuildCompiler7[slurm-factory build-compiler]
    OIDC8 --> BuildCompiler8[slurm-factory build-compiler]
    OIDC9 --> BuildCompiler9[slurm-factory build-compiler]
    
    BuildCompiler1 --> Sign1[GPG Sign Packages]
    BuildCompiler2 --> Sign2[GPG Sign Packages]
    BuildCompiler3 --> Sign3[GPG Sign Packages]
    BuildCompiler4 --> Sign4[GPG Sign Packages]
    BuildCompiler5 --> Sign5[GPG Sign Packages]
    BuildCompiler6 --> Sign6[GPG Sign Packages]
    BuildCompiler7 --> Sign7[GPG Sign Packages]
    BuildCompiler8 --> Sign8[GPG Sign Packages]
    BuildCompiler9 --> Sign9[GPG Sign Packages]
    
    Sign1 --> Upload1[Upload to S3 Buildcache]
    Sign2 --> Upload2[Upload to S3 Buildcache]
    Sign3 --> Upload3[Upload to S3 Buildcache]
    Sign4 --> Upload4[Upload to S3 Buildcache]
    Sign5 --> Upload5[Upload to S3 Buildcache]
    Sign6 --> Upload6[Upload to S3 Buildcache]
    Sign7 --> Upload7[Upload to S3 Buildcache]
    Sign8 --> Upload8[Upload to S3 Buildcache]
    Sign9 --> Upload9[Upload to S3 Buildcache]
    
    Upload1 --> Test1[Test Installation]
    Upload2 --> Test2[Test Installation]
    Upload3 --> Test3[Test Installation]
    Upload4 --> Test4[Test Installation]
    Upload5 --> Test5[Test Installation]
    Upload6 --> Test6[Test Installation]
    Upload7 --> Test7[Test Installation]
    Upload8 --> Test8[Test Installation]
    Upload9 --> Test9[Test Installation]
    
    Test1 --> End1([Success])
    Test2 --> End2([Success])
    Test3 --> End3([Success])
    Test4 --> End4([Success])
    Test5 --> End5([Success])
    Test6 --> End6([Success])
    Test7 --> End7([Success])
    Test8 --> End8([Success])
    Test9 --> End9([Success])
    
    style Start fill:#4CAF50
    style End1 fill:#2196F3
    style End2 fill:#2196F3
    style End3 fill:#2196F3
    style End4 fill:#2196F3
    style End5 fill:#2196F3
    style End6 fill:#2196F3
    style End7 fill:#2196F3
    style End8 fill:#2196F3
    style End9 fill:#2196F3
```

**Configuration**:
```yaml
name: Build and Publish Compiler Buildcache to S3

on:
  workflow_dispatch:
    inputs:
      compiler_versions:
        description: 'Compiler versions (comma-separated or "all")'
        required: true
        default: 'all'
        type: string

env:
  S3_BUCKET: slurm-factory-spack-buildcache-4b670
  CLOUDFRONT_URL: https://slurm-factory-spack-binary-cache.vantagecompute.ai
```

**Matrix Strategy**:
- Builds all requested compiler versions in parallel
- Each build is independent and can succeed/fail separately
- Uses self-hosted runners for performance
- 6-hour timeout per compiler build

**Key Steps**:
1. **Checkout**: Get latest code from repository
2. **Setup Python**: Install Python from `pyproject.toml` version
3. **Install uv**: Fast Python package manager
4. **Clean**: Remove previous build artifacts
5. **AWS OIDC**: Authenticate with AWS using GitHub OIDC
6. **Validate GPG**: Ensure signing keys are configured
7. **Build Compiler**: Run `slurm-factory build-compiler --publish`
8. **Sign Packages**: GPG sign all buildcache packages
9. **Upload to S3**: Sync buildcache to S3 bucket
10. **Test**: Install compiler from buildcache and verify

**Outputs**:
- Compiler buildcache at: `s3://slurm-factory-spack-buildcache-4b670/compilers/{version}/buildcache`
- Accessible via: `https://slurm-factory-spack-binary-cache.vantagecompute.ai/compilers/{version}/buildcache`

### 2. Slurm Dependencies Buildcache (`build-and-publish-slurm-all.yml`)

**Purpose**: Build Slurm packages with all dependencies for all compiler combinations

**Trigger**: Manual workflow dispatch

**Workflow Diagram**:

```mermaid
flowchart TD
    Start([Workflow Dispatch]) --> PrepareMatrix[Prepare Matrix<br/>Slurm × Compiler]
    
    PrepareMatrix --> Matrix{Matrix Build<br/>4 Slurm × 8 Compilers = 32 combinations}
    
    Matrix --> Build1[Slurm 25.11 + GCC 14.2.0]
    Matrix --> Build2[Slurm 25.11 + GCC 13.4.0]
    Matrix --> Build3[Slurm 25.11 + GCC 12.5.0]
    Matrix --> BuildN[... 32 combinations ...]
    
    Build1 --> Steps1[Build Steps]
    Build2 --> Steps2[Build Steps]
    Build3 --> Steps3[Build Steps]
    BuildN --> StepsN[Build Steps]
    
    Steps1 --> Checkout1[Checkout Code]
    Steps2 --> Checkout2[Checkout Code]
    Steps3 --> Checkout3[Checkout Code]
    StepsN --> CheckoutN[Checkout Code]
    
    Checkout1 --> OIDC1[AWS OIDC Auth]
    Checkout2 --> OIDC2[AWS OIDC Auth]
    Checkout3 --> OIDC3[AWS OIDC Auth]
    CheckoutN --> OIDCN[AWS OIDC Auth]
    
    OIDC1 --> BuildSlurm1[slurm-factory build<br/>--publish=all --gpu]
    OIDC2 --> BuildSlurm2[slurm-factory build<br/>--publish=all --gpu]
    OIDC3 --> BuildSlurm3[slurm-factory build<br/>--publish=all --gpu]
    OIDCN --> BuildSlurmN[slurm-factory build<br/>--publish=all --gpu]
    
    BuildSlurm1 --> Docker1[Docker Build<br/>Spack Container]
    BuildSlurm2 --> Docker2[Docker Build<br/>Spack Container]
    BuildSlurm3 --> Docker3[Docker Build<br/>Spack Container]
    BuildSlurmN --> DockerN[Docker Build<br/>Spack Container]
    
    Docker1 --> CompilerCache1[Pull Compiler<br/>from Buildcache]
    Docker2 --> CompilerCache2[Pull Compiler<br/>from Buildcache]
    Docker3 --> CompilerCache3[Pull Compiler<br/>from Buildcache]
    DockerN --> CompilerCacheN[Pull Compiler<br/>from Buildcache]
    
    CompilerCache1 --> SpackBuild1[Spack Build<br/>Slurm + Deps]
    CompilerCache2 --> SpackBuild2[Spack Build<br/>Slurm + Deps]
    CompilerCache3 --> SpackBuild3[Spack Build<br/>Slurm + Deps]
    CompilerCacheN --> SpackBuildN[Spack Build<br/>Slurm + Deps]
    
    SpackBuild1 --> Sign1[GPG Sign<br/>All Packages]
    SpackBuild2 --> Sign2[GPG Sign<br/>All Packages]
    SpackBuild3 --> Sign3[GPG Sign<br/>All Packages]
    SpackBuildN --> SignN[GPG Sign<br/>All Packages]
    
    Sign1 --> Upload1[Upload to S3<br/>Buildcache]
    Sign2 --> Upload2[Upload to S3<br/>Buildcache]
    Sign3 --> Upload3[Upload to S3<br/>Buildcache]
    SignN --> UploadN[Upload to S3<br/>Buildcache]
    
    Upload1 --> Test1[Test Install<br/>from Buildcache]
    Upload2 --> Test2[Test Install<br/>from Buildcache]
    Upload3 --> Test3[Test Install<br/>from Buildcache]
    UploadN --> TestN[Test Install<br/>from Buildcache]
    
    Test1 --> End1([Success])
    Test2 --> End2([Success])
    Test3 --> End3([Success])
    TestN --> EndN([Success])
    
    style Start fill:#4CAF50
    style End1 fill:#2196F3
    style End2 fill:#2196F3
    style End3 fill:#2196F3
    style EndN fill:#2196F3
    style Matrix fill:#FF9800
```

**Configuration**:
```yaml
name: Build and Publish Slurm Dependencies for All Compilers

on:
  workflow_dispatch:
    inputs:
      slurm_versions:
        description: 'Slurm versions (comma-separated or "all")'
        required: true
        default: 'all'
      compiler_versions:
        description: 'Compiler versions (comma-separated or "all")'
        required: true
        default: 'all'
```

**Matrix Strategy**:
- Cartesian product: Slurm versions × Compiler versions
- Default: 4 Slurm versions × 8 compilers = **32 parallel builds**
- Each combination runs independently
- 8-hour timeout per build (GPU builds can be slow)

**Build Options**:
- `--gpu`: Include CUDA/ROCm support (~180 packages)
- `--publish=all`: Publish all dependencies to buildcache
- `--no-cache`: Force fresh Docker build

**Outputs**:
- Buildcache at: `s3://slurm-factory-spack-buildcache-4b670/slurm/{slurm_version}/{compiler_version}/buildcache`
- Includes: Slurm, OpenMPI, PMIx, Munge, OpenSSL, HDF5, CUDA, and all dependencies

### 3. Slurm Tarball Publishing (`build-and-publish-slurm-tarball.yml`)

**Purpose**: Build complete Slurm tarballs and publish to public S3 bucket

**Trigger**: Manual workflow dispatch

**Workflow Diagram**:

```mermaid
flowchart TD
    Start([Workflow Dispatch<br/>Select Slurm Version]) --> Matrix{Matrix Build<br/>8 Compiler Versions}
    
    Matrix --> Build1[GCC 14.2.0]
    Matrix --> Build2[GCC 13.4.0]
    Matrix --> Build3[GCC 12.5.0]
    Matrix --> Build4[GCC 11.5.0]
    Matrix --> Build5[GCC 10.5.0]
    Matrix --> Build6[GCC 9.5.0]
    Matrix --> Build7[GCC 8.5.0]
    Matrix --> Build8[GCC 7.5.0]
    
    Build1 --> Steps1[Build Steps]
    Build2 --> Steps2[Build Steps]
    Build3 --> Steps3[Build Steps]
    Build4 --> Steps4[Build Steps]
    Build5 --> Steps5[Build Steps]
    Build6 --> Steps6[Build Steps]
    Build7 --> Steps7[Build Steps]
    Build8 --> Steps8[Build Steps]
    
    Steps1 --> Clean1[Clean Previous Builds]
    Steps2 --> Clean2[Clean Previous Builds]
    Steps3 --> Clean3[Clean Previous Builds]
    Steps4 --> Clean4[Clean Previous Builds]
    Steps5 --> Clean5[Clean Previous Builds]
    Steps6 --> Clean6[Clean Previous Builds]
    Steps7 --> Clean7[Clean Previous Builds]
    Steps8 --> Clean8[Clean Previous Builds]
    
    Clean1 --> BuildTar1[slurm-factory build --gpu]
    Clean2 --> BuildTar2[slurm-factory build --gpu]
    Clean3 --> BuildTar3[slurm-factory build --gpu]
    Clean4 --> BuildTar4[slurm-factory build --gpu]
    Clean5 --> BuildTar5[slurm-factory build --gpu]
    Clean6 --> BuildTar6[slurm-factory build --gpu]
    Clean7 --> BuildTar7[slurm-factory build --gpu]
    Clean8 --> BuildTar8[slurm-factory build --gpu]
    
    BuildTar1 --> Docker1[Docker: Spack Build]
    BuildTar2 --> Docker2[Docker: Spack Build]
    BuildTar3 --> Docker3[Docker: Spack Build]
    BuildTar4 --> Docker4[Docker: Spack Build]
    BuildTar5 --> Docker5[Docker: Spack Build]
    BuildTar6 --> Docker6[Docker: Spack Build]
    BuildTar7 --> Docker7[Docker: Spack Build]
    BuildTar8 --> Docker8[Docker: Spack Build]
    
    Docker1 --> Package1[Create Tarball<br/>view/ + modules/ + data/]
    Docker2 --> Package2[Create Tarball<br/>view/ + modules/ + data/]
    Docker3 --> Package3[Create Tarball<br/>view/ + modules/ + data/]
    Docker4 --> Package4[Create Tarball<br/>view/ + modules/ + data/]
    Docker5 --> Package5[Create Tarball<br/>view/ + modules/ + data/]
    Docker6 --> Package6[Create Tarball<br/>view/ + modules/ + data/]
    Docker7 --> Package7[Create Tarball<br/>view/ + modules/ + data/]
    Docker8 --> Package8[Create Tarball<br/>view/ + modules/ + data/]
    
    Package1 --> OIDC1[AWS OIDC Auth]
    Package2 --> OIDC2[AWS OIDC Auth]
    Package3 --> OIDC3[AWS OIDC Auth]
    Package4 --> OIDC4[AWS OIDC Auth]
    Package5 --> OIDC5[AWS OIDC Auth]
    Package6 --> OIDC6[AWS OIDC Auth]
    Package7 --> OIDC7[AWS OIDC Auth]
    Package8 --> OIDC8[AWS OIDC Auth]
    
    OIDC1 --> Upload1[Upload to<br/>s3://vantage-public-assets]
    OIDC2 --> Upload2[Upload to<br/>s3://vantage-public-assets]
    OIDC3 --> Upload3[Upload to<br/>s3://vantage-public-assets]
    OIDC4 --> Upload4[Upload to<br/>s3://vantage-public-assets]
    OIDC5 --> Upload5[Upload to<br/>s3://vantage-public-assets]
    OIDC6 --> Upload6[Upload to<br/>s3://vantage-public-assets]
    OIDC7 --> Upload7[Upload to<br/>s3://vantage-public-assets]
    OIDC8 --> Upload8[Upload to<br/>s3://vantage-public-assets]
    
    Upload1 --> End1([Public Download])
    Upload2 --> End2([Public Download])
    Upload3 --> End3([Public Download])
    Upload4 --> End4([Public Download])
    Upload5 --> End5([Public Download])
    Upload6 --> End6([Public Download])
    Upload7 --> End7([Public Download])
    Upload8 --> End8([Public Download])
    
    style Start fill:#4CAF50
    style End1 fill:#2196F3
    style End2 fill:#2196F3
    style End3 fill:#2196F3
    style End4 fill:#2196F3
    style End5 fill:#2196F3
    style End6 fill:#2196F3
    style End7 fill:#2196F3
    style End8 fill:#2196F3
```

**Configuration**:
```yaml
name: Build and Publish Slurm Tarballs to S3

on:
  workflow_dispatch:
    inputs:
      slurm_version:
        description: 'Slurm version to build'
        required: true
        default: '25.11'
      gpu_support:
        description: 'Enable GPU support'
        required: false
        default: true
        type: boolean
```

**Outputs**:
- Tarball: `slurm-{version}-gcc{compiler}-software.tar.gz`
- Location: `s3://vantage-public-assets/slurm-factory/{version}/{compiler}/`
- Public URL: `https://vantage-public-assets.s3.amazonaws.com/slurm-factory/{version}/{compiler}/slurm-{version}-gcc{compiler}-software.tar.gz`

### 4. CI Tests (`ci.yml`)

**Purpose**: Run linters, type checking, and unit tests on every pull request

**Trigger**: Pull requests to `main` branch

**Jobs**:

1. **commitlint**: Validate commit messages follow Conventional Commits
2. **ci-tests**: Run linters, type checker, and unit tests

**Steps**:
```yaml
- Checkout code
- Install just (task runner)
- Install uv (package manager)
- Run linters (ruff, codespell)
- Run type checker (pyright)
- Run unit tests (pytest)
```

**Requirements**:
- All tests must pass before PR can be merged
- Commit messages must follow `type(scope): message` format
- Code coverage threshold: 80%

### 5. Documentation Deploy (`update-docs.yml`)

**Purpose**: Build and deploy Docusaurus documentation to GitHub Pages

**Trigger**: Push to `main` branch or manual dispatch

**Steps**:
1. Checkout repository with full history
2. Setup Node.js LTS
3. Install Docusaurus dependencies
4. Build documentation
5. Deploy to GitHub Pages

**Output**: https://vantagecompute.github.io/slurm-factory

## Build Process Diagrams

### Compiler Build Process

```mermaid
flowchart LR
    Start([slurm-factory<br/>build-compiler]) --> Docker[Create Docker<br/>Container]
    Docker --> Base[Ubuntu 24.04<br/>Base Image]
    Base --> Spack[Install Spack<br/>v1.0.0]
    Spack --> Bootstrap[Bootstrap<br/>Spack]
    Bootstrap --> BuildGCC[Build GCC<br/>from Source]
    BuildGCC --> Runtime[Build gcc-runtime<br/>Package]
    Runtime --> Binutils[Build binutils]
    Binutils --> Libs[Build Libraries<br/>gmp, mpfr, mpc]
    Libs --> Sign[GPG Sign<br/>Packages]
    Sign --> Package[Create Buildcache<br/>Index]
    Package --> Upload{Publish?}
    Upload -->|Yes| S3[Upload to S3<br/>Buildcache]
    Upload -->|No| Local[Store Locally]
    S3 --> CDN[CloudFront CDN<br/>Distribution]
    Local --> Done1([Complete])
    CDN --> Done2([Complete])
    
    style Start fill:#4CAF50
    style Done1 fill:#2196F3
    style Done2 fill:#2196F3
    style Upload fill:#FF9800
```

### Slurm Build Process

```mermaid
flowchart TB
    Start([slurm-factory build]) --> Docker[Create Docker<br/>Container]
    Docker --> Base[Ubuntu 24.04<br/>Base Image]
    Base --> Spack[Install Spack<br/>v1.0.0]
    Spack --> CustomRepo[Add Custom<br/>Spack Repo]
    CustomRepo --> Mirror{Buildcache<br/>Available?}
    
    Mirror -->|Yes| CompilerCache[Pull Compiler<br/>from Buildcache]
    Mirror -->|No| BuildCompiler[Build Compiler<br/>from Source]
    
    CompilerCache --> RegisterCompiler[Register Compiler<br/>with Spack]
    BuildCompiler --> RegisterCompiler
    
    RegisterCompiler --> DepsCache{Dependencies<br/>in Buildcache?}
    
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
    style Mirror fill:#FF9800
    style DepsCache fill:#FF9800
    style PublishOpt fill:#FF9800
```

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
| `AWS_ROLE_ARN` | GitHub Actions IAM role ARN | All build workflows |
| `GPG_PRIVATE_KEY` | GPG private key for signing | Compiler & Slurm builds |
| `GPG_KEY_ID` | GPG key ID | Compiler & Slurm builds |

### Environment Variables

| Variable | Value | Purpose |
|----------|-------|---------|
| `S3_BUCKET` | `slurm-factory-spack-buildcache-4b670` | Buildcache S3 bucket |
| `CLOUDFRONT_URL` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai` | Public CDN URL |

## Monitoring and Notifications

### Workflow Status

Monitor workflow runs at:
https://github.com/vantagecompute/slurm-factory/actions

### Notifications

Failed workflows generate:
- GitHub status checks on PRs
- Email notifications to repository admins
- Slack notifications (if configured)

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

```bash
# Re-run failed jobs only
gh workflow run build-and-publish-compiler-buildcache.yml \
  -f compiler_versions="13.4.0"

# Re-run entire workflow
gh run rerun <run-id>
```

### Debugging Locally

Test workflows locally with [act](https://github.com/nektos/act):

```bash
# Install act
brew install act  # macOS
# or
sudo snap install act  # Linux

# Run CI workflow locally
act pull_request
```

## Best Practices

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new feature
fix: fix bug
docs: update documentation
chore: update dependencies
ci: update CI workflow
```

### Pull Requests

1. Create feature branch
2. Make changes
3. Run `just lint` and `just unit`
4. Push and create PR
5. Wait for CI to pass
6. Request review
7. Merge after approval

### Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create git tag: `git tag v1.0.0`
4. Push tag: `git push origin v1.0.0`
5. GitHub Actions will create release
6. Publish to PyPI: `uv build && uv publish`

## See Also

- [Infrastructure](./infrastructure.md) - AWS infrastructure details
- [Slurm Factory Spack Build Cache](./slurm-factory-spack-build-cache.md) - Using the buildcache
- [Contributing](./contributing.md) - Development guide
- [Architecture](./architecture.md) - Build system overview
