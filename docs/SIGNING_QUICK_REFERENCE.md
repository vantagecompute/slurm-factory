# Buildcache Signing - Quick Reference

This document provides quick commands and snippets for implementing package signing. See [BUILDCACHE_SIGNING_IMPLEMENTATION_PLAN.md](./BUILDCACHE_SIGNING_IMPLEMENTATION_PLAN.md) for the complete implementation plan.

## Quick Setup Guide

### 1. Generate GPG Key (One-time Setup)

```bash
# Generate key
gpg --full-generate-key
# Choose: RSA and RSA, 4096 bits, 2 years expiration
# Name: Vantage Compute Slurm Factory
# Email: slurm-factory@vantagecompute.ai

# Get key ID
gpg --list-secret-keys --keyid-format LONG
# Look for line: sec   rsa4096/KEYID

# Export public key
gpg --armor --export slurm-factory@vantagecompute.ai > vantage-slurm-factory.pub

# Export private key (for GitHub/AWS secrets)
gpg --armor --export-secret-keys slurm-factory@vantagecompute.ai | base64 -w0 > private-key.txt
```

### 2. Add to GitHub Secrets

```bash
# In GitHub repository settings -> Secrets and variables -> Actions
GPG_PRIVATE_KEY=<paste content of private-key.txt>
GPG_PASSPHRASE=<your passphrase>
GPG_KEY_ID=<key ID from step 1>
```

### 3. Publish Public Key

```bash
# Upload to S3
aws s3 cp vantage-slurm-factory.pub \
  s3://slurm-factory-spack-buildcache-4b670/keys/vantage-slurm-factory.pub \
  --acl public-read

# Upload to key servers (optional)
gpg --send-keys <KEY_ID>
```

## Code Snippets

### Import Key in Workflow

```yaml
- name: Import GPG signing key
  env:
    GPG_PRIVATE_KEY: ${{ secrets.GPG_PRIVATE_KEY }}
    GPG_PASSPHRASE: ${{ secrets.GPG_PASSPHRASE }}
  run: |
    echo "$GPG_PRIVATE_KEY" | base64 -d | gpg --batch --import
    gpg --list-secret-keys
```

### Environment Variables

```bash
# For signing
export ENABLE_SIGNING=true
export GPG_KEY_ID=0x1234567890ABCDEF
export GPG_PASSPHRASE=your-passphrase

# For verification
export SPACK_GNUPGHOME=$HOME/.spack/gnupg
```

### Spack Commands

```bash
# Import public key to Spack
spack gpg trust vantage-slurm-factory.pub

# List trusted keys
spack gpg list

# Push signed packages
spack buildcache push --key 0x1234567890ABCDEF s3-buildcache gcc

# Install with signature verification (default behavior after transition)
spack install gcc@13.4.0

# Force signature verification
spack install --require-signed gcc@13.4.0

# Skip verification (not recommended)
spack install --no-check-signature gcc@13.4.0
```

## Testing Commands

### Test Key Generation

```bash
# Generate test key
gpg --batch --passphrase '' --quick-gen-key "Test Key <test@example.com>" rsa4096 sign 1y

# Export test key
gpg --armor --export test@example.com > test-key.pub
```

### Test Signing Flow

```bash
# Sign a test package
spack buildcache push --key <KEY_ID> /tmp/test-mirror gcc

# Verify signature
spack buildcache list -l /tmp/test-mirror
# Look for "signed: true" in output
```

### Test Verification

```bash
# Import key
spack gpg trust test-key.pub

# Install from signed mirror
spack mirror add test-mirror /tmp/test-mirror
spack install --cache-only gcc@13.4.0
```

## Current Files to Modify

### 1. `slurm_factory/utils.py`

**Functions to update:**
- `publish_compiler_to_buildcache()` - Add signing support
- `push_to_buildcache()` - Add signing support

**Changes:**
- Replace `--unsigned` with signing flags
- Add GPG key import in Docker container
- Pass signing configuration

