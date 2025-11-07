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

from typing import Any, Dict, List

from slurm_factory.constants import COMPILER_TOOLCHAINS, SLURM_VERSIONS

# Template name for relocatable module files (relative to Spack templates directory)
TEMPLATE_NAME = "modules/relocatable_modulefile.lua"


def get_gcc_buildcache_requirements(compiler_version: str) -> List[str]:
    """
    Get the GCC requirements that match what's built in compiler bootstrap.

    This ensures consistency between compiler bootstrap and Slurm build configurations,
    preventing variant mismatches that would cause Spack to build GCC from source
    instead of using the buildcache.

    Args:
        compiler_version: GCC version (e.g., "13.4.0")

    Returns:
        List of Spack requirement strings for GCC package

    """
    return [
        f"@{compiler_version}",
        "+binutils",
        "+piclibs",
        "~nvptx",
        "languages=c,c++,fortran",
    ]


def generate_compiler_bootstrap_config(
    gcc_version: str = "13.4.0",
    buildcache_root: str = "/opt/slurm-factory-cache/spack-buildcache",
    sourcecache_root: str = "/opt/slurm-factory-cache/spack-sourcecache",
) -> Dict[str, Any]:
    """
    Generate Spack configuration to bootstrap a custom GCC compiler.

    This builds GCC with its own glibc to ensure compatibility across different distros.
    The built compiler is then used to compile Slurm and dependencies.

    Args:
        gcc_version: GCC version to build
        (e.g., "15.2.0", "14.3.0", "13.4.0", "12.5.0", "11.5.0", "10.5.0", "9.5.0", "8.5.0", "7.5.0")
        buildcache_root: Directory for binary build cache
        sourcecache_root: Directory for source cache

    Returns:
        Dictionary representing the Spack environment configuration for compiler bootstrap

    """
    if gcc_version not in COMPILER_TOOLCHAINS:
        raise ValueError(
            f"Unsupported compiler version: {gcc_version}. "
            f"Supported versions: {list(COMPILER_TOOLCHAINS.keys())}"
        )

    gcc_ver, glibc_ver, description = COMPILER_TOOLCHAINS[gcc_version]

    # Build gcc with specific glibc version for cross-distro compatibility
    config: Dict[str, Any] = {
        "spack": {
            "specs": [
                # Use binutils@2.44 instead of 2.45 to avoid build failures
                # 2.44 is stable enough for GCC 14.2 while avoiding 2.45 issues
                f"gcc@{gcc_ver} +binutils +piclibs languages='c,c++,fortran' ^binutils@2.44",
                # Build autotools in compiler env so they're available in /opt/spack-compiler
                # but not during Slurm build (which needs different versions for libjwt compatibility)
                "autoconf@2.72",
                "automake@1.16.5",
                "libtool@2.4.7",
                # NOTE: gcc-runtime and compiler-wrapper will be built as dependencies
                # during the Slurm build phase, not during compiler bootstrap
            ],
            "concretizer": {
                "unify": "when_possible",
                "reuse": {
                    "roots": True,
                    "from": [{"type": "buildcache"}],
                },
            },
            "packages": {
                "all": {
                    "target": ["x86_64_v3"],
                    "buildable": True,
                },
                # CRITICAL: Prevent gcc from being used as external (Spack auto-detects and adds it)
                "gcc": {
                    "externals": [],
                    "buildable": True,
                },
                # Build autotools from source in compiler env
                "autoconf": {"buildable": True},
                "automake": {"buildable": True},
                "libtool": {"buildable": True},
                # Build tools as externals for speed
                "cmake": {"externals": [{"spec": "cmake@3.28.3", "prefix": "/usr"}], "buildable": False},
                "m4": {"externals": [{"spec": "m4@1.4.18", "prefix": "/usr"}], "buildable": False},
                "gmake": {"externals": [{"spec": "gmake@4.3", "prefix": "/usr"}], "buildable": False},
                # Pin binutils to 2.44 to avoid build failures with 2.45 while supporting newer GCC
                "binutils": {"version": ["2.44"], "buildable": True},
            },
            "view": {
                "/opt/spack-compiler": {
                    "root": "/opt/spack-compiler",
                    "select": [f"gcc@{gcc_ver}"],
                    "link": "all",
                    "link_type": "symlink",
                }
            },
            "config": {
                "install_tree": {
                    "root": "/opt/spack-compiler-install",
                    "padded_length": 128,
                },
                "build_stage": ["/tmp/spack-stage"],
                "source_cache": sourcecache_root,
                "misc_cache": buildcache_root,
                "build_jobs": 4,
                "ccache": False,  # Disabled - system ccache incompatible with Spack-built compilers
                "binary_index_ttl": 600,
            },
            "mirrors": {
                "spack-public": {"url": "https://mirror.spack.io", "signed": False},
                "slurm-factory-buildcache": {
                    "url": f"https://slurm-factory-spack-binary-cache.vantagecompute.ai/compilers/{gcc_ver}/buildcache",
                    "signed": True,
                },
            },
        }
    }

    return config


