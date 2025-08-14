#!/usr/bin/env python3
"""
Final comprehensive validation of truly relocatable Slurm configuration.
This script tests all 6 critical relocatability features.
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

def validate_relocatable_config():
    """Comprehensive validation of relocatable configuration"""
    print("🔍 Final Validation: Truly Relocatable Slurm Configuration")
    print("=" * 60)
    
    # Test 1: Generate standard configuration
    print("\n1. Testing standard configuration generation...")
    yaml_output = run_command("uv run python -c \"from slurm_factory.spack_yaml import generate_yaml_string; print(generate_yaml_string('25.05'))\"")
    
    if not yaml_output:
        print("❌ Failed to generate YAML configuration")
        return False
    
    try:
        config = yaml.safe_load(yaml_output)
    except yaml.YAMLError as e:
        print(f"❌ Invalid YAML generated: {e}")
        return False
    
    print("✅ YAML configuration generated successfully")
    
    # Test 2: Check all 6 relocatability features
    features_found = []
    
    # Feature 1: Bootstrapped compiler in specs
    specs = config.get('spack', {}).get('specs', [])
    has_bootstrapped_gcc = any('gcc@13.3.0' in str(spec) and '+binutils' in str(spec) for spec in specs)
    has_gcc_runtime = any('gcc-runtime@13.3.0' in str(spec) for spec in specs)
    has_slurm_with_gcc = any('slurm@' in str(spec) and '%gcc@13.3.0' in str(spec) for spec in specs)
    
    if has_bootstrapped_gcc and has_gcc_runtime and has_slurm_with_gcc:
        features_found.append("✅ Bootstrapped Compiler (gcc@13.3.0 +binutils)")
    else:
        print("❌ Missing bootstrapped compiler configuration")
        print(f"   gcc@13.3.0 +binutils: {has_bootstrapped_gcc}")
        print(f"   gcc-runtime@13.3.0: {has_gcc_runtime}")
        print(f"   slurm with %gcc@13.3.0: {has_slurm_with_gcc}")
    
    # Feature 2: Toolchains configuration
    toolchains = config.get('spack', {}).get('toolchains', {})
    expected_toolchains = {'c': 'gcc@13.3.0', 'cxx': 'gcc@13.3.0', 'fortran': 'gcc@13.3.0'}
    if toolchains == expected_toolchains:
        features_found.append("✅ Toolchains Configuration")
    else:
        print(f"❌ Missing or incorrect toolchains: {toolchains}")
    
    # Feature 3: Shared linking policy
    shared_linking_policy = config.get('spack', {}).get('config', {}).get('shared_linking', {}).get('missing_library_policy')
    if shared_linking_policy == 'error':
        features_found.append("✅ Shared Linking Policy (error)")
    else:
        print(f"❌ Missing or incorrect shared linking policy: {shared_linking_policy}")
    
    # Feature 4: Install tree padding
    padded_length = config.get('spack', {}).get('config', {}).get('install_tree', {}).get('padded_length')
    if padded_length == 0:
        features_found.append("✅ Install Tree Padding (0)")
    else:
        print(f"❌ Missing or incorrect install tree padding: {padded_length}")
    
    # Feature 5: Module exclude_env_vars
    modules_config = config.get('spack', {}).get('modules', {}).get('default', {}).get('lmod', {}).get('all', {})
    exclude_vars = modules_config.get('exclude_env_vars', [])
    expected_excluded = {'LD_LIBRARY_PATH', 'DYLD_LIBRARY_PATH'}
    if set(exclude_vars) >= expected_excluded:
        features_found.append("✅ Module LD_LIBRARY_PATH Exclusion")
    else:
        print(f"❌ Missing module exclude_env_vars: {exclude_vars}")
    
    # Feature 6: Spack-built runtime dependencies
    packages = config.get('spack', {}).get('packages', {})
    runtime_deps = ['linux-pam', 'libevent', 'jansson', 'libyaml', 'bzip2', 'xz', 'zstd']
    spack_built_count = sum(1 for dep in runtime_deps if packages.get(dep, {}).get('buildable', False))
    
    if spack_built_count >= 6:  # Allow some flexibility
        features_found.append("✅ Spack-Built Runtime Dependencies")
    else:
        print(f"❌ Insufficient Spack-built runtime dependencies: {spack_built_count}/7")
    
    print(f"\n📊 Features implemented: {len(features_found)}/6")
    for feature in features_found:
        print(f"   {feature}")
    
    # Test 3: Verify --verify flag works
    print("\n2. Testing --verify flag...")
    verify_output = run_command("uv run python -c \"from slurm_factory.spack_yaml import generate_yaml_string; print(generate_yaml_string('25.05', enable_verification=True))\"")
    
    if verify_output:
        verify_config = yaml.safe_load(verify_output)
        verify_settings = verify_config.get('spack', {}).get('config', {}).get('verify', {})
        expected_verify = {'relocatable': True, 'dependencies': True, 'shared_libraries': True}
        
        if verify_settings == expected_verify:
            print("✅ Verification mode working correctly")
        else:
            print(f"❌ Verification settings incorrect: {verify_settings}")
            return False
    else:
        print("❌ Failed to generate verification configuration")
        return False
    
    # Test 4: CLI integration
    print("\n3. Testing CLI integration...")
    cli_help = run_command("uv run slurm-factory build --help")
    if "--verify" in cli_help:
        print("✅ CLI --verify flag available")
    else:
        print("❌ CLI --verify flag missing")
        return False
    
    # Final assessment
    if len(features_found) == 6:
        print("\n🎉 SUCCESS: All relocatability features implemented!")
        print("\n📋 Next Steps:")
        print("   1. Test build process: uv run slurm-factory build --minimal")
        print("   2. Verify relocatability: spack -e . verify libraries slurm")
        print("   3. Test module loading without LD_LIBRARY_PATH")
        print("   4. Deploy to production HPC systems")
        return True
    else:
        print(f"\n❌ INCOMPLETE: {len(features_found)}/6 features implemented")
        return False

if __name__ == "__main__":
    success = validate_relocatable_config()
    sys.exit(0 if success else 1)
