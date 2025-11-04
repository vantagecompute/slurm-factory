# Implementation Roadmap - Affected Code Areas

This document provides a quick reference of all code areas that need modification for buildcache signing implementation.

## Files to Create

### 1. `slurm_factory/signing.py` (NEW)

**Purpose**: Core signing configuration and utilities

**Key Components**:
- `SigningConfig` class - Configuration management
- `import_signing_key()` - Import GPG keys in Docker containers
- `get_signing_flags()` - Generate spack command flags
- `setup_signing_in_container()` - Configure GPG in Docker

**Estimated Lines**: ~200-300

**Priority**: HIGH - Required before any other changes

---

## Files to Modify

### 2. `slurm_factory/utils.py`

**Lines to Change**: 793, 795, 797, 902, 906, 910

**Function 1**: `publish_compiler_to_buildcache()` (line ~716)
```python
# Add parameter
signing_config: Optional[SigningConfig] = None

# Replace line 793-797
# OLD:
f"spack -e . buildcache push --unsigned --update-index "

# NEW:
signing_flags = " ".join(get_signing_flags(signing_config))
f"spack -e . buildcache push {signing_flags} --update-index "
```

**Function 2**: `push_to_buildcache()` (line ~840)
```python
# Add parameter
signing_config: Optional[SigningConfig] = None

# Replace line 902
# OLD:
push_cmd = "spack buildcache push --unsigned --update-index s3-buildcache slurm"

# NEW:
signing_flags = " ".join(get_signing_flags(signing_config))
push_cmd = f"spack buildcache push {signing_flags} --update-index s3-buildcache slurm"

# Similar changes for lines 906 and 910
```

**Estimated Changes**: ~30 lines modified, ~50 lines added

**Priority**: HIGH - Core functionality

---

### 3. `slurm_factory/spack_yaml.py`

**Lines to Change**: Mirror configuration sections

**Function 1**: `generate_compiler_bootstrap_config()` (line ~54)
```python
# Line ~147-151: Update mirrors section
"mirrors": {
    "spack-public": {"url": "https://mirror.spack.io", "signed": False},
    "slurm-factory-buildcache": {
        "url": f"https://slurm-factory-spack-binary-cache.vantagecompute.ai/compilers/{gcc_ver}/buildcache",
        "signed": True,  # CHANGE: Was False
    },
}
```

**Function 2**: `generate_spack_config()` (line ~302)
```python
# Line ~594-602: Update mirrors section
"mirrors": {
    "spack-public": {"url": "https://mirror.spack.io", "signed": False},
    "slurm-factory-buildcache": {
        "url": f"https://slurm-factory-spack-binary-cache.vantagecompute.ai/compilers/{compiler_version}/buildcache",
        "signed": True,  # CHANGE: Was False
    },
}

# Add GPG configuration (new section)
if verify_signatures:
    config["spack"]["config"]["suppress_gpg_warnings"] = False
```

**Estimated Changes**: ~10 lines modified, ~5 lines added

**Priority**: MEDIUM - Affects buildcache behavior

---

### 4. `slurm_factory/main.py`

**Functions to Update**: 
- `build_compiler()` - Add signing options
- `build()` - Add signing options

**New Parameters**:
```python
@app.command()
def build_compiler(
    # ... existing parameters ...
    enable_signing: bool = typer.Option(
        True,
        "--enable-signing/--disable-signing",
        help="Enable GPG signing of buildcache packages",
    ),
    gpg_key_id: Optional[str] = typer.Option(
        None,
        "--gpg-key-id",
        help="GPG key ID for signing (env: GPG_KEY_ID)",
    ),
):
    """Build compiler with signing support."""
    from .signing import SigningConfig
    
    signing_config = SigningConfig(
        enabled=enable_signing,
        key_id=gpg_key_id,
    )
    
    # Pass to builder
    create_compiler_package(
        # ... existing args ...
        signing_config=signing_config,
    )
```

**Estimated Changes**: ~40 lines added across 2 commands

**Priority**: MEDIUM - CLI interface

---

### 5. `slurm_factory/builder.py`

**Functions to Update**:
- `create_compiler_package()` - Accept signing_config parameter
- `create_slurm_package()` - Accept signing_config parameter

**Changes**:
```python
def create_compiler_package(
    # ... existing parameters ...
    signing_config: Optional[SigningConfig] = None,
):
    """Create compiler package with optional signing."""
    if signing_config is None:
        from .signing import SigningConfig
        signing_config = SigningConfig.from_environment()
    
    # Pass to publish function
    publish_compiler_to_buildcache(
        # ... existing args ...
        signing_config=signing_config,
    )
```

**Estimated Changes**: ~20 lines modified

**Priority**: MEDIUM - Integration layer

---

## Workflow Files to Modify

### 6. `.github/workflows/build-and-publish-compiler-buildcache.yml`

