# GitHub Actions Workflows

This directory contains GitHub Actions workflows for CI/CD, buildcache publishing, and documentation.

## Workflow Summary

| Workflow | File | Trigger | Purpose |
|----------|------|---------|---------|
| **CI Workflow** | `ci.yml` | PR to main | Linting, typechecking, unit & integration tests |
| **Build and Publish Slurm Dependencies** | `build-and-publish-slurm-dependencies.yml` | Manual | Build Slurm dependencies for all toolchains |
| **Build and Publish Slurm** | `build-and-publish-slurm.yml` | Manual | Build complete Slurm packages with tarballs |
| **Build and Release** | `publish.yml` | Tag push | Build, test, publish to PyPI, create GitHub release |
| **Update Documentation** | `update-docs.yml` | Push to main | Auto-update and deploy docs to GitHub Pages |
| **Copilot Setup Steps** | `copilot-setup-steps.yml` | Manual/PR | Setup environment for GitHub Copilot agent |

---

## 1. CI Workflow

**File:** `ci.yml`

Runs on pull requests to `main` branch. Performs code quality checks and tests.

**Jobs:**
- **commitlint**: Validates commit messages follow conventional commit format
- **ci-tests**: Runs linters, typecheck, unit tests, and integration tests

**Commands:**
```bash
just lint        # Run linters
just typecheck   # Run type checking
just unit        # Run unit tests
just integration # Run integration tests
```

---

## 2. Build and Publish Slurm Dependencies

**File:** `build-and-publish-slurm-dependencies.yml`

Builds and publishes **only Slurm dependencies** (excluding Slurm itself) to S3 buildcache.

**Trigger:** Manual (`workflow_dispatch`)

**Inputs:**
| Input | Description | Default |
|-------|-------------|---------|
| `toolchain_versions` | Toolchains to build (comma-separated or "all") | `all` |

**Supported Toolchains:**
- `resolute` (Ubuntu 25.04)
- `noble` (Ubuntu 24.04)
- `jammy` (Ubuntu 22.04)
- `rockylinux10`
- `rockylinux9`
- `rockylinux8`

**Build Command:**
```bash
slurm-factory build-slurm \
  --slurm-version 25.11 \
  --toolchain <toolchain> \
  --gpu \
  --no-cache \
  --publish=deps \
  --signing-key "$GPG_KEY_ID" \
  --gpg-private-key "$GPG_PRIVATE_KEY" \
  --gpg-passphrase "$GPG_PASSPHRASE"
```

**Buildcache Location:**
- S3: `s3://slurm-factory-spack-buildcache-4b670/<toolchain>/slurm/deps/`
- CloudFront: `https://slurm-factory-spack-binary-cache.vantagecompute.ai/<toolchain>/slurm/deps/`

---

## 3. Build and Publish Slurm

**File:** `build-and-publish-slurm.yml`

Builds and publishes **complete Slurm packages** (Slurm + dependencies + tarballs) to S3 buildcache.

**Trigger:** Manual (`workflow_dispatch`)

**Inputs:**
| Input | Description | Default |
|-------|-------------|---------|
| `slurm_versions` | Slurm versions to build (comma-separated or "all") | `all` |
| `toolchains` | Toolchains to use (comma-separated or "all") | `all` |

**Supported Slurm Versions:**
- `25.11`, `24.11`, `23.11`

**Build Command:**
```bash
slurm-factory build-slurm \
  --slurm-version <slurm_version> \
  --toolchain <toolchain> \
  --gpu \
  --no-cache \
  --publish=slurm \
  --signing-key "$GPG_KEY_ID" \
  --gpg-private-key "$GPG_PRIVATE_KEY" \
  --gpg-passphrase "$GPG_PASSPHRASE"
```

**Buildcache Location:**
- S3: `s3://slurm-factory-spack-buildcache-4b670/<toolchain>/slurm/<slurm_version>/`
- CloudFront: `https://slurm-factory-spack-binary-cache.vantagecompute.ai/<toolchain>/slurm/<slurm_version>/`

