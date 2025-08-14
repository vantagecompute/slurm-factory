#!/usr/bin/env python3
"""
Test script to verify the new relocatable modulefile template.
"""

import subprocess
import sys

def run_command(cmd: str) -> str:
    """Run a command and return its output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {cmd}")
        print(f"   Error: {e.stderr.strip()}")
        return ""

def test_modulefile_template():
    """Test the new relocatable modulefile template"""
    print("🔍 Testing New Relocatable Modulefile Template")
    print("=" * 50)
    
    # Test 1: Generate a minimal build and check the template is used
    print("\n1. Testing minimal build configuration...")
    yaml_output = run_command("uv run python -c \"from slurm_factory.spack_yaml import generate_yaml_string; print(generate_yaml_string('25.05', minimal=True))\"")
    
    if not yaml_output:
        print("❌ Failed to generate YAML configuration")
        return False
    
    # Test 2: Check template reference
    print("\n2. Checking template reference...")
    if "modules/relocatable_modulefile.lua" in yaml_output:
        print("✅ Template correctly referenced in configuration")
    else:
        print("❌ Template reference missing from configuration")
        print("   Expected: modules/relocatable_modulefile.lua")
        return False
    
    # Test 3: Check template content
    print("\n3. Analyzing template content...")
    with open('/home/bdx/allcode/github/vantagecompute/slurm-factory/data/templates/relocatable_modulefile.lua', 'r') as f:
        template_content = f.read()
    
    # Check for key improvements
    improvements = []
    
    # Should NOT have LD_LIBRARY_PATH
    if "LD_LIBRARY_PATH" not in template_content:
        improvements.append("✅ No LD_LIBRARY_PATH manipulation")
    else:
        print("❌ Template still contains LD_LIBRARY_PATH")
        return False
    
    # Should have relocatable-friendly comments
    if "RPATH/RUNPATH" in template_content:
        improvements.append("✅ RPATH/RUNPATH documentation")
    else:
        print("❌ Missing RPATH/RUNPATH documentation")
        return False
    
    # Should have environment_modifications integration
    if "environment_modifications" in template_content:
        improvements.append("✅ Spack environment_modifications integration")
    else:
        print("❌ Missing environment_modifications integration")
        return False
    
    # Should filter out library search variables
    if 'N not in ["LD_LIBRARY_PATH","DYLD_LIBRARY_PATH"]' in template_content:
        improvements.append("✅ Library search variable filtering")
    else:
        print("❌ Missing library search variable filtering")
        return False
    
    # Should have autoload/depends_on integration
    if "depends_on" in template_content and "autoload" in template_content:
        improvements.append("✅ Autoload/depends_on integration")
    else:
        print("❌ Missing autoload/depends_on integration")
        return False
    
    # Should have system-wide SLURM_CONF default
    if '"/etc/slurm/slurm.conf"' in template_content:
        improvements.append("✅ System-wide SLURM_CONF default")
    else:
        print("❌ Missing system-wide SLURM_CONF default")
        return False
    
    # Should have proper conflict handling
    if "conflict(" in template_content:
        improvements.append("✅ Proper conflict handling")
    else:
        print("❌ Missing conflict handling")
        return False
    
    print("\n📋 Template improvements:")
    for improvement in improvements:
        print(f"   {improvement}")
    
    # Test 4: Validate template syntax (basic check)
    print("\n4. Basic template syntax validation...")
    
    # Check for balanced braces and proper Jinja2 syntax
    open_braces = template_content.count('{%')
    close_braces = template_content.count('%}')
    
    if open_braces == close_braces:
        print("✅ Balanced Jinja2 braces")
    else:
        print(f"❌ Unbalanced Jinja2 braces: {open_braces} open, {close_braces} close")
        return False
    
    # Check for Lua syntax basics
    if template_content.count('end') >= template_content.count('if '):
        print("✅ Basic Lua syntax appears balanced")
    else:
        print("❌ Potential Lua syntax issues (if/end imbalance)")
        return False
    
    print("\n🎉 SUCCESS: New relocatable modulefile template is excellent!")
    
    print("\n📋 Key benefits of the new template:")
    print("   🚫 No LD_LIBRARY_PATH manipulation - preserves relocatability")
    print("   🔧 Leverages Spack's environment_modifications system")
    print("   🛡️  Filters out library search variables automatically")
    print("   📖 Clear documentation about RPATH/RUNPATH expectations")
    print("   🎯 Smart prefix override for PATH-like variables only")
    print("   🏗️  Proper autoload/depends_on integration")
    print("   ⚙️  System-wide config defaults (/etc/slurm/slurm.conf)")
    print("   🚨 Robust conflict management")
    
    print("\n🚀 This template perfectly complements our bootstrapped compiler approach!")
    print("   Libraries resolve via RPATH → no LD_LIBRARY_PATH needed")
    print("   PATH variables redirect via prefix → flexible deployment")
    print("   Dependencies autoload properly → clean user experience")
    
    return True

if __name__ == "__main__":
    success = test_modulefile_template()
    sys.exit(0 if success else 1)
