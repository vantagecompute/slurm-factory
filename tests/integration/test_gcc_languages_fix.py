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


def _assert_gcc_has_languages_variant(version: str, script: str) -> None:
    """Helper to check if GCC spec includes languages variant.
    
    Note: String matching is appropriate here since we're testing that the generated
    shell script contains the correct Spack spec string that will be executed.
    We want to ensure the exact spec format is correct in the build script.
    """
    expected = f"gcc@{version} languages=c,c++,fortran"
    assert expected in script, \
        f"GCC spec for version {version} should include explicit languages variant"
    print(f"✓ GCC {version} spec includes languages variant")


def test_gcc_languages_variant_in_build_script():
    """Test that GCC spec includes explicit languages variant"""
    
    # Test all supported compiler versions from COMPILER_TOOLCHAINS
    for version in constants.COMPILER_TOOLCHAINS.keys():
        script = constants.get_spack_build_script(version)
        _assert_gcc_has_languages_variant(version, script)
    
    print(f"\n✅ All {len(constants.COMPILER_TOOLCHAINS)} supported GCC versions tested!")
    print("This fix ensures that GCC specs have the languages variant set,")
    print("which prevents _cc_path(), _cxx_path(), and _fortran_path() from returning None.")


if __name__ == "__main__":
    test_gcc_languages_variant_in_build_script()