def generate_compiler_bootstrap_yaml(
    compiler_version: str = "13.4.0",
    buildcache_root: str = "/opt/slurm-factory-cache/spack-buildcache",
    sourcecache_root: str = "/opt/slurm-factory-cache/spack-sourcecache",
) -> str:
    """
    Generate a YAML string for bootstrapping a custom GCC compiler.

    Args:
        compiler_version: GCC version to build
        buildcache_root: Directory for binary build cache
        sourcecache_root: Directory for source cache

    Returns:
        YAML string representation of the compiler bootstrap configuration

    """
    import yaml

    config = generate_compiler_bootstrap_config(
        gcc_version=compiler_version,
        buildcache_root=buildcache_root,
        sourcecache_root=sourcecache_root,
    )

    # Generate YAML with proper formatting
    yaml_content = yaml.dump(config, default_flow_style=False, sort_keys=False, indent=2)

    gcc_ver, glibc_ver, description = COMPILER_TOOLCHAINS[compiler_version]
    header = f"# Compiler Bootstrap Configuration for GCC {gcc_ver} (glibc {glibc_ver})\n# {description}\n"

    return f"{header}{yaml_content}"


def generate_module_config(
    slurm_version: str = "25.11",
    gpu_support: bool = False,
    compiler_version: str = "13.4.0",
    enable_hierarchy: bool = False,
) -> Dict[str, Any]:
    """
    Generate the Lmod module configuration section for Spack.

    Args:
        slurm_version: Slurm version to build (25.11, 24.11, 23.11)
        gpu_support: Whether to include GPU support (NVML, RSMI)
        compiler_version: GCC compiler version to use
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
                "core_compilers": [f"gcc@{compiler_version}"],  # Mark gcc as core for relocatable binaries
                "hierarchy": hierarchy,
                "include": (
                    ["slurm", "openmpi", "mysql-connector-c"]
                ),
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

    # Remove unnecessary GPU PATH duplication - RPATH covers libs and PATH already includes {prefix}/bin
    if gpu_support:
        pass  # nothing to add here; RPATH covers libs and PATH already includes {prefix}/bin

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
    enable_verification: bool = False,
    compiler_version: str = "13.4.0",
    enable_hierarchy: bool = False,
) -> Dict[str, Any]:
    """
    Generate a Spack environment configuration dictionary.

    Args:
        slurm_version: Slurm version to build (25.11, 24.11, 23.11)
        gpu_support: Whether to include GPU support (NVML, RSMI)
        install_tree_root: Root directory for Spack installations
        view_root: Root directory for Spack view
        enable_verification: Whether to enable relocatability verification checks
        compiler_version: GCC compiler version to use (always built by Spack)
        enable_hierarchy: Whether to use Core/Compiler/MPI hierarchy (default: False)

    Returns:
        Dictionary representing the Spack environment configuration

    """
    if slurm_version not in SLURM_VERSIONS:
        raise ValueError(
            f"Unsupported Slurm version: {slurm_version}. Supported versions: {list(SLURM_VERSIONS.keys())}"
        )

    slurm_package_version = SLURM_VERSIONS[slurm_version]

    # Always use Spack-built compiler
    compiler_spec = f"%gcc@{compiler_version}"

    # Build Slurm spec with conditional features
    gpu_flags = "+nvml +rsmi" if gpu_support else "~nvml ~rsmi"

    # Spec definitions for packages
    openldap_spec = f"openldap@2.6.8+client_only~perl+sasl+dynamic+shared~static tls=openssl {compiler_spec}"
    curl_spec = (
        f"slurm_factory.curl@8.15.0+nghttp2+libssh2+libssh+gssapi+ldap+librtmp+libidn2 "
        f"libs=shared,static tls=openssl {compiler_spec}"
    )
    specs = [
        # Install GCC first from buildcache (built separately with build-compiler command)
        # gcc-runtime will be built as a dependency of gcc
        f"gcc@{compiler_version} +binutils +piclibs languages=c,c++,fortran {compiler_spec}",
        # All packages below will use %gcc@{compiler_version}
        f"zlib@1.3.1 {compiler_spec}",  # Build zlib first (needed by OpenSSL and others)
        # Build OpenSSL with explicit zlib dependency
        f"slurm_factory.openssl@3.6.0 ^zlib@1.3.1 {compiler_spec}",
        f"jansson@2.14 {compiler_spec}",  # JSON library for libjwt
        # JWT library with all dependencies - let Spack choose available version
        f"libjwt ^openssl@3.6.0 ^zlib@1.3.1 ^jansson@2.14 {compiler_spec}",
        openldap_spec,  # Build openldap before curl since curl+ldap needs it
        curl_spec,
        f"patchelf@0.18.0 {compiler_spec}",  # For RPATH fixing during relocatability
    ]
    # Using slurm_factory.freeipmi@1.6.16 for GCC 14 compatibility
    # (1.6.9 has implicit function declaration errors)
    specs.append(f"slurm_factory.freeipmi@1.6.16 {compiler_spec}")
    specs.append(f"openmpi@5.0.3 schedulers=slurm fabrics=auto {compiler_spec}")
    specs.append(f"pmix@5.0.5 ~munge ~python {compiler_spec}")
    specs.append(f"mysql-connector-c {compiler_spec}")
    specs.append(f"hdf5@1.14.6 +hl +cxx {compiler_spec}")
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
                "unify": True,  # Allow compiler to differ from dependencies
                "reuse": {
                    "roots": True,
                    "from": [{"type": "buildcache"}],
                },
            },
            "config": {
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
                # "build_stage": "/tmp/spack-stage",
                # "misc_cache": sourcecache_root,
                # "binary_index_root": binary_index_root,
                "checksum": True,
                "deprecated": True,
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
            # Force all packages to be buildable from source
            "packages": {
                "all": {
                    "target": ["x86_64_v3"],
                    "require": "target=x86_64_v3",
                    "buildable": True,
                },
                "cmake": {
                    "externals": [{"spec": "cmake@3.28.3", "prefix": "/usr"}],
                    "buildable": False,
                    "require": "@3.28.3",
                },
                "python": {
                    "externals": [{"spec": "python@3.12.3", "prefix": "/usr"}],
                    "buildable": False,
                    "require": "@3.12.3",
                },
                "autoconf": {
                    "buildable": True,  # Build from source for libjwt compatibility
                },
                "automake": {
                    "buildable": True,  # Build from source for libjwt compatibility
                },
                "libtool": {
                    "buildable": True,  # Build from source for libjwt compatibility
                },
                "gmake": {"externals": [{"spec": "gmake@4.3", "prefix": "/usr"}], "buildable": False},
                "m4": {"externals": [{"spec": "m4@1.4.18", "prefix": "/usr"}], "buildable": False},
                "pkgconf": {"externals": [{"spec": "pkgconf@1.8.1", "prefix": "/usr"}], "buildable": False},
                "diffutils": {
                    "externals": [{"spec": "diffutils@3.10", "prefix": "/usr"}],
                    "buildable": False,
                },
                "findutils": {
                    "externals": [{"spec": "findutils@4.9.0", "prefix": "/usr"}],
                    "buildable": False,
                },
                # Build gettext from source to avoid libstdc++ compatibility issues with older compilers
                # System gettext's msgfmt may require newer GLIBCXX versions than available in GCC 10.x
                "gettext": {"buildable": True},
                # Use system build tools to avoid compiler wrapper issues during configure
                "libmd": {"externals": [{"spec": "libmd@1.1.0", "prefix": "/usr"}], "buildable": False},
                "libbsd": {"externals": [{"spec": "libbsd@0.12.1", "prefix": "/usr"}], "buildable": False},
                "libsigsegv": {
                    "externals": [{"spec": "libsigsegv@2.14", "prefix": "/usr"}],
                    "buildable": False,
                },
                "tar": {"externals": [{"spec": "tar@1.34", "prefix": "/usr"}], "buildable": False},
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
                },
                "rapidjson": {"buildable": True},
                "openldap": {
                    "buildable": True,
                    "version": ["2.6.8"],
                },
                "curl": {
                    "buildable": True,
                    "version": ["8.15.0"],
                    "variants": "libs=shared,static tls=openssl",
                },
                "openssl": {
                    "buildable": True,
                    "version": ["3:"],
                    "variants": "~docs +shared ~static",  # Remove system cert dependencies
                    "require": ["^ca-certificates-mozilla"],  # Force use of Spack certs
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
                    "require": [
                        "^openssl@3:",
                        "^jansson",
                        "^automake@:1.16.3",  # libjwt@1.15.3 incompatible with automake 1.16.5
                    ],  # Ensure it uses Spack-built OpenSSL 3.x and jansson
                },  # JWT token support - essential for Slurm REST API
                # MySQL client library for Slurm accounting storage
                "mysql-connector-c": {"buildable": True},
                "librdkafka": {
                    "buildable": True,
                },
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
                    "version": [compiler_version],
                    "variants": "+binutils +piclibs languages=c,c++,fortran",
                },
                # gcc-runtime will be built automatically as a dependency of gcc
                # It provides runtime libraries for packages compiled with this GCC version
                "gcc-runtime": {
                    "buildable": True,
                    "version": [compiler_version],
                },
                "slurm": {
                    "version": [slurm_package_version],
                    "buildable": True,
                    "variants": "+shared ~static +pic",  # Consistent shared library preference
                    "prefer": ["slurm_factory.slurm"],  # Prefer our custom namespace
                },
                # OpenMPI configuration for consistent build
                "openmpi": {
                    "buildable": True,
                    "version": ["5.0.3"],
                    "variants": "schedulers=slurm fabrics=auto",
                },
            },
            "develop": {},
            "view": {
                "default": {
                    "root": view_root,
                    "link_type": "hardlink",  # Use hardlinks instead of symlinks for easier copying
                    "projections": {"all": "."},  # Merge all packages into unified FHS structure
                    # No 'select' - include all installed packages automatically
                    # Only exclude external packages that are system-provided
                    "exclude": [
                        "cmake",
                        "autoconf",
                        "automake",
                        "libtool",
                        "python",
                        "gmake",
                        "m4",
                        "pkgconf",
                        "diffutils",
                        "findutils",
                        "gettext",
                        "libmd",
                        "libbsd",
                        "libsigsegv",
                        "tar",
                        "bison",
                        "glibc",
                        "gcc",
                    ]
                    + (["cuda", "rocm-core", "rocm-smi-lib"] if gpu_support else []),
                }
            },
            "mirrors": {
                # Only use spack-public mirror for source downloads, not binaries
                # In single-stage builds, we build everything from source
                "spack-public": {"url": "https://mirror.spack.io", "signed": False},
                # Use slurm-factory buildcache for compiler binaries
                "slurm-factory-buildcache": {
                    "url": f"https://slurm-factory-spack-binary-cache.vantagecompute.ai/compilers/{compiler_version}/buildcache",
                    "signed": True,
                },
            },
            # Start with empty compilers - GCC will be downloaded from buildcache and explicitly detected
            # via spack compiler find (system compiler detection is disabled)
            "compilers": [],
            "modules": generate_module_config(
                slurm_version, gpu_support, compiler_version, enable_hierarchy
            ),
        }
    }

    # Add MPI provider configuration only for full builds (when OpenMPI is included)
    config["spack"]["packages"]["all"]["providers"] = {"mpi": ["openmpi"]}

    # Add verification settings if enabled (useful for CI and pre-release checks)
    if enable_verification:
        config["spack"]["config"]["verify"] = {
            "relocatable": True,  # Verify binaries are relocatable
            "dependencies": True,  # Verify all dependencies are present
            "shared_libraries": True,  # Check shared library dependencies
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
    compiler_version: str = "13.4.0",
    gpu_support: bool = False,
    enable_verification: bool = False,
    enable_hierarchy: bool = False,
) -> str:
    """
    Generate a YAML string representation of the Spack environment configuration.

    Args:
        slurm_version: Slurm version to build
        compiler_version: GCC compiler version to use (always built by Spack)
        gpu_support: Whether to include GPU support
        enable_verification: Whether to enable relocatability verification checks
        enable_hierarchy: Whether to use Core/Compiler/MPI hierarchy

    Returns:
        YAML string representation of the configuration

    """
    import yaml

    config = generate_spack_config(
        slurm_version=slurm_version,
        compiler_version=compiler_version,
        gpu_support=gpu_support,
        enable_verification=enable_verification,
        enable_hierarchy=enable_hierarchy,
    )
    header = get_comment_header(slurm_version, gpu_support)

    # Generate YAML with proper formatting
    yaml_content = yaml.dump(config, default_flow_style=False, sort_keys=False, indent=2)

    return f"{header}\n{yaml_content}"


# Convenience functions for common configurations
def cpu_only_config(slurm_version: str = "25.11", enable_verification: bool = False) -> Dict[str, Any]:
    """Generate CPU-only configuration (default, optimized for size)."""
    return generate_spack_config(
        slurm_version=slurm_version, gpu_support=False, enable_verification=enable_verification
    )


def gpu_enabled_config(slurm_version: str = "25.11", enable_verification: bool = False) -> Dict[str, Any]:
    """Generate GPU-enabled configuration (larger, includes CUDA/ROCm)."""
    return generate_spack_config(
        slurm_version=slurm_version, gpu_support=True, enable_verification=enable_verification
    )


def verification_config(slurm_version: str = "25.11", gpu_support: bool = False) -> Dict[str, Any]:
    """Generate configuration with verification enabled (for CI and pre-release checks)."""
    return generate_spack_config(
        slurm_version=slurm_version, gpu_support=gpu_support, enable_verification=True
    )


if __name__ == "__main__":
    # Example usage - generate configurations for testing
    print("=== CPU-only Slurm 25.11 (default gcc 13.4.0) ===")
    print(generate_yaml_string("25.11", gpu_support=False))

    print("\n=== GPU-enabled Slurm 25.11 (default gcc 13.4.0) ===")
    print(generate_yaml_string("25.11", gpu_support=True))

    print("\n=== Slurm 25.11 with gcc 10.5.0 for RHEL 8 compatibility ===")
    print(generate_yaml_string("25.11", compiler_version="10.5.0", gpu_support=False))

    print("\n=== CPU-only Slurm 25.11 with Verification (CI) ===")
    print(generate_yaml_string("25.11", gpu_support=False, enable_verification=True))
