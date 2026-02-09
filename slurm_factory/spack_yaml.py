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

"""
Dynamic Spack environment configuration generator for slurm-factory.

This module generates Spack environment configurations as Python dictionaries,
allowing for easy parameterization of Slurm versions and GPU support options.
"""

from typing import Any, Dict

import yaml

from slurm_factory.constants import COMPILER_TOOLCHAINS, SLURM_FACTORY_SPACK_CACHE_BASE_URL, SLURM_VERSIONS

# Template name for relocatable module files (relative to Spack templates directory)
TEMPLATE_NAME = "modules/relocatable_modulefile.lua"


def get_mirrors(buildcache: str, toolchain: str, slurm_version: str) -> Dict[str, Dict[str, bool | str]]:
    """Return the mirrors dictionary based on buildcache."""
    mirrors: Dict[str, Dict[str, bool | str]] = {
        "spack-public": {
            "url": "https://mirror.spack.io",
            "signed": False,
            "binary": False,
            "source": True,
        }
    }

    if (buildcache == "all") or (buildcache == "deps"):
        mirrors["slurm-deps-buildcache"] = {
            "url": f"{SLURM_FACTORY_SPACK_CACHE_BASE_URL}/{toolchain}/slurm/deps",
            "signed": True,
            "binary": True,
            "source": False,
        }

        if buildcache == "all":
            mirrors["slurm-buildcache"] = {
                "url": f"{SLURM_FACTORY_SPACK_CACHE_BASE_URL}/{toolchain}/slurm/{slurm_version}",
                "signed": True,
                "binary": True,
                "source": False,
            }

    return mirrors


def generate_module_config(
    slurm_version: str = "25.11",
    gpu_support: bool = False,
    toolchain: str = "noble",
    enable_hierarchy: bool = False,
) -> Dict[str, Any]:
    """
    Generate the Lmod module configuration section for Spack.

    Args:
        slurm_version: Slurm version to build (25.11, 24.11, 23.11)
        gpu_support: Whether to include GPU support (NVML, RSMI)
        toolchain: OS toolchain identifier (e.g., "noble", "jammy", "rockylinux9")
        enable_hierarchy: Whether to use Core/Compiler/MPI hierarchy
            (default: False for backward compatibility)

    Returns:
        Dictionary representing the modules configuration section

    """
    if slurm_version not in SLURM_VERSIONS:
        raise ValueError(
            f"Unsupported Slurm version: {slurm_version}. Supported versions: {list(SLURM_VERSIONS.keys())}"
        )

    slurm_package_version = SLURM_VERSIONS[slurm_version]

    # Get GCC version from toolchain
    if toolchain not in COMPILER_TOOLCHAINS:
        raise ValueError(
            f"Unsupported toolchain: {toolchain}. Supported toolchains: {list(COMPILER_TOOLCHAINS.keys())}"
        )

    _, gcc_version, _, _, _ = COMPILER_TOOLCHAINS[toolchain]

    slurm_package_version = SLURM_VERSIONS[slurm_version]

    # Build type description for metadata
    if gpu_support:
        build_type = "GPU-enabled build"
    else:
        build_type = "standard build"

    # Configure module hierarchy
    # Core/Compiler/MPI hierarchy provides better dependency management
    # but adds complexity for simple deployments
    if enable_hierarchy:
        # 3-tier hierarchy: Core -> Compiler -> MPI
        # Core: packages built with any compiler (e.g., gcc-runtime)
        # Compiler: packages that depend on a specific compiler (e.g., openmpi)
        # MPI: packages that depend on both compiler and MPI implementation (e.g., slurm with MPI)
        hierarchy = ["mpi"]
    else:
        # Flat hierarchy for simpler deployment and backward compatibility
        hierarchy = []

    # Base module configuration
    modules_config: Dict[str, Any] = {
        "default": {
            "enable": ["lmod"],
            "lmod": {
                "core_compilers": [f"gcc@{gcc_version}"],  # Mark gcc as core for relocatable binaries
                "hierarchy": hierarchy,
                "include": (["slurm", "openmpi", "mysql"]),
                "slurm": {
                    "template": TEMPLATE_NAME,  # Apply our custom template only to Slurm
                    "autoload": "direct",
                    "conflict": ["{name}"],
                    "environment": {
                        "set": {
                            # Allow runtime override with environment variable fallback
                            "SLURM_CONF": "/etc/slurm/slurm.conf",
                            "SLURM_ROOT": "{prefix}",
                            # Add build-specific metadata
                            "SLURM_BUILD_TYPE": build_type,
                            "SLURM_VERSION": slurm_package_version,
                            # Add dynamic prefix support for redistributable packages
                            "SLURM_PREFIX": "{prefix}",
                            # Add hint for users about customization capability
                            "SLURM_MODULE_HELP": (
                                "Set SLURM_INSTALL_PREFIX before loading to override installation path"
                            ),
                            # Explicit compiler information for relocatability tracking
                            "SLURM_COMPILER": "{compiler.name}@{compiler.version}",
                            "SLURM_TARGET_ARCH": "{architecture}",
                            # GCC runtime prefix for relocatability (avoid guessing libdir)
                            "SLURM_GCC_RUNTIME_PREFIX": "{^gcc-runtime.prefix}",
                        },
                        "prepend_path": {
                            # Rely on RPATH/RUNPATH for library discovery - no LD_LIBRARY_PATH needed
                            "PATH": "{prefix}/bin:{prefix}/sbin",
                            "CPATH": "{prefix}/include",
                            "PKG_CONFIG_PATH": "{prefix}/lib/pkgconfig",
                            "MANPATH": "{prefix}/share/man",
                            "CMAKE_PREFIX_PATH": "{prefix}",
                        },
                    },
                },
            },
        },
    }

    openmpi_config: Dict[str, Any] = {
        "environment": {"set": {"OMPI_MCA_plm": "slurm"}},
    }
    if enable_hierarchy:
        # In hierarchical mode, automatically load OpenMPI when compiler module is loaded
        openmpi_config["autoload"] = "direct"  # type: ignore[assignment]
        modules_config["default"]["lmod"]["openmpi"] = openmpi_config  # type: ignore[index]

    return modules_config


