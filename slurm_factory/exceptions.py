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
