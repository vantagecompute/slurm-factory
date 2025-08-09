"""
Dynamic Spack environment configuration generator for slurm-factory.

This module generates Spack environment configurations as Python dictionaries,
allowing for easy parameterization of Slurm versions and GPU support options.
"""

from typing import Any, Dict

from slurm_factory.constants import SLURM_VERSIONS


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
            "dbus system-socket=/var/run/dbus/system_bus_socket",
            slurm_spec,
        ]

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
                "root": view_root,
                "link_type": "hardlink",  # Use hardlinks instead of symlinks for easier copying
            },
            "config": {
                "install_tree": {"root": install_tree_root},
                "build_stage": "/tmp/spack-stage",
                "misc_cache": sourcecache_root,
                "binary_index_root": binary_index_root,
                "checksum": True,
                "deprecated": True,
            },
            "mirrors": {"local-buildcache": {"url": f"file://{buildcache_root}", "signed": False}},
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
                    }
                }
            ],
            "packages": {
                "cmake": {"externals": [{"spec": "cmake@3.28.3", "prefix": "/usr"}], "buildable": False},
                "python": {"externals": [{"spec": "python@3.12.3", "prefix": "/usr"}], "buildable": False},
                # Slurm core dependencies - installed as Ubuntu packages in LXD profile
                "curl": {"externals": [{"spec": "curl@8.5.0", "prefix": "/usr"}], "buildable": False},
                "glib": {"externals": [{"spec": "glib@2.80.0", "prefix": "/usr"}], "buildable": False},
                "json-c": {
                    "externals": [{"spec": "json-c@0.17", "prefix": "/usr"}], 
                    "buildable": False,
                    "version": ["0.17"]  # Use recent non-deprecated version
                },
                "lz4": {"externals": [{"spec": "lz4@1.9.4", "prefix": "/usr"}], "buildable": False},
                "openssl": {"externals": [{"spec": "openssl@3.0.13", "prefix": "/usr"}], "buildable": False},
                "pkgconf": {"externals": [{"spec": "pkgconf@1.8.1", "prefix": "/usr"}], "buildable": False},
                "readline": {"externals": [{"spec": "readline@8.2", "prefix": "/usr"}], "buildable": False},
                "zlib": {"externals": [{"spec": "zlib@1.3", "prefix": "/usr", "extra_attributes": {"libs": "/usr/lib/x86_64-linux-gnu"}}], "buildable": False},
                "zlib-api": {"externals": [{"spec": "zlib@1.3", "prefix": "/usr", "extra_attributes": {"libs": "/usr/lib/x86_64-linux-gnu"}}], "buildable": False},
                # Slurm optional dependencies - installed as Ubuntu packages in LXD profile
                "hwloc": {"externals": [{"spec": "hwloc@2.10.0", "prefix": "/usr"}], "buildable": False},
                "hdf5": {"externals": [{"spec": "hdf5@1.10.10", "prefix": "/usr"}], "buildable": False},
                "dbus": {"externals": [{"spec": "dbus@1.14.10", "prefix": "/usr"}], "buildable": False},
                "linux-pam": {"externals": [{"spec": "linux-pam@1.5.3", "prefix": "/usr"}], "buildable": False},
                "libyaml": {"externals": [{"spec": "libyaml@0.2.5", "prefix": "/usr"}], "buildable": False},
                # Build tools and system utilities (high-impact build optimizations)
                "autoconf": {"externals": [{"spec": "autoconf@2.71", "prefix": "/usr"}], "buildable": False},
                "automake": {"externals": [{"spec": "automake@1.16.5", "prefix": "/usr"}], "buildable": False},
                "libtool": {"externals": [{"spec": "libtool@2.4.7", "prefix": "/usr"}], "buildable": False},
                "bison": {"externals": [{"spec": "bison@3.8.2", "prefix": "/usr"}], "buildable": False},
                "flex": {"externals": [{"spec": "flex@2.6.4", "prefix": "/usr"}], "buildable": False},
                "findutils": {"externals": [{"spec": "findutils@4.9.0", "prefix": "/usr"}], "buildable": False},
                "diffutils": {"externals": [{"spec": "diffutils@3.10", "prefix": "/usr"}], "buildable": False},
                "tar": {"externals": [{"spec": "tar@1.34", "prefix": "/usr"}], "buildable": False},
                "gawk": {"externals": [{"spec": "gawk@5.2.1", "prefix": "/usr"}], "buildable": False},
                "gettext": {"externals": [{"spec": "gettext@0.21", "prefix": "/usr"}], "buildable": False},
                "ncurses": {"externals": [{"spec": "ncurses@6.4", "prefix": "/usr", "extra_attributes": {"libs": "/usr/lib/x86_64-linux-gnu"}}], "buildable": False},
                "bzip2": {"externals": [{"spec": "bzip2@1.0.8", "prefix": "/usr", "extra_attributes": {"libs": "/usr/lib/x86_64-linux-gnu"}}], "buildable": False},
                "xz": {"externals": [{"spec": "xz@5.4.5", "prefix": "/usr", "extra_attributes": {"libs": "/usr/lib/x86_64-linux-gnu"}}], "buildable": False},
                "zstd": {"externals": [{"spec": "zstd@1.5.5", "prefix": "/usr", "extra_attributes": {"libs": "/usr/lib/x86_64-linux-gnu"}}], "buildable": False},
                "libxml2": {"externals": [{"spec": "libxml2@2.9.14", "prefix": "/usr", "extra_attributes": {"libs": "/usr/lib/x86_64-linux-gnu"}}], "buildable": False},
                # Additional build tools and system packages (more build optimizations)
                "gmake": {"externals": [{"spec": "gmake@4.3", "prefix": "/usr"}], "buildable": False},
                "m4": {"externals": [{"spec": "m4@1.4.18", "prefix": "/usr"}], "buildable": False},
                "mawk": {"externals": [{"spec": "mawk@1.3.4", "prefix": "/usr"}], "buildable": False},
                "pkg-config": {"externals": [{"spec": "pkg-config@0.29.2", "prefix": "/usr"}], "buildable": False},
                "gdbm": {"externals": [{"spec": "gdbm@1.23", "prefix": "/usr", "extra_attributes": {"libs": "/usr/lib/x86_64-linux-gnu"}}], "buildable": False},
                "berkeley-db": {"externals": [{"spec": "berkeley-db@5.3.28", "prefix": "/usr", "extra_attributes": {"libs": "/usr/lib/x86_64-linux-gnu"}}], "buildable": False},
                "jansson": {"externals": [{"spec": "jansson@2.14", "prefix": "/usr", "extra_attributes": {"libs": "/usr/lib/x86_64-linux-gnu"}}], "buildable": False},
                "libgcrypt": {"externals": [{"spec": "libgcrypt@1.10.1", "prefix": "/usr", "extra_attributes": {"libs": "/usr/lib/x86_64-linux-gnu"}}], "buildable": False},
                "libgpg-error": {"externals": [{"spec": "libgpg-error@1.47", "prefix": "/usr", "extra_attributes": {"libs": "/usr/lib/x86_64-linux-gnu"}}], "buildable": False},
                "libsigsegv": {"externals": [{"spec": "libsigsegv@2.14", "prefix": "/usr", "extra_attributes": {"libs": "/usr/lib/x86_64-linux-gnu"}}], "buildable": False},
                "libevent": {"externals": [{"spec": "libevent@2.1.12", "prefix": "/usr", "extra_attributes": {"libs": "/usr/lib/x86_64-linux-gnu"}}], "buildable": False},
                "numactl": {"externals": [{"spec": "numactl@2.0.16", "prefix": "/usr", "extra_attributes": {"libs": "/usr/lib/x86_64-linux-gnu"}}], "buildable": False},
                # PMix - configure for when needed (full builds only)
                "pmix": {
                    "variants": "~munge ~python",
                    "version": ["5.0.8"],
                    "externals": [],
                    "buildable": True
                },
                "gcc": {
                    "externals": [
                        {
                            "spec": "gcc@13.3.0 languages:='c,c++,fortran'",
                            "prefix": "/usr",
                            "extra_attributes": {
                                "compilers": {
                                    "c": "/usr/bin/gcc",
                                    "cxx": "/usr/bin/g++",
                                    "fortran": "/usr/bin/gfortran",
                                },
                                "flags": {},
                                "environment": {},
                                "extra_rpaths": [],
                            },
                            "modules": [],  # Required field
                        }
                    ]
                },
                "slurm": {"version": [slurm_package_version]},
                "all": {
                    "target": ["x86_64"],
                    "prefer": ["%gcc", "+shared"],  # Prefer binary packages when available
                },
            },
            "modules": {
                "default": {
                    "enable": ["lmod"],
                    "lmod": {
                        "core_compilers": ["gcc@13.3.0"],
                        "all": {"autoload": "direct", "conflict": ["{{name}}"]},
                        "slurm": {
                            "environment": {
                                "set": {"SLURM_CONF": "/etc/slurm/slurm.conf", "SLURM_ROOT": "{{prefix}}"}
                            }
                        },
                    },
                }
            },
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
    
    # Replace double braces with single braces for Spack template variables
    yaml_content = yaml_content.replace("{{name}}", "{name}").replace("{{prefix}}", "{prefix}")

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
