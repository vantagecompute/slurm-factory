# How to Verify GPG Signatures

This guide explains how to verify GPG signatures for Slurm Factory packages, both for Spack buildcache packages and standalone tarballs.

## Overview

All Slurm Factory packages are GPG-signed with key `DFB92630BCA5AB71` for security and integrity verification:

- **Spack buildcache packages** - Automatically verified by Spack during installation
- **Standalone tarballs** - Must be manually verified before extraction

**Why verify signatures?**

- ✅ **Authenticity** - Confirms packages came from Vantage Compute
- ✅ **Integrity** - Ensures no tampering or corruption during download
- ✅ **Security** - Protects against man-in-the-middle attacks
- ✅ **Trust** - Establishes provenance for production deployments

## GPG Key Information

**Signing Key Details:**

- **Key ID**: `DFB92630BCA5AB71`
- **Owner**: Vantage Compute Corporation (Slurm Factory Spack Cache Signing Key)
- **Email**: `info@vantagecompute.ai`
- **Type**: RSA 4096-bit

## Verifying Standalone Tarballs

### Step 1: Download Tarball and Signature

```bash
# Set versions
SLURM_VERSION=25.11
COMPILER_VERSION=15.2.0
CLOUDFRONT_URL=https://slurm-factory-spack-binary-cache.vantagecompute.ai

# Download tarball
wget "${CLOUDFRONT_URL}/builds/${SLURM_VERSION}/${COMPILER_VERSION}/slurm-${SLURM_VERSION}-gcc${COMPILER_VERSION}-software.tar.gz"

# Download GPG signature (.asc file)
wget "${CLOUDFRONT_URL}/builds/${SLURM_VERSION}/${COMPILER_VERSION}/slurm-${SLURM_VERSION}-gcc${COMPILER_VERSION}-software.tar.gz.asc"
```

### Step 2: Import the Public GPG Key

```bash
# Import from keyserver (recommended)
gpg --keyserver keyserver.ubuntu.com --recv-keys DFB92630BCA5AB71

# Alternative: Import from the buildcache
curl https://slurm-factory-spack-binary-cache.vantagecompute.ai/build_cache/_pgp/DFB92630BCA5AB71.pub | gpg --import

# Verify the key was imported
gpg --list-keys DFB92630BCA5AB71
```

**Expected output:**

```text
pub   rsa4096 2025-XX-XX [SC]
      XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
uid           [ unknown] Vantage Compute Corporation (Slurm Factory Spack Cache Signing Key) <info@vantagecompute.ai>
sub   rsa4096 2025-XX-XX [E]
```

### Step 3: Verify the Signature

```bash
# Verify tarball signature
gpg --verify slurm-${SLURM_VERSION}-gcc${COMPILER_VERSION}-software.tar.gz.asc \
             slurm-${SLURM_VERSION}-gcc${COMPILER_VERSION}-software.tar.gz
```

**Expected output for valid signature:**

```text
gpg: Signature made Sun Nov 17 14:48:23 2025 UTC
gpg:                using RSA key DFB92630BCA5AB71
gpg: Good signature from "Vantage Compute Corporation (Slurm Factory Spack Cache Signing Key) <info@vantagecompute.ai>" [unknown]
gpg: WARNING: This key is not certified with a trusted signature!
gpg:          There is no indication that the signature belongs to the owner.
Primary key fingerprint: XXXX XXXX XXXX XXXX XXXX  XXXX DFB9 2630 BCA5 AB71
```

**Key indicators:**

- ✅ `Good signature from "Vantage Compute Corporation"` - **REQUIRED**
- ⚠️ `WARNING: This key is not certified` - **EXPECTED** (see Step 4 to resolve)
- ❌ `BAD signature` - **STOP! Do not use the tarball**

### Step 4: Trust the Key (Optional)

The "untrusted signature" warning appears because you haven't explicitly trusted the key. To remove this warning:

