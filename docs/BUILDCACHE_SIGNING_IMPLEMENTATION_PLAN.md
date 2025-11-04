# Buildcache Package Signing Implementation Plan

## Executive Summary

This document outlines the implementation plan for adding GPG signing support to the Slurm Factory buildcache. Currently, all buildcache operations use the `--unsigned` flag and mirrors are configured with `signed: False`, which poses security risks for package distribution. This plan details the steps needed to implement secure package signing using Spack's GPG integration.

## Background

### Current State

The Slurm Factory project currently pushes unsigned packages to S3 buildcache:

1. **Compiler buildcache** (`publish_compiler_to_buildcache` in `utils.py`):
   - Uses `spack buildcache push --unsigned --update-index`
   - Published to: `s3://slurm-factory-spack-buildcache-4b670/compilers/{version}/buildcache`

2. **Slurm buildcache** (`push_to_buildcache` in `utils.py`):
   - Uses `spack buildcache push --unsigned --update-index`
   - Published to: `s3://slurm-factory-spack-buildcache-4b670/slurm/{version}/{compiler}/buildcache`

3. **Mirror configuration** (`spack_yaml.py`):
   - All mirrors configured with `"signed": False`
   - Installations use `--no-check-signature` flag

### Security Risks

Without package signing:
- **No authenticity verification**: Users cannot verify packages come from Vantage Compute
- **No integrity protection**: Packages could be modified in transit or on S3
- **Supply chain vulnerability**: Compromised S3 credentials could allow malicious package injection
- **No audit trail**: Cannot track who signed which package version

## Goals

1. **Security**: Enable cryptographic verification of all buildcache packages
2. **Trust**: Establish Vantage Compute as the verified publisher
3. **Compliance**: Meet security best practices for software distribution
4. **Transparency**: Provide clear documentation on package verification
5. **Backward Compatibility**: Support both signed and unsigned workflows during transition

## Implementation Phases

### Phase 1: GPG Key Management (Week 1)

#### 1.1 Key Generation

**Create organization GPG key:**
```bash
# Generate 4096-bit RSA key (industry standard)
gpg --full-generate-key
# Key type: RSA and RSA
# Key size: 4096
# Expiration: 2 years (renewable)
# Identity: Vantage Compute Slurm Factory <slurm-factory@vantagecompute.ai>
```

**Key properties:**
- **Algorithm**: RSA 4096-bit
- **Usage**: Signing only (not encryption)
- **Expiration**: 2 years with renewal process
- **Subkeys**: Optional signing subkeys for different environments
- **Passphrase**: Stored in GitHub Secrets / AWS Secrets Manager

**Export public key:**
```bash
# ASCII-armored public key for distribution
gpg --armor --export slurm-factory@vantagecompute.ai > vantage-slurm-factory.pub

# Binary public key for Spack
gpg --export slurm-factory@vantagecompute.ai > vantage-slurm-factory.gpg
```

#### 1.2 Key Storage and Distribution

**Secure storage locations:**

1. **Private key** (never commit to git):
   - GitHub Actions: `GPG_PRIVATE_KEY` secret (base64-encoded)
   - AWS Secrets Manager: For non-GitHub workflows
   - Developer machines: Individual GPG keyrings (import only)

2. **Public key distribution**:
   - S3 bucket: `s3://slurm-factory-spack-buildcache-4b670/keys/vantage-slurm-factory.pub`
   - CloudFront CDN: `https://slurm-factory-spack-binary-cache.vantagecompute.ai/keys/`
   - Git repository: `data/gpg-keys/vantage-slurm-factory.pub` (for transparency)
   - Key servers: Upload to `keys.openpgp.org`, `pgp.mit.edu`

**GitHub Actions secret setup:**
```bash
# Export private key (base64-encoded for GitHub secret)
gpg --armor --export-secret-keys slurm-factory@vantagecompute.ai | base64 -w0 > private-key-base64.txt

# Add to GitHub secrets as GPG_PRIVATE_KEY
# Add passphrase as GPG_PASSPHRASE
```

#### 1.3 Key Rotation Policy

