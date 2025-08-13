"""
Dynamic Spack environment configuration generator for slurm-factory.

This module generates Spack environment configurations as Python dictionaries,
allowing for easy parameterization of Slurm versions and GPU support options.
"""

from typing import Any, Dict

from slurm_factory.constants import SLURM_VERSIONS

# Template name for relocatable module files (relative to Spack templates directory)
TEMPLATE_NAME = "modules/relocatable_modulefile.lua"


def generate_module_config(
    slurm_version: str = "25.05",
    gpu_support: bool = False,
    minimal: bool = False,
) -> Dict[str, Any]:
    """
    Generate the Lmod module configuration section for Spack.
    
    Args:
        slurm_version: Slurm version to build (25.05, 24.11, 23.11, 23.02)
        gpu_support: Whether to include GPU support (NVML, RSMI)
        minimal: Whether to build minimal Slurm (without OpenMPI and extra features)
        
    Returns:
        Dictionary representing the modules configuration section
    """
    if slurm_version not in SLURM_VERSIONS:
        raise ValueError(
            f"Unsupported Slurm version: {slurm_version}. Supported versions: {list(SLURM_VERSIONS.keys())}"
        )
    
    slurm_package_version = SLURM_VERSIONS[slurm_version]
    
    # Build type description for metadata
    if minimal:
        build_type = "minimal build"
    elif gpu_support:
        build_type = "GPU-enabled build"
    else:
        build_type = "standard build"
    
    # Base module configuration
    modules_config = {
        "default": {
            "enable": ["lmod"],
            "lmod": {
                "core_compilers": ["gcc@13.3.0"],
                "hierarchy": [],  # Flat hierarchy for simpler deployment
                "include": ["slurm"],  # Only generate modules for Slurm
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
                            "SLURM_MODULE_HELP": "Set SLURM_INSTALL_PREFIX before loading to override installation path"
                        },
                        "prepend_path": {
                            # Use environment variable in paths with fallback to build-time prefix
                            "LD_LIBRARY_PATH": "{prefix}/lib",
                            "PATH": "{prefix}/bin:{prefix}/sbin",
                            "CPATH": "{prefix}/include",
                            "PKG_CONFIG_PATH": "{prefix}/lib/pkgconfig",
                            "MANPATH": "{prefix}/share/man",
                            "CMAKE_PREFIX_PATH": "{prefix}"
                        },
                    }
                },
            },
        },
    }
    
    # Add GPU-specific dependencies if GPU support is enabled
    if gpu_support:
        # Add GPU-specific library paths for CUDA/ROCm with dynamic prefix support
        current_ld_path = modules_config["default"]["lmod"]["slurm"]["environment"]["prepend_path"]["LD_LIBRARY_PATH"]
        modules_config["default"]["lmod"]["slurm"]["environment"]["prepend_path"]["LD_LIBRARY_PATH"] = current_ld_path + ":{prefix}/lib64"
        
        current_path = modules_config["default"]["lmod"]["slurm"]["environment"]["prepend_path"]["PATH"]
        modules_config["default"]["lmod"]["slurm"]["environment"]["prepend_path"]["PATH"] = current_path + ":{prefix}/bin"
    
    # Configure OpenMPI module behavior based on build type
    if not minimal:
        modules_config["default"]["lmod"]["openmpi"] = {
            "environment": {
                "set": {"OMPI_MCA_plm": "slurm"}
            }
        }
    
    return modules_config