### 2. `slurm_factory/spack_yaml.py`

**Functions to update:**
- `generate_compiler_bootstrap_config()` - Update mirror config
- `generate_spack_config()` - Update mirror config

**Changes:**
- Set `"signed": True` for slurm-factory mirrors
- Keep `"signed": False` for spack-public mirror

### 3. `slurm_factory/main.py`

**Commands to update:**
- `build_compiler` - Add signing options
- `build` - Add signing options

**Changes:**
- Add `--enable-signing/--disable-signing` flags
- Add `--gpg-key-id` option
- Pass signing config to builder functions

### 4. GitHub Workflows

**Files to update:**
- `.github/workflows/build-and-publish-compiler-buildcache.yml`
- `.github/workflows/build-and-publish-slurm-all.yml`

**Changes:**
- Add GPG key import step
- Set environment variables
- Pass signing flags to CLI

## Key Management Cheat Sheet

### Check Key Status

```bash
# List all keys
gpg --list-keys

# Check expiration
gpg --list-keys --with-colons | grep '^pub' | awk -F: '{print $7}'

# Extend expiration
gpg --edit-key <KEY_ID>
> expire
> (select new expiration)
> save
```

### Backup and Restore

```bash
# Backup (store offline)
gpg --export-secret-keys --armor <KEY_ID> > private-backup.asc
gpg --gen-revoke <KEY_ID> > revoke-cert.asc

# Restore
gpg --import private-backup.asc
```

### Key Rotation

```bash
# Generate new key before expiration (30 days)
# Update GitHub secrets with new key
# Publish new public key
# Continue using old key during overlap
# Switch to new key
# Archive old private key
```

## Troubleshooting

### Issue: GPG command not found in container

```bash
# Add to Dockerfile
RUN apt-get update && apt-get install -y gnupg
```

### Issue: Passphrase prompt in non-interactive mode

```bash
# Use GPG agent or batch mode
echo "$GPG_PASSPHRASE" | gpg --batch --passphrase-fd 0 --import
```

### Issue: Signature verification fails

```bash
# Check if key is imported
spack gpg list

# Re-import public key
spack gpg trust vantage-slurm-factory.pub

# Check package signature
spack buildcache list -l -v
```

### Issue: Key expired

```bash
# Extend key expiration (before it expires)
gpg --edit-key <KEY_ID>
> expire
> 2y
> save

# Re-export and distribute public key
gpg --armor --export <KEY_ID> > vantage-slurm-factory.pub
```

## Migration Checklist

- [ ] Generate production GPG key
- [ ] Store private key in GitHub Secrets
- [ ] Publish public key to S3/CloudFront
- [ ] Update code to support signing
- [ ] Update workflows with signing
- [ ] Test signing in staging
- [ ] Deploy to production with dual mode (signed + unsigned)
- [ ] Update documentation
- [ ] Announce signing to users
- [ ] Enable signature verification by default
- [ ] Remove unsigned fallback

## Security Reminders

- ✅ Never commit private keys to git
- ✅ Use strong passphrase (20+ characters)
- ✅ Store revocation certificate offline
- ✅ Limit access to private keys (maintainers only)
- ✅ Enable 2FA on GitHub/AWS
- ✅ Rotate keys every 2 years
- ✅ Monitor for unauthorized signing
- ✅ Keep backup of private key offline

## References

- [Spack GPG Commands](https://spack.readthedocs.io/en/latest/command_index.html#spack-gpg)
- [Spack Buildcache Signing](https://spack.readthedocs.io/en/latest/binary_caches.html#signing-binaries)
- [GPG Manual](https://www.gnupg.org/documentation/manuals/gnupg/)

---

For complete implementation details, see [BUILDCACHE_SIGNING_IMPLEMENTATION_PLAN.md](./BUILDCACHE_SIGNING_IMPLEMENTATION_PLAN.md).
