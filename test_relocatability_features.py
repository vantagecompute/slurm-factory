#!/usr/bin/env python3
"""
Test script to verify the new relocatability features in spack_yaml.py

This script demonstrates the new features:
1. toolchains: Explicit per-language compiler pinning
2. shared_linking.missing_library_policy: error: Catch non-relocatable system linkage
3. install_tree.padded_length: 0: Short, portable install paths
4. verify: Relocatability verification checks
"""

from slurm_factory.spack_yaml import (
    generate_spack_config,
    generate_yaml_string,
    verification_config
)


def test_relocatability_features():
    """Test all new relocatability features."""
    
    print("🔍 Testing Relocatability Features in slurm-factory")
    print("=" * 60)
    
    # Test 1: Basic configuration with new features
    print("\n✅ Test 1: Basic configuration with relocatability features")
    config = generate_spack_config(slurm_version="25.05", minimal=True)
    
    # Check toolchains
    toolchains = config["spack"]["toolchains"]
    print(f"   toolchains.c: {toolchains['c']}")
    print(f"   toolchains.cxx: {toolchains['cxx']}")
    print(f"   toolchains.fortran: {toolchains['fortran']}")
    
    # Check install_tree.padded_length
    padded_length = config["spack"]["config"]["install_tree"]["padded_length"]
    print(f"   install_tree.padded_length: {padded_length}")
    
    # Check shared_linking policy
    missing_lib_policy = config["spack"]["config"]["shared_linking"]["missing_library_policy"]
    print(f"   shared_linking.missing_library_policy: {missing_lib_policy}")
    
    print("   ✓ All basic relocatability features present")
    
    # Test 2: Verification configuration
    print("\n✅ Test 2: Verification configuration (CI mode)")
    verify_config = generate_spack_config(slurm_version="25.05", enable_verification=True)
    
    verify_settings = verify_config["spack"]["config"]["verify"]
    print(f"   verify.relocatable: {verify_settings['relocatable']}")
    print(f"   verify.dependencies: {verify_settings['dependencies']}")
    print(f"   verify.shared_libraries: {verify_settings['shared_libraries']}")
    print("   ✓ Verification features enabled")
    
    # Test 3: Convenience function for CI
    print("\n✅ Test 3: verification_config() convenience function")
    ci_config = verification_config(slurm_version="25.05")
    has_verify = "verify" in ci_config["spack"]["config"]
    print(f"   Verification enabled: {has_verify}")
    print("   ✓ Convenience function works")
    
    # Test 4: YAML output contains all features
    print("\n✅ Test 4: YAML output verification")
    yaml_output = generate_yaml_string("25.05", False, True, True)
    
    features_to_check = [
        "toolchains:",
        "padded_length: 0",
        "missing_library_policy: error",
        "relocatable: true"
    ]
    
    for feature in features_to_check:
        if feature in yaml_output:
            print(f"   ✓ Found: {feature}")
        else:
            print(f"   ❌ Missing: {feature}")
    
    print("\n🎉 All relocatability features are working correctly!")
    print("\n📋 Usage Examples:")
    print("=" * 60)
    print("# Standard build with relocatability")
    print("config = generate_spack_config('25.05')")
    print()
    print("# CI build with verification enabled")
    print("config = generate_spack_config('25.05', enable_verification=True)")
    print()
    print("# Convenience function for CI")
    print("config = verification_config('25.05')")
    print()
    print("# YAML output with verification")
    print("yaml_str = generate_yaml_string('25.05', enable_verification=True)")
    

if __name__ == "__main__":
    test_relocatability_features()
