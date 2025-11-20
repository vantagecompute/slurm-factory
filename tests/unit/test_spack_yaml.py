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

"""Unit tests for slurm_factory.spack_yaml module."""

import pytest
import yaml

from slurm_factory.constants import SLURM_VERSIONS
from slurm_factory.spack_yaml import (
    cpu_only_config,
    generate_module_config,
    generate_spack_config,
    generate_yaml_string,
    get_comment_header,
    gpu_enabled_config,
    verification_config,
)


class TestSpackConfigGeneration:
    """Test Spack configuration generation."""

    def test_generate_spack_config_default(self):
        """Test default Spack configuration generation."""
        config = generate_spack_config()
        
        # Test top-level structure
        assert "spack" in config
        spack_config = config["spack"]
        
        # Test required sections
        required_sections = ["specs", "concretizer", "view", "config", "mirrors", "compilers", "packages", "modules"]
        for section in required_sections:
            assert section in spack_config, f"Missing section: {section}"
        
        # Test default specs
        assert isinstance(spack_config["specs"], list)
        assert len(spack_config["specs"]) > 0
        
        # Test that all specs have compiler constraints (using default noble toolchain: gcc@13.3.0)
        # EXCEPT gcc itself which should not have a compiler spec (it's built with system compiler)
        for spec in spack_config["specs"]:
            if not spec.startswith("gcc@"):
                assert "%gcc@13.3.0" in spec, f"Spec missing compiler constraint: {spec}"
            else:
                # GCC should not have a compiler spec - it's built with system compiler from Ubuntu
                assert "%" not in spec, f"GCC spec should not have compiler constraint: {spec}"

    def test_generate_spack_config_versions(self):
        """Test configuration generation for all supported Slurm versions."""
        for version in SLURM_VERSIONS.keys():
            config = generate_spack_config(slurm_version=version)
            assert "spack" in config
            # Check that the slurm package version is correct
            slurm_specs = [spec for spec in config["spack"]["specs"] if "slurm_factory.slurm@" in spec]
            assert len(slurm_specs) > 0, f"No slurm spec found for version {version}"
            expected_package_version = SLURM_VERSIONS[version]
            slurm_spec = slurm_specs[0]
            assert expected_package_version in slurm_spec, f"Incorrect package version in {slurm_spec}"

    def test_generate_spack_config_gpu_support(self):
        """Test GPU support configuration."""
        # CPU-only config
        cpu_config = generate_spack_config(gpu_support=False)
        slurm_specs = [spec for spec in cpu_config["spack"]["specs"] if "slurm_factory.slurm@" in spec]
        slurm_spec = slurm_specs[0]
        assert "~nvml" in slurm_spec
        assert "~rsmi" in slurm_spec
        # GPU-enabled config
        gpu_config = generate_spack_config(gpu_support=True)
        slurm_specs = [spec for spec in gpu_config["spack"]["specs"] if "slurm_factory.slurm@" in spec]
        slurm_spec = slurm_specs[0]
        assert "+nvml" in slurm_spec
        assert "+rsmi" in slurm_spec
        # Check view configuration uses hardlinks
        assert gpu_config["spack"]["view"]["default"]["link_type"] == "hardlink"

    def test_compiler_configuration(self):
        """Test compiler configuration."""
        config = generate_spack_config()
        compilers = config["spack"]["compilers"]
        # Compilers start empty - GCC is installed from buildcache and detected via spack compiler find
        assert len(compilers) == 0

    def test_gcc_buildcache_configuration(self):
        """Test that GCC compiler is properly configured from system."""
        # Use noble toolchain (Ubuntu 24.04 with GCC 13.3.0)
        toolchain = "noble"
        config = generate_spack_config(toolchain=toolchain)
        compilers = config["spack"]["compilers"]
        # System compiler should be detected and configured
        assert isinstance(compilers, list)
        # No pre-built compilers are needed with system toolchain approach
        # The compiler is found via 'spack compiler find --scope site'

    def test_package_configurations(self):
        """Test package-specific configurations."""
        config = generate_spack_config()
        packages = config["spack"]["packages"]
        # Test build tools are buildable (no longer using externals)
        build_tools = [
            "cmake", "python", "gmake", "m4", "pkgconf",
            "diffutils", "findutils", "tar", "gettext"
        ]
        for tool in build_tools:
            assert tool in packages
            assert packages[tool]["buildable"] is True
        # Test autotools are buildable (built from source for libjwt compatibility)
        buildable_tools = ["autoconf", "automake", "libtool"]
        for tool in buildable_tools:
            assert tool in packages
            assert packages[tool]["buildable"] is True
        # Test runtime libraries are buildable
        runtime_libs = ["munge", "json-c", "curl", "openssl", "readline", "ncurses"]
        for lib in runtime_libs:
            assert lib in packages
            assert packages[lib]["buildable"] is True
        # Test libjwt configuration
        assert "libjwt" in packages
        libjwt_config = packages["libjwt"]
        assert libjwt_config["buildable"] is True
        assert "require" in libjwt_config
        requirements = libjwt_config["require"]
        assert "^slurm_factory.openssl@3:" in requirements
        assert "^jansson" in requirements