**Key lifecycle:**
- **Primary key**: Rotated every 2 years
- **Signing subkeys**: Can be rotated independently
- **Revocation certificates**: Generated and stored securely offline
- **Old keys**: Kept for signature verification of old packages (append-only)

**Rotation process:**
1. Generate new key 30 days before expiration
2. Publish new public key to all distribution points
3. Update GitHub/AWS secrets with new private key
4. Continue signing with old key during transition (30 days)
5. Start signing with new key
6. Archive old private key securely (for emergency verification)
7. Update documentation with new key fingerprint

### Phase 2: Code Implementation (Week 2-3)

#### 2.1 New Configuration Module

Create `slurm_factory/signing.py`:

```python
"""GPG signing support for buildcache packages."""

import logging
import os
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class SigningConfig:
    """Configuration for GPG signing of buildcache packages."""
    
    def __init__(
        self,
        enabled: bool = True,
        key_id: Optional[str] = None,
        key_file: Optional[str] = None,
        passphrase: Optional[str] = None,
    ):
        self.enabled = enabled
        self.key_id = key_id or os.environ.get("GPG_KEY_ID")
        self.key_file = key_file or os.environ.get("GPG_KEY_FILE")
        self.passphrase = passphrase or os.environ.get("GPG_PASSPHRASE")
    
    @classmethod
    def from_environment(cls) -> "SigningConfig":
        """Create signing config from environment variables."""
        return cls(
            enabled=os.environ.get("ENABLE_SIGNING", "true").lower() == "true",
            key_id=os.environ.get("GPG_KEY_ID"),
            key_file=os.environ.get("GPG_KEY_FILE"),
            passphrase=os.environ.get("GPG_PASSPHRASE"),
        )
    
    def is_configured(self) -> bool:
        """Check if signing is properly configured."""
        if not self.enabled:
            return False
        return bool(self.key_id or self.key_file)


def import_signing_key(
    key_file: Optional[str] = None,
    key_data: Optional[str] = None,
) -> str:
    """
    Import GPG signing key into Spack's GPG keyring.
    
    Args:
        key_file: Path to GPG private key file
        key_data: Base64-encoded GPG private key data (GitHub Actions)
    
    Returns:
        Key ID/fingerprint of imported key
    """
    if key_data:
        # Decode base64 key data (from GitHub Actions secret)
        import base64
        key_bytes = base64.b64decode(key_data)
        result = subprocess.run(
            ["spack", "gpg", "trust", "-"],
            input=key_bytes,
            capture_output=True,
            timeout=30,
        )
    elif key_file:
        # Import from file
        result = subprocess.run(
            ["spack", "gpg", "trust", key_file],
            capture_output=True,
            text=True,
            timeout=30,
        )
    else:
        raise ValueError("Either key_file or key_data must be provided")
    
    if result.returncode != 0:
        raise RuntimeError(f"Failed to import GPG key: {result.stderr}")
    
    # Extract key ID from output
    # Parse "gpg: key XXXXXXXX: secret key imported"
    for line in result.stderr.split("\n"):
        if "secret key imported" in line:
            key_id = line.split("key ")[1].split(":")[0].strip()
            logger.info(f"Imported signing key: {key_id}")
            return key_id
    
    raise RuntimeError("Could not determine key ID from import output")


def get_signing_flags(config: SigningConfig) -> list[str]:
    """
    Get command-line flags for spack buildcache push.
    
    Args:
        config: Signing configuration
    
    Returns:
        List of flags to add to buildcache push command
    """
    if not config.enabled or not config.is_configured():
        logger.warning("Signing disabled or not configured, using --unsigned")
        return ["--unsigned"]
    
    flags = []
    if config.key_id:
        flags.extend(["--key", config.key_id])
    
    # Spack will use the default signing key if no --key specified
    return flags
```

#### 2.2 Update `utils.py`

**Modify `publish_compiler_to_buildcache`:**