**Section 1**: Add GPG key import step (after "Configure AWS credentials")
```yaml
- name: Import GPG signing key
  env:
    GPG_PRIVATE_KEY: ${{ secrets.GPG_PRIVATE_KEY }}
    GPG_PASSPHRASE: ${{ secrets.GPG_PASSPHRASE }}
  run: |
    echo "Setting up GPG signing..."
    echo "$GPG_PRIVATE_KEY" | base64 -d | gpg --batch --import
    echo "GPG key imported successfully"
    gpg --list-secret-keys
```

**Section 2**: Update build step (line ~82-87)
```yaml
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

**Estimated Changes**: ~15 lines added

**Priority**: HIGH - CI/CD integration

---

### 7. `.github/workflows/build-and-publish-slurm-all.yml`

**Similar changes as above**:
- Add GPG key import step
- Update environment variables
- Add `--enable-signing` flag to build commands

**Estimated Changes**: ~15 lines added

**Priority**: HIGH - CI/CD integration

---

### 8. `.github/workflows/build-and-publish-slurm-tarball.yml`

**Similar changes as above**

**Estimated Changes**: ~15 lines added

**Priority**: MEDIUM - Additional workflow

---

## Test Files to Create

### 9. `tests/test_signing.py` (NEW)

**Test Coverage**:
- `test_signing_config_default()` - Default configuration
- `test_signing_config_from_environment()` - Environment variables
- `test_signing_flags_enabled()` - Signing enabled
- `test_signing_flags_disabled()` - Signing disabled
- `test_signing_config_not_configured()` - Invalid config
- `test_import_signing_key()` - Key import (integration)
- `test_signed_buildcache_workflow()` - Full workflow (integration)

**Estimated Lines**: ~150-200

**Priority**: HIGH - Quality assurance

---

### 10. `tests/test_utils.py`

**New Tests to Add**:
- `test_publish_compiler_with_signing()` - Signing enabled
- `test_publish_compiler_without_signing()` - Signing disabled
- `test_push_to_buildcache_with_signing()` - Various publish modes

**Estimated Lines**: ~50 lines added

**Priority**: MEDIUM - Existing functionality

---

### 11. `tests/test_spack_yaml.py`

**Tests to Update**:
- Update assertions for `signed: True` in mirrors
- Test signature verification configuration

**Estimated Lines**: ~20 lines modified

**Priority**: LOW - Configuration validation

---

## Documentation Files to Create/Update

### 12. `docusaurus/docs/package-signing.md` (NEW)

**Content**:
- User guide for signature verification
- Key import instructions
- Troubleshooting
- Security best practices

**Estimated Lines**: ~200

**Priority**: HIGH - User documentation

---

### 13. `docusaurus/docs/contributing.md`

**Section to Add**: "Package Signing for Maintainers"
- How to build signed packages
- GPG key access requirements
- Local development without signing

**Estimated Lines**: ~30 lines added

**Priority**: MEDIUM - Developer documentation

---

### 14. `README.md`

**Updates**:
- Mention signed packages in features
- Link to package-signing documentation
- Update installation examples (remove `--no-check-signature`)

**Estimated Lines**: ~10 lines modified

**Priority**: LOW - Main README

---

## GitHub Secrets Required

Add to repository settings:

1. **GPG_PRIVATE_KEY**: Base64-encoded private key
2. **GPG_PASSPHRASE**: Key passphrase
3. **GPG_KEY_ID**: Key fingerprint (e.g., `0x1234567890ABCDEF`)

**Priority**: CRITICAL - Required before CI/CD testing

---

## Data Files to Add

### 15. `data/gpg-keys/vantage-slurm-factory.pub` (NEW)

**Content**: ASCII-armored public GPG key

**Purpose**: Version-controlled copy of public key for transparency

**Estimated Lines**: ~50 (GPG public key block)

**Priority**: MEDIUM - Transparency

---

## Summary Statistics

| Category | Files | Est. Lines Added | Est. Lines Modified | Priority |
|----------|-------|------------------|---------------------|----------|
| **New Code** | 2 | 350-500 | 0 | HIGH |
| **Modified Code** | 4 | 130 | 80 | HIGH |
| **Workflows** | 3 | 45 | 10 | HIGH |
| **Tests** | 3 | 220 | 20 | HIGH |
| **Documentation** | 3 | 240 | 10 | MEDIUM |
| **Data Files** | 1 | 50 | 0 | MEDIUM |
| **TOTAL** | **16** | **1035-1185** | **120** | - |

## Implementation Order

1. **Week 1**: Generate GPG keys, add GitHub secrets
2. **Week 2**: Create `signing.py`, update `utils.py` and `builder.py`
3. **Week 2**: Update `spack_yaml.py` and `main.py`
4. **Week 3**: Update GitHub workflows, test in CI
5. **Week 4**: Create tests, update documentation
6. **Week 5**: Full integration testing
7. **Week 6**: Gradual rollout and monitoring

## Quick Links

- [Full Implementation Plan](./BUILDCACHE_SIGNING_IMPLEMENTATION_PLAN.md)
- [Quick Reference](./SIGNING_QUICK_REFERENCE.md)
- [Docs Index](./README.md)

---

**Last Updated**: 2025-11-04  
**Total Estimated Effort**: 6 weeks  
**Team Size**: 1-2 developers
