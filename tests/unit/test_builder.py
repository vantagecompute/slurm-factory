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

from unittest.mock import MagicMock, patch

import pytest

from slurm_factory.builders import slurm_builder
from slurm_factory.exceptions import SlurmFactoryError


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


class TestExceptionHandling:
    """Test exception handling in slurm_builder module."""

    @patch('slurm_factory.builders.slurm_builder.subprocess.run')
    @patch('slurm_factory.builders.slurm_builder.Path')
    def test_push_slurm_to_buildcache_does_not_wrap_slurm_factory_error(self, mock_path, mock_run):
        """Test that SlurmFactoryError is not re-wrapped when raised in _push_slurm_to_buildcache."""
        # Mock Path.home() to return a path with .aws directory
        mock_home = MagicMock()
        mock_home.__truediv__ = lambda self, other: MagicMock(exists=lambda: True)
        mock_path.home.return_value = mock_home

        # Mock subprocess.run to return a failed result
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Original error from spack buildcache"
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        # Call _push_slurm_to_buildcache and expect a SlurmFactoryError
        with pytest.raises(SlurmFactoryError) as exc_info:
            slurm_builder._push_slurm_to_buildcache(
                image_tag="test-image",
                slurm_version="23.11",
                toolchain="jammy",
                publish_mode="slurm",
                signing_key="test-key",
                gpg_private_key="test-gpg-key",
                gpg_passphrase="test-passphrase",
            )

        # Verify the error message is NOT nested (should only contain "Failed to push to buildcache" once)
        error_message = str(exc_info.value)
        assert error_message.count("Failed to push to buildcache") == 1, (
            f"Error message should contain 'Failed to push to buildcache' only once, "
            f"but got: {error_message}"
        )

    @patch('slurm_factory.builders.slurm_builder.subprocess.run')
    @patch('slurm_factory.builders.slurm_builder.Path')
    @patch('slurm_factory.builders.slurm_builder._push_slurm_to_buildcache')
    @patch('slurm_factory.builders.slurm_builder._extract_slurm_tarball_from_image')
    @patch('slurm_factory.builders.slurm_builder.build_docker_image')
    @patch('slurm_factory.builders.slurm_builder.remove_old_docker_image')
    @patch('slurm_factory.builders.slurm_builder.generate_yaml_string')
    @patch('slurm_factory.builders.slurm_builder._get_slurm_builder_dockerfile')
    @patch('slurm_factory.builders.slurm_builder.console')
    def test_create_slurm_package_does_not_wrap_slurm_factory_error(
        self,
        mock_console,
        mock_get_dockerfile,
        mock_generate_yaml,
        mock_remove_image,
        mock_build_image,
        mock_extract,
        mock_push,
        mock_path,
        mock_run,
    ):
        """Test that SlurmFactoryError is not re-wrapped when raised in create_slurm_package."""
        # Setup mocks
        mock_generate_yaml.return_value = "mock_yaml"
        mock_get_dockerfile.return_value = "mock_dockerfile"

        # Mock _push_slurm_to_buildcache to raise a SlurmFactoryError
        original_error_msg = "Failed to push to buildcache: Original spack error"
        mock_push.side_effect = SlurmFactoryError(original_error_msg)

        # Call create_slurm_package and expect the same SlurmFactoryError to bubble up
        with pytest.raises(SlurmFactoryError) as exc_info:
            slurm_builder.create_slurm_package(
                image_tag="test-image",
                slurm_version="23.11",
                toolchain="jammy",
                cache_dir="/tmp/test",
                publish="slurm",
                signing_key="test-key",
                gpg_private_key="test-gpg-key",
                gpg_passphrase="test-passphrase",
            )

        # Verify the error message is NOT nested
        error_message = str(exc_info.value)
        # The message should be exactly the original error, not wrapped with "Failed to create slurm package"
        assert error_message == original_error_msg, (
            f"Error message should not be wrapped. Expected: '{original_error_msg}', "
            f"but got: '{error_message}'"
        )