```python
def publish_compiler_to_buildcache(
    image_tag: str,
    cache_dir: str,
    compiler_version: str = "13.4.0",
    verbose: bool = False,
    signing_config: Optional[SigningConfig] = None,
) -> None:
    """Publish compiler binaries to S3 buildcache with optional signing."""
    
    if signing_config is None:
        signing_config = SigningConfig.from_environment()
    
    # Import signing key if configured
    if signing_config.is_configured():
        # Set up GPG in container
        signing_setup_cmd = setup_signing_in_container(signing_config)
    else:
        signing_setup_cmd = ""
    
    # Get signing flags
    signing_flags = " ".join(get_signing_flags(signing_config))
    
    # Build command with signing support
    cmd = [
        # ... existing docker run setup ...
        "bash", "-c",
        f"{signing_setup_cmd}"
        f"source /opt/spack/share/spack/setup-env.sh && "
        f"cd /root/compiler-bootstrap && "
        f"spack mirror add --scope site s3-buildcache {s3_mirror_url} && "
        f"spack -e . buildcache push {signing_flags} --update-index "
        f"--without-build-dependencies s3-buildcache && "
        f"spack buildcache push {signing_flags} --update-index "
        f"--without-build-dependencies s3-buildcache gcc-runtime@{compiler_version} && "
        f"spack buildcache push {signing_flags} --update-index "
        f"--without-build-dependencies s3-buildcache compiler-wrapper@1.0",
    ]
```

**Similar updates for `push_to_buildcache`:**

```python
def push_to_buildcache(
    image_tag: str,
    version: str,
    compiler_version: str,
    publish_mode: str = "all",
    verbose: bool = False,
    signing_config: Optional[SigningConfig] = None,
) -> None:
    """Push Slurm specs to buildcache with optional signing."""
    
    if signing_config is None:
        signing_config = SigningConfig.from_environment()
    
    signing_flags = " ".join(get_signing_flags(signing_config))
    
    # Determine what to push based on publish_mode
    if publish_mode == "slurm":
        push_cmd = f"spack buildcache push {signing_flags} --update-index s3-buildcache slurm"
    elif publish_mode == "deps":
        push_cmd = f"spack -e . buildcache push {signing_flags} --update-index --only dependencies s3-buildcache"
    else:  # all
        push_cmd = f"spack -e . buildcache push {signing_flags} --update-index s3-buildcache"
```

#### 2.3 Update `spack_yaml.py`

**Add signing configuration to mirrors:**

```python
def generate_spack_config(
    # ... existing parameters ...
    verify_signatures: bool = True,
) -> Dict[str, Any]:
    """Generate Spack environment configuration with signing support."""
    
    # ... existing code ...
    
    config["spack"]["mirrors"] = {
        "spack-public": {
            "url": "https://mirror.spack.io",
            "signed": False,  # Spack public mirror is not signed
        },
        "slurm-factory-buildcache": {
            "url": f"https://slurm-factory-spack-binary-cache.vantagecompute.ai/compilers/{compiler_version}/buildcache",
            "signed": True,  # Our buildcache is now signed
        },
    }
    
    # Add GPG configuration
    if verify_signatures:
        config["spack"]["config"]["verify_ssl"] = True
        config["spack"]["config"]["suppress_gpg_warnings"] = False
```

#### 2.4 Update CLI Interface

**Add signing options to `main.py`:**

```python
@app.command()
def build_compiler(
    # ... existing parameters ...
    enable_signing: bool = typer.Option(
        True,
        "--enable-signing/--disable-signing",
        help="Enable GPG signing of buildcache packages (default: enabled)",
    ),
    gpg_key_id: Optional[str] = typer.Option(
        None,
        "--gpg-key-id",
        help="GPG key ID to use for signing (reads from GPG_KEY_ID env if not specified)",
    ),
):
    """Build compiler toolchain with optional signing."""
    
    signing_config = SigningConfig(
        enabled=enable_signing,
        key_id=gpg_key_id,
    )
    
    create_compiler_package(
        # ... existing parameters ...
        signing_config=signing_config,
    )
```

### Phase 3: CI/CD Integration (Week 3)

#### 3.1 GitHub Actions Setup

**Add secrets to GitHub repository:**