class TestModuleConfiguration:
    """Test module configuration generation."""

    def test_generate_module_config_default(self):
        """Test default module configuration."""
        module_config = generate_module_config()
        # Test structure
        assert "default" in module_config
        default_config = module_config["default"]
        assert "enable" in default_config
        assert "lmod" in default_config
        # Test Lmod configuration (using default noble toolchain: gcc@13.3.0)
        lmod_config = default_config["lmod"]
        assert "core_compilers" in lmod_config
        assert "gcc@13.3.0" in lmod_config["core_compilers"]
        assert lmod_config["hierarchy"] == []
        # Test included modules
        assert "slurm" in lmod_config["include"]
        assert "openmpi" in lmod_config["include"]

    def test_slurm_module_configuration(self):
        """Test Slurm-specific module configuration."""
        module_config = generate_module_config()
        slurm_config = module_config["default"]["lmod"]["slurm"]
        # Test environment variables
        env_vars = slurm_config["environment"]["set"]
        assert "SLURM_CONF" in env_vars
        assert "SLURM_ROOT" in env_vars
        assert "SLURM_BUILD_TYPE" in env_vars
        assert "SLURM_VERSION" in env_vars
        assert "SLURM_PREFIX" in env_vars
        assert "SLURM_MODULE_HELP" in env_vars
        assert "SLURM_COMPILER" in env_vars
        assert "SLURM_TARGET_ARCH" in env_vars
        assert "SLURM_GCC_RUNTIME_PREFIX" in env_vars
        # Test path modifications
        paths = slurm_config["environment"]["prepend_path"]
        assert "PATH" in paths
        assert "CPATH" in paths
        assert "PKG_CONFIG_PATH" in paths
        assert "MANPATH" in paths
        assert "CMAKE_PREFIX_PATH" in paths


class TestConvenienceFunctions:
    """Test convenience configuration functions."""

    def test_cpu_only_config(self):
        """Test CPU-only convenience function."""
        config = cpu_only_config()
        assert "spack" in config
        # Should be equivalent to generate_spack_config with defaults
        default_config = generate_spack_config()
        assert config == default_config

    def test_gpu_enabled_config(self):
        """Test GPU-enabled convenience function."""
        config = gpu_enabled_config()
        assert "spack" in config
        # Should have GPU support enabled
        slurm_specs = [spec for spec in config["spack"]["specs"] if "slurm_factory.slurm@" in spec]
        slurm_spec = slurm_specs[0]
        assert "+nvml" in slurm_spec
        assert "+rsmi" in slurm_spec

    def test_verification_config(self):
        """Test verification convenience function."""
        config = verification_config()
        assert "spack" in config
        # Should have verification enabled
        assert "verify" in config["spack"]["config"]
        verify_config = config["spack"]["config"]["verify"]
        assert verify_config["relocatable"] is True
        assert verify_config["dependencies"] is True
        assert verify_config["shared_libraries"] is True


