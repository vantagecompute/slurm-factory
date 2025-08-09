"""Unit tests for slurm_factory.exceptions module."""

import pytest

from slurm_factory.exceptions import (
    SlurmFactoryError,
    SlurmFactoryStreamExecError,
    SlurmFactoryInstanceCreationError,
)


class TestSlurmFactoryError:
    """Test SlurmFactoryError exception."""

    def test_slurm_factory_error_creation(self):
        """Test SlurmFactoryError creation with message."""
        message = "Test error message"
        error = SlurmFactoryError(message)
        
        assert isinstance(error, Exception)
        assert str(error) == message
        assert error.args == (message,)

    def test_slurm_factory_error_inheritance(self):
        """Test that SlurmFactoryError inherits from Exception."""
        error = SlurmFactoryError("test")
        assert isinstance(error, Exception)

    def test_slurm_factory_error_raise(self):
        """Test raising SlurmFactoryError."""
        message = "Test error for raising"
        
        with pytest.raises(SlurmFactoryError) as exc_info:
            raise SlurmFactoryError(message)
        
        assert str(exc_info.value) == message


class TestSlurmFactoryStreamExecError:
    """Test SlurmFactoryStreamExecError exception."""

    def test_stream_exec_error_creation(self):
        """Test SlurmFactoryStreamExecError creation with message."""
        message = "Command execution failed"
        error = SlurmFactoryStreamExecError(message)
        
        assert isinstance(error, Exception)
        assert str(error) == message
        assert error.args == (message,)

    def test_stream_exec_error_inheritance(self):
        """Test that SlurmFactoryStreamExecError inherits from Exception."""
        error = SlurmFactoryStreamExecError("test")
        assert isinstance(error, Exception)

    def test_stream_exec_error_raise(self):
        """Test raising SlurmFactoryStreamExecError."""
        message = "Stream execution failed"
        
        with pytest.raises(SlurmFactoryStreamExecError) as exc_info:
            raise SlurmFactoryStreamExecError(message)
        
        assert str(exc_info.value) == message


class TestSlurmFactoryInstanceCreationError:
    """Test SlurmFactoryInstanceCreationError exception."""

    def test_instance_creation_error_creation(self):
        """Test SlurmFactoryInstanceCreationError creation with message."""
        message = "Instance creation failed"
        error = SlurmFactoryInstanceCreationError(message)
        
        assert isinstance(error, Exception)
        assert str(error) == message
        assert error.args == (message,)

    def test_instance_creation_error_inheritance(self):
        """Test that SlurmFactoryInstanceCreationError inherits from Exception."""
        error = SlurmFactoryInstanceCreationError("test")
        assert isinstance(error, Exception)

    def test_instance_creation_error_raise(self):
        """Test raising SlurmFactoryInstanceCreationError."""
        message = "Base instance creation failed"
        
        with pytest.raises(SlurmFactoryInstanceCreationError) as exc_info:
            raise SlurmFactoryInstanceCreationError(message)
        
        assert str(exc_info.value) == message


class TestExceptionHierarchy:
    """Test exception hierarchy and relationships."""

    def test_all_exceptions_inherit_from_exception(self):
        """Test that all custom exceptions inherit from Exception."""
        exceptions = [
            SlurmFactoryError("test"),
            SlurmFactoryStreamExecError("test"),
            SlurmFactoryInstanceCreationError("test"),
        ]
        
        for exc in exceptions:
            assert isinstance(exc, Exception)

    def test_exception_independence(self):
        """Test that exceptions are independent (not inheriting from each other)."""
        base_error = SlurmFactoryError("base")
        stream_error = SlurmFactoryStreamExecError("stream")
        creation_error = SlurmFactoryInstanceCreationError("creation")
        
        # Check they are not instances of each other
        assert not isinstance(stream_error, SlurmFactoryError)
        assert not isinstance(creation_error, SlurmFactoryError)
        assert not isinstance(base_error, SlurmFactoryStreamExecError)
        assert not isinstance(creation_error, SlurmFactoryStreamExecError)
        assert not isinstance(base_error, SlurmFactoryInstanceCreationError)
        assert not isinstance(stream_error, SlurmFactoryInstanceCreationError)

    def test_exception_catching(self):
        """Test catching specific exceptions."""
        # Test catching specific exception types
        with pytest.raises(SlurmFactoryError):
            raise SlurmFactoryError("specific error")
        
        with pytest.raises(SlurmFactoryStreamExecError):
            raise SlurmFactoryStreamExecError("stream error")
        
        with pytest.raises(SlurmFactoryInstanceCreationError):
            raise SlurmFactoryInstanceCreationError("creation error")

    def test_exception_messages_preserved(self):
        """Test that exception messages are preserved through raise/catch cycle."""
        messages = [
            "Base error occurred",
            "Stream execution failed with exit code 1",
            "Instance creation timeout after 300 seconds",
        ]
        
        exception_types = [
            SlurmFactoryError,
            SlurmFactoryStreamExecError,
            SlurmFactoryInstanceCreationError,
        ]
        
        for exc_type, message in zip(exception_types, messages):
            with pytest.raises(exc_type) as exc_info:
                raise exc_type(message)
            
            assert str(exc_info.value) == message


if __name__ == "__main__":
    pytest.main([__file__])
