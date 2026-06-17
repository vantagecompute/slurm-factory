#!/usr/bin/env python3
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

"""Generate the Docusaurus packages page from slurm-factory constants and cache contents."""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from slurm_factory.config import Settings  # noqa: E402
from slurm_factory.constants import (  # noqa: E402
    COMPILER_TOOLCHAINS,
    SLURM_FACTORY_SPACK_CACHE_BASE_URL,
    SLURM_VERSIONS,
)

ARCHITECTURES = ("amd64", "arm64")
PREFERRED_TOOLCHAIN_ORDER = (
    "resolute",
    "noble",
    "jammy",
    "rockylinux10",
    "rockylinux9",
    "rockylinux8",
)
TARBALL_RE = re.compile(
    r"^slurm-(?P<version>\d+\.\d+)-(?P<toolchain>[a-z0-9]+)(?:-(?P<architecture>amd64|arm64))?-software\.tar\.gz$"
)


@dataclass(frozen=True)
class CachedTarball:
    """A tarball discovered in the local slurm-factory cache."""

    version: str
    toolchain: str
    architecture: str
    path: Path
    size_bytes: int


def ordered_toolchains() -> list[str]:
    """Return supported toolchains in documentation-friendly order."""
    preferred = [toolchain for toolchain in PREFERRED_TOOLCHAIN_ORDER if toolchain in COMPILER_TOOLCHAINS]
    remaining = sorted(set(COMPILER_TOOLCHAINS) - set(preferred))
    return preferred + remaining


def discover_cached_tarballs(cache_dir: Path) -> list[CachedTarball]:
    """Find redistributable Slurm tarballs in the local cache."""
    builds_dir = cache_dir / "builds"
    if not builds_dir.exists():
        return []

    tarballs: list[CachedTarball] = []
    for tarball in sorted(builds_dir.rglob("slurm-*-software.tar.gz")):
        match = TARBALL_RE.match(tarball.name)
        if not match:
            continue
        tarballs.append(
            CachedTarball(
                version=match.group("version"),
                toolchain=match.group("toolchain"),
                architecture=match.group("architecture") or "unspecified",
                path=tarball,
                size_bytes=tarball.stat().st_size,
            )
        )
    return tarballs


def human_size(size_bytes: int) -> str:
    """Format a byte count for Markdown tables."""
    units = ("B", "KB", "MB", "GB", "TB")
    size = float(size_bytes)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= 1024
    return f"{size_bytes} B"


def tarball_url(version: str, toolchain: str, architecture: str) -> str:
    """Return the public tarball URL for a supported package combination."""
    filename = f"slurm-{version}-{toolchain}-{architecture}-software.tar.gz"
    return f"{SLURM_FACTORY_SPACK_CACHE_BASE_URL}/{toolchain}/{version}/{architecture}/{filename}"


def buildcache_url(version: str, toolchain: str) -> str:
    """Return the public Slurm buildcache URL for a supported version/toolchain."""
    return f"{SLURM_FACTORY_SPACK_CACHE_BASE_URL}/{toolchain}/slurm/{version}/"


def dependency_cache_url(toolchain: str) -> str:
    """Return the public dependency buildcache URL for a supported toolchain."""
    return f"{SLURM_FACTORY_SPACK_CACHE_BASE_URL}/{toolchain}/slurm/deps/"


def toolchain_table() -> str:
    """Render the supported toolchain table."""
    rows = [
        "| Toolchain | OS/Distribution | System GCC | glibc | Base image |",
        "|-----------|-----------------|------------|-------|------------|",
    ]
    for toolchain in ordered_toolchains():
        os_name, gcc_version, glibc_version, base_image, _ = COMPILER_TOOLCHAINS[toolchain]
        rows.append(f"| `{toolchain}` | {os_name} | {gcc_version} | {glibc_version} | `{base_image}` |")
    return "\n".join(rows)


def version_table() -> str:
    """Render the supported Slurm version table."""
    rows = [
        "| Slurm version | Spack package version | Status |",
        "|---------------|-----------------------|--------|",
    ]
    for index, (version, spack_version) in enumerate(SLURM_VERSIONS.items()):
        status = "Latest supported" if index == 0 else "Supported"
        rows.append(f"| `{version}` | `{spack_version}` | {status} |")
    return "\n".join(rows)


