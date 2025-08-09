"""Unit tests for slurm_factory.utils module."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from slurm_factory.utils import get_base_instance_name


class TestUtilityFunctions:
    """Test utility functions that don't require LXD."""

    def test_get_base_instance_name(self):
        """Test base instance name generation."""
        # Mock datetime to get predictable output
        with patch('slurm_factory.utils.datetime') as mock_datetime:
            mock_now = Mock()
            mock_now.strftime.return_value = "202408"
            mock_datetime.now.return_value = mock_now
            
            result = get_base_instance_name()
            
            # Should include base prefix and timestamp
            assert result == "slurm-factory-base-202408"
            mock_datetime.now.assert_called_once()
            mock_now.strftime.assert_called_once_with("%Y%m")

    def test_get_base_instance_name_format(self):
        """Test that base instance name has expected format."""
        result = get_base_instance_name()
        
        # Should start with base prefix
        assert result.startswith("slurm-factory-base-")
        
        # Should have timestamp at the end (6 digits for YYYYMM)
        parts = result.split("-")
        assert len(parts) == 4  # slurm, factory, base, timestamp
        assert parts[0] == "slurm"
        assert parts[1] == "factory"
        assert parts[2] == "base"
        
        # Timestamp should be 6 digits (YYYYMM format)
        timestamp = parts[3]
        assert len(timestamp) == 6
        assert timestamp.isdigit()

    def test_get_base_instance_name_different_months(self):
        """Test base instance name generation for different months."""
        test_dates = [
            ("2024-01-15", "202401"),
            ("2024-12-31", "202412"),
            ("2025-08-18", "202508"),
        ]
        
        for date_str, expected_timestamp in test_dates:
            with patch('slurm_factory.utils.datetime') as mock_datetime:
                mock_now = Mock()
                mock_now.strftime.return_value = expected_timestamp
                mock_datetime.now.return_value = mock_now
                
                result = get_base_instance_name()
                expected = f"slurm-factory-base-{expected_timestamp}"
                assert result == expected

    def test_get_base_instance_name_uniqueness_by_month(self):
        """Test that base instance names are unique by month/year."""
        # Same month should give same name
        with patch('slurm_factory.utils.datetime') as mock_datetime:
            mock_now = Mock()
            mock_now.strftime.return_value = "202408"
            mock_datetime.now.return_value = mock_now
            
            result1 = get_base_instance_name()
            result2 = get_base_instance_name()
            
            assert result1 == result2

        # Different month should give different name
        with patch('slurm_factory.utils.datetime') as mock_datetime:
            mock_now = Mock()
            mock_now.strftime.return_value = "202409"
            mock_datetime.now.return_value = mock_now
            
            result3 = get_base_instance_name()
            
            assert result3 != result1


class TestConstants:
    """Test constants and imports from utils module."""

    def test_imports_available(self):
        """Test that required imports are available."""
        # Test that we can import the module successfully
        from slurm_factory import utils
        
        # Test that key functions exist
        assert hasattr(utils, 'get_base_instance_name')
        assert callable(utils.get_base_instance_name)

    def test_logging_setup(self):
        """Test that logging is properly configured."""
        from slurm_factory import utils
        
        # Should have logger and console defined
        assert hasattr(utils, 'logger')
        assert hasattr(utils, 'console')

    def test_exception_imports(self):
        """Test that custom exceptions are imported."""
        from slurm_factory import utils
        
        # Should be able to access exception classes
        # (they're imported at module level)
        assert hasattr(utils, 'SlurmFactoryError')
        assert hasattr(utils, 'SlurmFactoryInstanceCreationError')
        assert hasattr(utils, 'SlurmFactoryStreamExecError')


class TestModuleStructure:
    """Test the overall structure of the utils module."""

    def test_module_docstring(self):
        """Test that module has appropriate docstring."""
        from slurm_factory import utils
        
        assert utils.__doc__ is not None
        assert len(utils.__doc__.strip()) > 0

    def test_required_functions_exist(self):
        """Test that expected functions exist in the module."""
        from slurm_factory import utils
        
        # Test for existence of key functions
        expected_functions = [
            'get_base_instance_name',
            '_stream_exec_output',  # Private but important
        ]
        
        for func_name in expected_functions:
            assert hasattr(utils, func_name)
            assert callable(getattr(utils, func_name))

    def test_module_imports(self):
        """Test that the module imports are working."""
        # This test ensures the module can be imported without errors
        try:
            from slurm_factory import utils
            assert utils is not None
        except ImportError as e:
            pytest.fail(f"Failed to import utils module: {e}")

    def test_datetime_usage(self):
        """Test that datetime is properly used in the module."""
        from slurm_factory import utils
        
        # The module should use datetime for timestamp generation
        # We can test this indirectly through get_base_instance_name
        result = utils.get_base_instance_name()
        
        # Should contain current year (this test will need updating after 2099!)
        current_year = datetime.now().year
        assert str(current_year) in result


class TestErrorHandling:
    """Test error handling in utility functions."""

    @patch('slurm_factory.utils.datetime')
    def test_get_base_instance_name_with_datetime_error(self, mock_datetime):
        """Test get_base_instance_name behavior when datetime fails."""
        # Make datetime.now() raise an exception
        mock_datetime.now.side_effect = RuntimeError("Time travel not implemented")
        
        # Should propagate the error (no special handling expected)
        with pytest.raises(RuntimeError, match="Time travel not implemented"):
            get_base_instance_name()

    @patch('slurm_factory.utils.datetime')
    def test_get_base_instance_name_with_strftime_error(self, mock_datetime):
        """Test get_base_instance_name behavior when strftime fails."""
        mock_now = Mock()
        mock_now.strftime.side_effect = ValueError("Invalid format")
        mock_datetime.now.return_value = mock_now
        
        # Should propagate the strftime error
        with pytest.raises(ValueError, match="Invalid format"):
            get_base_instance_name()


class TestIntegration:
    """Test integration aspects of the utils module."""

    def test_base_instance_prefix_consistency(self):
        """Test that base instance name uses consistent prefix."""
        from slurm_factory.constants import BASE_INSTANCE_PREFIX
        
        result = get_base_instance_name()
        
        # Should start with the constant prefix
        assert result.startswith(BASE_INSTANCE_PREFIX)

    def test_timestamp_format_consistency(self):
        """Test that timestamp format is consistent across calls."""
        # Make multiple calls and verify they all use the same format
        results = [get_base_instance_name() for _ in range(3)]
        
        # All should have the same format structure
        for result in results:
            parts = result.split("-")
            assert len(parts) == 4
            # Last part should be 6-digit timestamp
            assert len(parts[-1]) == 6
            assert parts[-1].isdigit()

    def test_real_time_behavior(self):
        """Test behavior with real system time."""
        # This test uses actual system time to ensure realistic behavior
        result = get_base_instance_name()
        
        # Extract timestamp and verify it's reasonable
        timestamp = result.split("-")[-1]
        year = int(timestamp[:4])
        month = int(timestamp[4:])
        
        # Year should be current or recent
        current_year = datetime.now().year
        assert year in [current_year - 1, current_year, current_year + 1]
        
        # Month should be valid
        assert 1 <= month <= 12


if __name__ == "__main__":
    pytest.main([__file__])
