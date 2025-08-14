#!/usr/bin/env python3
"""
Test script to verify the surgical fixes for truly self-contained + relocatable builds.
"""

import subprocess
import sys
import yaml
from pathlib import Path

def run_command(cmd: str) -> str:
    """Run a command and return its output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {cmd}")
        print(f"   Error: {e.stderr.strip()}")
        return ""

def test_surgical_fixes():
    """Test all surgical fixes for self-contained + relocatable builds"""
    print("🔍 Testing Surgical Fixes for Self-Contained + Relocatable Builds")
    print("=" * 70)
    
    # Test 1: Generate minimal configuration
    print("\n1. Testing minimal build configuration...")
    yaml_output = run_command("uv run python -c \"from slurm_factory.spack_yaml import generate_yaml_string; print(generate_yaml_string('25.05', minimal=True))\"")
    
    if not yaml_output:
        print("❌ Failed to generate YAML configuration")
        return False
    
    try:
        config = yaml.safe_load(yaml_output)
    except yaml.YAMLError as e:
        print(f"❌ Invalid YAML generated: {e}")
        return False
    
    print("✅ YAML configuration generated successfully")
    
    # Test 2: Verify no toolchains configuration (Fix #1)
    print("\n2. Checking for toolchains configuration...")
    if 'toolchains' in config.get('spack', {}):
        print("❌ Found toolchains configuration (should be removed)")
        print(f"   toolchains: {config['spack']['toolchains']}")
        return False
    else:
        print("✅ No toolchains configuration found (correct)")
    
    # Test 3: Verify PMIx is correctly handled (Fix #5 - user's request)
    print("\n3. Checking PMIx configuration...")
    specs = config.get('spack', {}).get('specs', [])
    view_packages = config.get('spack', {}).get('view', {}).get('default', {}).get('select', [])
    
    # Check that Slurm spec has ~pmix for minimal build
    slurm_spec = None
    for spec in specs:
        if 'slurm@' in str(spec):
            slurm_spec = str(spec)
            break
    
    if slurm_spec and '~pmix' in slurm_spec:
        print("✅ Slurm has ~pmix for minimal build")
    else:
        print(f"❌ Slurm spec incorrect: {slurm_spec}")
        return False
    
    # Check that PMIx is not in view packages for minimal build
    if 'pmix' not in view_packages:
        print("✅ PMIx not in view packages for minimal build")
    else:
        print("❌ PMIx found in view packages for minimal build")
        return False
    
    # Test 4: Verify SLURM_GCC_RUNTIME fix (Fix #3)
    print("\n4. Checking SLURM_GCC_RUNTIME configuration...")
    modules_config = config.get('spack', {}).get('modules', {}).get('default', {}).get('lmod', {})
    slurm_env = modules_config.get('slurm', {}).get('environment', {}).get('set', {})
    
    if 'SLURM_GCC_RUNTIME' in slurm_env:
        print(f"❌ Found old SLURM_GCC_RUNTIME: {slurm_env['SLURM_GCC_RUNTIME']}")
        return False
    elif 'SLURM_GCC_RUNTIME_PREFIX' in slurm_env:
        runtime_prefix = slurm_env['SLURM_GCC_RUNTIME_PREFIX']
        if '/lib64' not in runtime_prefix:
            print(f"✅ SLURM_GCC_RUNTIME_PREFIX without hardcoded lib64: {runtime_prefix}")
        else:
            print(f"❌ SLURM_GCC_RUNTIME_PREFIX still has lib64: {runtime_prefix}")
            return False
    else:
        print("❌ No GCC runtime prefix found")
        return False
    
    # Test 5: Verify LD_LIBRARY_PATH exclusion (Fix #4)
    print("\n5. Checking LD_LIBRARY_PATH exclusion...")
    exclude_vars = modules_config.get('all', {}).get('exclude_env_vars', [])
    if 'LD_LIBRARY_PATH' in exclude_vars and 'DYLD_LIBRARY_PATH' in exclude_vars:
        print("✅ LD_LIBRARY_PATH and DYLD_LIBRARY_PATH excluded from modules")
    else:
        print(f"❌ Missing library path exclusions: {exclude_vars}")
        return False
    
    # Test 6: Verify bootstrapped compiler specs (Fix #2)
    print("\n6. Checking bootstrapped compiler specs...")
    has_bootstrapped_gcc = any('gcc@13.3.0' in str(spec) and '+binutils' in str(spec) for spec in specs)
    has_gcc_runtime = any('gcc-runtime@13.3.0' in str(spec) for spec in specs)
    has_slurm_with_gcc = any('slurm@' in str(spec) and '%gcc@13.3.0' in str(spec) for spec in specs)
    
    if has_bootstrapped_gcc and has_gcc_runtime and has_slurm_with_gcc:
        print("✅ Bootstrapped compiler workflow configured correctly")
    else:
        print("❌ Missing bootstrapped compiler configuration")
        print(f"   gcc@13.3.0 +binutils: {has_bootstrapped_gcc}")
        print(f"   gcc-runtime@13.3.0: {has_gcc_runtime}")
        print(f"   slurm with %gcc@13.3.0: {has_slurm_with_gcc}")
        return False
    
    # Test 7: Verify shared linking policy and other relocatability features
    print("\n7. Checking relocatability configuration...")
    spack_config = config.get('spack', {}).get('config', {})
    
    shared_linking_policy = spack_config.get('shared_linking', {}).get('missing_library_policy')
    padded_length = spack_config.get('install_tree', {}).get('padded_length')
    
    if shared_linking_policy == 'error':
        print("✅ Shared linking policy set to 'error'")
    else:
        print(f"❌ Incorrect shared linking policy: {shared_linking_policy}")
        return False
    
    if padded_length == 0:
        print("✅ Install tree padding set to 0")
    else:
        print(f"❌ Incorrect install tree padding: {padded_length}")
        return False
    
    # Test 8: Test full build has PMIx
    print("\n8. Testing full build has PMIx...")
    full_yaml = run_command("uv run python -c \"from slurm_factory.spack_yaml import generate_yaml_string; print(generate_yaml_string('25.05', minimal=False))\"")
    full_config = yaml.safe_load(full_yaml)
    
    full_specs = full_config.get('spack', {}).get('specs', [])
    full_view = full_config.get('spack', {}).get('view', {}).get('default', {}).get('select', [])
    
    full_slurm_spec = None
    for spec in full_specs:
        if 'slurm@' in str(spec):
            full_slurm_spec = str(spec)
            break
    
    if full_slurm_spec and '+pmix' in full_slurm_spec and 'pmix' in full_view:
        print("✅ Full build correctly includes PMIx")
    else:
        print(f"❌ Full build PMIx configuration incorrect")
        print(f"   Slurm spec: {full_slurm_spec}")
        print(f"   PMIx in view: {'pmix' in full_view}")
        return False
    
    print("\n🎉 SUCCESS: All surgical fixes implemented correctly!")
    print("\n📋 Summary of fixes applied:")
    print("   ✅ Fix #1: No toolchains configuration (Spack handles this automatically)")
    print("   ✅ Fix #2: Bootstrapped compiler workflow (gcc@13.3.0 +binutils)")
    print("   ✅ Fix #3: SLURM_GCC_RUNTIME_PREFIX without hardcoded lib64")
    print("   ✅ Fix #4: LD_LIBRARY_PATH excluded from all modules") 
    print("   ✅ Fix #5: PMIx only included in non-minimal builds")
    print("   ✅ Fix #6: Shared linking policy and relocatability features")
    print("   ✅ Fix #7: Full build correctly includes PMIx")
    
    print("\n🚀 Next Steps:")
    print("   1. spack -e . concretize")
    print("   2. spack -e . install gcc@13.3.0") 
    print("   3. spack -e . compiler find $(spack -e . location -i gcc@13.3.0)")
    print("   4. spack -e . install")
    print("   5. spack -e . verify libraries slurm")
    
    return True

if __name__ == "__main__":
    success = test_surgical_fixes()
    sys.exit(0 if success else 1)
