"""
Slurm Factory - Modern Python CLI for Building Relocatable Slurm Packages.

A comprehensive tool for building optimized, relocatable Slurm workload manager
packages using LXD containers and the Spack package manager. Features a modern
Typer CLI interface, comprehensive exception handling, and intelligent caching.

Main modules:
- main: Typer CLI application with global options
- builder: Build orchestration and LXD management
- config: Pydantic settings and cache management  
- constants: Enums, templates, and build configuration
- spack_yaml: Dynamic Spack configuration generation
- utils: LXD operations and package creation utilities
- exceptions: Custom exception hierarchy
"""

from slurm_factory.builder import build
from slurm_factory.config import Settings
from slurm_factory.constants import SlurmVersion
from slurm_factory.exceptions import (
    SlurmFactoryError,
    SlurmFactoryStreamExecError,
    SlurmFactoryInstanceCreationError,
)
from slurm_factory.main import app
from slurm_factory.spack_yaml import generate_spack_config, generate_yaml_string

__version__ = "1.0.0"
__author__ = "Vantage Compute Corporation"
__email__ = "support@vantagecompute.com"

__all__ = [
    # Main API
    "app",
    "build",
    "Settings",
    "SlurmVersion",
    "generate_spack_config",
    "generate_yaml_string",
    # Exceptions
    "SlurmFactoryError",
    "SlurmFactoryStreamExecError",
    "SlurmFactoryInstanceCreationError",
    # Version info
    "__version__",
    "__author__",
    "__email__",
]