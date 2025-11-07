"""Test that flex library is included in the final build for relocatability."""

import pytest
from slurm_factory.spack_yaml import generate_spack_config


class TestFlexInclusion:
    """Test flex library inclusion for relocatable builds."""

    def test_flex_not_in_exclude_list(self):
        """Verify flex is not excluded from the view to ensure libfl is available at runtime."""
        config = generate_spack_config(
            slurm_version="25.11",
            compiler_version="13.4.0",
            gpu_support=False,
        )
        
        view_config = config["spack"]["view"]
        view_root_key = list(view_config.keys())[0]  # Get the view root path
        exclude_list = view_config[view_root_key]["exclude"]
        
        # flex should NOT be in the exclude list
        # This ensures libfl.so is packaged for runtime use
        assert "flex" not in exclude_list, (
            "flex should not be excluded from the view. "
            "Some packages may have runtime dependencies on libfl.so, "
            "and excluding it would break relocatability by requiring "
            "the target system to have libfl2 installed."
        )

    def test_flex_is_buildable(self):
        """Verify that flex will be built by Spack, not used from system."""
        config = generate_spack_config(
            slurm_version="25.11",
            compiler_version="13.4.0",
            gpu_support=False,
        )
        
        packages = config["spack"]["packages"]
        
        # Check if flex has specific configuration
        if "flex" in packages:
            # If configured, it should be buildable
            assert packages["flex"].get("buildable", True) is True
        else:
            # If not configured, defaults to buildable (from "all" config)
            assert packages["all"]["buildable"] is True

    def test_bison_still_excluded(self):
        """Verify bison (build-only tool) remains excluded."""
        config = generate_spack_config(
            slurm_version="25.11",
            compiler_version="13.4.0",
            gpu_support=False,
        )
        
        view_config = config["spack"]["view"]
        view_root_key = list(view_config.keys())[0]
        exclude_list = view_config[view_root_key]["exclude"]
        
        # bison should remain in the exclude list (build-only tool)
        assert "bison" in exclude_list, (
            "bison should remain excluded as it's only needed at build time"
        )

    def test_exclude_list_consistency(self):
        """Verify the exclude list contains expected build-only tools."""
        config = generate_spack_config(
            slurm_version="25.11",
            compiler_version="13.4.0",
            gpu_support=False,
        )
        
        view_config = config["spack"]["view"]
        view_root_key = list(view_config.keys())[0]
        exclude_list = view_config[view_root_key]["exclude"]
        
        # These are all build-only tools that should be excluded
        expected_excludes = [
            "cmake",      # Build system
            "autoconf",   # Build system
            "automake",   # Build system  
            "libtool",    # Build system
            "gmake",      # Build tool
            "m4",         # Macro processor (build-only)
            "bison",      # Parser generator (build-only)
            "gcc",        # Compiler (separate package)
            "glibc",      # System library
        ]
        
        for tool in expected_excludes:
            assert tool in exclude_list, f"{tool} should be excluded from the view"
        
        # flex should NOT be in the list
        assert "flex" not in exclude_list, "flex should be included for libfl.so"