1. `GPG_PRIVATE_KEY`: Base64-encoded private key
2. `GPG_PASSPHRASE`: Key passphrase
3. `GPG_KEY_ID`: Key fingerprint (e.g., `0x1234567890ABCDEF`)

**Update workflow files:**

`.github/workflows/build-and-publish-compiler-buildcache.yml`:

```yaml
jobs:
  build-compiler-buildcache:
    steps:
      # ... existing steps ...
      
      - name: Import GPG signing key
        env:
          GPG_PRIVATE_KEY: ${{ secrets.GPG_PRIVATE_KEY }}
          GPG_PASSPHRASE: ${{ secrets.GPG_PASSPHRASE }}
        run: |
          echo "Setting up GPG signing..."
          echo "$GPG_PRIVATE_KEY" | base64 -d | gpg --batch --import
          echo "GPG key imported successfully"
          gpg --list-secret-keys
      
      - name: Build compiler and publish to buildcache
        env:
          GPG_KEY_ID: ${{ secrets.GPG_KEY_ID }}
          GPG_PASSPHRASE: ${{ secrets.GPG_PASSPHRASE }}
          ENABLE_SIGNING: "true"
        run: |
          uv run slurm-factory build-compiler \
            --compiler-version ${{ matrix.compiler_version }} \
            --publish \
            --enable-signing
```

#### 3.2 AWS Secrets Manager (Optional)

For non-GitHub workflows:

```python
def get_signing_config_from_aws() -> SigningConfig:
    """Retrieve signing configuration from AWS Secrets Manager."""
    import boto3
    
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId='slurm-factory/gpg-signing-key')
    
    secret = json.loads(response['SecretString'])
    return SigningConfig(
        enabled=True,
        key_id=secret['key_id'],
        key_file=secret.get('key_file'),
        passphrase=secret['passphrase'],
    )
```

### Phase 4: Documentation (Week 4)

#### 4.1 User Documentation

Create `docusaurus/docs/package-signing.md`:

```markdown
# Package Signing and Verification

All Slurm Factory buildcache packages are cryptographically signed using GPG
to ensure authenticity and integrity.

## Verifying Package Signatures

### Importing the Public Key

Download and import the Vantage Compute signing key:

\`\`\`bash
# Download public key
curl -O https://slurm-factory-spack-binary-cache.vantagecompute.ai/keys/vantage-slurm-factory.pub

# Import into Spack's GPG keyring
spack gpg trust vantage-slurm-factory.pub

# Verify import
spack gpg list
\`\`\`

### Automatic Signature Verification

When installing from signed buildcache, Spack automatically verifies signatures:

\`\`\`bash
# Signatures verified automatically
spack install gcc@13.4.0

# Force verification (fail if signature missing)
spack install --require-signed gcc@13.4.0
\`\`\`

### Manual Verification

Verify a specific package signature:

\`\`\`bash
# List available packages with signatures
spack buildcache list -l

# Install with explicit verification
spack install --verify gcc@13.4.0
\`\`\`

## Key Information

**Signing Key Details:**
- **Email**: slurm-factory@vantagecompute.ai
- **Fingerprint**: `[FINGERPRINT WILL BE ADDED]`
- **Algorithm**: RSA 4096-bit
- **Expires**: [EXPIRATION DATE]

**Public Key Locations:**
- HTTPS: https://slurm-factory-spack-binary-cache.vantagecompute.ai/keys/vantage-slurm-factory.pub
- S3: s3://slurm-factory-spack-buildcache-4b670/keys/vantage-slurm-factory.pub
- Key Server: keys.openpgp.org

## Security Contact

Report security issues to: security@vantagecompute.ai
```

#### 4.2 Developer Documentation

Update `docs/contributing.md`:

```markdown
## Package Signing

### For Maintainers

Building signed packages requires access to the GPG signing key:

\`\`\`bash
# Set up GPG key (one time)
export GPG_KEY_ID="[KEY_ID]"
export GPG_PASSPHRASE="[PASSPHRASE]"

# Build with signing enabled
slurm-factory build-compiler --compiler-version 13.4.0 --publish --enable-signing
\`\`\`

### For Contributors

Contributors do not need signing keys for development:

\`\`\`bash
# Build locally without signing
slurm-factory build-compiler --compiler-version 13.4.0 --disable-signing
\`\`\`

### Signing Key Management

- Private keys are stored in GitHub Secrets and AWS Secrets Manager
- Only release maintainers have access to signing keys
- Key rotation occurs every 2 years
- Revocation certificates are stored offline
```

