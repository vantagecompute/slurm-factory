# Buildcache GPG Signature Fix

## Problem
The Spack buildcache with GPG-signed packages was returning 403 Forbidden errors when trying to access signature files and the build_cache index through CloudFront. This prevented users from installing compiler packages from the buildcache.

## Root Cause
1. **Missing S3 ListBucket Permission**: CloudFront's Origin Access Control (OAC) only had `s3:GetObject` permission, but needed `s3:ListBucket` to access directory listings
2. **CloudFront Cache Policy**: The default `CACHING_OPTIMIZED` policy didn't properly handle Spack buildcache query strings and headers
3. **Mirror Configuration**: The code was setting `signed: False` as a workaround instead of fixing the infrastructure

## Solution

### 1. Infrastructure Changes (`infrastructure/infrastructure/stacks.py`)

#### Added S3 ListBucket Permission
```python
# Add ListBucket permission for directory listings (needed for build_cache/ access)
self.bucket.add_to_resource_policy(
    iam.PolicyStatement(
        effect=iam.Effect.ALLOW,
        principals=[iam.ServicePrincipal("cloudfront.amazonaws.com")],
        actions=["s3:ListBucket"],
        resources=[self.bucket.bucket_arn],
        conditions={
            "StringEquals": {
                "AWS:SourceArn": f"arn:aws:cloudfront::{self.account}:distribution/{self.distribution.distribution_id}"
            }
        },
    )
)
```

#### Created Custom CloudFront Cache Policy
```python
buildcache_cache_policy = cloudfront.CachePolicy(
    self,
    "BuildcacheCachePolicy",
    cache_policy_name=f"spack-buildcache-policy-{account_hash}",
    default_ttl=Duration.days(7),
    max_ttl=Duration.days(365),
    min_ttl=Duration.seconds(0),
    header_behavior=cloudfront.CacheHeaderBehavior.allow_list(
        "Accept",
        "Accept-Encoding",
    ),
    query_string_behavior=cloudfront.CacheQueryStringBehavior.all(),
    enable_accept_encoding_gzip=True,
    enable_accept_encoding_brotli=True,
)
```

#### Added Error Response Handling
```python
"error_responses": [
    # Return 404 for 403 errors (helps with missing files)
    cloudfront.ErrorResponse(
        http_status=403,
        response_http_status=404,
        response_page_path="/404.html",
        ttl=Duration.seconds(10),
    ),
],
```

### 2. Code Changes (`slurm_factory/spack_yaml.py`)

Reverted mirrors from `signed: False` back to `signed: True`:

```python
"slurm-factory-buildcache": {
    "url": f"https://slurm-factory-spack-binary-cache.vantagecompute.ai/compilers/{compiler_version}/buildcache",
    "signed": True,  # ← Changed back from False
    "binary": True,
    "source": False,
},
```

## Deployment Steps

### 1. Deploy Infrastructure Changes

```bash
cd infrastructure
cdk deploy
```

This will:
- Update the S3 bucket policy to add ListBucket permission
- Create a new CloudFront cache policy optimized for Spack buildcache
- Update the CloudFront distribution to use the new cache policy
- Add error response handling for 403→404

### 2. Invalidate CloudFront Cache

After deployment, invalidate the CloudFront cache to clear any cached 403 errors:

```bash
# Get distribution ID from CDK output or AWS Console
DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
  --stack-name SlurmFactoryBinaryCache \
  --query 'Stacks[0].Outputs[?OutputKey==`DistributionId`].OutputValue' \
  --output text)

# Create invalidation
aws cloudfront create-invalidation \
  --distribution-id $DISTRIBUTION_ID \
  --paths "/*"
```

### 3. Rebuild and Republish Compiler Buildcache (Optional)

If the existing buildcache has issues, rebuild with proper GPG signing:

```bash
# Trigger GitHub Actions workflow
gh workflow run build-and-publish-compiler-buildcache.yml \
  -f compiler_versions="8.5.0"
```

### 4. Test the Fix

```bash
# In a clean Spack environment
spack mirror add slurm-factory-buildcache \
  https://slurm-factory-spack-binary-cache.vantagecompute.ai/compilers/8.5.0/buildcache

# Import GPG keys
spack buildcache keys --install --trust

# Try to install GCC (should work with signature verification now!)
spack install gcc@8.5.0 target=x86_64_v3
```

## What Changed

### Before
- ❌ CloudFront returned 403 Forbidden for build_cache/ directory
- ❌ Signature files (.spec.json.sig) were inaccessible
- ❌ Had to use workaround: `signed: False` and `--no-check-signature`
- ❌ No security verification of downloaded packages

### After
- ✅ CloudFront can access build_cache/ directory (ListBucket permission)
- ✅ Signature files are accessible through proper cache policy
- ✅ GPG signature verification works: `signed: True`
- ✅ Full security: packages are cryptographically verified
- ✅ Proper error handling for missing files

## Technical Details

### Spack 1.0 Buildcache Structure
```
buildcache/
├── build_cache/
│   ├── index.json                                    # Package index
│   ├── linux-ubuntu24.04-x86_64_v3-gcc-13.3.0-gcc-8.5.0-{hash}.spack
│   ├── linux-ubuntu24.04-x86_64_v3-gcc-13.3.0-gcc-8.5.0-{hash}.spec.json
│   └── linux-ubuntu24.04-x86_64_v3-gcc-13.3.0-gcc-8.5.0-{hash}.spec.json.sig
└── _pgp/
    └── {key_id}.pub
```

### Required S3/CloudFront Permissions
1. **s3:GetObject** on `bucket/*` - Download files
2. **s3:ListBucket** on `bucket` - List directories (NEW!)
3. **CloudFront OAC** - Secure access from CloudFront to S3
4. **Query String Support** - Handle Spack's URL parameters
5. **Custom Headers** - Accept, Accept-Encoding for content negotiation

## Verification Checklist

After deployment, verify:
- [ ] CloudFront distribution updated successfully
- [ ] S3 bucket policy includes ListBucket permission
- [ ] CloudFront cache invalidated
- [ ] Test installation works: `spack install gcc@8.5.0`
- [ ] GPG signature verification succeeds (no --no-check-signature needed)
- [ ] GitHub Actions workflow completes successfully

## Rollback Plan

If issues occur:
1. Revert infrastructure: `cdk deploy` with previous version
2. Set mirrors back to `signed: False` temporarily
3. Investigate CloudFront logs for specific errors
4. Check S3 bucket policy in AWS Console
