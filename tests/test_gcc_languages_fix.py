#!/usr/bin/env python3
"""
Test that GCC spec has languages variant properly set.

This test validates that when we specify 'gcc@X.Y.Z languages=c,c++,fortran',
the spec satisfies the language checks that GCC._cc_path() uses.
"""

import sys
import os

# Add slurm_factory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import directly from constants module to avoid loading the whole package
from slurm_factory import constants


def test_gcc_languages_variant_in_build_script():
    """Test that GCC spec includes explicit languages variant"""
    
    # Get the build script for GCC 13.4.0
    script = constants.get_spack_build_script("13.4.0")
    
    # Check that the GCC spec includes the languages variant
    assert "gcc@13.4.0 languages=c,c++,fortran" in script, \
        "GCC spec should include explicit languages variant"
    
    print("✓ GCC spec includes languages=c,c++,fortran variant")
    
    # Also check for other compiler versions
    for version in ["14.3.0", "13.4.0", "12.5.0", "11.5.0", "10.5.0"]:
        script = constants.get_spack_build_script(version)
        assert f"gcc@{version} languages=c,c++,fortran" in script, \
            f"GCC spec for version {version} should include explicit languages variant"
        print(f"✓ GCC {version} spec includes languages variant")
    
    print("\n✅ All tests passed!")
    print("This fix ensures that GCC specs have the languages variant set,")
    print("which prevents _cc_path(), _cxx_path(), and _fortran_path() from returning None.")


if __name__ == "__main__":
    test_gcc_languages_variant_in_build_script()