def generate_spack_config(
    slurm_version: str = "25.05",
    gpu_support: bool = False,
    minimal: bool = False,
    install_tree_root: str = "/opt/slurm/software",
    view_root: str = "/opt/slurm/view",
    buildcache_root: str = "/opt/slurm-factory-cache/spack-buildcache",
    sourcecache_root: str = "/opt/slurm-factory-cache/spack-sourcecache",
    binary_index_root: str = "/opt/slurm-factory-cache/binary_index",
) -> Dict[str, Any]:
    """
    Generate a Spack environment configuration dictionary.

    Args:
        slurm_version: Slurm version to build (25.05, 24.11, 23.11, 23.02)
        gpu_support: Whether to include GPU support (NVML, RSMI)
        minimal: Whether to build minimal Slurm (without OpenMPI and extra features)
        install_tree_root: Root directory for Spack installations
        view_root: Root directory for Spack view
        buildcache_root: Directory for binary build cache
        sourcecache_root: Directory for source cache
        binary_index_root: Directory for binary index

    Returns:
        Dictionary representing the Spack environment configuration

    """
    if slurm_version not in SLURM_VERSIONS:
        raise ValueError(
            f"Unsupported Slurm version: {slurm_version}. Supported versions: {list(SLURM_VERSIONS.keys())}"
        )

    slurm_package_version = SLURM_VERSIONS[slurm_version]

    # Build Slurm spec with conditional features
    gpu_flags = "+nvml +rsmi" if gpu_support else "~nvml ~rsmi"
    
    if minimal:
        # Minimal build: basic Slurm without many optional features
        slurm_spec = (
            f"slurm@{slurm_package_version} +readline ~hwloc ~pmix ~restd "
            f"{gpu_flags} ~cgroup sysconfdir=/etc/slurm"
        )
        specs = [slurm_spec]  # Only Slurm, no OpenMPI or dbus
    else:
        # Full build: Slurm with OpenMPI and standard features
        slurm_spec = (
            f"slurm@{slurm_package_version} +readline +hwloc +pmix +restd "
            f"{gpu_flags} +cgroup sysconfdir=/etc/slurm"
        )
        specs = [
            "openmpi@5.0.3 schedulers=slurm fabrics=auto ^hwloc ^libevent ^pmix",
            slurm_spec,
        ]

    # Base view packages (runtime dependencies)
    view_packages = ["slurm", "munge", "json-c", "curl", "openssl", "readline", "ncurses", "lz4", "zlib-ng", "hwloc", "numactl", "gcc-runtime"]
    
    # Add conditional packages based on build type
    if not minimal:
        view_packages.extend(["openmpi", "pmix", "libevent"])
    
    if gpu_support:
        view_packages.extend(["cuda", "rocm"])

    # Base configuration
    config = {
        "spack": {
            "specs": specs,
            "concretizer": {
                "unify": True,  # Ensures only one package per spec in the environment
                "reuse": True,  # Reuse packages when possible to reduce redundancy
            },
            "develop": {},
            "view": {
                "default": {
                    "root": view_root,
                    "link_type": "hardlink",  # Use hardlinks instead of symlinks for easier copying
                    "select": view_packages  # Only include essential runtime dependencies in view
                }
            },
            "config": {
                "install_tree": {"root": install_tree_root},
                "build_stage": "/tmp/spack-stage",
                "misc_cache": sourcecache_root,
                "binary_index_root": binary_index_root,
                "checksum": True,
                "deprecated": True,
                # Spack 1.x performance enhancements
                "build_jobs": 4,  # Parallel build jobs
                "ccache": True,   # Disable ccache since it's not available
                "connect_timeout": 30,  # Network timeout for downloads
                "verify_ssl": True,     # Security setting
                "suppress_gpg_warnings": False  # Show GPG warnings
            },
            "mirrors": {
                "local-buildcache": {"url": f"file://{buildcache_root}", "signed": False},
                # Add multiple mirror sources for redundancy (Spack 1.x feature)
                "spack-public": {"url": "https://mirror.spack.io", "signed": True},
                "binary-mirror": {"url": f"file://{binary_index_root}", "signed": False}
            },
            "compilers": [
                {
                    "compiler": {
                        "spec": "gcc@=13.3.0",
                        "paths": {
                            "cc": "/usr/bin/gcc",
                            "cxx": "/usr/bin/g++",
                            "f77": "/usr/bin/gfortran",
                            "fc": "/usr/bin/gfortran",
                        },
                        "operating_system": "ubuntu24.04",
                        "target": "x86_64",
                        "modules": [],  # Required field
                        # Spack 1.x enhancements
                        "environment": {},  # Environment variables for compiler
                        "extra_rpaths": []  # Additional runtime library paths
                    }
                }
            ],
            "packages": {
                # Keep build tools as externals (not needed at runtime)
                # Use 'require' in Spack 1.x to enforce external usage
                "cmake": {"externals": [{"spec": "cmake@3.28.3", "prefix": "/usr"}], "buildable": False, "require": "@3.28.3"},
                "python": {"externals": [{"spec": "python@3.12.3", "prefix": "/usr"}], "buildable": False, "require": "@3.12.3"},
                "autoconf": {"externals": [{"spec": "autoconf@2.71", "prefix": "/usr"}], "buildable": False, "require": "@2.71"},
                "automake": {"externals": [{"spec": "automake@1.16.5", "prefix": "/usr"}], "buildable": False, "require": "@1.16.5"},
                "libtool": {"externals": [{"spec": "libtool@2.4.7", "prefix": "/usr"}], "buildable": False, "require": "@2.4.7"},
                "bison": {"externals": [{"spec": "bison@3.8.2", "prefix": "/usr"}], "buildable": False, "require": "@3.8.2"},
                "flex": {"externals": [{"spec": "flex@2.6.4", "prefix": "/usr"}], "buildable": False, "require": "@2.6.4"},
                "findutils": {"externals": [{"spec": "findutils@4.9.0", "prefix": "/usr"}], "buildable": False},
                "diffutils": {"externals": [{"spec": "diffutils@3.10", "prefix": "/usr"}], "buildable": False},
                "tar": {"externals": [{"spec": "tar@1.34", "prefix": "/usr"}], "buildable": False},
                "gawk": {"externals": [{"spec": "gawk@5.2.1", "prefix": "/usr"}], "buildable": False},
                "gettext": {"externals": [{"spec": "gettext@0.21", "prefix": "/usr"}], "buildable": False},
                "gmake": {"externals": [{"spec": "gmake@4.3", "prefix": "/usr"}], "buildable": False},
                "m4": {"externals": [{"spec": "m4@1.4.18", "prefix": "/usr"}], "buildable": False},
                "mawk": {"externals": [{"spec": "mawk@1.3.4", "prefix": "/usr"}], "buildable": False},
                "pkg-config": {"externals": [{"spec": "pkg-config@0.29.2", "prefix": "/usr"}], "buildable": False},
                "pkgconf": {"externals": [{"spec": "pkgconf@1.8.1", "prefix": "/usr"}], "buildable": False},
                
                # Essential runtime libraries that must be built for Slurm linking
                # These are critical dependencies that Slurm links against at runtime
                "munge": {"buildable": True},                             # Authentication - let Spack pick latest available
                "json-c": {"buildable": True},                            # JSON parsing - linked at runtime
                "curl": {"buildable": True},                              # HTTP client for REST API
                "openssl": {"buildable": True, "version": ["3:"]},        # SSL/TLS for curl and auth - use OpenSSL 3.x series
                "readline": {"buildable": True},                          # Interactive command line
                "ncurses": {"buildable": True},                           # Terminal control for readline
                "lz4": {"buildable": True},                               # Fast compression - linked at runtime
                "zlib-ng": {"buildable": True},                           # lz4 compression lib - linked at runtime
                "hwloc": {"buildable": True, "version": ["2:"]},          # Hardware topology - use hwloc 2.x series
                "numactl": {"buildable": True},                           # NUMA support - used by Slurm for memory binding
                
                # System libraries that can use externals (build-time or utilities only)
                # These are not linked at runtime by Slurm or are system-level abstractions
                "bzip2": {"externals": [{"spec": "bzip2@1.0.8", "prefix": "/usr"}], "buildable": False},
                "xz": {"externals": [{"spec": "xz@5.4.5", "prefix": "/usr"}], "buildable": False},
                "zstd": {"externals": [{"spec": "zstd@1.5.5", "prefix": "/usr"}], "buildable": False},
                "dbus": {
                    "externals": [{"spec": "dbus@1.14.10", "prefix": "/usr"}], 
                    "buildable": False,
                    "variants": "system-socket=/var/run/dbus/system_bus_socket"
                },
                "linux-pam": {"externals": [{"spec": "linux-pam@1.5.3", "prefix": "/usr"}], "buildable": False},
                "libyaml": {"externals": [{"spec": "libyaml@0.2.5", "prefix": "/usr"}], "buildable": False},
                "glib": {"externals": [{"spec": "glib@2.80.0", "prefix": "/usr"}], "buildable": False},
                "libxml2": {"externals": [{"spec": "libxml2@2.9.14", "prefix": "/usr"}], "buildable": False},
                "libevent": {"externals": [{"spec": "libevent@2.1.12", "prefix": "/usr"}], "buildable": False},
                "gdbm": {"externals": [{"spec": "gdbm@1.23", "prefix": "/usr"}], "buildable": False},
                "berkeley-db": {"externals": [{"spec": "berkeley-db@5.3.28", "prefix": "/usr"}], "buildable": False},
                "jansson": {"externals": [{"spec": "jansson@2.14", "prefix": "/usr"}], "buildable": False},
                "libgcrypt": {"externals": [{"spec": "libgcrypt@1.10.1", "prefix": "/usr"}], "buildable": False},
                "libgpg-error": {"externals": [{"spec": "libgpg-error@1.47", "prefix": "/usr"}], "buildable": False},
                "libsigsegv": {"externals": [{"spec": "libsigsegv@2.14", "prefix": "/usr"}], "buildable": False},
                "hdf5": {"externals": [{"spec": "hdf5@1.10.10", "prefix": "/usr"}], "buildable": False},
                
                "pmix": {
                    "variants": "~munge ~python",
                    "version": ["5.0.8"],
                    "buildable": True
                },
                
                # GCC runtime (needed for dynamic linking)
                "gcc-runtime": {"buildable": True, "version": ["13.3.0"]},
                
                # Slurm itself
                "slurm": {"version": [slurm_package_version], "buildable": True},
                
                # Global preferences with Spack 1.x enhancements
                "all": {
                    "target": ["x86_64"],
                    "prefer": ["%gcc@13.3.0", "+shared", "~static"],  # More specific preferences
                    "variants": "+shared ~static",  # Consistent shared library preference
                    "permissions": {
                        "read": "world",
                        "write": "user"
                    }
                },
            },
            "modules": generate_module_config(slurm_version, gpu_support, minimal),
        }
    }

    # Add MPI provider configuration only for full builds (when OpenMPI is included)
    if not minimal:
        config["spack"]["packages"]["all"]["providers"] = {"mpi": ["openmpi"]}

    return config