def generate_spack_config(
    slurm_version: str = "25.11",
    gpu_support: bool = False,
    install_tree_root: str = "/opt/slurm/software",
    view_root: str = "/opt/slurm/view",  # Use separate view directory
    toolchain: str = "noble",
    buildcache: str = "none",
    enable_hierarchy: bool = False,
) -> Dict[str, Any]:
    """
    Generate a Spack environment configuration dictionary.

    Args:
        slurm_version: Slurm version to build (25.11, 24.11, 23.11)
        gpu_support: Whether to include GPU support (NVML, RSMI)
        install_tree_root: Root directory for Spack installations
        view_root: Root directory for Spack view
        toolchain: OS toolchain identifier (e.g., "noble", "jammy", "rockylinux9")
        buildcache: Buildcache source ("none", "s3", "oci")
        enable_hierarchy: Whether to use Core/Compiler/MPI hierarchy (default: False)

    Returns:
        Dictionary representing the Spack environment configuration

    """
    if slurm_version not in SLURM_VERSIONS:
        raise ValueError(
            f"Unsupported Slurm version: {slurm_version}. Supported versions: {list(SLURM_VERSIONS.keys())}"
        )

    slurm_package_version = SLURM_VERSIONS[slurm_version]

    # Get compiler info - base_image determines GLIBC version
    if toolchain not in COMPILER_TOOLCHAINS:
        raise ValueError(
            f"Unsupported toolchain: {toolchain}. Supported toolchains: {list(COMPILER_TOOLCHAINS.keys())}"
        )

    _, gcc_version, _, _, _ = COMPILER_TOOLCHAINS[toolchain]

    # Always use system compiler from toolchain
    compiler_spec = f"%gcc@{gcc_version}"

    # Build Slurm spec with conditional features
    gpu_flags = "+nvml +rsmi" if gpu_support else "~nvml ~rsmi"

    # Spec definitions for packages
    # cyrus-sasl 2.1.28 has old-style function definitions incompatible with GCC 15+
    cyrus_sasl_spec = (
        "cyrus-sasl cflags='-Wno-error=implicit-function-declaration "
        "-Wno-error=incompatible-pointer-types -std=gnu89'"
    )
    openldap_spec = (
        f"openldap@2.6.8+client_only~perl+sasl+dynamic+shared~static tls=openssl "
        f"^openssl@3.6.0 ^{cyrus_sasl_spec} {compiler_spec}"
    )
    # Match curl spec from slurm package.py: libs=shared,static +nghttp2 +libssh2 +ldap +gssapi +libidn2
    # Using slurm_factory.curl with exact variants to match slurm dependency requirements
    curl_spec = (
        f"slurm_factory.curl@8.15.0 libs=shared,static +nghttp2+libssh2+ldap+gssapi+libidn2 "
        f"tls=openssl ^openssl@3.6.0 ^openldap@2.6.8 {compiler_spec}"
    )
    specs = [
        # System compiler from toolchain - no custom build needed
        # gcc-runtime will be built as a dependency of gcc
        # NOTE: Do NOT specify compiler for gcc itself - it uses system compiler
        # The GCC version is determined by the OS toolchain (e.g., noble = GCC 13.2.0)
        f"gcc@{gcc_version} +binutils +piclibs languages=c,c++,fortran",
        # All packages below will use %gcc@{compiler_version}
        f"gettext@0.23.1 {compiler_spec}",  # Provides libintl.so.8 needed by glib, krb5, etc.
        f"zlib@1.3.1 {compiler_spec}",  # Build zlib first (needed by OpenSSL and others)
        # Build OpenSSL with explicit zlib dependency
        f"openssl@3.6.0 ^zlib@1.3.1 {compiler_spec}",
        f"jansson@2.14 {compiler_spec}",  # JSON library for libjwt
        # JWT library with all dependencies - let Spack choose available version
        f"libjwt ^openssl@3.6.0 ^zlib@1.3.1 ^jansson@2.14 {compiler_spec}",
        f"gettext {compiler_spec}",  # Provides libintl.so.8 needed by glib, krb5, etc.
        openldap_spec,  # Build openldap before curl since curl+ldap needs it
        curl_spec,
        f"patchelf@0.18.0 {compiler_spec}",  # For RPATH fixing during relocatability
    ]
    # Using slurm_factory.freeipmi@1.6.16 for GCC 14 compatibility
    # (1.6.9 has implicit function declaration errors)
    specs.append(f"slurm_factory.freeipmi@1.6.16 {compiler_spec}")
    # OpenMPI with slurm scheduler support - explicitly depend on our slurm_factory.slurm
    specs.append(
        f"openmpi@5.0.8 schedulers=slurm fabrics=auto {compiler_spec}"
    )
    specs.append(f"pmix@5.0.5 ~munge ~python {compiler_spec}")
    # Use custom MySQL from slurm_factory repo with ABI check disabled
    specs.append(f"mysql@8.0.35 +client_only {compiler_spec}")
    specs.append(f"hdf5@1.14.6 +hl +cxx {compiler_spec}")
    # CUDA is configured in packages section below - it's a pre-built binary, not compiled
    specs.append(
        f"slurm_factory.slurm@{slurm_package_version} {gpu_flags} sysconfdir=/etc/slurm {compiler_spec}"
    )

    config: Dict[str, Any] = {
        "spack": {
            "specs": specs,
            "repos": {
                "slurm_factory": {
                    "git": "https://github.com/vantagecompute/slurm-factory-spack-repo.git",
                    "branch": "main",
                },
            },
            "concretizer": {
                "unify": "when_possible",
                "reuse": True,
            },
            "config": {
                "verify": {
                    "relocatable": True,  # Verify binaries are relocatable
                    "dependencies": True,  # Verify all dependencies are present
                    "shared_libraries": True,  # Check shared library dependencies
                },
                "install_tree": {
                    "root": install_tree_root,
                    # Padding enables buildcache relocation from shorter to longer paths.
                    # Value is in bytes - reserves space in binaries for install prefix path.
                    # 128 bytes allows ~50 character path length increase during relocation.
                    # Fixes CannotGrowString error when extracting packages built with short prefixes.
                    # Must match or exceed the padding used when creating the buildcache.
                    "padded_length": 128,
                    "projections": {
                        "all": "{name}-{version}-{hash:7}"  # Short paths for better relocatability
                    },
                },
                "build_stage": "/opt/spack-stage",
                # "misc_cache": sourcecache_root,
                # "binary_index_root": binary_index_root,
                "checksum": True,
                "deprecated": False,
                # Spack 1.x performance enhancements
                "build_jobs": 4,  # Parallel build jobs
                "ccache": False,  # Disabled - system ccache incompatible with Spack-built compilers
                "connect_timeout": 30,  # Network timeout for downloads
                "verify_ssl": True,  # Security setting
                "suppress_gpg_warnings": False,  # Show GPG warnings
                # Enhanced RPATH configuration for Spack 1.x
                # This ensures binaries are truly relocatable with proper RPATH/RUNPATH
                "shared_linking": {
                    "type": "rpath",  # Use RPATH for relocatable binaries (Spack 1.x)
                    "bind": False,  # Don't bind absolute paths - allow relocation
                    "missing_library_policy": "warn",  # Warn on missing system libraries
                },
                "db_lock_timeout": 120,  # Database lock timeout in seconds
            },
            # Package configuration: Build runtime dependencies, use build tools from compiler bootstrap env
            # Build tools (cmake, python, etc.) are build-only deps - not included in Slurm runtime
            # Libraries are runtime deps - must be built for self-contained Slurm
            "packages": {
                "all": {
                    "target": ["x86_64"],
                    "buildable": True,
                    "providers": {"mpi": ["openmpi"]},
                },
                # System build tools (build-time only, NOT runtime dependencies of Slurm)
                "cmake": {"buildable": True},
                "python": {"buildable": True},
                "gmake": {"buildable": True},
                "m4": {"buildable": True},
                "pkgconf": {"buildable": True},
                "diffutils": {"buildable": True},
                "findutils": {"buildable": True},
                "gettext": {"buildable": True},
                "libbsd": {"buildable": True},
                "libsigsegv": {"buildable": True},
                "tar": {"buildable": True},
                # Build autotools from source for libjwt compatibility
                "autoconf": {"buildable": True},
                "automake": {
                    "buildable": True,
                    "version": [":1.16.3"],  # libjwt@1.15.3 incompatible with automake 1.16.5
                },
                "libtool": {"buildable": True},
                # Build runtime libraries (these ARE Slurm dependencies)
                "libmd": {"buildable": True},
                # Build xz and bzip2 from source to avoid library version conflicts
                "xz": {"buildable": True},
                "bzip2": {"buildable": True},
                # Runtime libraries that must be built for Slurm linking
                # These are critical dependencies that Slurm links against at runtime
                "munge": {"buildable": True},  # Authentication - let Spack pick latest available
                "json-c": {"buildable": True},  # JSON parsing - linked at runtime
                "libpciaccess": {"buildable": True},  # PCI access library
                "cyrus-sasl": {
                    "buildable": True,
                    "require": [
                        (
                            "cflags='-Wno-error=implicit-function-declaration "
                            "-Wno-error=incompatible-pointer-types -std=gnu89'"
                        )
                    ],
                },  # SASL authentication (cflags set in spec)
                "rapidjson": {"buildable": True},
                "openldap": {
                    "buildable": True,
                    "version": ["2.6.8"],
                },
                "curl": {
                    "buildable": True,
                    "version": ["8.15.0"],
                },
                "ca-certificates-mozilla": {"buildable": True},  # Self-contained SSL certificates
                "readline": {"buildable": True},  # Interactive command line
                "ncurses": {"buildable": True},  # Terminal control for readline
                "lz4": {"buildable": True},  # Fast compression - linked at runtime
                "zlib-ng": {
                    "buildable": True,
                    "variants": "+compat",
                },  # zlib-ng with zlib compatibility - linked at runtime
                "hwloc": {"buildable": True, "version": ["2:"]},  # Hardware topology - use hwloc 2.x series
                "numactl": {"buildable": True},  # NUMA support - used by Slurm for memory binding
                # Build ALL system libraries from source for complete isolation
                "dbus": {
                    "buildable": True,
                    "variants": "system-socket=/var/run/dbus/system_bus_socket",
                },
                "glib": {"buildable": True},
                "libxml2": {"buildable": True},
                # Build these inside Spack to avoid Perl XS module linking to external system libraries
                "gdbm": {"buildable": True},
                "berkeley-db": {"buildable": True},
                # Force Perl to use Spack-built dependencies for XS modules
                "perl": {"require": ["^bzip2", "^gdbm", "^berkeley-db"]},
                "libgcrypt": {"buildable": True},
                "libgpg-error": {"buildable": True},
                # Additional REST API dependencies - build for relocatability
                "http-parser": {"buildable": True},  # HTTP parsing for REST API
                "libjwt": {
                    "buildable": True,
                },  # JWT token support - essential for Slurm REST API
                # MySQL client library for Slurm accounting (from slurm_factory repo)
                "mysql": {
                    "buildable": True,
                    "version": ["8.0.35"],
                },
                "librdkafka": {"buildable": True},
                # PMIx configuration for consistent version
                "pmix": {
                    "buildable": True,
                    "version": ["5.0.5"],
                    "variants": "~munge ~python",  # Removed +shared as it doesn't exist
                },
                "hdf5": {"buildable": True},
                # Runtime-linked libraries: build with Spack for true relocatability
                # These may be linked by Slurm or its dependencies at runtime
                "linux-pam": {"buildable": True},  # Slurm PAM authentication
                "libevent": {"buildable": True},  # Used by PMIx and OpenMPI
                "jansson": {"buildable": True},  # JSON parsing for some Slurm features (shared is default)
                "libyaml": {"buildable": True},  # Configuration parsing
                # NOTE: bzip2 and xz are configured as external packages above to avoid library conflicts
                "zstd": {"buildable": True},  # Fast compression (transitive)
                # GCC compiler - downloaded from buildcache (built separately with build-compiler command)
                # Let Spack install it from buildcache so gcc-runtime can find it properly
                # The compiler is registered separately via 'spack compiler add' after bootstrap
                "gcc": {
                    "buildable": True,
                    "externals": [],  # Prevent using system GCC
                    "version": [gcc_version],
                    "variants": "+binutils +piclibs languages=c,c++,fortran",
                },
                # gcc-runtime will be built automatically as a dependency of gcc
                # It provides runtime libraries for packages compiled with this GCC version
                "gcc-runtime": {
                    "buildable": True,
                    "version": [gcc_version],
                },
                "slurm_factory.slurm": {
                    "version": [slurm_package_version],
                    "buildable": True,
                    "variants": "+shared ~static +pic",  # Consistent shared library preference
                },
                # OpenMPI configuration for consistent build
                "openmpi": {
                    "buildable": True,
                    "version": ["5.0.8"],
                    "variants": "schedulers=slurm fabrics=auto",
                },
                "cuda": {
                    "buildable": True,
                    "version": ["12.9.0"],
                },
            },
            "develop": {},
            "view": {
                "default": {
                    "root": view_root,
                    "link_type": "hardlink",  # Use hardlinks instead of symlinks for easier copying
                    "link": "all",  # Explicitly link all installed specs (except excluded ones)
                    "projections": {"all": "."},  # Merge all packages into unified FHS structure
                    # No 'select' - include all installed packages automatically
                    # Exclude build tools (external, not runtime deps) and compiler
                    "exclude": [
                        "cmake",
                        "python",
                        "gmake",
                        "m4",
                        "pkgconf",
                        "diffutils",
                        "findutils",
                        "libbsd",
                        "libsigsegv",
                        "tar",
                        "flex",  # Build-only tool - lexer generator
                        "bison",  # Build-only tool - parser generator
                        "autoconf",  # Build-only tool - configure script generator
                        "automake",  # Build-only tool - makefile generator
                        "gcc",  # Compiler is in separate location
                    ]
                    + (["cuda", "rocm-core", "rocm-smi-lib"] if gpu_support else []),
                }
            },
            "mirrors": get_mirrors(buildcache, toolchain, slurm_version),
            # Start with empty compilers - GCC will be downloaded from buildcache and explicitly detected
            # via spack compiler find (system compiler detection is disabled)
            "compilers": [],
            "modules": generate_module_config(slurm_version, gpu_support, toolchain, enable_hierarchy),
        }
    }

    return config


