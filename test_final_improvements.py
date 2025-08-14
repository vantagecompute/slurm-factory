#!/usr/bin/env python3
"""
Test script to verify the final high-impact improvements for truly self-contained + relocatable builds.
"""

import subprocess
import sys
import yaml

def run_command(cmd: str) -> str:
    """Run a command and return its output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {cmd}")
        print(f"   Error: {e.stderr.strip()}")
        return ""

def test_final_improvements():
    """Test all final high-impact improvements"""
    print("🎯 Testing Final High-Impact Improvements")
    print("=" * 50)
    
    # Test 1: Minimal build configuration
    print("\n1. Testing minimal build improvements...")
    minimal_yaml = run_command("uv run python -c \"from slurm_factory.spack_yaml import generate_yaml_string; print(generate_yaml_string('25.05', minimal=True))\"")
    
    if not minimal_yaml:
        print("❌ Failed to generate minimal YAML configuration")
        return False
    
    try:
        minimal_config = yaml.safe_load(minimal_yaml)
    except yaml.YAMLError as e:
        print(f"❌ Invalid YAML generated: {e}")
        return False
    
    # Test 2: Verify Munge in specs
    print("\n2. Checking Munge in specs...")
    specs = minimal_config.get('spack', {}).get('specs', [])
    has_munge_spec = any('munge' in str(spec) and '%gcc@13.3.0' in str(spec) for spec in specs)
    
    if has_munge_spec:
        print("✅ Munge included in specs with correct compiler")
    else:
        print("❌ Munge missing from specs or wrong compiler")
        print(f"   Specs: {specs}")
        return False
    
    # Test 3: Verify view alignment with variants
    print("\n3. Checking view alignment with Slurm variants...")
    view_packages = minimal_config.get('spack', {}).get('view', {}).get('default', {}).get('select', [])
    
    # For minimal build: hwloc should NOT be in view (since Slurm is ~hwloc)
    if 'hwloc' not in view_packages:
        print("✅ hwloc correctly excluded from minimal build view")
    else:
        print("❌ hwloc found in minimal build view (should be excluded)")
        return False
    
    # Verify Slurm has ~hwloc variant
    slurm_spec = None
    for spec in specs:
        if 'slurm@' in str(spec):
            slurm_spec = str(spec)
            break
    
    if slurm_spec and '~hwloc' in slurm_spec:
        print("✅ Slurm correctly configured with ~hwloc for minimal build")
    else:
        print(f"❌ Slurm spec incorrect: {slurm_spec}")
        return False
    
    # Test 4: Verify compiler preference
    print("\n4. Checking compiler preference...")
    packages_config = minimal_config.get('spack', {}).get('packages', {}).get('all', {})
    compiler_pref = packages_config.get('compiler', [])
    
    if 'gcc@13.3.0' in compiler_pref:
        print("✅ Compiler preference set to gcc@13.3.0")
    else:
        print(f"❌ Compiler preference incorrect: {compiler_pref}")
        return False
    
    # Test 5: Test full build includes hwloc
    print("\n5. Testing full build includes hwloc...")
    full_yaml = run_command("uv run python -c \"from slurm_factory.spack_yaml import generate_yaml_string; print(generate_yaml_string('25.05', minimal=False))\"")
    full_config = yaml.safe_load(full_yaml)
    
    full_view = full_config.get('spack', {}).get('view', {}).get('default', {}).get('select', [])
    full_specs = full_config.get('spack', {}).get('specs', [])
    
    # Full build should have hwloc in view and +hwloc in Slurm spec
    if 'hwloc' in full_view:
        print("✅ hwloc correctly included in full build view")
    else:
        print("❌ hwloc missing from full build view")
        return False
    
    full_slurm_spec = None
    for spec in full_specs:
        if 'slurm@' in str(spec):
            full_slurm_spec = str(spec)
            break
    
    if full_slurm_spec and '+hwloc' in full_slurm_spec:
        print("✅ Slurm correctly configured with +hwloc for full build")
    else:
        print(f"❌ Full build Slurm spec incorrect: {full_slurm_spec}")
        return False
    
    # Test 6: Verify all previous relocatability features still work
    print("\n6. Verifying relocatability features are preserved...")
    
    # Check bootstrapped compiler
    has_bootstrapped_gcc = any('gcc@13.3.0' in str(spec) and '+binutils' in str(spec) for spec in specs)
    has_gcc_runtime = any('gcc-runtime@13.3.0' in str(spec) for spec in specs)
    
    if has_bootstrapped_gcc and has_gcc_runtime:
        print("✅ Bootstrapped compiler workflow preserved")
    else:
        print("❌ Bootstrapped compiler configuration missing")
        return False
    
    # Check LD_LIBRARY_PATH exclusion
    modules_config = minimal_config.get('spack', {}).get('modules', {}).get('default', {}).get('lmod', {})
    exclude_vars = modules_config.get('all', {}).get('exclude_env_vars', [])
    
    if 'LD_LIBRARY_PATH' in exclude_vars:
        print("✅ LD_LIBRARY_PATH exclusion preserved")
    else:
        print("❌ LD_LIBRARY_PATH exclusion missing")
        return False
    
    # Check shared linking policy
    spack_config = minimal_config.get('spack', {}).get('config', {})
    shared_linking_policy = spack_config.get('shared_linking', {}).get('missing_library_policy')
    
    if shared_linking_policy == 'error':
        print("✅ Shared linking policy preserved")
    else:
        print("❌ Shared linking policy missing")
        return False
    
    print("\n🎉 SUCCESS: All high-impact improvements implemented correctly!")
    
    print("\n📋 Summary of improvements:")
    print("   ✅ Munge explicitly included in specs with correct compiler")
    print("   ✅ View packages aligned with Slurm variants")
    print("     • Minimal: hwloc excluded (matches ~hwloc)")
    print("     • Full: hwloc included (matches +hwloc)")
    print("   ✅ Compiler preference set to gcc@13.3.0")
    print("   ✅ All previous relocatability features preserved")
    
    print("\n🚀 Bootstrap workflow:")
    print("   1. spack -e . concretize")
    print("   2. spack -e . install gcc@13.3.0")
    print("   3. spack -e . compiler find $(spack -e . location -i gcc@13.3.0)")
    print("   4. spack -e . install")
    
    print("\n🔍 Relocatability validation commands:")
    print("   spack -e . verify libraries slurm")
    print("   ldd $(spack -e . location -i slurm)/bin/slurmctld | grep -E '=> /(lib|usr)' || echo 'No host libs'")
    print("   patchelf --print-rpath $(spack -e . location -i slurm)/bin/slurmctld")
    
    return True

if __name__ == "__main__":
    success = test_final_improvements()
    sys.exit(0 if success else 1)
