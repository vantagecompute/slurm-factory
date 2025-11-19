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

"""Unit tests for slurm_factory.builders module."""

import pytest

from slurm_factory.builders import slurm_builder, toolchain_builder
from slurm_factory.constants import SlurmVersion


class TestSlurmBuilderModule:
    """Test the slurm_builder module structure and exports."""

    def test_module_imports(self):
        """Test that the slurm_builder module imports successfully."""
        assert hasattr(slurm_builder, 'create_slurm_package')
        assert callable(slurm_builder.create_slurm_package)

    def test_module_docstring(self):
        """Test that the module has a docstring."""
        assert slurm_builder.__doc__ is not None
        assert len(slurm_builder.__doc__) > 0

    def test_create_slurm_package_function_exists(self):
        """Test that the create_slurm_package function exists and is callable."""
        assert hasattr(slurm_builder, 'create_slurm_package')
        assert callable(slurm_builder.create_slurm_package)

    def test_get_module_template_content_exists(self):
        """Test that helper functions exist."""
        assert hasattr(slurm_builder, 'get_module_template_content')
        assert callable(slurm_builder.get_module_template_content)
        
    def test_get_move_slurm_assets_to_container_str_exists(self):
        """Test that get_move_slurm_assets_to_container_str function exists."""
        assert hasattr(slurm_builder, 'get_move_slurm_assets_to_container_str')
        assert callable(slurm_builder.get_move_slurm_assets_to_container_str)


class TestToolchainBuilderModule:
    """Test the toolchain_builder module structure and exports."""

    def test_build_compiler_function_exists(self):
        """Test that the build_compiler function exists and is callable."""
        assert hasattr(toolchain_builder, 'build_compiler')
        assert callable(toolchain_builder.build_compiler)
