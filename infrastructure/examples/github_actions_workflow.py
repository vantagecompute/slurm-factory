"""Example GitHub Actions workflow for uploading to S3 buildcache.

This file demonstrates how to configure a workflow to use the OIDC role
for uploading build artifacts to the S3 binary cache.

Copy this to .github/workflows/ in your repository.
"""

example_workflow = """
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
          uv run slurm-factory build-compiler \\
            --compiler-version ${{ inputs.compiler_version }} \\
            --publish
      
      - name: Upload to S3 buildcache
        run: |
          aws s3 sync \\
            ~/.slurm-factory/buildcache/ \\
            s3://slurm-factory-spack-binary-cache/compilers/${{ inputs.compiler_version }}/buildcache/
      
      - name: Upload compiler tarball
        run: |
          TARBALL=$(ls ~/.slurm-factory/compilers/${{ inputs.compiler_version }}/*.tar.gz | head -1)
          if [ -f "$TARBALL" ]; then
            aws s3 cp \\
              "$TARBALL" \\
              s3://slurm-factory-spack-binary-cache/compilers/${{ inputs.compiler_version }}/
          fi
"""

if __name__ == "__main__":
    print(example_workflow)
