# Infrastructure as Code

This directory contains AWS CDK infrastructure code for the slurm-factory project, managed via a Typer CLI.

## Overview

The infrastructure includes:

- **S3 Bucket** (`slurm-factory-spack-binary-cache`) - Stores Spack binary cache artifacts
- **CloudFront Distribution** - CDN for fast global access to build artifacts
- **IAM Policies** - Access control for users and GitHub Actions
- **GitHub OIDC** - Secure authentication for GitHub Actions workflows
- **Route53 DNS** (optional) - Custom domain support with automatic certificate validation

## Quick Start

### Prerequisites

1. Install AWS CDK CLI:

```bash
npm install -g aws-cdk
```

1. Install Python dependencies:

```bash
cd infrastructure
pip install -e .
```

1. Configure AWS credentials:

```bash
aws configure
```

### Bootstrap CDK (First Time Only)

```bash
infra bootstrap --region us-east-1
```

### Deploy Infrastructure

Basic deployment:

```bash
infra deploy
```

With custom domain:

```bash
infra deploy \
  --domain cache.slurm-factory.com \
  --hosted-zone-id Z1234567890ABC
```

### View Outputs

```bash
infra outputs
```

## CLI Commands

### `infra bootstrap`

Bootstrap CDK in your AWS account (run once per account/region):

```bash
infra bootstrap --region us-east-1 --profile myprofile
```

### `infra deploy`

Deploy the infrastructure stack:

```bash
# Basic deployment
infra deploy

# With custom domain
infra deploy \
  --domain cache.slurm-factory.com \
  --hosted-zone-id Z1234567890ABC

# Different GitHub org/repo
infra deploy \
  --github-org myorg \
  --github-repo myrepo

# Skip approval prompts
infra deploy --no-approval
```

### `infra synth`

Generate CloudFormation templates without deploying:

```bash
infra synth --output ./cdk.out
```

### `infra diff`

Show differences between deployed stack and current code:

```bash
infra diff
```

### `infra destroy`

Destroy the infrastructure (S3 bucket retained):

```bash
infra destroy --force
```

### `infra outputs`

Display stack outputs (bucket name, URLs, role ARNs):

```bash
infra outputs
```

## Architecture

### Components

1. **S3 Bucket**
   - Name: `slurm-factory-spack-binary-cache`
   - Encryption: S3-managed (AES-256)
   - Lifecycle: Delete old versions after 90 days
   - Retention: Bucket retained on stack deletion
    - CORS: Public read/list responses for browser-based documentation clients

2. **CloudFront Distribution**
   - Domain: `slurm-factory-spack-binary-cache.vantagecompute.ai`
    - Origin: S3 bucket via Origin Access Control (OAC)
   - HTTPS: Redirect HTTP to HTTPS
   - Caching: Optimized cache policy
    - CORS: Response headers policy for public `GET`, `HEAD`, and `OPTIONS` requests
   - Compression: Enabled
   - Price class: US/Europe/Asia (PriceClass100)

3. **IAM Permissions**
   - **User `james`**: Full read/write access for manual uploads
   - **GitHub Actions Role**: Automated uploads via OIDC

4. **GitHub OIDC Integration**
   - Provider: `token.actions.githubusercontent.com`
   - Audience: `sts.amazonaws.com`
   - Condition: Repository path matching
   - Session duration: 1 hour

### Security

- S3 bucket access restricted to:
  - CloudFront OAC (read/list for public distribution)
  - IAM user `james` (read/write)
  - GitHub Actions role (read/write via OIDC)
- HTTPS-only access via CloudFront
- Encrypted at rest (S3-managed keys)
- Public access blocked on S3, only accessible via CloudFront

## Usage with slurm-factory

### GitHub Actions Workflow

Configure your workflow to use OIDC authentication:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      id-token: write  # Required for OIDC
      contents: read
    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::ACCOUNT_ID:role/slurm-factory-github-actions
          aws-region: us-east-1
      
      - name: Upload to S3
        run: |
          aws s3 sync ./buildcache/ s3://slurm-factory-spack-binary-cache/compilers/13.4.0/
```

### Building and Publishing a Compiler

```bash
### Manual Upload (user james)

```bash
# Build compiler
uv run slurm-factory build-compiler --compiler-version 11.5.0 --publish

# Upload to S3
aws s3 sync \
  ~/.slurm-factory/buildcache/ \
  s3://slurm-factory-spack-binary-cache/compilers/11.5.0/buildcache/
```
```

### Building Slurm with Binary Cache

```bash
# Build Slurm using compiler from buildcache
uv run slurm-factory build \
  --slurm-version 25.11 \
  --compiler-version 11.5.0 \
  --use-buildcache \
  --enable-buildcache \
  --publish-s3
```

## CDK Stack Structure

```text
infrastructure/
├── app.py                      # CDK app entry point
├── cdk.json                    # CDK configuration
├── pyproject.toml              # Python package config
├── s3-bucket-policy.json       # Reference policy (not used by CDK)
├── README.md                   # This file
└── infrastructure/
    ├── __init__.py
    ├── cli.py                  # Typer CLI commands
    └── stacks.py               # CDK stack definitions
```

## Directory Structure in S3

Accessed via CloudFront at `https://slurm-factory-spack-binary-cache.vantagecompute.ai`:

```text
s3://slurm-factory-spack-binary-cache/
├── compilers/
│   ├── 11.5.0/
│   │   ├── buildcache/
│   │   │   ├── compilers/
│   │   │   ├── indices/

│   │   │   ├── providers/
│   │   │   └── tags/
│   │   └── gcc-11.5.0-compiler.tar.gz
│   ├── 13.4.0/
│   └── ...
└── slurm/
    ├── 25.11/
    │   ├── 11.5.0/
    │   └── 13.4.0/
    └── ...
```

**Public URL**: `https://slurm-factory-spack-binary-cache.vantagecompute.ai/compilers/11.5.0/gcc-11.5.0-compiler.tar.gz`

## Development

### Running Tests

```bash
cd infrastructure
pytest
```

### Linting

```bash
ruff check .
mypy .
```

### Local Development

```bash
# Install in editable mode
pip install -e .

# Run CLI
infra --help
```

## Troubleshooting

### CDK Bootstrap Errors

If bootstrap fails, ensure you have:

- Valid AWS credentials configured
- Sufficient IAM permissions
- CDK CLI installed globally

### Deployment Issues

Check the CloudFormation console for detailed error messages:

```bash
aws cloudformation describe-stack-events \
  --stack-name SlurmFactoryInfraStack \
  --max-items 20
```

### Custom Domain Not Working

Verify:

1. Hosted zone ID is correct
2. Domain name matches hosted zone
3. Certificate is in `us-east-1` region
4. DNS propagation has completed (can take up to 48 hours)

## References

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [GitHub Actions OIDC](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)
- [CloudFront Best Practices](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/best-practices.html)
