# GitHub Actions Workflow Example

This example demonstrates how to use the OIDC role for uploading build artifacts to S3.

## Workflow File

Create `.github/workflows/upload-buildcache.yml`:

```yaml
name: Upload to Binary Cache

on:
  workflow_dispatch:
    inputs:
      compiler_version:
        description: 'Compiler version to upload'
        required: true
        default: '13.4.0'

jobs:
  upload-to-cache:
    runs-on: ubuntu-latest
    permissions:
      id-token: write  # Required for OIDC authentication
      contents: read
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Configure AWS credentials via OIDC
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::266735843730:role/slurm-factory-github-actions
          aws-region: us-east-1
          role-session-name: GitHubActions-${{ github.run_id }}
      
      - name: Verify AWS credentials
        run: |
          aws sts get-caller-identity
          aws s3 ls s3://slurm-factory-spack-binary-cache/ || echo "Bucket is empty"
      
      - name: Build compiler
        run: |
          uv run slurm-factory build-compiler \
            --compiler-version ${{ inputs.compiler_version }} \
            --publish
      
      - name: Upload to S3 buildcache
        run: |
          aws s3 sync \
            ~/.slurm-factory/buildcache/ \
            s3://slurm-factory-spack-binary-cache/compilers/${{ inputs.compiler_version }}/buildcache/
      
      - name: Upload compiler tarball
        run: |
          TARBALL=$(ls ~/.slurm-factory/compilers/${{ inputs.compiler_version }}/*.tar.gz | head -1)
          if [ -f "$TARBALL" ]; then
            aws s3 cp \
              "$TARBALL" \
              s3://slurm-factory-spack-binary-cache/compilers/${{ inputs.compiler_version }}/
          fi
```

## Key Points

1. **OIDC Permissions**: The workflow requires `id-token: write` permission
2. **Role ARN**: Get this from `infra outputs` after deploying the stack
3. **Session Name**: Uses the GitHub run ID for traceability
4. **Private Access**: Objects are uploaded without public ACLs (accessed via CloudFront)

## Testing

1. Deploy the infrastructure: `infra deploy`
2. Get the role ARN: `infra outputs`
3. Update the workflow with the correct role ARN
4. Trigger the workflow manually from GitHub Actions UI
