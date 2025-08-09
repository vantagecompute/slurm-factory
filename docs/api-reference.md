---
# Copyright (c) 2025 Vantage Compute Corporation.
layout: page
title: API Reference
permalink: /api-reference/
---

---
layout: page
title: API Reference
description: Complete API reference for slurm-factory Python module
permalink: /api-reference/
---

# API Reference

Complete reference for the slurm-factory Python API and command-line interface.

## Command Line Interface

### `slurm-factory build`

Build a Slurm package with specified version and options.

```bash
uv run slurm-factory build [OPTIONS] SLURM_VERSION
```

**Arguments:**
- `SLURM_VERSION`: Slurm version to build (25.05, 24.11, 24.05, 23.11, 23.02)

**Options:**
- `--gpu / --no-gpu`: Enable GPU support (default: False)
- `--output-dir PATH`: Custom output directory
- `--help`: Show help message

**Examples:**
```bash
# Build CPU-only package
uv run slurm-factory build 25.05

# Build with GPU support
uv run slurm-factory build 25.05 --gpu

# Custom output directory
uv run slurm-factory build 25.05 --output-dir /custom/path
```

### `slurm-factory list`

List built packages and available versions.

```bash
uv run slurm-factory list [OPTIONS]
```

**Options:**
- `--built`: Show only built packages
- `--available`: Show available Slurm versions
- `--help`: Show help message

### `slurm-factory clean`

Clean build artifacts and cache.

```bash
uv run slurm-factory clean [OPTIONS]
```

**Options:**
- `--all`: Clean everything including cache
- `--builds`: Clean only build artifacts
- `--cache`: Clean only Spack cache
- `--help`: Show help message

### `slurm-factory version`

Show version information.

```bash
uv run slurm-factory version
```

## Python API

### Core Classes

#### `SlurmBuilder`

Main class for building Slurm packages.

```python
from slurm_factory.builder import SlurmBuilder

class SlurmBuilder:
    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize the Slurm builder.
        
        Args:
            output_dir: Custom output directory for packages
        """
    
    def build_slurm_package(
        self, 
        slurm_version: str, 
        gpu: bool = False
    ) -> BuildResult:
        """Build a Slurm package.
        
        Args:
            slurm_version: Version of Slurm to build
            gpu: Enable GPU support
            
        Returns:
            BuildResult with success status and package paths
            
        Raises:
            BuildError: If build fails
            ContainerError: If container operations fail
        """
```

**Example Usage:**
```python
from slurm_factory.builder import SlurmBuilder

# Create builder
builder = SlurmBuilder()

# Build package
result = builder.build_slurm_package("25.05", gpu=False)

if result.success:
    print(f"Built packages: {result.packages}")
else:
    print(f"Build failed: {result.errors}")
```

#### `SlurmVersion`

Enum for supported Slurm versions.

```python
from slurm_factory.constants import SlurmVersion

class SlurmVersion(str, Enum):
    V25_05 = "25.05"
    V24_11 = "24.11"
    V24_05 = "24.05"
    V23_11 = "23.11"
    V23_02 = "23.02"
```

#### `BuildResult`

Result object returned by build operations.

```python
@dataclass
class BuildResult:
    success: bool
    packages: List[Path]
    build_time: timedelta
    errors: List[str]
    slurm_version: str
    gpu_enabled: bool
```

### Configuration

#### `Config`

Configuration management class.

```python
from slurm_factory.config import Config

class Config:
    @property
    def build_dir(self) -> Path:
        """Build directory path."""
    
    @property
    def cache_dir(self) -> Path:
        """Cache directory path."""
    
    @property
    def output_dir(self) -> Path:
        """Output directory path."""
    
    def get_container_config(self) -> ContainerConfig:
        """Get container configuration."""
    
    def get_spack_config(self, version: str, gpu: bool) -> SpackConfig:
        """Get Spack configuration for version."""
```

### Constants

#### Version Mappings

```python
from slurm_factory.constants import SLURM_VERSIONS

# Dictionary mapping versions to download URLs and hashes
SLURM_VERSIONS = {
    "25.05": {
        "url": "https://github.com/SchedMD/slurm/archive/refs/tags/slurm-25-05.tar.gz",
        "hash": "sha256:...",
        "spack_spec": "slurm@25.05"
    },
    # ... other versions
}
```

#### Script Templates

```python
from slurm_factory.constants import (
    SPACK_INSTALL_SCRIPT,
    SLURM_BUILD_SCRIPT,
    PACKAGE_CREATION_SCRIPT
)

# Access script templates for customization
script = SPACK_INSTALL_SCRIPT.substitute(
    spack_version="v0.20.1",
    python_version="3.11"
)
```

### Exceptions

#### `BuildError`

Base exception for build-related errors.

```python
class BuildError(Exception):
    """Base exception for build errors."""
    
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(message)
        self.details = details or {}
```

#### `ContainerError`

Exception for container-related errors.

```python
class ContainerError(BuildError):
    """Exception for container operations."""
    
    def __init__(self, message: str, container_id: Optional[str] = None):
        super().__init__(message)
        self.container_id = container_id
```

#### `SpackError`

Exception for Spack-related errors.