class TestYAMLGeneration:
    """Test YAML string generation."""

    def test_generate_yaml_string(self):
        """Test YAML string generation."""
        yaml_string = generate_yaml_string()
        # Test that it's a valid YAML string
        assert isinstance(yaml_string, str)
        assert len(yaml_string) > 0
        # Test that it can be parsed as YAML
        parsed = yaml.safe_load(yaml_string)
        assert "spack" in parsed
        # Test that it has a comment header
        lines = yaml_string.split('\n')
        assert lines[0].startswith("#")

    def test_generate_yaml_string_versions(self):
        """Test YAML generation for different versions."""
        for version in SLURM_VERSIONS.keys():
            yaml_string = generate_yaml_string(slurm_version=version)
            # Should be valid YAML
            parsed = yaml.safe_load(yaml_string)
            assert "spack" in parsed
            # Should contain the correct version in comment
            assert version in yaml_string

    def test_get_comment_header(self):
        """Test comment header generation."""
        header = get_comment_header("25.11", True)
        assert "25.11" in header
        assert "with GPU support" in header

        header = get_comment_header("25.11", False)
        assert "25.11" in header
        assert "(without GPU support)" in header


class TestConfigurationValidation:
    """Test configuration validation and consistency."""

    def test_view_packages_consistency(self):
        """Test that view configuration uses hardlinks."""
        # Standard build
        config = generate_spack_config()
        view_config = config["spack"]["view"]["default"]
        # Should use hardlink for easier copying
        assert view_config["link_type"] == "hardlink"
        # Should exclude build tools (not autoconf - it's buildable but not excluded)
        assert "cmake" in view_config["exclude"]
        assert "tar" in view_config["exclude"]

    def test_gpu_view_packages(self):
        """Test view configuration for GPU build."""
        config = generate_spack_config(gpu_support=True)
        view_config = config["spack"]["view"]["default"]
        # Should use hardlink for easier copying
        assert view_config["link_type"] == "hardlink"
        # GPU packages should be excluded from view (they'll be copied separately)
        assert "cuda" in view_config["exclude"]
        assert "rocm-core" in view_config["exclude"]

    def test_concretizer_settings(self):
        """Test concretizer configuration."""
        config = generate_spack_config()
        concretizer = config["spack"]["concretizer"]
        # unify is set to "when_possible" for better dependency resolution
        assert concretizer["unify"] == "when_possible"
        assert concretizer["reuse"]["roots"] is True  # Reuse from buildcache

    def test_mirror_configuration(self):
        """Test mirror configuration."""
        config = generate_spack_config()
        mirrors = config["spack"]["mirrors"]
        # Should have spack-public mirror for source downloads
        assert "spack-public" in mirrors
        # Test mirror properties
        assert mirrors["spack-public"]["url"] == "https://mirror.spack.io"
        assert mirrors["spack-public"]["signed"] is False


class TestParameterValidation:
    """Test parameter validation."""

    def test_invalid_slurm_version(self):
        """Test invalid Slurm version handling."""
        with pytest.raises(ValueError) as exc_info:
            generate_spack_config(slurm_version="99.99")
        assert "Unsupported Slurm version" in str(exc_info.value)

    def test_valid_parameters(self):
        """Test valid parameter combinations."""
        # All valid combinations should work without errors
        for version in SLURM_VERSIONS.keys():
            for gpu in [True, False]:
                config = generate_spack_config(slurm_version=version, gpu_support=gpu)
                assert "spack" in config


if __name__ == "__main__":
    pytest.main([__file__])
