"""Unit tests for slurm_factory.spack_yaml module."""

import pytest
import yaml
from typing import Dict, Any

from slurm_factory.spack_yaml import (
    generate_spack_config,
    get_comment_header,
    generate_yaml_string,
    cpu_only_config,
    gpu_enabled_config,
    minimal_config,
)
from slurm_factory.constants import SLURM_VERSIONS


class TestGenerateSpackConfig:
    """Test generate_spack_config function."""
    
    def test_generate_spack_config_defaults(self):
        """Test generate_spack_config with default parameters."""
        config = generate_spack_config()
        
        # Check top-level structure
        assert "spack" in config
        spack_config = config["spack"]
        
        # Check required sections
        assert "specs" in spack_config
        assert "concretizer" in spack_config
        assert "view" in spack_config
        assert "config" in spack_config
        assert "mirrors" in spack_config
        assert "compilers" in spack_config
        assert "packages" in spack_config
        assert "modules" in spack_config
    
    def test_generate_spack_config_minimal_build(self):
        """Test generate_spack_config for minimal build."""
        config = generate_spack_config(minimal=True)
        specs = config["spack"]["specs"]
        
        # Minimal build should only have Slurm spec
        assert len(specs) == 1
        assert "slurm@25-05-1-1" in specs[0]
        assert "~hwloc" in specs[0]  # Minimal should disable hwloc
        assert "~pmix" in specs[0]   # Minimal should disable pmix
        assert "~restd" in specs[0]  # Minimal should disable restd
        assert "~cgroup" in specs[0] # Minimal should disable cgroup
    
    def test_generate_spack_config_full_build(self):
        """Test generate_spack_config for full build."""
        config = generate_spack_config(minimal=False)
        specs = config["spack"]["specs"]
        
        # Full build should have multiple specs
        assert len(specs) == 3
        
        # Check for OpenMPI spec
        openmpi_spec = next((s for s in specs if "openmpi" in s), None)
        assert openmpi_spec is not None
        assert "schedulers=slurm" in openmpi_spec
        
        # Check for dbus spec
        dbus_spec = next((s for s in specs if "dbus" in s), None)
        assert dbus_spec is not None
        
        # Check Slurm spec has full features
        slurm_spec = next((s for s in specs if "slurm@" in s), None)
        assert slurm_spec is not None
        assert "+hwloc" in slurm_spec  # Full should enable hwloc
        assert "+pmix" in slurm_spec   # Full should enable pmix
        assert "+restd" in slurm_spec  # Full should enable restd
        assert "+cgroup" in slurm_spec # Full should enable cgroup
    
    def test_generate_spack_config_gpu_support(self):
        """Test generate_spack_config with GPU support."""
        config = generate_spack_config(gpu_support=True)
        specs = config["spack"]["specs"]
        
        # Find Slurm spec
        slurm_spec = next((s for s in specs if "slurm@" in s), None)
        assert slurm_spec is not None
        assert "+nvml" in slurm_spec
        assert "+rsmi" in slurm_spec
    
    def test_generate_spack_config_no_gpu_support(self):
        """Test generate_spack_config without GPU support."""
        config = generate_spack_config(gpu_support=False)
        specs = config["spack"]["specs"]
        
        # Find Slurm spec
        slurm_spec = next((s for s in specs if "slurm@" in s), None)
        assert slurm_spec is not None
        assert "~nvml" in slurm_spec
        assert "~rsmi" in slurm_spec
    
    def test_generate_spack_config_custom_paths(self):
        """Test generate_spack_config with custom paths."""
        config = generate_spack_config(
            install_tree_root="/custom/software",
            view_root="/custom/view",
            buildcache_root="/custom/buildcache",
            sourcecache_root="/custom/sourcecache",
            binary_index_root="/custom/binary_index",
        )
        spack_config = config["spack"]
        
        # Check install tree
        assert spack_config["config"]["install_tree"]["root"] == "/custom/software"
        
        # Check view
        assert spack_config["view"]["root"] == "/custom/view"
        
        # Check buildcache mirror
        assert "file:///custom/buildcache" in spack_config["mirrors"]["local-buildcache"]["url"]
        
        # Check source cache
        assert spack_config["config"]["misc_cache"] == "/custom/sourcecache"
        
        # Check binary index
        assert spack_config["config"]["binary_index_root"] == "/custom/binary_index"
    
    def test_generate_spack_config_different_versions(self):
        """Test generate_spack_config with different Slurm versions."""
        for version_key, version_value in SLURM_VERSIONS.items():
            config = generate_spack_config(slurm_version=version_key)
            specs = config["spack"]["specs"]
            
            # Find Slurm spec
            slurm_spec = next((s for s in specs if "slurm@" in s), None)
            assert slurm_spec is not None
            assert f"slurm@{version_value}" in slurm_spec
            
            # Check packages section
            assert config["spack"]["packages"]["slurm"]["version"] == [version_value]
    
    def test_generate_spack_config_invalid_version(self):
        """Test generate_spack_config with invalid Slurm version."""
        with pytest.raises(ValueError, match="Unsupported Slurm version"):
            generate_spack_config(slurm_version="99.99")
    
    def test_generate_spack_config_compiler_configuration(self):
        """Test compiler configuration in generated config."""
        config = generate_spack_config()
        compilers = config["spack"]["compilers"]
        
        assert len(compilers) == 1
        compiler = compilers[0]["compiler"]
        
        assert compiler["spec"] == "gcc@=13.3.0"
        assert compiler["paths"]["cc"] == "/usr/bin/gcc"
        assert compiler["paths"]["cxx"] == "/usr/bin/g++"
        assert compiler["paths"]["f77"] == "/usr/bin/gfortran"
        assert compiler["paths"]["fc"] == "/usr/bin/gfortran"
        assert compiler["operating_system"] == "ubuntu24.04"
        assert compiler["target"] == "x86_64"
    
    def test_generate_spack_config_external_packages(self):
        """Test external package configuration."""
        config = generate_spack_config()
        packages = config["spack"]["packages"]
        
        # Test cmake external
        assert "cmake" in packages
        cmake_config = packages["cmake"]
        assert cmake_config["buildable"] is False
        assert len(cmake_config["externals"]) == 1
        assert cmake_config["externals"][0]["spec"] == "cmake@3.28.3"
        assert cmake_config["externals"][0]["prefix"] == "/usr"
        
        # Test python external
        assert "python" in packages
        python_config = packages["python"]
        assert python_config["buildable"] is False
        assert python_config["externals"][0]["spec"] == "python@3.12.3"
        
        # Test Slurm core dependency externals
        core_externals = ["curl", "glib", "json-c", "lz4", "openssl", "pkgconf", "readline", "zlib-api"]
        for package in core_externals:
            assert package in packages, f"Missing external package: {package}"
            pkg_config = packages[package]
            assert pkg_config["buildable"] is False, f"{package} should not be buildable"
            assert len(pkg_config["externals"]) == 1, f"{package} should have exactly one external"
            assert pkg_config["externals"][0]["prefix"] == "/usr", f"{package} should use /usr prefix"
        
        # Test Slurm optional dependency externals
        optional_externals = ["hwloc", "hdf5", "dbus", "linux-pam", "libyaml"]
        for package in optional_externals:
            assert package in packages, f"Missing optional external package: {package}"
            pkg_config = packages[package]
            assert pkg_config["buildable"] is False, f"{package} should not be buildable"
            assert len(pkg_config["externals"]) == 1, f"{package} should have exactly one external"
            assert pkg_config["externals"][0]["prefix"] == "/usr", f"{package} should use /usr prefix"
        
        # Test json-c version specification (should still be present)
        json_c_config = packages["json-c"]
        assert "version" in json_c_config, "json-c should retain version specification"
        assert json_c_config["version"] == ["0.17"], "json-c should specify version 0.17"
        
        # Test gcc external
        assert "gcc" in packages
        gcc_config = packages["gcc"]
        gcc_external = gcc_config["externals"][0]
        assert "gcc@13.3.0" in gcc_external["spec"]
        assert gcc_external["prefix"] == "/usr"
    
    def test_slurm_external_dependencies(self):
        """Test that all Slurm external dependencies are properly configured."""
        config = generate_spack_config()
        packages = config["spack"]["packages"]
        
        # Define expected external packages with their Ubuntu package equivalents and versions
        expected_externals = {
            # Core Slurm dependencies
            "curl": ("libcurl4-openssl-dev", "8.5.0"),
            "glib": ("libglib2.0-dev", "2.80.0"), 
            "json-c": ("libjson-c-dev", "0.17"),
            "lz4": ("liblz4-dev", "1.9.4"),
            "openssl": ("libssl-dev", "3.0.13"),
            "pkgconf": ("pkg-config", "1.8.1"),
            "readline": ("libreadline-dev", "8.2"),
            "zlib-api": ("zlib1g-dev", "1.3"),
            # Optional Slurm dependencies
            "hwloc": ("libhwloc-dev", "2.10.0"),
            "hdf5": ("libhdf5-dev", "1.10.10"),
            "dbus": ("libdbus-1-dev", "1.14.10"),
            "linux-pam": ("libpam0g-dev", "1.5.3"),
            "libyaml": ("libyaml-dev", "0.2.5"),
            # Build tools and system utilities
            "autoconf": ("autoconf", "2.71"),
            "automake": ("automake", "1.16.5"),
            "libtool": ("libtool", "2.4.7"),
            "bison": ("bison", "3.8.2"),
            "flex": ("flex", "2.6.4"),
            "findutils": ("findutils", "4.9.0"),
            "diffutils": ("diffutils", "3.10"),
            "tar": ("tar", "1.34"),
            "gawk": ("gawk", "5.2.1"),
            "gettext": ("gettext", "0.21"),
            "ncurses": ("libncurses-dev", "6.4"),
            "bzip2": ("libbz2-dev", "1.0.8"),
            "xz": ("liblzma-dev", "5.4.5"),
            "zstd": ("libzstd-dev", "1.5.5"),
            "libxml2": ("libxml2-dev", "2.9.14"),
        }
        
        for spack_name, (ubuntu_pkg, version) in expected_externals.items():
            assert spack_name in packages, f"Missing external package: {spack_name} (Ubuntu: {ubuntu_pkg})"
            
            pkg_config = packages[spack_name]
            assert pkg_config["buildable"] is False, f"{spack_name} should not be buildable (uses {ubuntu_pkg})"
            assert "externals" in pkg_config, f"{spack_name} should have externals configuration"
            assert len(pkg_config["externals"]) == 1, f"{spack_name} should have exactly one external"
            
            external = pkg_config["externals"][0]
            assert external["prefix"] == "/usr", f"{spack_name} should use /usr prefix"
            assert "spec" in external, f"{spack_name} should have spec in external"
            # Check that the spec contains a version
            expected_spec = f"{spack_name}@{version}" if spack_name != "zlib-api" else f"zlib@{version}"
            assert expected_spec in external["spec"], f"{spack_name} spec should contain version {version}"
    
    def test_external_packages_build_optimization(self):
        """Test that external packages properly optimize build by preventing compilation."""
        config = generate_spack_config()
        packages = config["spack"]["packages"]
        
        # These packages should all be external and non-buildable for build optimization
        # Note: gcc doesn't have buildable=false set, it's handled differently
        optimization_packages = [
            "cmake", "python",  # System tools
            "curl", "glib", "json-c", "lz4", "openssl", "pkgconf", "readline", "zlib-api",  # Core deps
            "hwloc", "hdf5", "dbus", "linux-pam", "libyaml",  # Optional deps
            # Build tools and system utilities
            "autoconf", "automake", "libtool", "bison", "flex", "findutils", "diffutils", 
            "tar", "gawk", "gettext", "ncurses", "bzip2", "xz", "zstd", "libxml2"
        ]
        
        for pkg in optimization_packages:
            assert pkg in packages, f"Optimization package {pkg} should be configured"
            pkg_config = packages[pkg]
            assert pkg_config["buildable"] is False, f"{pkg} should not be buildable for optimization"
            assert "externals" in pkg_config, f"{pkg} should have external configuration"
            
        # Special case: gcc has externals but no explicit buildable=false
        assert "gcc" in packages, "gcc should be configured as external"
        assert "externals" in packages["gcc"], "gcc should have external configuration"
    
    def test_generate_spack_config_modules_configuration(self):
        """Test module configuration."""
        config = generate_spack_config()
        modules = config["spack"]["modules"]["default"]
        
        assert "lmod" in modules["enable"]
        lmod_config = modules["lmod"]
        
        assert lmod_config["core_compilers"] == ["gcc@13.3.0"]
        assert lmod_config["all"]["autoload"] == "direct"
        
        # Check Slurm-specific module config
        slurm_module = lmod_config["slurm"]
        env_vars = slurm_module["environment"]["set"]
        assert env_vars["SLURM_CONF"] == "/etc/slurm/slurm.conf"
        assert env_vars["SLURM_ROOT"] == "{{prefix}}"
    
    def test_generate_spack_config_concretizer_settings(self):
        """Test concretizer settings."""
        config = generate_spack_config()
        concretizer = config["spack"]["concretizer"]
        
        assert concretizer["unify"] is True
        assert concretizer["reuse"] is True
    
    def test_generate_spack_config_view_settings(self):
        """Test view settings."""
        config = generate_spack_config()
        view = config["spack"]["view"]
        
        assert view["root"] == "/opt/slurm/view"
        assert view["link_type"] == "hardlink"


