"""Exceptions for slurm-factory package."""


class SlurmFactoryError(Exception):
    """Base class for exceptions raised by the slurm-factory package."""

    def __init__(self, message: str):
        """Initialize SlurmFactoryError."""
        super().__init__(message)


class SlurmFactoryStreamExecError(Exception):
    """Exception raised for errors during streaming command execution in slurm-factory."""

    def __init__(self, message: str):
        """Initialize SlurmFactoryStreamExecError."""
        super().__init__(message)


class SlurmFactoryInstanceCreationError(Exception):
    """Exception raised for errors during base instance creation in slurm-factory."""

    def __init__(self, message: str):
        """Initialize SlurmFactoryInstanceCreationError."""
        super().__init__(message)