def get_comment_header(slurm_version: str, gpu_support: bool, minimal: bool = False) -> str:
    """Generate a descriptive comment header for the configuration."""
    if minimal:
        desc = "(minimal build - basic Slurm only)"
    elif gpu_support:
        desc = "with GPU support"
    else:
        desc = "(optimized for minimal runtime footprint)"
    return f"# Spack environment for building Slurm {slurm_version} {desc}"


def generate_yaml_string(slurm_version: str = "25.05", gpu_support: bool = False, minimal: bool = False) -> str:
    """
    Generate a YAML string representation of the Spack environment configuration.

    Args:
        slurm_version: Slurm version to build
        gpu_support: Whether to include GPU support
        minimal: Whether to build minimal Slurm

    Returns:
        YAML string representation of the configuration

    """
    import yaml

    config = generate_spack_config(slurm_version=slurm_version, gpu_support=gpu_support, minimal=minimal)
    header = get_comment_header(slurm_version, gpu_support, minimal)

    # Generate YAML with proper formatting
    yaml_content = yaml.dump(config, default_flow_style=False, sort_keys=False, indent=2)

    return f"{header}\n{yaml_content}"


# Convenience functions for common configurations
def cpu_only_config(slurm_version: str = "25.05") -> Dict[str, Any]:
    """Generate CPU-only configuration (default, optimized for size)."""
    return generate_spack_config(slurm_version=slurm_version, gpu_support=False, minimal=False)


def gpu_enabled_config(slurm_version: str = "25.05") -> Dict[str, Any]:
    """Generate GPU-enabled configuration (larger, includes CUDA/ROCm)."""
    return generate_spack_config(slurm_version=slurm_version, gpu_support=True, minimal=False)


def minimal_config(slurm_version: str = "25.05") -> Dict[str, Any]:
    """Generate minimal configuration (smallest, basic Slurm only)."""
    return generate_spack_config(slurm_version=slurm_version, gpu_support=False, minimal=True)


if __name__ == "__main__":
    # Example usage - generate configurations for testing
    print("=== CPU-only Slurm 25.05 ===")
    print(generate_yaml_string("25.05", False, False))

    print("\n=== GPU-enabled Slurm 25.05 ===")
    print(generate_yaml_string("25.05", True, False))
    
    print("\n=== Minimal Slurm 25.05 ===")
    print(generate_yaml_string("25.05", False, True))
