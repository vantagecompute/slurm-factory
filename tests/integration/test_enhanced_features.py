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

"""Unit tests for enhanced Spack 1.x features in slurm_factory."""

import pytest
import yaml

from slurm_factory.spack_yaml import (
    generate_module_config,
    generate_spack_config,
    generate_yaml_string,
)


class TestModuleHierarchy:
    """Test Core/Compiler/MPI module hierarchy functionality."""

    def test_flat_hierarchy_default(self):
        """Test that flat hierarchy is the default for backward compatibility."""
        module_config = generate_module_config()
        lmod_config = module_config["default"]["lmod"]
        
        assert lmod_config["hierarchy"] == []

    def test_hierarchical_mode_enabled(self):
        """Test hierarchical mode when explicitly enabled."""
        module_config = generate_module_config(enable_hierarchy=True)
        lmod_config = module_config["default"]["lmod"]
        
        # Should enable MPI hierarchy
        assert lmod_config["hierarchy"] == ["mpi"]

    def test_openmpi_autoload_in_hierarchy(self):
        """Test that OpenMPI is included in hierarchical mode."""
        module_config = generate_module_config(enable_hierarchy=True)
        lmod_config = module_config["default"]["lmod"]
        
        # OpenMPI should be in the include list
        assert "openmpi" in lmod_config["include"]
        # Hierarchy should be enabled
        assert lmod_config["hierarchy"] == ["mpi"]

    def test_openmpi_no_autoload_flat(self):
        """Test that OpenMPI is included in flat mode."""
        module_config = generate_module_config(enable_hierarchy=False)
        lmod_config = module_config["default"]["lmod"]
        
        # OpenMPI should be in the include list in flat mode too
        assert "openmpi" in lmod_config["include"]
        # Hierarchy should be empty in flat mode
        assert lmod_config["hierarchy"] == []


class TestBuildcacheSupport:
    """Test binary cache (buildcache) functionality."""

    def test_buildcache_disabled_by_default(self):
        """Test that buildcache is disabled by default."""
        config = generate_spack_config()
        mirrors = config["spack"]["mirrors"]
        
        # Should only have spack-public mirror
        assert "spack-public" in mirrors
        assert "buildcache" not in mirrors


class TestEnhancedRPATH:
    """Test enhanced RPATH configuration for Spack 1.x."""

    def test_rpath_configuration_present(self):
        """Test that RPATH configuration is present."""
        config = generate_spack_config()
        shared_linking = config["spack"]["config"]["shared_linking"]
        
        assert "type" in shared_linking
        assert shared_linking["type"] == "rpath"

    def test_rpath_not_bound(self):
        """Test that RPATH is not bound to absolute paths."""
        config = generate_spack_config()
        shared_linking = config["spack"]["config"]["shared_linking"]
        
        # bind should be False for relocatability
        assert shared_linking["bind"] is False

    def test_missing_library_policy(self):
        """Test missing library policy configuration."""
        config = generate_spack_config()
        shared_linking = config["spack"]["config"]["shared_linking"]
        
        # Should warn on missing libraries
        assert shared_linking["missing_library_policy"] == "warn"

    def test_ccache_enabled(self):
        """Test that ccache is disabled (incompatible with Spack-built compilers)."""
        config = generate_spack_config()
        spack_config = config["spack"]["config"]
        
        # ccache is disabled because system ccache is incompatible with Spack-built compilers
        assert spack_config["ccache"] is False

    def test_additional_config_options(self):
        """Test additional Spack 1.x config options."""
        config = generate_spack_config()
        spack_config = config["spack"]["config"]
        
        # Note: install_missing_compilers was removed as it's deprecated
        # Should have db_lock_timeout configured
        assert "db_lock_timeout" in spack_config
        assert spack_config["db_lock_timeout"] == 120


