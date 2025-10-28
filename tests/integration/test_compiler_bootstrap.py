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

"""Unit tests for compiler bootstrap configuration and Dockerfile generation."""

import pytest
import yaml

from slurm_factory.constants import (
    CONTAINER_SPACK_PROJECT_DIR,
    get_dockerfile,
    get_spack_build_script,
)
from slurm_factory.spack_yaml import (
    generate_compiler_bootstrap_config,
    generate_compiler_bootstrap_yaml,
    generate_spack_config,
    generate_yaml_string,
)


class TestCompilerBootstrapConfig:
    """Test compiler bootstrap configuration generation."""

    def test_compiler_bootstrap_has_gcc_spec(self):
        """Test that compiler bootstrap config includes GCC spec."""
        config = generate_compiler_bootstrap_config("13.4.0")
        
        assert "spack" in config
        assert "specs" in config["spack"]
        
        # Should have gcc spec
        gcc_specs = [spec for spec in config["spack"]["specs"] if spec.startswith("gcc@")]
        assert len(gcc_specs) == 1
        assert "gcc@13.4.0" in gcc_specs[0]
        
    def test_compiler_bootstrap_view_configuration(self):
        """Test that compiler bootstrap creates view at /opt/spack-compiler."""
        config = generate_compiler_bootstrap_config("13.4.0")
        
        assert "view" in config["spack"]
        assert "/opt/spack-compiler" in config["spack"]["view"]
        
        view_config = config["spack"]["view"]["/opt/spack-compiler"]
        assert view_config["root"] == "/opt/spack-compiler"
        assert "gcc@13.4.0" in view_config["select"]
        
    def test_compiler_bootstrap_prevents_system_gcc(self):
        """Test that compiler bootstrap prevents use of system GCC."""
        config = generate_compiler_bootstrap_config("13.4.0")
        
        # GCC package should have empty externals to prevent system GCC detection
        assert "gcc" in config["spack"]["packages"]
        gcc_config = config["spack"]["packages"]["gcc"]
        assert "externals" in gcc_config
        assert gcc_config["externals"] == []
        assert gcc_config["buildable"] is True
        
    def test_compiler_bootstrap_yaml_generation(self):
        """Test that compiler bootstrap YAML can be generated and parsed."""
        yaml_str = generate_compiler_bootstrap_yaml("13.4.0")
        
        # Should be valid YAML
        parsed = yaml.safe_load(yaml_str)
        assert "spack" in parsed
        assert "specs" in parsed["spack"]
        
        # Should have comment header
        lines = yaml_str.split('\n')
        assert lines[0].startswith("#")
        assert "13.4.0" in yaml_str


class TestSlurmEnvironmentConfig:
    """Test Slurm environment configuration."""

    def test_slurm_env_uses_compiler_from_buildcache(self):
        """Test that Slurm environment config expects compiler from buildcache."""
        config = generate_spack_config(compiler_version="13.4.0")
        
        # Check that all specs (except gcc itself) use the compiler constraint
        for spec in config["spack"]["specs"]:
            if not spec.startswith("#"):  # Skip comments
                # Skip gcc spec itself - it comes from buildcache, not built with gcc@13.4.0
                if not spec.startswith("gcc@"):
                    assert "%gcc@13.4.0" in spec, f"Spec missing compiler constraint: {spec}"
                
    def test_slurm_env_gcc_requirements_match_bootstrap(self):
        """Test that GCC in Slurm environment is configured to be installed from buildcache."""
        
        compiler_version = "13.4.0"
        
        # Get GCC config from Slurm environment
        slurm_config = generate_spack_config(compiler_version=compiler_version)
        gcc_package_config = slurm_config["spack"]["packages"]["gcc"]
        
        # GCC should be buildable (from buildcache) with correct version and variants
        assert gcc_package_config["buildable"] is True
        assert gcc_package_config["version"] == [compiler_version]
        assert "+binutils" in gcc_package_config["variants"]
        assert "+piclibs" in gcc_package_config["variants"]
        assert "languages=c,c++,fortran" in gcc_package_config["variants"]
        
        # gcc-runtime should be buildable during Slurm build phase
        gcc_runtime_config = slurm_config["spack"]["packages"]["gcc-runtime"]
        assert gcc_runtime_config["buildable"] is True
        assert gcc_runtime_config["version"] == [compiler_version]
            
    def test_slurm_env_prevents_system_gcc(self):
        """Test that Slurm environment uses buildcache GCC, not system GCC."""
        compiler_version = "13.4.0"
        config = generate_spack_config(compiler_version=compiler_version)
        
        # GCC package should be buildable (from buildcache), not external
        gcc_config = config["spack"]["packages"]["gcc"]
        assert gcc_config["buildable"] is True  # Install from buildcache
        assert gcc_config["version"] == [compiler_version]  # Specific version
        
        # The buildcache mirror should be configured to provide gcc binaries
        mirrors = config["spack"]["mirrors"]
        assert "slurm-factory-buildcache" in mirrors
        # Note: Spack adds build_cache/ subdirectory automatically
        assert f"compilers/{compiler_version}" in mirrors["slurm-factory-buildcache"]["url"]
        
    def test_slurm_env_has_empty_compilers_list(self):
        """Test that Slurm environment starts with empty compilers list."""
        config = generate_spack_config()
        
        # Compilers should be empty - GCC will be registered after installation
        assert "compilers" in config["spack"]
        assert config["spack"]["compilers"] == []


