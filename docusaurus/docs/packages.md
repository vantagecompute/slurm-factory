# Packages

This page is generated from the current `slurm_factory.constants` source plus local cache contents.
Regenerate it with:

```bash
uv run python scripts/generate_packages_page.py
```

Generated: 2026-06-17 17:25 UTC

## Current Support Matrix

Slurm Factory currently defines **4 Slurm versions**, **6 OS toolchains**,
and **2 artifact architectures**, for **48 public tarball combinations**
plus matching Spack buildcache mirrors.

### Slurm Versions

| Slurm version | Spack package version | Status |
|---------------|-----------------------|--------|
| `26.05` | `26-05-0-1` | Latest supported |
| `25.11` | `25-11-6-1` | Supported |
| `24.11` | `24-11-6-1` | Supported |
| `23.11` | `23-11-11-1` | Supported |

### OS Toolchains

| Toolchain | OS/Distribution | System GCC | glibc | Base image |
|-----------|-----------------|------------|-------|------------|
| `resolute` | Ubuntu 26.04 (Resolute) | 15.2.0 | 2.42 | `ubuntu:resolute` |
| `noble` | Ubuntu 24.04 (Noble) | 13.3.0 | 2.39 | `ubuntu:noble` |
| `jammy` | Ubuntu 22.04 (Jammy) | 11.4.0 | 2.35 | `ubuntu:jammy` |
| `rockylinux10` | Rocky Linux 10 | 14.3.1 | 2.39 | `rockylinux/rockylinux:10` |
| `rockylinux9` | Rocky Linux 9 | 11.5.0 | 2.34 | `rockylinux/rockylinux:9` |
| `rockylinux8` | Rocky Linux 8 | 8.5.0 | 2.28 | `rockylinux/rockylinux:8` |

### Architectures

| Architecture | Notes |
|--------------|-------|
| `amd64` | Built on x86_64 runners and published with the `amd64` artifact label. |
| `arm64` | Built on ARM64 runners and published with the `arm64` artifact label. |

## Public Package Matrix

Tarballs use this naming pattern:

```text
slurm-{version}-{toolchain}-{architecture}-software.tar.gz
```

Each tarball has a detached GPG signature at the same URL with `.asc` appended.