### Phase 5: Testing (Week 4-5)

#### 5.1 Unit Tests

Create `tests/test_signing.py`:

```python
import pytest
from slurm_factory.signing import SigningConfig, get_signing_flags


def test_signing_config_default():
    """Test default signing configuration."""
    config = SigningConfig()
    assert config.enabled is True
    assert config.key_id is None


def test_signing_config_from_environment(monkeypatch):
    """Test signing config from environment variables."""
    monkeypatch.setenv("GPG_KEY_ID", "0x1234567890ABCDEF")
    monkeypatch.setenv("ENABLE_SIGNING", "true")
    
    config = SigningConfig.from_environment()
    assert config.enabled is True
    assert config.key_id == "0x1234567890ABCDEF"


def test_signing_flags_enabled():
    """Test signing flags when enabled."""
    config = SigningConfig(enabled=True, key_id="0x1234567890ABCDEF")
    flags = get_signing_flags(config)
    assert flags == ["--key", "0x1234567890ABCDEF"]


def test_signing_flags_disabled():
    """Test signing flags when disabled."""
    config = SigningConfig(enabled=False)
    flags = get_signing_flags(config)
    assert flags == ["--unsigned"]


def test_signing_config_not_configured():
    """Test signing config validation."""
    config = SigningConfig(enabled=True, key_id=None)
    assert config.is_configured() is False
```

#### 5.2 Integration Tests

```python
def test_signed_buildcache_workflow():
    """Integration test for signed buildcache workflow."""
    # This would be a longer test that:
    # 1. Generates a test GPG key
    # 2. Builds a package with signing
    # 3. Verifies the signature
    # 4. Tests installation with signature verification
    pass
```

### Phase 6: Transition Plan (Week 5-6)

#### 6.1 Gradual Rollout

**Week 1-2: Dual Signing**
- Sign all new packages
- Keep `--unsigned` fallback for compatibility
- Publish public key to all distribution points
- Update documentation

**Week 3-4: Soft Enforcement**
- Mirror config: `"signed": True` but optional verification
- Users can opt-in to signature verification
- Monitor for signature verification errors

**Week 5-6: Full Enforcement**
- Remove `--unsigned` flags from all operations
- Mirror config: Require signatures
- Remove `--no-check-signature` from examples
- Archive unsigned packages (with warnings)

#### 6.2 Backward Compatibility

**Support matrix:**

| Phase | New Packages | Old Packages | Verification |
|-------|--------------|--------------|--------------|
| 1-2   | Signed       | Unsigned     | Optional     |
| 3-4   | Signed       | Unsigned     | Recommended  |
| 5-6   | Signed       | Deprecated   | Required     |

**Migration for existing users:**

```bash
# Import public key (once)
spack gpg trust https://slurm-factory-spack-binary-cache.vantagecompute.ai/keys/vantage-slurm-factory.pub

# Continue using packages normally - signatures verified automatically
spack install gcc@13.4.0
```

## Implementation Checklist

### Phase 1: GPG Key Management
- [ ] Generate organization GPG key (4096-bit RSA)
- [ ] Export public and private keys
- [ ] Store private key in GitHub Secrets
- [ ] Store private key in AWS Secrets Manager
- [ ] Publish public key to S3/CloudFront
- [ ] Upload public key to key servers
- [ ] Create revocation certificate (offline storage)
- [ ] Document key fingerprint and expiration

### Phase 2: Code Implementation
- [ ] Create `slurm_factory/signing.py` module
- [ ] Implement `SigningConfig` class
- [ ] Implement `import_signing_key()` function
- [ ] Implement `get_signing_flags()` function
- [ ] Update `publish_compiler_to_buildcache()` in utils.py
- [ ] Update `push_to_buildcache()` in utils.py
- [ ] Update mirror configuration in spack_yaml.py
- [ ] Add CLI options to main.py
- [ ] Add environment variable support

