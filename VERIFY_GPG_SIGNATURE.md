# How to Verify GPG Signatures

## What Happened in the Docker Build

During the build, we:
1. **Created** a tarball: `slurm-25.11-gcc13.4.0-software.tar.gz`
2. **Signed** it with our GPG key, creating: `slurm-25.11-gcc13.4.0-software.tar.gz.asc`
3. **Verified** the signature to prove authenticity

## How Users Verify Signatures

### Step 1: Get the Public Key

Users need to import the **public** GPG key (not the private key):

```bash
# Import the public key from a keyserver
gpg --keyserver keyserver.ubuntu.com --recv-keys DFB92630BCA5AB71

# Or import from a file if you publish the public key
gpg --import vantage-compute-public.key
```

### Step 2: Verify the Signature

Once the public key is imported, anyone can verify the tarball:

```bash
gpg --verify slurm-25.11-gcc13.4.0-software.tar.gz.asc slurm-25.11-gcc13.4.0-software.tar.gz
```

This will output:
```
gpg: Signature made Sun Nov 17 14:48:23 2025 UTC
gpg:                using RSA key DFB92630BCA5AB71
gpg: Good signature from "Vantage Compute Corporation (Slurm Factory Spack Build Cache Signing Key) <info@vantagecompute.ai>"
```

### Step 3: Trust the Key (Optional)

To avoid "untrusted signature" warnings, users can mark your key as trusted:

```bash
gpg --edit-key DFB92630BCA5AB71
# Then type: trust
# Choose: 5 (I trust ultimately)
# Type: quit
```

## Publishing Best Practices

### 1. Publish Your Public Key

Export and publish your public key so users can import it:

```bash
# Export the public key
gpg --armor --export DFB92630BCA5AB71 > vantage-compute-public.key

# Upload to keyservers
gpg --keyserver keyserver.ubuntu.com --send-keys DFB92630BCA5AB71
gpg --keyserver keys.openpgp.org --send-keys DFB92630BCA5AB71
```

### 2. Include Instructions in Documentation

Add to your docs:

```markdown
## Verify Downloaded Packages

All Slurm Factory packages are GPG-signed. To verify:

1. Import our public key:
   \`\`\`bash
   gpg --keyserver keyserver.ubuntu.com --recv-keys DFB92630BCA5AB71
   \`\`\`

2. Verify the signature:
   \`\`\`bash
   gpg --verify slurm-VERSION-gccVERSION-software.tar.gz.asc slurm-VERSION-gccVERSION-software.tar.gz
   \`\`\`
```

### 3. Store Signatures Alongside Tarballs in S3

```bash
# Upload both files to S3
aws s3 cp slurm-25.11-gcc13.4.0-software.tar.gz s3://bucket/builds/
aws s3 cp slurm-25.11-gcc13.4.0-software.tar.gz.asc s3://bucket/builds/
```

## What the Signature Proves

✅ **Authenticity**: The file was created by someone with access to the private key  
✅ **Integrity**: The file hasn't been modified since signing  
✅ **Non-repudiation**: Can't deny signing the file

## Testing Verification Locally

Extract the signature and tarball from the container:

```bash
# Extract the tarball
docker run --rm slurm-factory-gpg-test:latest cat /root/.slurm-factory/25.11/13.4.0/slurm-25.11-gcc13.4.0-software.tar.gz > test.tar.gz

# Extract the signature
docker run --rm slurm-factory-gpg-test:latest cat /root/.slurm-factory/25.11/13.4.0/slurm-25.11-gcc13.4.0-software.tar.gz.asc > test.tar.gz.asc

# Export public key from the container (or use the one you already have)
echo "$GPG_PRIVATE_KEY" | base64 -d | gpg --import

# Verify
gpg --verify test.tar.gz.asc test.tar.gz
```

## Spack Buildcache Integration

For Spack buildcaches, the signature verification is automatic:

```bash
# Spack will verify signatures when you run:
spack buildcache keys --install --trust

# Then Spack automatically verifies packages during install:
spack install /<hash>
```