| Slurm | Toolchain | Architectures | Spack buildcache | Tarball URL pattern |
|-------|-----------|---------------|------------------|---------------------|
| `26.05` | `resolute` | `amd64`, `arm64` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/resolute/slurm/26.05/` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/resolute/26.05/<architecture>/slurm-26.05-resolute-<architecture>-software.tar.gz` |
| `26.05` | `noble` | `amd64`, `arm64` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/noble/slurm/26.05/` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/noble/26.05/<architecture>/slurm-26.05-noble-<architecture>-software.tar.gz` |
| `26.05` | `jammy` | `amd64`, `arm64` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/jammy/slurm/26.05/` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/jammy/26.05/<architecture>/slurm-26.05-jammy-<architecture>-software.tar.gz` |
| `26.05` | `rockylinux10` | `amd64`, `arm64` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/rockylinux10/slurm/26.05/` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/rockylinux10/26.05/<architecture>/slurm-26.05-rockylinux10-<architecture>-software.tar.gz` |
| `26.05` | `rockylinux9` | `amd64`, `arm64` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/rockylinux9/slurm/26.05/` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/rockylinux9/26.05/<architecture>/slurm-26.05-rockylinux9-<architecture>-software.tar.gz` |
| `26.05` | `rockylinux8` | `amd64`, `arm64` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/rockylinux8/slurm/26.05/` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/rockylinux8/26.05/<architecture>/slurm-26.05-rockylinux8-<architecture>-software.tar.gz` |
| `25.11` | `resolute` | `amd64`, `arm64` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/resolute/slurm/25.11/` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/resolute/25.11/<architecture>/slurm-25.11-resolute-<architecture>-software.tar.gz` |
| `25.11` | `noble` | `amd64`, `arm64` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/noble/slurm/25.11/` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/noble/25.11/<architecture>/slurm-25.11-noble-<architecture>-software.tar.gz` |
| `25.11` | `jammy` | `amd64`, `arm64` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/jammy/slurm/25.11/` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/jammy/25.11/<architecture>/slurm-25.11-jammy-<architecture>-software.tar.gz` |
| `25.11` | `rockylinux10` | `amd64`, `arm64` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/rockylinux10/slurm/25.11/` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/rockylinux10/25.11/<architecture>/slurm-25.11-rockylinux10-<architecture>-software.tar.gz` |
| `25.11` | `rockylinux9` | `amd64`, `arm64` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/rockylinux9/slurm/25.11/` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/rockylinux9/25.11/<architecture>/slurm-25.11-rockylinux9-<architecture>-software.tar.gz` |
| `25.11` | `rockylinux8` | `amd64`, `arm64` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/rockylinux8/slurm/25.11/` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/rockylinux8/25.11/<architecture>/slurm-25.11-rockylinux8-<architecture>-software.tar.gz` |
| `24.11` | `resolute` | `amd64`, `arm64` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/resolute/slurm/24.11/` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/resolute/24.11/<architecture>/slurm-24.11-resolute-<architecture>-software.tar.gz` |
| `24.11` | `noble` | `amd64`, `arm64` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/noble/slurm/24.11/` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/noble/24.11/<architecture>/slurm-24.11-noble-<architecture>-software.tar.gz` |
| `24.11` | `jammy` | `amd64`, `arm64` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/jammy/slurm/24.11/` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/jammy/24.11/<architecture>/slurm-24.11-jammy-<architecture>-software.tar.gz` |
| `24.11` | `rockylinux10` | `amd64`, `arm64` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/rockylinux10/slurm/24.11/` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/rockylinux10/24.11/<architecture>/slurm-24.11-rockylinux10-<architecture>-software.tar.gz` |
| `24.11` | `rockylinux9` | `amd64`, `arm64` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/rockylinux9/slurm/24.11/` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/rockylinux9/24.11/<architecture>/slurm-24.11-rockylinux9-<architecture>-software.tar.gz` |
| `24.11` | `rockylinux8` | `amd64`, `arm64` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/rockylinux8/slurm/24.11/` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/rockylinux8/24.11/<architecture>/slurm-24.11-rockylinux8-<architecture>-software.tar.gz` |
| `23.11` | `resolute` | `amd64`, `arm64` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/resolute/slurm/23.11/` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/resolute/23.11/<architecture>/slurm-23.11-resolute-<architecture>-software.tar.gz` |
| `23.11` | `noble` | `amd64`, `arm64` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/noble/slurm/23.11/` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/noble/23.11/<architecture>/slurm-23.11-noble-<architecture>-software.tar.gz` |
| `23.11` | `jammy` | `amd64`, `arm64` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/jammy/slurm/23.11/` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/jammy/23.11/<architecture>/slurm-23.11-jammy-<architecture>-software.tar.gz` |
| `23.11` | `rockylinux10` | `amd64`, `arm64` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/rockylinux10/slurm/23.11/` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/rockylinux10/23.11/<architecture>/slurm-23.11-rockylinux10-<architecture>-software.tar.gz` |
| `23.11` | `rockylinux9` | `amd64`, `arm64` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/rockylinux9/slurm/23.11/` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/rockylinux9/23.11/<architecture>/slurm-23.11-rockylinux9-<architecture>-software.tar.gz` |
| `23.11` | `rockylinux8` | `amd64`, `arm64` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/rockylinux8/slurm/23.11/` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/rockylinux8/23.11/<architecture>/slurm-23.11-rockylinux8-<architecture>-software.tar.gz` |

## Dependency Buildcaches

Dependencies are shared across Slurm versions within each OS toolchain.

| Toolchain | Dependency buildcache |
|-----------|-----------------------|
| `resolute` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/resolute/slurm/deps/` |
| `noble` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/noble/slurm/deps/` |
| `jammy` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/jammy/slurm/deps/` |
| `rockylinux10` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/rockylinux10/slurm/deps/` |
| `rockylinux9` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/rockylinux9/slurm/deps/` |
| `rockylinux8` | `https://slurm-factory-spack-binary-cache.vantagecompute.ai/rockylinux8/slurm/deps/` |

## Local Cache Snapshot

The generator scans `SLURM_FACTORY_CACHE_DIR` when it is set, otherwise it scans `~/.slurm-factory`.
Set `SLURM_FACTORY_CACHE_DIR` before running the generator to scan a different cache.

| Slurm | Toolchain | Architecture | Size | Cache-relative path |
|-------|-----------|--------------|------|------------|
| `26.05` | `noble` | `unspecified` | 215.6 MB | `builds/noble/26.05/slurm-26.05-noble-software.tar.gz` |
