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
    install_tree_root: str = "/srv/slurm/software",
    view_root: str = "/srv/slurm/view",
    buildcache_root: str = "/opt/slurm-factory-cache/spack-buildcache",
    sourcecache_root: str = "/opt/slurm-factory-cache/spack-sourcecache",
    binary_index_root: str = "/opt/slurm-factory-cache/binary_index",
) -> Dict[str, Any]:
    """
    Generate a Spack environment configuration dictionary.

    Args:
        slurm_version: Slurm version to build (25.05, 24.11, 23.11, 23.02)
        gpu_support: Whether to include GPU support (NVML, RSMI)
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

    # Build Slurm spec with conditional GPU support
    gpu_flags = "+nvml +rsmi" if gpu_support else "~nvml ~rsmi"
    slurm_spec = f"slurm@{slurm_package_version} +readline +hwloc +pmix +restd {gpu_flags} +cgroup sysconfdir=/etc/slurm"

    # Base configuration
    config = {
        "spack": {
            "specs": [
                "openmpi@5.0.3 schedulers=slurm fabrics=auto ^hwloc ^libevent ^pmix",
                "dbus system-socket=/var/run/dbus/system_bus_socket",
                slurm_spec,
            ],
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
                "json-c": {
                    "version": ["0.18"]  # Use recent non-deprecated version
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
                    "providers": {"mpi": ["openmpi"]},
                    "target": ["x86_64"],
                    "prefer": ["%gcc", "+shared"],  # Prefer binary packages when available
                },
            },
            "modules": {
                "default": {
                    "enable": ["lmod"],
                    "lmod": {
                        "core_compilers": ["gcc@13.3.0"],
                        "all": {"autoload": "direct", "conflict": ["{name}"]},
                        "slurm": {
                            "environment": {
                                "set": {"SLURM_CONF": "/etc/slurm/slurm.conf", "SLURM_ROOT": "{prefix}"}
                            }
                        },
                    },
                }
            },
        }
    }

    return config


def get_comment_header(slurm_version: str, gpu_support: bool) -> str:
    """Generate a descriptive comment header for the configuration."""
    gpu_desc = "with GPU support" if gpu_support else "(optimized for minimal runtime footprint)"
    return f"# Spack environment for building Slurm {slurm_version} {gpu_desc}"


def generate_yaml_string(slurm_version: str = "25.05", gpu_support: bool = False) -> str:
    """
    Generate a YAML string representation of the Spack environment configuration.

    Args:
        slurm_version: Slurm version to build
        gpu_support: Whether to include GPU support

    Returns:
        YAML string representation of the configuration

    """
    import yaml

    config = generate_spack_config(slurm_version=slurm_version, gpu_support=gpu_support)
    header = get_comment_header(slurm_version, gpu_support)

    # Generate YAML with proper formatting
    yaml_content = yaml.dump(config, default_flow_style=False, sort_keys=False, indent=2)

    return f"{header}\n{yaml_content}"


# Convenience functions for common configurations
def cpu_only_config(slurm_version: str = "25.05") -> Dict[str, Any]:
    """Generate CPU-only configuration (default, optimized for size)."""
    return generate_spack_config(slurm_version=slurm_version, gpu_support=False)


def gpu_enabled_config(slurm_version: str = "25.05") -> Dict[str, Any]:
    """Generate GPU-enabled configuration (larger, includes CUDA/ROCm)."""
    return generate_spack_config(slurm_version=slurm_version, gpu_support=True)


if __name__ == "__main__":
    # Example usage - generate configurations for testing
    print("=== CPU-only Slurm 25.05 ===")
    print(generate_yaml_string("25.05", False))

    print("\n=== GPU-enabled Slurm 25.05 ===")
    print(generate_yaml_string("25.05", True))

