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

"""Unit tests for slurm_factory.config module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from slurm_factory.config import Settings


class TestSettings:
    """Test Settings dataclass."""

    def test_settings_initialization(self):
        """Test Settings initialization with project name."""
        project_name = "test-project"
        settings = Settings(project_name=project_name)
        
        assert settings.project_name == project_name
        assert isinstance(settings, Settings)

    def test_home_cache_dir_property(self):
        """Test home_cache_dir property."""
        settings = Settings(project_name="test")
        
        expected_path = Path.home() / ".slurm-factory"
        assert settings.home_cache_dir == expected_path
        assert isinstance(settings.home_cache_dir, Path)

    def test_builds_dir_property(self):
        """Test builds_dir property."""
        settings = Settings(project_name="test")
        
        expected_path = Path.home() / ".slurm-factory" / "builds"
        assert settings.builds_dir == expected_path
        assert isinstance(settings.builds_dir, Path)

    def test_spack_buildcache_dir_property(self):
        """Test spack_buildcache_dir property."""
        settings = Settings(project_name="test")
        
        expected_path = Path.home() / ".slurm-factory" / "spack-buildcache"
        assert settings.spack_buildcache_dir == expected_path
        assert isinstance(settings.spack_buildcache_dir, Path)

    def test_spack_sourcecache_dir_property(self):
        """Test spack_sourcecache_dir property."""
        settings = Settings(project_name="test")
        
        expected_path = Path.home() / ".slurm-factory" / "spack-sourcecache"
        assert settings.spack_sourcecache_dir == expected_path
        assert isinstance(settings.spack_sourcecache_dir, Path)

    def test_all_cache_dirs_under_home_cache(self):
        """Test that all cache directories are under home_cache_dir."""
        settings = Settings(project_name="test")
        
        home_cache = settings.home_cache_dir
        
        # All cache dirs should be subdirectories of home_cache_dir
        assert settings.builds_dir.parent == home_cache
        assert settings.spack_buildcache_dir.parent == home_cache
        assert settings.spack_sourcecache_dir.parent == home_cache

    @patch('pathlib.Path.mkdir')
    def test_ensure_cache_dirs_creates_directories(self, mock_mkdir):
        """Test that ensure_cache_dirs creates all required directories."""
        settings = Settings(project_name="test")
        
        settings.ensure_cache_dirs()
        
        # Should call mkdir for each directory
        assert mock_mkdir.call_count == 4
        
        # Check that all calls used the correct parameters
        for call in mock_mkdir.call_args_list:
            args, kwargs = call
            # In Python, mkdir is called with keyword arguments
            assert 'mode' in kwargs
            assert kwargs['mode'] == 0o777
            assert kwargs['exist_ok'] is True

    def test_ensure_cache_dirs_with_real_directories(self):
        """Test ensure_cache_dirs with real temporary directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock Path.home() to return our temp directory
            with patch('pathlib.Path.home', return_value=Path(temp_dir)):
                settings = Settings(project_name="test")
                
                # Ensure directories don't exist initially
                assert not settings.home_cache_dir.exists()
                assert not settings.builds_dir.exists()
                assert not settings.spack_buildcache_dir.exists()
                assert not settings.spack_sourcecache_dir.exists()
                
                # Create directories
                settings.ensure_cache_dirs()
                
                # Verify all directories now exist
                assert settings.home_cache_dir.exists()
                assert settings.home_cache_dir.is_dir()
                assert settings.builds_dir.exists()
                assert settings.builds_dir.is_dir()
                assert settings.spack_buildcache_dir.exists()
                assert settings.spack_buildcache_dir.is_dir()
                assert settings.spack_sourcecache_dir.exists()
                assert settings.spack_sourcecache_dir.is_dir()

    def test_ensure_cache_dirs_permissions(self):
        """Test that directories are created with correct permissions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('pathlib.Path.home', return_value=Path(temp_dir)):
                settings = Settings(project_name="test")
                settings.ensure_cache_dirs()
                
                # Check permissions (on Unix systems)
                if os.name == 'posix':
                    # Get the actual permissions
                    home_stat = settings.home_cache_dir.stat()
                    builds_stat = settings.builds_dir.stat()
                    buildcache_stat = settings.spack_buildcache_dir.stat()
                    sourcecache_stat = settings.spack_sourcecache_dir.stat()
                    
                    # Check that directories were created (permissions may be modified by umask)
                    assert settings.home_cache_dir.exists()
                    assert settings.builds_dir.exists()
                    assert settings.spack_buildcache_dir.exists()
                    assert settings.spack_sourcecache_dir.exists()

    def test_ensure_cache_dirs_idempotent(self):
        """Test that ensure_cache_dirs can be called multiple times safely."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('pathlib.Path.home', return_value=Path(temp_dir)):
                settings = Settings(project_name="test")
                
                # Call multiple times
                settings.ensure_cache_dirs()
                settings.ensure_cache_dirs()
                settings.ensure_cache_dirs()
                
                # Should still work and directories should exist
                assert settings.home_cache_dir.exists()
                assert settings.builds_dir.exists()
                assert settings.spack_buildcache_dir.exists()
                assert settings.spack_sourcecache_dir.exists()

    def test_different_project_names(self):
        """Test Settings with different project names."""
        project_names = ["slurm-factory", "test-project", "my-custom-project"]
        
        for name in project_names:
            settings = Settings(project_name=name)
            assert settings.project_name == name
            
            # All paths should be the same regardless of project name
            # (project name only affects LXD project, not local cache paths)
            expected_home = Path.home() / ".slurm-factory"
            assert settings.home_cache_dir == expected_home


class TestSettingsIntegration:
    """Test Settings integration scenarios."""

    def test_settings_with_environment_variables(self):
        """Test Settings behavior with different environment variables."""
        # Test that Settings works regardless of environment
        settings = Settings(project_name="env-test")
        
        # Should always use the same cache directory structure
        assert str(settings.home_cache_dir).endswith(".slurm-factory")
        assert str(settings.builds_dir).endswith("builds")
        assert str(settings.spack_buildcache_dir).endswith("spack-buildcache")
        assert str(settings.spack_sourcecache_dir).endswith("spack-sourcecache")

    def test_path_string_representations(self):
        """Test string representations of paths."""
        settings = Settings(project_name="test")
        
        # All paths should be valid string representations
        assert isinstance(str(settings.home_cache_dir), str)
        assert isinstance(str(settings.builds_dir), str)
        assert isinstance(str(settings.spack_buildcache_dir), str)
        assert isinstance(str(settings.spack_sourcecache_dir), str)
        
        # Should contain expected components
        home_str = str(settings.home_cache_dir)
        assert ".slurm-factory" in home_str
        
        builds_str = str(settings.builds_dir)
        assert ".slurm-factory" in builds_str
        assert "builds" in builds_str

    def test_settings_dataclass_features(self):
        """Test dataclass features of Settings."""
        settings1 = Settings(project_name="test1")
        settings2 = Settings(project_name="test1")
        settings3 = Settings(project_name="test2")
        
        # Test equality
        assert settings1 == settings2
        assert settings1 != settings3
        
        # Test repr
        repr_str = repr(settings1)
        assert "Settings" in repr_str
        assert "test1" in repr_str


if __name__ == "__main__":
    pytest.main([__file__])
