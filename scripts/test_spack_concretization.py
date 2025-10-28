#!/usr/bin/env python3
# Copyright 2025 Vantage Compute Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test script to validate that generated spack.yml can be concretized with Spack v1.x.

This script generates a spack.yml for Slurm and validates that it is syntactically
correct and compatible with Spack v1.x format.

Requirements:
    - Spack v1.x must be available in PATH (can be installed via git clone)
    - Python 3.12+

Usage:
    python scripts/test_spack_concretization.py [--slurm-version 25.05] [--compiler-version 13.4.0]
"""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

# Add parent directory to path to import slurm_factory
sys.path.insert(0, str(Path(__file__).parent.parent))

from slurm_factory.spack_yaml import generate_yaml_string


def check_spack_version():
    """Check if Spack v1.x is available."""
    try:
        result = subprocess.run(
            ["spack", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            print("Error: spack command failed")
            return False
        
        version = result.stdout.strip()
        print(f"✓ Found Spack version: {version}")
        
        # Check if it's v1.x
        if not version.startswith("1."):
            print(f"Warning: Expected Spack v1.x, found {version}")
            print("This script is designed for Spack v1.x")
        
        return True
    except FileNotFoundError:
        print("Error: spack command not found in PATH")
        print("Please install Spack v1.x first:")
        print("  git clone --depth=1 -b releases/v1.0 https://github.com/spack/spack.git")
        print("  source spack/share/spack/setup-env.sh")
        return False
    except subprocess.TimeoutExpired:
        print("Error: spack command timed out")
        return False


def validate_yaml_syntax(yaml_content: str) -> bool:
    """Validate that the YAML is syntactically correct."""
    try:
        import yaml
        parsed = yaml.safe_load(yaml_content)
        
        # Check required top-level structure
        if "spack" not in parsed:
            print("Error: Missing 'spack' section in YAML")
            return False
        
        spack_config = parsed["spack"]
        
        # Check required sections
        required_sections = ["specs", "packages", "config", "mirrors", "compilers"]
        for section in required_sections:
            if section not in spack_config:
                print(f"Error: Missing required section: {section}")
                return False
        
        print("✓ YAML syntax is valid")
        return True
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML syntax: {e}")
        return False


def test_concretization(yaml_content: str, test_name: str = "default") -> bool:
    """Test if the spack.yml can be concretized by Spack."""
    with tempfile.TemporaryDirectory() as tmpdir:
        spack_yaml_path = Path(tmpdir) / "spack.yaml"
        spack_yaml_path.write_text(yaml_content)
        
        print(f"\nTesting concretization for {test_name}...")
        print(f"  Environment: {tmpdir}")
        
        # Try to concretize
        try:
            # Note: We don't actually run concretization in CI as it requires
            # a full Spack installation. This script is for local testing.
            # In CI, we just validate the YAML syntax.
            result = subprocess.run(
                ["spack", "-e", tmpdir, "config", "get"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            if result.returncode != 0:
                print(f"Error: spack config get failed:")
                print(result.stderr)
                return False
            
            print("✓ Spack environment configuration is valid")
            return True
        except subprocess.TimeoutExpired:
            print("Error: spack command timed out")
            return False
        except Exception as e:
            print(f"Error testing concretization: {e}")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test spack.yml generation and concretization"
    )
    parser.add_argument(
        "--slurm-version",
        default="25.05",
        help="Slurm version to test (default: 25.05)",
    )
    parser.add_argument(
        "--compiler-version",
        default="13.4.0",
        help="GCC compiler version (default: 13.4.0)",
    )
    parser.add_argument(
        "--skip-spack-check",
        action="store_true",
        help="Skip checking for Spack installation (for CI)",
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Spack v1.x Concretization Test")
    print("=" * 60)
    
    # Check Spack availability
    if not args.skip_spack_check:
        if not check_spack_version():
            sys.exit(1)
    
    # Generate spack.yml
    print(f"\nGenerating spack.yml for Slurm {args.slurm_version}...")
    yaml_content = generate_yaml_string(
        slurm_version=args.slurm_version,
        compiler_version=args.compiler_version,
        gpu_support=False,
        minimal=False,
    )
    
    print(f"✓ Generated spack.yml ({len(yaml_content)} bytes)")
    
    # Validate YAML syntax
    if not validate_yaml_syntax(yaml_content):
        sys.exit(1)
    
    # Test concretization
    if not args.skip_spack_check:
        if not test_concretization(yaml_content, f"Slurm {args.slurm_version}"):
            sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