def matrix_table() -> str:
    """Render the full public artifact matrix."""
    rows = [
        "| Slurm | Toolchain | Architectures | Spack buildcache | Tarball URL pattern |",
        "|-------|-----------|---------------|------------------|---------------------|",
    ]
    architectures = ", ".join(f"`{architecture}`" for architecture in ARCHITECTURES)
    for version in SLURM_VERSIONS:
        for toolchain in ordered_toolchains():
            sample_url = tarball_url(version, toolchain, "<architecture>")
            rows.append(
                f"| `{version}` | `{toolchain}` | {architectures} | "
                f"`{buildcache_url(version, toolchain)}` | `{sample_url}` |"
            )
    return "\n".join(rows)


def local_cache_table(cache_dir: Path, tarballs: list[CachedTarball]) -> str:
    """Render local cache discovery results."""
    if not tarballs:
        return (
            "No local tarballs were found in the configured cache when this page was generated."
        )

    rows = [
        "| Slurm | Toolchain | Architecture | Size | Cache-relative path |",
        "|-------|-----------|--------------|------|------------|",
    ]
    for tarball in tarballs:
        try:
            relative_path = tarball.path.relative_to(cache_dir)
        except ValueError:
            relative_path = Path(tarball.path.name)
        rows.append(
            f"| `{tarball.version}` | `{tarball.toolchain}` | `{tarball.architecture}` | "
            f"{human_size(tarball.size_bytes)} | `{relative_path}` |"
        )
    return "\n".join(rows)


def render_page(cache_dir: Path, tarballs: list[CachedTarball]) -> str:
    """Render the complete packages Markdown page."""
    generated_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    toolchain_count = len(COMPILER_TOOLCHAINS)
    version_count = len(SLURM_VERSIONS)
    package_count = toolchain_count * version_count * len(ARCHITECTURES)
    dependency_rows = "\n".join(
        f"| `{toolchain}` | `{dependency_cache_url(toolchain)}` |"
        for toolchain in ordered_toolchains()
    )

    return f"""# Packages

This page is generated from the current `slurm_factory.constants` source plus local cache contents.
Regenerate it with:

```bash
uv run python scripts/generate_packages_page.py
```

Generated: {generated_at}

## Current Support Matrix

Slurm Factory currently defines **{version_count} Slurm versions**, **{toolchain_count} OS toolchains**,
and **{len(ARCHITECTURES)} artifact architectures**, for **{package_count} public tarball combinations**
plus matching Spack buildcache mirrors.

### Slurm Versions

{version_table()}

### OS Toolchains

{toolchain_table()}

### Architectures

| Architecture | Notes |
|--------------|-------|
| `amd64` | Built on x86_64 runners and published with the `amd64` artifact label. |
| `arm64` | Built on ARM64 runners and published with the `arm64` artifact label. |

## Public Package Matrix

Tarballs use this naming pattern:

```text
slurm-{{version}}-{{toolchain}}-{{architecture}}-software.tar.gz
```

Each tarball has a detached GPG signature at the same URL with `.asc` appended.

{matrix_table()}

## Dependency Buildcaches

Dependencies are shared across Slurm versions within each OS toolchain.

| Toolchain | Dependency buildcache |
|-----------|-----------------------|
{dependency_rows}

## Local Cache Snapshot

The generator scans `SLURM_FACTORY_CACHE_DIR` when it is set, otherwise it scans `~/.slurm-factory`.
Set `SLURM_FACTORY_CACHE_DIR` before running the generator to scan a different cache.

{local_cache_table(cache_dir, tarballs)}
"""


def main() -> None:
    """Generate the Docusaurus packages page."""
    settings = Settings(project_name="slurm-factory")
    cache_dir = Path(os.environ.get("SLURM_FACTORY_CACHE_DIR", settings.home_cache_dir)).expanduser()
    tarballs = discover_cached_tarballs(cache_dir)
    output_path = REPO_ROOT / "docusaurus" / "docs" / "packages.md"
    output_path.write_text(render_page(cache_dir, tarballs), encoding="utf-8")
    print(f"Generated {output_path} with {len(tarballs)} local cache artifact(s)")


if __name__ == "__main__":
    main()