def get_comment_header(slurm_version: str, gpu_support: bool) -> str:
    """Generate a descriptive comment header for the configuration."""
    if gpu_support:
        desc = "with GPU support"
    else:
        desc = "(without GPU support)"
    return f"# Spack environment for building Slurm {slurm_version} {desc}"


def generate_yaml_string(
    slurm_version: str = "25.11",
    toolchain: str = "noble",
    buildcache: str = "none",
    gpu_support: bool = False,
    enable_hierarchy: bool = False,
) -> str:
    """
    Generate a YAML string representation of the Spack environment configuration.

    Args:
        slurm_version: Slurm version to build
        toolchain: OS toolchain identifier (e.g., "noble", "jammy", "rockylinux9")
        buildcache: "none", "all", "deps"
        gpu_support: Whether to include GPU support
        enable_hierarchy: Whether to use Core/Compiler/MPI hierarchy

    Returns:
        YAML string representation of the configuration

    """
    config = generate_spack_config(
        slurm_version=slurm_version,
        toolchain=toolchain,
        buildcache=buildcache,
        gpu_support=gpu_support,
        enable_hierarchy=enable_hierarchy,
    )
    header = get_comment_header(slurm_version, gpu_support)

    # Generate YAML with proper formatting
    yaml_content = yaml.dump(config, default_flow_style=False, sort_keys=False, indent=2)

    return f"{header}\n{yaml_content}"