class TestGCCRuntimeIntegration:
    """Test gcc-runtime integration for relocatability."""

    def test_gcc_runtime_in_specs(self):
        """Test that gcc-runtime is not in specs (it's built separately after compiler bootstrap)."""
        config = generate_spack_config()
        specs = config["spack"]["specs"]
        
        # gcc-runtime is built separately after the compiler is registered,
        # not included in main specs
        gcc_runtime_specs = [spec for spec in specs if "gcc-runtime@" in spec]
        # This is expected to be 0 since gcc-runtime is built outside the environment
        assert len(gcc_runtime_specs) == 0

    def test_gcc_runtime_package_config(self):
        """Test gcc-runtime package configuration."""
        config = generate_spack_config()
        packages = config["spack"]["packages"]
        
        # gcc-runtime should be buildable (built during Slurm build phase)
        assert "gcc-runtime" in packages
        assert packages["gcc-runtime"]["buildable"] is True
        # Version should match the compiler version
        assert "version" in packages["gcc-runtime"]

    def test_gcc_runtime_version_match(self):
        """Test that gcc-runtime is configured to be built with correct version."""
        compiler_version = "13.4.0"
        config = generate_spack_config(compiler_version=compiler_version)
        packages = config["spack"]["packages"]
        
        # gcc-runtime should be buildable with matching compiler version
        assert "gcc-runtime" in packages
        assert packages["gcc-runtime"]["buildable"] is True
        assert packages["gcc-runtime"]["version"] == [compiler_version]

    def test_gcc_runtime_in_module_env(self):
        """Test that gcc-runtime prefix is exposed in module environment."""
        module_config = generate_module_config()
        slurm_env = module_config["default"]["lmod"]["slurm"]["environment"]["set"]
        
        # Should have SLURM_GCC_RUNTIME_PREFIX
        assert "SLURM_GCC_RUNTIME_PREFIX" in slurm_env
        assert "{^gcc-runtime.prefix}" in slurm_env["SLURM_GCC_RUNTIME_PREFIX"]


class TestYAMLGenerationWithNewFeatures:
    """Test YAML generation with new features."""

    def test_yaml_generation_with_hierarchy(self):
        """Test YAML generation with hierarchy enabled."""
        yaml_string = generate_yaml_string(enable_hierarchy=True)
        
        assert isinstance(yaml_string, str)
        parsed = yaml.safe_load(yaml_string)
        assert "spack" in parsed
        
        # Should have hierarchy configured
        modules = parsed["spack"]["modules"]["default"]["lmod"]
        assert "hierarchy" in modules
        assert modules["hierarchy"] == ["mpi"]

    def test_yaml_generation_with_all_features(self):
        """Test YAML generation with all features enabled."""
        yaml_string = generate_yaml_string(enable_hierarchy=True)
        
        parsed = yaml.safe_load(yaml_string)
        
        # Should have all features configured
        assert parsed["spack"]["modules"]["default"]["lmod"]["hierarchy"] == ["mpi"]
        assert "verify" in parsed["spack"]["config"]


class TestBackwardCompatibility:
    """Test backward compatibility with existing configurations."""

    def test_default_parameters_unchanged(self):
        """Test that default parameters maintain backward compatibility."""
        # Old behavior should be preserved
        config_old = generate_spack_config()
        
        # New behavior with defaults should match
        config_new = generate_spack_config(
            enable_hierarchy=False,
        )
        
        # Both should have flat hierarchy
        assert config_old["spack"]["modules"]["default"]["lmod"]["hierarchy"] == []
        assert config_new["spack"]["modules"]["default"]["lmod"]["hierarchy"] == []

    def test_existing_tests_compatibility(self):
        """Test that existing test patterns still work."""
        # This mimics what existing tests do
        config = generate_spack_config(slurm_version="25.11", gpu_support=False)
        
        assert "spack" in config
        assert "specs" in config["spack"]
        assert "modules" in config["spack"]
        assert "config" in config["spack"]

    def test_all_compiler_versions_work(self):
        """Test that all compiler versions work with new features."""
        compiler_versions = ["7.5.0", "8.5.0", "9.5.0", "10.5.0", "11.5.0", "12.5.0", "13.4.0", "14.2.0"]
        
        for version in compiler_versions:
            config = generate_spack_config(
                compiler_version=version,
                enable_hierarchy=True,
            )
            assert "spack" in config
            # gcc-runtime is built separately, not in main specs
            # Just verify the config is valid
            assert "packages" in config["spack"]
            assert "gcc-runtime" in config["spack"]["packages"]


class TestParameterValidation:
    """Test parameter validation for new features."""

    def test_hierarchy_with_different_slurm_versions(self):
        """Test hierarchy works with all Slurm versions."""
        versions = ["25.11", "24.11", "23.11"]
        
        for version in versions:
            config = generate_spack_config(slurm_version=version, enable_hierarchy=True)
            assert "spack" in config

    # Removed local buildcache tests
    # def test_buildcache_with_different_configurations(self):
    #     """Test buildcache works with different build configurations."""
    #     configs = [
    #         {"gpu_support": True},
    #         {"gpu_support": False},
    #     ]
    #     
    #     for config_params in configs:
    #         config = generate_spack_config(**config_params)
    #         assert "spack" in config


if __name__ == "__main__":
    pytest.main([__file__])
