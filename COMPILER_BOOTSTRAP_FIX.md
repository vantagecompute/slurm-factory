# Compiler Bootstrap Fix - Summary

## Issue Description
The Slurm Factory Dockerfile had a critical bug where the Slurm build was attempted in the wrong Spack environment, causing builds to fail.

## Root Cause
In `slurm_factory/constants.py`, the `get_spack_build_script()` function generated a bash script that:
1. Created a temporary environment at `/tmp/compiler-install` to install GCC
2. Registered the compiler globally
3. **BUG**: Stayed in the `/tmp/compiler-install` environment and tried to build Slurm there
4. This environment only has the `gcc` spec, not the Slurm specs!

## The Fix
Added two critical lines to switch to the Slurm project environment:

```bash
echo '==> Switching to Slurm project environment...' && \
cd /root/spack-project && \
spack env activate . && \
```

## Before (Broken)
```bash
# In /tmp/compiler-install
spack compiler find --scope site /opt/spack-compiler-view
spack env activate .              # ❌ Still in compiler-install env!
spack concretize                  # ❌ No Slurm specs here!
spack install                     # ❌ Fails - nothing to build!
```

## After (Fixed)
```bash
# In /tmp/compiler-install
spack compiler find --scope site /opt/spack-compiler-view

# Switch to Slurm environment
cd /root/spack-project             # ✓ Change directory
spack env activate .               # ✓ Activate Slurm env
spack concretize                   # ✓ Concretize Slurm specs
spack install                      # ✓ Build Slurm successfully
```

## Why This Works
From Spack documentation on compiler scopes:
- Compilers registered at `--scope site` are **global**
- They are available to **all** Spack environments
- No need to stay in the compiler-install environment
- Can switch to any environment and use the registered compiler

Reference: https://spack.readthedocs.io/en/latest/configuring_compilers.html

## Files Changed
1. `slurm_factory/constants.py`
   - Updated `get_spack_build_script()` to switch directories
   - Added comprehensive docstring explaining two-stage process

2. `slurm_factory/spack_yaml.py`
   - Enhanced docstrings for `generate_compiler_bootstrap_config()`
   - Documented `get_gcc_buildcache_requirements()` importance

3. `tests/test_compiler_bootstrap.py` (new)
   - 15 test cases validating the fix
   - Tests environment switching order
   - Validates GCC requirements consistency

## Validation
All validation tests pass:
```
✓ Compiler install dir created
✓ Compiler view at /opt/spack-compiler-view
✓ Compiler registration command present
✓ Directory switch to /root/spack-project
✓ Switch happens BEFORE environment activation
✓ Environment activation in correct environment
✓ GCC requirements match between bootstrap and Slurm
✓ Both configs prevent system GCC detection
```

## Build Process Flow (Corrected)

### Stage 1: Compiler Bootstrap
```bash
cd /tmp/compiler-install
cat > spack.yaml <<EOF
spack:
  specs:
  - gcc@13.4.0
  view: /opt/spack-compiler-view
EOF

spack -e . install --cache-only
# Installs gcc to /opt/spack-compiler-install
# Creates view at /opt/spack-compiler-view

spack compiler find --scope site /opt/spack-compiler-view
# Registers gcc@13.4.0 globally
```

### Stage 2: Slurm Build
```bash
cd /root/spack-project
# spack.yaml here has Slurm specs with %gcc@13.4.0

spack env activate .
spack concretize
# Uses registered gcc@13.4.0 for all specs

spack install
# Builds Slurm and dependencies
```

## Key Learnings

1. **Spack Environment Isolation**
   - Each environment has its own specs
   - Activating wrong environment = building wrong specs
   - Always verify you're in the correct directory before `spack env activate`

2. **Global Compiler Registration**
   - `spack compiler find --scope site` makes compiler available everywhere
   - No need to stay in the environment where compiler was built
   - Compiler paths are absolute, work from any environment

3. **Variant Consistency**
   - GCC variants must match between bootstrap and Slurm environments
   - Function `get_gcc_buildcache_requirements()` ensures this
   - Mismatched variants = rebuild from source (wastes time)

4. **Toolchains Not Needed**
   - Reviewed Spack toolchains documentation
   - Toolchains are for complex multi-compiler setups
   - Our simple GCC-only case doesn't need toolchains
   - Current approach is simpler and more maintainable

## Testing
Created test Dockerfile that validates:
- Compiler bootstrap spack.yaml concretizes correctly
- Compiler registration works  
- Slurm environment uses registered compiler
- All specs constrained to %gcc@13.4.0

## References
- [Spack Compiler Configuration](https://spack.readthedocs.io/en/latest/configuring_compilers.html)
- [Spack Toolchains](https://spack.readthedocs.io/en/latest/toolchains_yaml.html)
- [Spack Environments](https://spack.readthedocs.io/en/latest/environments.html)
- [Spack Views](https://spack.readthedocs.io/en/latest/environments.html#filesystem-views)