# Convenience functions for common configurations
def cpu_only_config(slurm_version: str = "25.11") -> Dict[str, Any]:
    """Generate CPU-only configuration (default, optimized for size)."""
    return generate_spack_config(slurm_version=slurm_version, gpu_support=False)


def gpu_enabled_config(slurm_version: str = "25.11") -> Dict[str, Any]:
    """Generate GPU-enabled configuration (larger, includes CUDA/ROCm)."""
    return generate_spack_config(slurm_version=slurm_version, gpu_support=True)


def verification_config(slurm_version: str = "25.11", gpu_support: bool = False) -> Dict[str, Any]:
    """Generate configuration with verification enabled (for CI and pre-release checks)."""
    return generate_spack_config(slurm_version=slurm_version, gpu_support=gpu_support)


if __name__ == "__main__":
    # Example usage - generate configurations for testing
    print("=== CPU-only Slurm 25.11 (default toolchain: noble) ===")
    print(generate_yaml_string("25.11", gpu_support=False))

    print("\n=== GPU-enabled Slurm 25.11 (default toolchain: noble) ===")
    print(generate_yaml_string("25.11", gpu_support=True))

    print("\n=== Slurm 25.11 with rockylinux8 toolchain ===")
    print(generate_yaml_string("25.11", toolchain="rockylinux8", gpu_support=False))

    print("\n=== CPU-only Slurm 25.11 with Verification (CI) ===")
    print(generate_yaml_string("25.11", gpu_support=False))
