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

"""Test that libfl-dev is available as a build-time dependency."""

import pytest
from slurm_factory.utils import get_install_system_deps_script


class TestLibflBuildDependency:
    """Test libfl-dev availability during builds."""

    def test_libfl_dev_in_system_deps(self):
        """Verify libfl-dev is installed in the build container."""
        deps_script = get_install_system_deps_script()

        # libfl-dev should be in the apt install list
        assert "libfl-dev" in deps_script, (
            "libfl-dev must be available during builds. "
            "Some packages may use flex-generated code that links with -lfl. "
            "Having libfl-dev provides libfl.a (static library) for build-time linking."
        )

    def test_flex_also_installed(self):
        """Verify flex tool is available alongside libfl-dev."""
        deps_script = get_install_system_deps_script()

        # Both flex and libfl-dev should be present
        assert "flex" in deps_script, "flex tool must be available"
        assert "libfl-dev" in deps_script, "libfl-dev must be available"

    def test_flex_not_in_runtime_view(self):
        """Verify flex is excluded from the final runtime package."""
        from slurm_factory.spack_yaml import generate_spack_config
        
        config = generate_spack_config(
            slurm_version="25.11",
            compiler_version="13.4.0",
            gpu_support=False,
        )
        
        view_config = config["spack"]["view"]
        view_root_key = list(view_config.keys())[0]
        exclude_list = view_config[view_root_key]["exclude"]
        
        # flex should be excluded from runtime view (build-only tool)
        assert "flex" in exclude_list, (
            "flex should be excluded from the runtime view. "
            "It's only needed at build time. Modern packages either: "
            "1) Don't link with libfl at all (%option noyywrap), "
            "2) Link statically with libfl.a (no runtime dependency), or "
            "3) Include flex-generated code directly in their source."
        )

    def test_bison_also_excluded(self):
        """Verify bison (similar build-only tool) is also excluded."""
        from slurm_factory.spack_yaml import generate_spack_config
        
        config = generate_spack_config(
            slurm_version="25.11",
            compiler_version="13.4.0",
            gpu_support=False,
        )
        
        view_config = config["spack"]["view"]
        view_root_key = list(view_config.keys())[0]
        exclude_list = view_config[view_root_key]["exclude"]
        
        # bison should also be excluded (parser generator, build-only)
        assert "bison" in exclude_list, (
            "bison should be excluded (build-only tool like flex)"
        )