### Phase 3: CI/CD Integration
- [ ] Add GPG secrets to GitHub repository
- [ ] Update compiler buildcache workflow
- [ ] Update Slurm buildcache workflow
- [ ] Test signing in CI/CD pipeline
- [ ] Document AWS Secrets Manager setup (optional)

### Phase 4: Documentation
- [ ] Create package signing documentation
- [ ] Update user installation guide
- [ ] Update contributor guide
- [ ] Add security contact information
- [ ] Document key rotation procedure
- [ ] Create troubleshooting guide

### Phase 5: Testing
- [ ] Write unit tests for signing module
- [ ] Write integration tests for signed packages
- [ ] Test signature verification workflow
- [ ] Test backward compatibility
- [ ] Test key rotation process

### Phase 6: Transition
- [ ] Enable dual signing (signed + unsigned)
- [ ] Monitor for signature verification errors
- [ ] Publish announcements about signing
- [ ] Soft-enforce signature verification
- [ ] Full enforcement with required signatures
- [ ] Archive unsigned packages

## Security Considerations

### Key Security
- **Private key access**: Limit to release maintainers only
- **Key storage**: Never commit private keys to git
- **GitHub Secrets**: Use for CI/CD workflows
- **AWS Secrets Manager**: For non-GitHub automation
- **Passphrase**: Strong, randomly generated, stored separately
- **Key rotation**: Every 2 years with 30-day overlap

### Operational Security
- **Audit trail**: Log all signing operations
- **Access control**: Require 2FA for GitHub/AWS access
- **Monitoring**: Alert on unsigned package uploads
- **Incident response**: Plan for key compromise scenarios
- **Backup**: Offline backup of revocation certificates

### Verification Best Practices
- **Default behavior**: Verify signatures by default
- **Error handling**: Clear error messages for verification failures
- **Trust model**: Web of trust vs. direct trust
- **Key distribution**: Multiple independent channels
- **Expiration**: Enforce key expiration checks

## Success Metrics

### Security Metrics
- 100% of new packages signed within 30 days
- 0 unsigned packages after transition period
- 95%+ signature verification success rate
- < 1 hour key rotation downtime

### User Metrics
- Clear documentation for verification process
- < 5 support tickets about signing per month
- Positive user feedback on security improvements

### Operational Metrics
- CI/CD pipelines continue to function
- No increase in build times
- Automated key rotation process
- Regular security audits

## References

- [Spack Buildcache Documentation](https://spack.readthedocs.io/en/latest/binary_caches.html)
- [Spack GPG Documentation](https://spack.readthedocs.io/en/latest/signing.html)
- [OpenPGP Best Practices](https://riseup.net/en/security/message-security/openpgp/best-practices)
- [GPG Key Management](https://www.gnupg.org/documentation/manuals/gnupg/)

## Timeline Summary

| Week | Phase | Deliverables |
|------|-------|--------------|
| 1    | Phase 1 | GPG keys generated and distributed |
| 2-3  | Phase 2 | Code implementation complete |
| 3    | Phase 3 | CI/CD integration and testing |
| 4    | Phase 4 | Documentation complete |
| 4-5  | Phase 5 | All tests passing |
| 5-6  | Phase 6 | Gradual rollout and full enforcement |

**Total Duration**: 6 weeks

## Open Questions

1. Should we use a single signing key or separate keys per environment (dev/staging/prod)?
2. What should the key expiration period be? (Currently proposing 2 years)
3. Should we maintain a separate key for emergency revocations?
4. Do we need to sign old unsigned packages retroactively?
5. What is the process for adding additional authorized signers?

## Next Steps

1. **Immediate**: Review and approve this implementation plan
2. **Week 1**: Generate and distribute GPG keys
3. **Week 2**: Begin code implementation
4. **Week 3**: Submit initial PR for review
5. **Week 4**: Complete documentation and testing
6. **Week 5-6**: Execute transition plan

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-04  
**Author**: GitHub Copilot Agent  
**Reviewers**: TBD