class TestGetCommentHeader:
    """Test get_comment_header function."""
    
    def test_get_comment_header_minimal(self):
        """Test comment header for minimal build."""
        header = get_comment_header("25.05", False, minimal=True)
        assert header == "# Spack environment for building Slurm 25.05 (minimal build - basic Slurm only)"
    
    def test_get_comment_header_gpu(self):
        """Test comment header for GPU build."""
        header = get_comment_header("24.11", True, minimal=False)
        assert header == "# Spack environment for building Slurm 24.11 with GPU support"
    
    def test_get_comment_header_cpu_only(self):
        """Test comment header for CPU-only build."""
        header = get_comment_header("23.11", False, minimal=False)
        assert header == "# Spack environment for building Slurm 23.11 (optimized for minimal runtime footprint)"


class TestGenerateYamlString:
    """Test generate_yaml_string function."""
    
    def test_generate_yaml_string_valid_yaml(self):
        """Test that generate_yaml_string produces valid YAML."""
        yaml_str = generate_yaml_string()
        
        # Should not raise exception
        parsed = yaml.safe_load(yaml_str)
        assert "spack" in parsed
    
    def test_generate_yaml_string_includes_header(self):
        """Test that YAML string includes comment header."""
        yaml_str = generate_yaml_string("25.05", True, False)
        lines = yaml_str.split('\n')
        assert lines[0].startswith("# Spack environment for building Slurm 25.05")
    
    def test_generate_yaml_string_template_replacement(self):
        """Test that template variables are correctly replaced."""
        yaml_str = generate_yaml_string()
        
        # Should contain single braces, not double braces
        assert "{name}" in yaml_str
        assert "{prefix}" in yaml_str
        assert "{{name}}" not in yaml_str
        assert "{{prefix}}" not in yaml_str
    
    def test_generate_yaml_string_different_configs(self):
        """Test generate_yaml_string with different configurations."""
        configs = [
            ("25.05", False, False),  # CPU-only
            ("24.11", True, False),   # GPU-enabled
            ("23.11", False, True),   # Minimal
        ]
        
        for version, gpu, minimal in configs:
            yaml_str = generate_yaml_string(version, gpu, minimal)
            
            # Should be valid YAML
            parsed = yaml.safe_load(yaml_str)
            assert "spack" in parsed
            
            # Should contain version-specific content
            assert version in yaml_str
    
    def test_generate_yaml_string_formatting(self):
        """Test YAML string formatting."""
        yaml_str = generate_yaml_string()
        
        # Should have proper indentation and structure
        lines = yaml_str.split('\n')
        
        # Find the spack section
        spack_line_idx = next(i for i, line in enumerate(lines) if line.strip() == "spack:")
        
        # Following lines should be properly indented
        specs_line_idx = next(i for i, line in enumerate(lines[spack_line_idx:]) 
                             if line.strip().startswith("specs:")) + spack_line_idx
        
        # Specs line should be indented under spack
        assert lines[specs_line_idx].startswith("  specs:")


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_cpu_only_config(self):
        """Test cpu_only_config function."""
        config = cpu_only_config("24.11")
        
        # Should be equivalent to generate_spack_config with defaults
        expected = generate_spack_config(slurm_version="24.11", gpu_support=False, minimal=False)
        assert config == expected
        
        # Verify it's CPU-only
        specs = config["spack"]["specs"]
        slurm_spec = next((s for s in specs if "slurm@" in s), None)
        assert "~nvml" in slurm_spec
        assert "~rsmi" in slurm_spec
    
    def test_gpu_enabled_config(self):
        """Test gpu_enabled_config function."""
        config = gpu_enabled_config("23.11")
        
        # Should be equivalent to generate_spack_config with GPU enabled
        expected = generate_spack_config(slurm_version="23.11", gpu_support=True, minimal=False)
        assert config == expected
        
        # Verify it has GPU support
        specs = config["spack"]["specs"]
        slurm_spec = next((s for s in specs if "slurm@" in s), None)
        assert "+nvml" in slurm_spec
        assert "+rsmi" in slurm_spec
    
    def test_minimal_config(self):
        """Test minimal_config function."""
        config = minimal_config("23.02")
        
        # Should be equivalent to generate_spack_config with minimal=True
        expected = generate_spack_config(slurm_version="23.02", gpu_support=False, minimal=True)
        assert config == expected
        
        # Verify it's minimal
        specs = config["spack"]["specs"]
        assert len(specs) == 1  # Only Slurm spec
        
        slurm_spec = specs[0]
        assert "~hwloc" in slurm_spec
        assert "~pmix" in slurm_spec
        assert "~restd" in slurm_spec
    
    def test_convenience_functions_default_version(self):
        """Test convenience functions with default version."""
        cpu_config = cpu_only_config()
        gpu_config = gpu_enabled_config()
        min_config = minimal_config()
        
        # All should use default version 25.05
        for config in [cpu_config, gpu_config, min_config]:
            specs = config["spack"]["specs"]
            slurm_spec = next((s for s in specs if "slurm@" in s), None)
            assert "slurm@25-05-1-1" in slurm_spec


