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

    def test_hierarchical_mode_minimal_build(self):
        """Test that minimal builds don't use hierarchy even if requested."""
        module_config = generate_module_config(minimal=True, enable_hierarchy=True)
        lmod_config = module_config["default"]["lmod"]
        
        # Minimal builds should remain flat
        assert lmod_config["hierarchy"] == []

    def test_openmpi_autoload_in_hierarchy(self):
        """Test that OpenMPI has autoload enabled in hierarchical mode."""
        module_config = generate_module_config(enable_hierarchy=True)
        lmod_config = module_config["default"]["lmod"]
        
        # OpenMPI should have autoload in hierarchical mode
        assert "openmpi" in lmod_config
        assert "autoload" in lmod_config["openmpi"]
        assert lmod_config["openmpi"]["autoload"] == "direct"

    def test_openmpi_no_autoload_flat(self):
        """Test that OpenMPI doesn't have autoload in flat mode."""
        module_config = generate_module_config(enable_hierarchy=False)
        lmod_config = module_config["default"]["lmod"]
        
        # OpenMPI should not have autoload in flat mode
        assert "openmpi" in lmod_config
        assert "autoload" not in lmod_config["openmpi"]


class TestBuildcacheSupport:
    """Test binary cache (buildcache) functionality."""

    def test_buildcache_disabled_by_default(self):
        """Test that buildcache is disabled by default."""
        config = generate_spack_config()
        mirrors = config["spack"]["mirrors"]
        
        # Should only have spack-public mirror
        assert "spack-public" in mirrors
        assert "buildcache" not in mirrors

    def test_buildcache_enabled(self):
        """Test buildcache configuration when enabled."""
        config = generate_spack_config(enable_buildcache=True)
        mirrors = config["spack"]["mirrors"]
        
        # Should have buildcache mirror
        assert "buildcache" in mirrors
        assert mirrors["buildcache"]["signed"] is False
        assert "file://" in mirrors["buildcache"]["url"]

    def test_buildcache_config_paths(self):
        """Test that buildcache adds necessary config paths."""
        config = generate_spack_config(enable_buildcache=True)
        spack_config = config["spack"]["config"]
        
        # Should have source_cache and misc_cache configured
        assert "source_cache" in spack_config
        assert "misc_cache" in spack_config

    def test_buildcache_padded_length(self):
        """Test that buildcache enables padded install paths."""
        config = generate_spack_config(enable_buildcache=True)
        install_tree = config["spack"]["config"]["install_tree"]
        
        # Should use padded length for relocatability
        assert install_tree["padded_length"] == 128


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
        """Test that ccache is enabled for faster rebuilds."""
        config = generate_spack_config()
        spack_config = config["spack"]["config"]
        
        assert spack_config["ccache"] is True

    def test_additional_config_options(self):
        """Test additional Spack 1.x config options."""
        config = generate_spack_config()
        spack_config = config["spack"]["config"]
        
        # Should have install_missing_compilers disabled
        assert spack_config["install_missing_compilers"] is False
        # Should have db_lock_timeout configured
        assert "db_lock_timeout" in spack_config
        assert spack_config["db_lock_timeout"] == 120


class TestGCCRuntimeIntegration:
    """Test gcc-runtime integration for relocatability."""

    def test_gcc_runtime_in_specs(self):
        """Test that gcc-runtime is included in specs."""
        config = generate_spack_config()
        specs = config["spack"]["specs"]
        
        # Should have gcc-runtime spec
        gcc_runtime_specs = [spec for spec in specs if "gcc-runtime@" in spec]
        assert len(gcc_runtime_specs) > 0

    def test_gcc_runtime_package_config(self):
        """Test gcc-runtime package configuration."""
        config = generate_spack_config()
        packages = config["spack"]["packages"]
        
        assert "gcc-runtime" in packages
        assert packages["gcc-runtime"]["buildable"] is True

    def test_gcc_runtime_version_match(self):
        """Test that gcc-runtime version matches compiler version."""
        compiler_version = "13.4.0"
        config = generate_spack_config(compiler_version=compiler_version)
        specs = config["spack"]["specs"]
        
        # Find gcc-runtime spec
        gcc_runtime_specs = [spec for spec in specs if "gcc-runtime@" in spec]
        assert len(gcc_runtime_specs) > 0
        assert compiler_version in gcc_runtime_specs[0]

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

    def test_yaml_generation_with_buildcache(self):
        """Test YAML generation with buildcache enabled."""
        yaml_string = generate_yaml_string(enable_buildcache=True)
        
        parsed = yaml.safe_load(yaml_string)
        mirrors = parsed["spack"]["mirrors"]
        
        # Should have buildcache mirror
        assert "buildcache" in mirrors

    def test_yaml_generation_with_all_features(self):
        """Test YAML generation with all features enabled."""
        yaml_string = generate_yaml_string(
            enable_hierarchy=True,
            enable_buildcache=True,
            enable_verification=True,
        )
        
        parsed = yaml.safe_load(yaml_string)
        
        # Should have all features configured
        assert parsed["spack"]["modules"]["default"]["lmod"]["hierarchy"] == ["mpi"]
        assert "buildcache" in parsed["spack"]["mirrors"]
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
            enable_buildcache=False,
        )
        
        # Both should have flat hierarchy
        assert config_old["spack"]["modules"]["default"]["lmod"]["hierarchy"] == []
        assert config_new["spack"]["modules"]["default"]["lmod"]["hierarchy"] == []
        
        # Both should not have buildcache
        assert "buildcache" not in config_old["spack"]["mirrors"]
        assert "buildcache" not in config_new["spack"]["mirrors"]

    def test_existing_tests_compatibility(self):
        """Test that existing test patterns still work."""
        # This mimics what existing tests do
        config = generate_spack_config(slurm_version="25.05", gpu_support=False, minimal=False)
        
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
                enable_buildcache=True,
            )
            assert "spack" in config
            # Check that gcc-runtime version matches
            gcc_runtime_specs = [spec for spec in config["spack"]["specs"] if "gcc-runtime@" in spec]
            assert len(gcc_runtime_specs) > 0
            assert version in gcc_runtime_specs[0]


class TestParameterValidation:
    """Test parameter validation for new features."""

    def test_hierarchy_with_different_slurm_versions(self):
        """Test hierarchy works with all Slurm versions."""
        versions = ["25.05", "24.11", "23.11", "23.02"]
        
        for version in versions:
            config = generate_spack_config(slurm_version=version, enable_hierarchy=True)
            assert "spack" in config

    def test_buildcache_with_different_configurations(self):
        """Test buildcache works with different build configurations."""
        configs = [
            {"gpu_support": True, "minimal": False},
            {"gpu_support": False, "minimal": False},
            {"gpu_support": False, "minimal": True},
        ]
        
        for config_params in configs:
            config = generate_spack_config(enable_buildcache=True, **config_params)
            assert "buildcache" in config["spack"]["mirrors"]

    def test_combined_features_minimal_build(self):
        """Test that features work correctly with minimal builds."""
        config = generate_spack_config(
            minimal=True,
            enable_hierarchy=True,
            enable_buildcache=True,
        )
        
        # Hierarchy should be disabled for minimal builds
        assert config["spack"]["modules"]["default"]["lmod"]["hierarchy"] == []
        # Buildcache should still be enabled
        assert "buildcache" in config["spack"]["mirrors"]


if __name__ == "__main__":
    pytest.main([__file__])
