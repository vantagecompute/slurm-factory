"""Main config module for slurm-builder."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Settings:
    """Common settings for the entire app."""

    project_name: str

    @property
    def home_cache_dir(self) -> Path:
        """Get the ~/.slurm-factory directory."""
        return Path.home() / ".slurm-factory"

    @property
    def builds_dir(self) -> Path:
        """Get the ~/.slurm-factory/builds directory."""
        return self.home_cache_dir / "builds"

    @property
    def spack_buildcache_dir(self) -> Path:
        """Get the ~/.slurm-factory/spack-buildcache directory."""
        return self.home_cache_dir / "spack-buildcache"

    @property
    def spack_sourcecache_dir(self) -> Path:
        """Get the ~/.slurm-factory/spack-sourcecache directory."""
        return self.home_cache_dir / "spack-sourcecache"

    def ensure_cache_dirs(self) -> None:
        """Create all cache directories if they don't exist with proper permissions."""
        # Create directories with proper permissions (777)
        self.home_cache_dir.mkdir(mode=0o777, exist_ok=True)
        self.builds_dir.mkdir(mode=0o777, exist_ok=True)
        self.spack_buildcache_dir.mkdir(mode=0o777, exist_ok=True)
        self.spack_sourcecache_dir.mkdir(mode=0o777, exist_ok=True)
