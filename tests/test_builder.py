"""Unit tests for slurm_factory.builder module."""

from unittest import mock

import pytest
import typer

from slurm_factory.builder import build
from slurm_factory.constants import SlurmVersion
from slurm_factory.exceptions import SlurmFactoryError


@pytest.fixture
def mock_context():
    """Provide a mocked typer context following Charmcraft patterns."""
    # Use a regular Mock for the context, not spec_set since we need obj attribute
    ctx = mock.Mock()
    ctx.obj = {
        "settings": mock.Mock(),
        "project_name": "test-project"
    }
    ctx.obj["settings"].home_cache_dir = "/tmp/test-cache"
    return ctx


class TestBuildFunction:
    """Test the main build function with proper mocking patterns."""

    @mock.patch('slurm_factory.builder.set_profile')
    @mock.patch('slurm_factory.builder.initialize_base_instance_buildcache')
    @mock.patch('slurm_factory.builder.get_base_instance')
    @mock.patch('slurm_factory.builder.get_base_instance_name')
    @mock.patch('slurm_factory.builder.Console')
    @mock.patch('slurm_factory.builder.lxd.LXC')
    def test_build_base_only_option(
        self,
        mock_lxc_class,
        mock_console,
        mock_get_base_instance_name,
        mock_get_base_instance,
        mock_create_buildcache,
        mock_set_profile,
        mock_context
    ):
        """Test build function with base_only option - this should work."""
        # Configure LXC mock - use the mocked class directly
        mock_lxc_service = mock.Mock()
        mock_lxc_class.return_value = mock_lxc_service
        mock_lxc_service.project_list.return_value = ["test-project"]
        
        # Configure base instance mock
        mock_base_instance = mock.Mock()
        mock_base_instance.instance_name = "test-base-instance"
        mock_get_base_instance.return_value = mock_base_instance
        mock_get_base_instance_name.return_value = "test-base-instance"
        
        # Call function with base_only=True (this should exit early and not trigger complex flows)
        result = build(mock_context, base_only=True)
        
        # Should return early with Exit(0)
        assert isinstance(result, typer.Exit)
        assert result.exit_code == 0
        
        # Basic verifications
        mock_context.obj["settings"].ensure_cache_dirs.assert_called_once()
        mock_lxc_service.project_list.assert_called_once()

    @mock.patch('slurm_factory.builder.set_profile')
    @mock.patch('slurm_factory.builder.initialize_base_instance_buildcache')
    @mock.patch('slurm_factory.builder.get_base_instance')
    @mock.patch('slurm_factory.builder.get_base_instance_name')
    @mock.patch('slurm_factory.builder.Console')
    @mock.patch('slurm_factory.builder.lxd.LXC')
    def test_build_project_creation(
        self,
        mock_lxc_class,
        mock_console,
        mock_get_base_instance_name,
        mock_get_base_instance,
        mock_create_buildcache,
        mock_set_profile,
        mock_context
    ):
        """Test build function creates project when it doesn't exist."""
        # Configure LXC mock - project doesn't exist
        mock_lxc_service = mock.Mock()
        mock_lxc_class.return_value = mock_lxc_service
        mock_lxc_service.project_list.return_value = []  # Empty list = project doesn't exist
        
        # Configure base instance mock
        mock_base_instance = mock.Mock()
        mock_base_instance.instance_name = "test-base-instance"
        mock_get_base_instance.return_value = mock_base_instance
        mock_get_base_instance_name.return_value = "test-base-instance"
        
        # Call function with base_only=True to avoid complex instance creation
        result = build(mock_context, base_only=True)
        
        # Should return Exit(0)
        assert isinstance(result, typer.Exit)
        assert result.exit_code == 0
        
        # Verify project creation
        mock_lxc_service.project_create.assert_called_once_with(project="test-project")
        mock_set_profile.assert_called_once()

    @mock.patch('slurm_factory.builder.set_profile')
    @mock.patch('slurm_factory.builder.initialize_base_instance_buildcache')
    @mock.patch('slurm_factory.builder.get_base_instance')
    @mock.patch('slurm_factory.builder.get_base_instance_name')
    @mock.patch('slurm_factory.builder.Console')
    @mock.patch('slurm_factory.builder.lxd.LXC')
    def test_build_with_gpu_support(
        self,
        mock_lxc_class,
        mock_console,
        mock_get_base_instance_name,
        mock_get_base_instance,
        mock_create_buildcache,
        mock_set_profile,
        mock_context
    ):
        """Test build function with GPU support enabled."""
        # Configure LXC mock
        mock_lxc_service = mock.Mock()
        mock_lxc_class.return_value = mock_lxc_service
        mock_lxc_service.project_list.return_value = ["test-project"]
        
        # Configure base instance mock
        mock_base_instance = mock.Mock()
        mock_base_instance.instance_name = "test-base-instance"
        mock_get_base_instance.return_value = mock_base_instance
        mock_get_base_instance_name.return_value = "test-base-instance"
        
        # Call function with GPU support and base_only=True
        result = build(mock_context, gpu=True, base_only=True)
        
        # Should return Exit(0)
        assert isinstance(result, typer.Exit)
        assert result.exit_code == 0

    @mock.patch('slurm_factory.builder.set_profile')
    @mock.patch('slurm_factory.builder.create_base_instance')
    @mock.patch('slurm_factory.builder.initialize_base_instance_buildcache')
    @mock.patch('slurm_factory.builder.get_base_instance')
    @mock.patch('slurm_factory.builder.get_base_instance_name')
    @mock.patch('slurm_factory.builder.Console')
    @mock.patch('slurm_factory.builder.lxd.LXC')
    def test_build_slurm_factory_error_handling(
        self,
        mock_lxc_class,
        mock_console,
        mock_get_base_instance_name,
        mock_get_base_instance,
        mock_create_buildcache,
        mock_create_base_instance,
        mock_set_profile,
        mock_context
    ):
        """Test build function handles SlurmFactoryError."""
        # Configure LXC mock
        mock_lxc_service = mock.Mock()
        mock_lxc_class.return_value = mock_lxc_service
        mock_lxc_service.project_list.return_value = ["test-project"]
        
        # Mock base instance
        mock_get_base_instance.return_value = None

        # Configure create_base_instance mock
        mock_create_base_instance = mock.Mock()
        mock_create_base_instance.return_value = mock_create_base_instance
        
        # Make create_buildcache raise SlurmFactoryError
        mock_create_buildcache.side_effect = SlurmFactoryError("Test error")
        
        # Call function
        result = build(mock_context, base_only=True)
        
        # Should return Exit(1) on error
        assert isinstance(result, typer.Exit)
        assert result.exit_code == 1

    @mock.patch('slurm_factory.builder.set_profile')
    @mock.patch('slurm_factory.builder.initialize_base_instance_buildcache')
    @mock.patch('slurm_factory.builder.get_base_instance')
    @mock.patch('slurm_factory.builder.get_base_instance_name')
    @mock.patch('slurm_factory.builder.Console')
    @mock.patch('slurm_factory.builder.lxd.LXC')
    def test_build_different_slurm_versions(
        self,
        mock_lxc_class,
        mock_console,
        mock_get_base_instance_name,
        mock_get_base_instance,
        mock_create_buildcache,
        mock_set_profile,
        mock_context
    ):
        """Test build function with different Slurm versions."""
        # Configure LXC mock
        mock_lxc_service = mock.Mock()
        mock_lxc_class.return_value = mock_lxc_service
        mock_lxc_service.project_list.return_value = ["test-project"]
        
        # Configure base instance mock
        mock_base_instance = mock.Mock()
        mock_base_instance.instance_name = "test-base-instance"
        mock_get_base_instance.return_value = mock_base_instance
        mock_get_base_instance_name.return_value = "test-base-instance"
        
        versions = [
            SlurmVersion.v25_05,
            SlurmVersion.v24_11,
            SlurmVersion.v23_11,
            SlurmVersion.v23_02,
        ]
        
        for version in versions:
            # Reset mocks for each iteration
            mock_create_buildcache.reset_mock()
            
            # Should not raise any errors
            result = build(mock_context, slurm_version=version, base_only=True)
            assert isinstance(result, typer.Exit)
            assert result.exit_code == 0