class TestDockerfileBuildScript:
    """Test Dockerfile build script generation."""

    def test_build_script_switches_to_slurm_environment(self):
        """Test that build script switches to Slurm project environment after compiler install."""
        script = get_spack_build_script("13.4.0")
        
        # Script should create compiler install environment
        assert "mkdir -p /tmp/compiler-install" in script
        assert "cd /tmp/compiler-install" in script
        
        # Script should install compiler (will use buildcache when available, build from source if needed)
        assert "spack -e . install" in script
        
        # Script should register compiler globally
        assert "spack compiler find --scope site /opt/spack-compiler-view" in script
        
        # CRITICAL: Script should switch to Slurm project directory
        assert f"cd {CONTAINER_SPACK_PROJECT_DIR}" in script
        assert "Switching to Slurm project environment" in script
        
        # Script should activate Slurm environment AFTER switching directory
        script_lines = script.split("\n")
        switch_idx = None
        activate_idx = None
        
        for i, line in enumerate(script_lines):
            if "Switching to Slurm project environment" in line:
                switch_idx = i
            if "spack env activate" in line and switch_idx is not None:
                activate_idx = i
                
        assert switch_idx is not None, "Could not find environment switch"
        assert activate_idx is not None, "Could not find environment activation"
        assert activate_idx > switch_idx, "Environment activation happens before directory switch"
        
    def test_build_script_compiler_verification(self):
        """Test that build script verifies correct compiler is configured."""
        script = get_spack_build_script("13.4.0")
        
        # Should verify the correct compiler is available
        assert "Verifying gcc@13.4.0 is available" in script
        assert "gcc@13.4.0 compiler not found" in script
        assert "spack compiler list" in script
        
    def test_build_script_prefers_buildcache_for_compiler_install(self):
        """Test that build script prefers buildcache for compiler installation."""
        script = get_spack_build_script("13.4.0")
        
        # Should install using concretizer configuration that prefers buildcache
        assert "spack -e . install" in script
        assert "Installing GCC compiler from buildcache" in script
        
        # Should check if compiler is available in buildcache before installing
        assert "spack buildcache list" in script
        assert "gcc@13.4.0 not found in buildcache" in script
        
        # Should verify that GCC was installed from buildcache
        assert "Verifying GCC was installed from buildcache" in script
        
    def test_dockerfile_includes_correct_build_script(self):
        """Test that generated Dockerfile includes the corrected build script."""
        spack_yaml = generate_yaml_string("25.11", compiler_version="13.4.0")
        dockerfile = get_dockerfile(
            spack_yaml_content=spack_yaml,
            version="25.11",
            compiler_version="13.4.0",
        )
        
        # Dockerfile should include the critical directory switch
        assert f"cd {CONTAINER_SPACK_PROJECT_DIR}" in dockerfile
        assert "Switching to Slurm project environment" in dockerfile
        
        # Dockerfile should create Slurm project directory
        assert CONTAINER_SPACK_PROJECT_DIR in dockerfile
        
        # Dockerfile should copy spack.yaml to correct location
        assert f"cat > {CONTAINER_SPACK_PROJECT_DIR}/spack.yaml" in dockerfile


class TestCompilerBootstrapIntegration:
    """Integration tests for compiler bootstrap process."""

    def test_full_dockerfile_generation(self):
        """Test complete Dockerfile generation with compiler bootstrap."""
        spack_yaml = generate_yaml_string("25.11", compiler_version="13.4.0")
        dockerfile = get_dockerfile(
            spack_yaml_content=spack_yaml,
            version="25.11",
            compiler_version="13.4.0",
        )
        
        # Dockerfile should have proper stage structure
        assert "FROM ubuntu:24.04 AS init" in dockerfile
        assert "FROM init AS builder" in dockerfile
        assert "FROM builder AS packager" in dockerfile
        
        # Builder stage should install Spack
        assert "Install Spack v1.0.0" in dockerfile or "SPACK_ROOT=/opt/spack" in dockerfile
        
        # Builder stage should copy spack.yaml
        assert "spack.yaml" in dockerfile
        
        # Builder stage should run build script
        assert "spack env activate" in dockerfile
        assert "spack concretize" in dockerfile
        assert "spack install" in dockerfile
        
    def test_compiler_and_slurm_yaml_compatibility(self):
        """Test that compiler bootstrap and Slurm configs are compatible."""
        compiler_version = "13.4.0"
        
        # Generate both configs
        compiler_config = generate_compiler_bootstrap_config(compiler_version)
        slurm_config = generate_spack_config(compiler_version=compiler_version)
        
        # Both should use the same GCC version
        compiler_gcc_specs = [s for s in compiler_config["spack"]["specs"] if s.startswith("gcc@")]
        assert len(compiler_gcc_specs) == 1
        assert f"gcc@{compiler_version}" in compiler_gcc_specs[0]
        
        # Slurm config should mark GCC as buildable (will be installed from buildcache)
        slurm_gcc_config = slurm_config["spack"]["packages"]["gcc"]
        assert slurm_gcc_config["buildable"] is True
        assert slurm_gcc_config["version"] == [compiler_version]
        
        # Verify variants match between compiler bootstrap and Slurm configs
        assert "+binutils" in slurm_gcc_config["variants"]
        assert "+piclibs" in slurm_gcc_config["variants"]
        
        # Compiler bootstrap config should prevent system GCC from being detected
        assert compiler_config["spack"]["packages"]["gcc"]["externals"] == []
        
        # Both configs should reference the same buildcache
        assert "slurm-factory-buildcache" in slurm_config["spack"]["mirrors"]
        # Note: Spack adds build_cache/ subdirectory automatically
        assert f"compilers/{compiler_version}" in slurm_config["spack"]["mirrors"]["slurm-factory-buildcache"]["url"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