**Tarballs:**
- Location: `https://slurm-factory-spack-binary-cache.vantagecompute.ai/builds/<slurm_version>/<toolchain>/`
- Files: `slurm-<version>-<toolchain>-software.tar.gz` + `.asc` signature

---

## 4. Build and Release

**File:** `publish.yml`

Builds Python package, publishes to PyPI, and creates GitHub release.

**Trigger:** Push of version tags (e.g., `1.0.0`, `1.0.0-alpha.1`, `1.0.0rc1`)

**Tag Patterns:**
- `X.Y.Z` (stable release)
- `X.Y.Z-alpha.N` / `X.Y.ZaN` (alpha)
- `X.Y.Z-beta.N` / `X.Y.ZbN` (beta)
- `X.Y.ZrcN` (release candidate)

**Jobs:**
1. **build**: Build Python wheel and sdist
2. **test-install**: Verify wheel installation works
3. **publish-pypi**: Upload to PyPI (trusted publishing)
4. **create-release**: Create GitHub release with artifacts

---

## 5. Update Documentation

**File:** `update-docs.yml`

Automatically updates and deploys documentation to GitHub Pages.

**Trigger:**
- Push to `main` with changes to `slurm_factory/`, `docusaurus/`, or `pyproject.toml`
- Manual (`workflow_dispatch`)

**Process:**
1. Build documentation with `just docs-build`
2. Create PR with changes (auto-labeled `deploy-docs`, `auto-merge`)
3. Auto-merge PR if clean
4. Deploy to GitHub Pages

---

## 6. Copilot Setup Steps

**File:** `copilot-setup-steps.yml`

Configures environment for GitHub Copilot coding agent.

**Trigger:**
- Changes to the workflow file
- Manual (`workflow_dispatch`)

**Setup:**
- Python 3.14
- uv package manager
- just command runner

---

## Environment & Secrets

### Required Secrets (for buildcache workflows)

| Secret | Description |
|--------|-------------|
| `AWS_ROLE_ARN` | AWS IAM role for OIDC authentication |
| `GPG_PRIVATE_KEY` | Base64-encoded GPG private key for signing |
| `GPG_KEY_ID` | GPG key ID (e.g., `DFB92630BCA5AB71`) |
| `GPG_PASSPHRASE` | GPG key passphrase |

### Required Environment

| Environment | Used By |
|-------------|---------|
| `release` | Buildcache publishing workflows |
| `pypi` | PyPI publishing |
| `github-pages` | Documentation deployment |

---

## Build Infrastructure

- **Runners:** `self-hosted` (for buildcache), `ubuntu-latest`/`ubuntu-24.04` (for CI)
- **Timeouts:** 3600 minutes (60 hours) for builds, 360 minutes per step
- **AWS Region:** `us-east-1`
- **S3 Bucket:** `slurm-factory-spack-buildcache-4b670`
- **CloudFront:** `https://slurm-factory-spack-binary-cache.vantagecompute.ai`

---

## Usage Examples

### Run CI locally
```bash
just lint && just typecheck && just unit && just integration
```

### Build dependencies for specific toolchains
```bash
# Via GitHub UI: Actions → "Build and Publish Slurm Dependencies" → Run workflow
# Input: toolchain_versions = "noble,rockylinux9"
```

### Build complete Slurm packages
```bash
# Via GitHub UI: Actions → "Build and Publish Slurm" → Run workflow
# Input: slurm_versions = "25.11"
# Input: toolchains = "noble,jammy"
```

### Using published buildcaches
```bash
# Add mirrors
TOOLCHAIN=noble
SLURM_VERSION=25.11
CLOUDFRONT_URL=https://slurm-factory-spack-binary-cache.vantagecompute.ai

spack mirror add slurm-factory-deps "${CLOUDFRONT_URL}/${TOOLCHAIN}/slurm/deps/"
spack mirror add slurm-factory-slurm "${CLOUDFRONT_URL}/${TOOLCHAIN}/slurm/${SLURM_VERSION}/"

# Import GPG keys and install
spack buildcache keys --install --trust
spack install slurm@${SLURM_VERSION}
```

### Create a release
```bash
# Tag and push to trigger release workflow
git tag 1.0.0
git push origin 1.0.0
```