```python
class SpackError(BuildError):
    """Exception for Spack operations."""
    
    def __init__(self, message: str, command: Optional[str] = None):
        super().__init__(message)
        self.command = command
```

### Utilities

#### Package Management

```python
from slurm_factory.utils import (
    list_built_packages,
    clean_build_artifacts,
    validate_package
)

def list_built_packages() -> List[PackageInfo]:
    """List all built packages."""

def clean_build_artifacts(keep_cache: bool = True) -> CleanResult:
    """Clean build artifacts."""

def validate_package(package_path: Path) -> ValidationResult:
    """Validate package integrity."""
```

#### Container Utilities

```python
from slurm_factory.container import (
    list_containers,
    cleanup_containers,
    get_container_info
)

def list_containers() -> List[ContainerInfo]:
    """List active build containers."""

def cleanup_containers() -> int:
    """Clean up orphaned containers."""

def get_container_info(container_id: str) -> ContainerInfo:
    """Get container information."""
```

## Data Structures

### Configuration Objects

#### `ContainerConfig`

```python
@dataclass
class ContainerConfig:
    image: str = "ubuntu:22.04"
    cpu_limit: Optional[str] = None
    memory_limit: str = "16GB"
    swap_limit: bool = False
    network: str = "default"
    storage_pool: str = "default"
```

#### `SpackConfig`

```python
@dataclass
class SpackConfig:
    version: str
    install_dir: Path
    cache_dir: Path
    build_jobs: int
    specs: List[str]
    variants: Dict[str, str]
```

#### `PackageInfo`

```python
@dataclass
class PackageInfo:
    slurm_version: str
    gpu_enabled: bool
    build_date: datetime
    software_package: Path
    module_package: Path
    size_mb: int
```

### Result Objects

#### `ValidationResult`

```python
@dataclass
class ValidationResult:
    valid: bool
    errors: List[str]
    warnings: List[str]
    package_info: Optional[PackageInfo] = None
```

#### `CleanResult`

```python
@dataclass
class CleanResult:
    files_removed: int
    space_freed_mb: int
    errors: List[str]
```

## Environment Variables

### Configuration Variables

```bash
# Build configuration
export SLURM_FACTORY_BUILD_DIR="$HOME/.slurm-factory"
export SLURM_FACTORY_CACHE_DIR="$HOME/.slurm-factory/cache"
export SLURM_FACTORY_OUTPUT_DIR="$HOME/.slurm-factory/builds"

# Container configuration
export SLURM_FACTORY_CONTAINER_CPU="8"
export SLURM_FACTORY_CONTAINER_MEMORY="16GB"
export SLURM_FACTORY_CONTAINER_IMAGE="ubuntu:22.04"

# Spack configuration
export SLURM_FACTORY_SPACK_JOBS="8"
export SLURM_FACTORY_SPACK_CACHE="$HOME/.slurm-factory/spack-cache"

# Logging
export SLURM_FACTORY_LOG_LEVEL="INFO"
export SLURM_FACTORY_LOG_FILE="$HOME/.slurm-factory/logs/slurm-factory.log"
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0    | Success |
| 1    | General error |
| 2    | Invalid arguments |
| 3    | Container error |
| 4    | Build error |
| 5    | Package error |
| 6    | Configuration error |

## Examples

### Basic Usage

```python
#!/usr/bin/env python3
"""Example: Build and deploy Slurm package."""

from pathlib import Path
from slurm_factory.builder import SlurmBuilder
from slurm_factory.utils import validate_package

def main():
    # Initialize builder
    builder = SlurmBuilder(output_dir=Path("/custom/output"))
    
    # Build package
    result = builder.build_slurm_package("25.05", gpu=False)
    
    if not result.success:
        print(f"Build failed: {result.errors}")
        return 1
    
    # Validate packages
    for package in result.packages:
        validation = validate_package(package)
        if not validation.valid:
            print(f"Package validation failed: {validation.errors}")
            return 1
    
    print(f"Successfully built {len(result.packages)} packages")
    print(f"Build time: {result.build_time}")
    return 0

if __name__ == "__main__":
    exit(main())
```

### Custom Configuration

```python
#!/usr/bin/env python3
"""Example: Custom build configuration."""

from slurm_factory.builder import SlurmBuilder
from slurm_factory.config import Config, ContainerConfig, SpackConfig

def main():
    # Custom container configuration
    container_config = ContainerConfig(
        cpu_limit="16",
        memory_limit="32GB",
        swap_limit=False
    )
    
    # Custom Spack configuration
    spack_config = SpackConfig(
        build_jobs=16,
        variants={"slurm": "+pmix +hwloc +numa"}
    )
    
    # Initialize with custom config
    config = Config()
    config.container_config = container_config
    config.spack_config = spack_config
    
    builder = SlurmBuilder(config=config)
    
    # Build with custom configuration
    result = builder.build_slurm_package("25.05", gpu=True)
    
    return 0 if result.success else 1

if __name__ == "__main__":
    exit(main())
```

---

**See also**: 
- [Architecture documentation](/slurm-factory/architecture/) for detailed design
- [Examples repository](https://github.com/vantagecompute/slurm-factory/tree/dev/examples)
- [Installation guide](/slurm-factory/installation/)
