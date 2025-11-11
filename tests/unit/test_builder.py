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

"""Unit tests for slurm_factory.builder module."""

import pytest

from slurm_factory import builder
from slurm_factory.constants import SlurmVersion


class TestBuilderModule:
    """Test the builder module structure and exports."""

    def test_module_imports(self):
        """Test that the builder module imports successfully."""
        assert hasattr(builder, 'build')
        assert callable(builder.build)

    def test_module_docstring(self):
        """Test that the module has a docstring."""
        assert builder.__doc__ is not None
        assert len(builder.__doc__) > 0

    def test_build_function_exists(self):
        """Test that the build function exists and is callable."""
        assert hasattr(builder, 'build')
        assert callable(builder.build)

    def test_build_compiler_function_exists(self):
        """Test that the build_compiler function exists and is callable."""
        assert hasattr(builder, 'build_compiler')
        assert callable(builder.build_compiler)
