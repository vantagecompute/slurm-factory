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

"""Test that libmd is built and included for runtime dependencies."""

import pytest
from slurm_factory.spack_yaml import generate_spack_config


class TestLibmdRuntimeDependency:
    """Test libmd runtime dependency handling."""

    def test_libmd_is_buildable(self):
        """Verify libmd is buildable by Spack, not external."""
        config = generate_spack_config(
            slurm_version="25.11",
            compiler_version="13.4.0",
            gpu_support=False,
        )

        packages = config["spack"]["packages"]

        # libmd should be buildable (not external)
        assert "libmd" in packages, "libmd should have package configuration"
        assert packages["libmd"]["buildable"] is True, (
            "libmd should be buildable to ensure relocatability. "
            "Using system libmd creates runtime dependencies on target system libraries."
        )

        # Verify no external configuration
        assert "externals" not in packages["libmd"], (
            "libmd should not use external (system) packages to maintain relocatability"
        )

    def test_libmd_included_in_runtime_view(self):
        """Verify libmd is included in the runtime view for packages that need it."""
        config = generate_spack_config(
            slurm_version="25.11",
            compiler_version="13.4.0",
            gpu_support=False,
        )

        view_config = config["spack"]["view"]
        view_root_key = list(view_config.keys())[0]
        exclude_list = view_config[view_root_key]["exclude"]

        # libmd should NOT be in the exclude list
        assert "libmd" not in exclude_list, (
            "libmd should be included in the runtime view. "
            "Some packages have runtime dependencies on libmd.so.0 "
            "for message digest functions (MD2, MD4, MD5, RIPEMD-160)."
        )

    def test_libmd_dev_in_system_deps(self):
        """Verify libmd-dev is available during builds."""
        from slurm_factory.constants import get_install_system_deps_script

        deps_script = get_install_system_deps_script()

        # libmd-dev should be available for building
        assert "libmd-dev" in deps_script, (
            "libmd-dev should be available in the build container "
            "to provide headers and development files during the build process."
        )

    def test_similar_packages_still_excluded(self):
        """Verify build-only tools remain excluded."""
        config = generate_spack_config(
            slurm_version="25.11",
            compiler_version="13.4.0",
            gpu_support=False,
        )

        view_config = config["spack"]["view"]
        view_root_key = list(view_config.keys())[0]
        exclude_list = view_config[view_root_key]["exclude"]

        # Build-only tools should still be excluded
        build_only_tools = ["bison", "flex", "cmake", "autoconf", "automake"]
        for tool in build_only_tools:
            assert tool in exclude_list, f"{tool} should remain excluded (build-only)"