```bash
# Start GPG key editor
gpg --edit-key DFB92630BCA5AB71

# In the GPG prompt, type:
trust

# Choose trust level:
# 5 = I trust ultimately (recommended for production)
# 4 = I trust fully
# 3 = I trust marginally

# Type: 5 <ENTER>
# Type: quit <ENTER>
```

After trusting the key, re-verify:

```bash
gpg --verify slurm-${SLURM_VERSION}-gcc${COMPILER_VERSION}-software.tar.gz.asc \
             slurm-${SLURM_VERSION}-gcc${COMPILER_VERSION}-software.tar.gz
```

Now the output should show:

```text
gpg: Good signature from "Vantage Compute Corporation (Slurm Factory Spack Cache Signing Key) <info@vantagecompute.ai>" [ultimate]
```

### Step 5: Extract and Use

**Only proceed if signature verification succeeded!**

```bash
# Extract tarball
sudo tar -xzf slurm-${SLURM_VERSION}-gcc${COMPILER_VERSION}-software.tar.gz -C /opt/

# Install
cd /opt
sudo ./data/slurm_assets/slurm_install.sh --full-init

# Verify installation
module load slurm/${SLURM_VERSION}
sinfo --version
```

## Verifying Spack Buildcache Packages

Spack automatically verifies GPG signatures for buildcache packages.

### Step 1: Import GPG Keys

```bash
# Set up Spack mirrors
SLURM_VERSION=25.11
COMPILER_VERSION=15.2.0
CLOUDFRONT_URL=https://slurm-factory-spack-binary-cache.vantagecompute.ai

spack mirror add slurm-factory-build-toolchain "${CLOUDFRONT_URL}/compilers/${COMPILER_VERSION}"
spack mirror add slurm-factory-slurm-deps "${CLOUDFRONT_URL}/deps/${COMPILER_VERSION}"
spack mirror add slurm-factory-slurm "${CLOUDFRONT_URL}/slurm/${SLURM_VERSION}/${COMPILER_VERSION}"

# Import and trust all GPG keys from buildcaches
spack buildcache keys --install --trust
```

This command:

1. Downloads all GPG public keys from `_pgp/` directories in the mirrors
2. Imports them into Spack's GPG keyring
3. Marks them as trusted for package verification

### Step 2: Verify Key Import

```bash
# List imported keys in Spack
spack gpg list

# Expected output includes:
# DFB92630BCA5AB71 Vantage Compute Corporation (Slurm Factory Spack Cache Signing Key) <info@vantagecompute.ai>
```

### Step 3: Install with Automatic Verification

```bash
# Install Slurm (signatures verified automatically)
spack install slurm@${SLURM_VERSION}%gcc@${COMPILER_VERSION}

# Spack will:
# 1. Download each package
# 2. Verify GPG signature
# 3. Abort installation if any signature is invalid
```

### Manual Package Verification

To manually check a specific package signature:

```bash
# Check package in buildcache
spack buildcache check slurm@${SLURM_VERSION}%gcc@${COMPILER_VERSION}

# List all packages and their signatures
spack buildcache list --allarch
```

## Troubleshooting

### "No public key" Error

If you see:

```text
gpg: Can't check signature: No public key
```

**Solution:** Import the public key (Step 2 above)

### "BAD signature" Error

If you see:

```text
gpg: BAD signature from "Vantage Compute Corporation"
```

**This means the file has been tampered with or is corrupted!**

**DO NOT use the tarball.** Instead:

1. Delete the downloaded files
2. Re-download from the official source
3. Verify signature again
4. Contact info@vantagecompute.ai if the issue persists

### Wrong Key ID

If verification shows a different key ID:

```text
gpg: Signature made by key XXXXXXXXXXXXXXXX
```

**This is NOT a Vantage Compute package!**

Only trust signatures from key `DFB92630BCA5AB71`.

### Expired Key

If the key has expired, you'll see:

```text
gpg: Good signature from "..." [expired]
```

**Solution:** Re-import the key to get the latest expiration date:

```bash
gpg --keyserver keyserver.ubuntu.com --recv-keys DFB92630BCA5AB71
```

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