class TestBuildParameterValidation:
    """Test parameter validation and edge cases."""

    @mock.patch('slurm_factory.builder.set_profile')
    @mock.patch('slurm_factory.builder.initialize_base_instance_buildcache')
    @mock.patch('slurm_factory.builder.get_base_instance')
    @mock.patch('slurm_factory.builder.get_base_instance_name')
    @mock.patch('slurm_factory.builder.Console')
    @mock.patch('slurm_factory.builder.lxd.LXC')
    def test_build_parameter_combinations(
        self,
        mock_lxc_class,
        mock_console,
        mock_get_base_instance_name,
        mock_get_base_instance,
        mock_create_buildcache,
        mock_set_profile,
        mock_context
    ):
        """Test build function with various parameter combinations."""
        # Configure LXC mock
        mock_lxc_service = mock.Mock()
        mock_lxc_class.return_value = mock_lxc_service
        mock_lxc_service.project_list.return_value = ["test-project"]
        
        # Configure base instance mock
        mock_base_instance = mock.Mock()
        mock_base_instance.instance_name = "test-base-instance"
        mock_get_base_instance.return_value = mock_base_instance
        mock_get_base_instance_name.return_value = "test-base-instance"
        
        test_cases = [
            {"gpu": True, "minimal": False, "verify": False},
            {"gpu": False, "minimal": True, "verify": False},
            {"gpu": True, "minimal": True, "verify": True},
            {"gpu": False, "minimal": False, "verify": True},
        ]
        
        for case in test_cases:
            # Reset mocks for each iteration
            mock_create_buildcache.reset_mock()
            
            # Should handle all parameter combinations
            result = build(mock_context, base_only=True, **case)
            assert isinstance(result, typer.Exit)
            assert result.exit_code == 0


if __name__ == "__main__":
    pytest.main([__file__])