class TestConfigurationIntegrity:
    """Test configuration integrity and consistency."""
    
    def test_all_versions_work(self):
        """Test that all supported versions work with all build types."""
        for version in SLURM_VERSIONS.keys():
            # Test all combinations
            configs = [
                generate_spack_config(slurm_version=version, gpu_support=False, minimal=False),
                generate_spack_config(slurm_version=version, gpu_support=True, minimal=False),
                generate_spack_config(slurm_version=version, gpu_support=False, minimal=True),
            ]
            
            for config in configs:
                # Basic structure validation
                assert "spack" in config
                assert "specs" in config["spack"]
                assert len(config["spack"]["specs"]) >= 1
                
                # Version consistency
                package_version = SLURM_VERSIONS[version]
                slurm_spec = next((s for s in config["spack"]["specs"] if "slurm@" in s), None)
                assert f"slurm@{package_version}" in slurm_spec
    
    def test_yaml_roundtrip(self):
        """Test that generated YAML can be parsed and regenerated."""
        original_config = generate_spack_config()
        yaml_str = generate_yaml_string()
        
        # Parse the YAML
        parsed = yaml.safe_load(yaml_str)
        
        # The parsed YAML should have the same structure as original config
        assert "spack" in parsed
        assert len(parsed["spack"]["specs"]) == len(original_config["spack"]["specs"])
    
    def test_config_immutability(self):
        """Test that generated configs don't share mutable state."""
        config1 = generate_spack_config(slurm_version="25.05")
        config2 = generate_spack_config(slurm_version="24.11")
        
        # Modify config1
        config1["spack"]["specs"].append("test-package")
        
        # config2 should not be affected
        assert "test-package" not in config2["spack"]["specs"]
    
    def test_minimal_vs_full_differences(self):
        """Test key differences between minimal and full configurations."""
        minimal_config = generate_spack_config(minimal=True)
        full_config = generate_spack_config(minimal=False)
        
        minimal_specs = minimal_config["spack"]["specs"]
        full_specs = full_config["spack"]["specs"]
        
        # Minimal should have fewer specs
        assert len(minimal_specs) < len(full_specs)
        
        # Full config should have OpenMPI and dbus
        openmpi_in_full = any("openmpi" in spec for spec in full_specs)
        dbus_in_full = any("dbus" in spec for spec in full_specs)
        assert openmpi_in_full
        assert dbus_in_full
        
        # Minimal should not have OpenMPI or dbus
        openmpi_in_minimal = any("openmpi" in spec for spec in minimal_specs)
        dbus_in_minimal = any("dbus" in spec for spec in minimal_specs)
        assert not openmpi_in_minimal
        assert not dbus_in_minimal
    
    def test_gpu_vs_cpu_differences(self):
        """Test key differences between GPU and CPU configurations."""
        gpu_config = generate_spack_config(gpu_support=True)
        cpu_config = generate_spack_config(gpu_support=False)
        
        gpu_specs = gpu_config["spack"]["specs"]
        cpu_specs = cpu_config["spack"]["specs"]
        
        # Find Slurm specs
        gpu_slurm = next((s for s in gpu_specs if "slurm@" in s), None)
        cpu_slurm = next((s for s in cpu_specs if "slurm@" in s), None)
        
        # GPU config should have GPU flags enabled
        assert "+nvml" in gpu_slurm
        assert "+rsmi" in gpu_slurm
        
        # CPU config should have GPU flags disabled
        assert "~nvml" in cpu_slurm
        assert "~rsmi" in cpu_slurm


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_invalid_slurm_version_error_message(self):
        """Test error message for invalid Slurm version."""
        with pytest.raises(ValueError) as exc_info:
            generate_spack_config(slurm_version="invalid")
        
        error_msg = str(exc_info.value)
        assert "Unsupported Slurm version: invalid" in error_msg
        assert "25.05" in error_msg  # Should list supported versions
    
    def test_empty_string_slurm_version(self):
        """Test error handling for empty string version."""
        with pytest.raises(ValueError):
            generate_spack_config(slurm_version="")
    
    def test_none_slurm_version(self):
        """Test error handling for None version."""
        with pytest.raises((ValueError, TypeError)):
            generate_spack_config(slurm_version=None)


class TestMainExecution:
    """Test the __main__ execution block."""
    
    def test_main_execution_imports(self):
        """Test that the module can be imported and main code runs."""
        # This is tested by the successful import of the module
        # The __main__ block should only print, not raise exceptions
        
        # Test that we can call the functions used in __main__
        yaml_configs = [
            generate_yaml_string("25.05", False, False),
            generate_yaml_string("25.05", True, False),
            generate_yaml_string("25.05", False, True),
        ]
        
        for yaml_config in yaml_configs:
            assert isinstance(yaml_config, str)
            assert "spack:" in yaml_config
            assert yaml_config.startswith("#")  # Should start with comment
