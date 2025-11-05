# Spack Patches for slurm-factory

This directory contains patches that need to be applied to fix issues with Spack and custom packages.

## compiler_wrapper None Check Patch

### Files
- `0001-Add-compiler_wrapper-package-with-better-None-handli.patch` - For slurm-factory-spack-repo

### Purpose
This patch adds a custom `compiler_wrapper` package to the slurm-factory-spack-repo that provides better error handling when compiler paths are None.

### How to Apply

1. Clone the slurm-factory-spack-repo:
   ```bash
   git clone https://github.com/vantagecompute/slurm-factory-spack-repo.git
   cd slurm-factory-spack-repo
   ```

2. Apply the patch:
   ```bash
   git am /path/to/slurm-factory/patches/0001-Add-compiler_wrapper-package-with-better-None-handli.patch
   ```

3. Push the changes:
   ```bash
   git push origin main
   ```

### What It Fixes
The builtin Spack `compiler_wrapper` package (in Spack v1.0.0) has a bug where it sets environment variables like `SPACK_CC` to `None` when the compiler package doesn't have the `cc` attribute properly set. This causes confusing errors like `exec: None: not found`.

Our custom package:
1. Checks if the compiler path is None before setting the environment variable
2. Fails fast with a clear error message explaining what went wrong
3. Helps diagnose configuration issues with compilers

### Note
This patch is a **defense-in-depth** measure. The main fix is in `slurm_factory/constants.py` where we explicitly specify the `languages` variant for GCC, which prevents the compiler paths from being None in the first place.
