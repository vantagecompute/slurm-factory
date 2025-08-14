# Truly Relocatable Slurm Build Implementation

## Overview

Successfully implemented **truly relocatable** Slurm builds using advanced Spack 1.x features and best practices. These improvements ensure that Slurm packages can be moved between systems without any host-specific dependencies or path issues.

## Key Improvements Implemented

### 1. 🏗️ Bootstrapped Compiler (Most Important)
**Problem**: Using `/usr/bin/gcc` bakes in host glibc/libstdc++ assumptions
**Solution**: Build with a Spack-managed compiler
```yaml
specs:
  - gcc@13.3.0 +binutils          # Build bootstrapped compiler first
  - gcc-runtime@13.3.0 +shared ~static  # Explicit runtime libraries
  - slurm@25-05-1-1 %gcc@13.3.0   # Build Slurm with Spack-built gcc
```
**Workflow**:
1. `spack -e . concretize` - Build plan includes gcc & gcc-runtime
2. `spack -e . install gcc` - Install bootstrapped compiler
3. `spack -e . compiler find` - Register installed gcc into environment
4. `spack -e . install` - Build Slurm with the bootstrapped gcc

### 2. 🚫 Removed LD_LIBRARY_PATH from Modules
**Problem**: LD_LIBRARY_PATH undermines relocatability and masks missing RPATHs
**Solution**: Rely on proper RPATH/RUNPATH configuration
```yaml
modules:
  default:
    lmod:
      all:
        exclude_env_vars: [LD_LIBRARY_PATH, DYLD_LIBRARY_PATH]
      slurm:
        environment:
          prepend_path:
            # Only essential paths - no LD_LIBRARY_PATH
            PATH: '{prefix}/bin:{prefix}/sbin'
            CPATH: '{prefix}/include'
            PKG_CONFIG_PATH: '{prefix}/lib/pkgconfig'
```

### 3. 📦 Spack-Built Runtime Dependencies
**Problem**: External packages reduce relocatability (not in buildcache)
**Solution**: Build runtime-linked libraries with Spack
```yaml
packages:
  # Now Spack-built for true relocatability
  linux-pam: {buildable: true}     # Slurm PAM authentication
  libevent: {buildable: true}       # Used by PMIx/OpenMPI
  jansson: {buildable: true}        # JSON parsing
  libyaml: {buildable: true}        # Configuration parsing
  bzip2: {buildable: true}          # Compression (transitive)
  xz: {buildable: true}             # LZMA compression (transitive)
  zstd: {buildable: true}           # Fast compression (transitive)
```

### 4. 🎯 Explicit Compiler Toolchains
**Purpose**: Consistent compiler usage across all languages
```yaml
toolchains:
  c: gcc@13.3.0
  cxx: gcc@13.3.0
  fortran: gcc@13.3.0
```

### 5. 🛡️ Enhanced Relocatability Validation
**Purpose**: Catch non-relocatable system linkage during builds
```yaml
config:
  shared_linking:
    missing_library_policy: error  # Fail on missing system libraries
  install_tree:
    padded_length: 0              # Short, portable install paths
  verify:                         # CI/testing verification
    relocatable: true
    dependencies: true
    shared_libraries: true
```

## API Enhancements

### New CLI Options
```bash
# Standard relocatable build
uv run slurm-factory build --minimal

# CI build with verification
uv run slurm-factory build --minimal --verify

# Check relocatability
spack -e . verify libraries slurm
```

### New Convenience Functions
```python
from slurm_factory.spack_yaml import verification_config

# Generate CI configuration with verification
config = verification_config('25.05', gpu_support=False)

# Check for bootstrapped compiler workflow
if any('gcc@13.3.0 +binutils' in spec for spec in config['spack']['specs']):
    print("✅ Bootstrapped compiler configured")
```

## Verification Steps

### 1. Check Specs Include Bootstrapped Compiler
```bash
spack -e . find --deps | grep "gcc@13.3.0.*+binutils"
```

### 2. Verify No System Library Dependencies
```bash
spack -e . verify libraries slurm
ldd $(spack -e . location -i slurm)/bin/slurmctld | grep -v /opt/slurm
```

### 3. Check RPATH Configuration
```bash
readelf -d $(spack -e . location -i slurm)/bin/slurmctld | grep RPATH
```

### 4. Test Module Loading Without LD_LIBRARY_PATH
```bash
unset LD_LIBRARY_PATH
module load slurm
slurmctld --version
```

## Benefits Achieved

### ✅ True Relocatability
- **No host dependencies**: All libraries built with Spack
- **Consistent compiler**: Same gcc used throughout the build
- **Proper RPATHs**: No need for LD_LIBRARY_PATH
- **Short paths**: Avoid filesystem limitations

### ✅ Enhanced Verification
- **Build-time checks**: Fail early on non-relocatable dependencies  
- **CI integration**: Optional verification mode for testing
- **Runtime validation**: Verify libraries and dependencies

### ✅ Cleaner Module System
- **No pollution**: LD_LIBRARY_PATH excluded globally
- **Self-contained**: All paths properly configured
- **Relocatable prefixes**: Dynamic path resolution

## Implementation Files

### Core Changes
- `slurm_factory/spack_yaml.py`: Enhanced configuration generation
- `slurm_factory/main.py`: Added `--verify` CLI flag
- `slurm_factory/builder.py`: Integrated verification parameter
- `data/templates/relocatable_modulefile.lua`: Custom relocatable template

### View Package Updates
Updated to include bootstrapped compiler and runtime dependencies:
```python
view_packages = [
    "slurm", "munge", "json-c", "curl", "openssl", "readline", "ncurses",
    "lz4", "zlib-ng", "hwloc", "numactl", "gcc-runtime", "gcc",
    # Additional runtime-linked packages for true relocatability  
    "linux-pam", "libevent", "jansson", "libyaml", "bzip2", "xz", "zstd"
]
```

## Migration from Previous Builds

### For Existing Users
1. **Backup existing configurations**
2. **Update to new slurm-factory version**
3. **Use `--verify` flag for CI pipelines**
4. **Test relocatability with verification tools**

### Compatibility Notes
- **Backward compatible**: Existing builds continue to work
- **Opt-in verification**: Only enabled with `--verify` flag
- **Progressive adoption**: Can migrate gradually

## Performance Impact

### Build Time
- **Slightly longer**: Additional packages built with Spack
- **One-time cost**: Bootstrapped compiler cached after first build
- **Parallelizable**: Multi-stage build process

### Runtime Benefits
- **Faster loading**: No LD_LIBRARY_PATH searching
- **Better caching**: Proper RPATH enables system library caching
- **Reduced conflicts**: Self-contained library dependencies

This implementation represents a significant improvement in relocatability, following Spack 1.x best practices and ensuring truly portable Slurm deployments.
