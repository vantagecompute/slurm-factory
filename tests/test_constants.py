"""Unit tests for slurm_factory.constants module."""

import pytest
from string import Template

from slurm_factory.constants import (
    SLURM_VERSIONS,
    SlurmVersion,
    BuildType,
    CONTAINER_CACHE_DIR,
    CONTAINER_PATCHES_DIR,
    CONTAINER_SPACK_PROJECT_DIR,
    CONTAINER_SLURM_DIR,
    CONTAINER_BUILD_OUTPUT_DIR,
    CONTAINER_ROOT_DIR,
    CONTAINER_SPACK_CACHE_DIR,
    CACHE_SUBDIRS,
    get_mkdir_commands,
    LXD_IMAGE,
    LXD_IMAGE_REMOTE,
    BASE_INSTANCE_PREFIX,
    BASE_INSTANCE_EXPIRY_DAYS,
    INSTANCE_NAME_PREFIX,
    CLOUD_INIT_TIMEOUT,
    SPACK_SETUP_SCRIPT,
    SPACK_REPO_PATH,
    SLURM_PATCH_FILES,
    BASH_HEADER,
    BASH_PREAMBLE,
    CACHE_SETUP_SCRIPT,
    PATCH_COPY_SCRIPT,
    SPACK_PROJECT_SETUP_SCRIPT,
    SPACK_BUILD_CACHE_SCRIPT,
    SPACK_INSTALL_SCRIPT,
    PACKAGE_CREATION_SCRIPT,
    COPY_OUTPUT_SCRIPT,
)


class TestSlurmVersions:
    """Test SLURM_VERSIONS constant and related functionality."""
    
    def test_slurm_versions_mapping(self):
        """Test that SLURM_VERSIONS contains expected mappings."""
        expected_versions = {
            "25.05": "25-05-1-1",
            "24.11": "24-11-6-1", 
            "23.11": "23-11-11-1",
            "23.02": "23-02-7-1",
        }
        assert SLURM_VERSIONS == expected_versions
    
    def test_slurm_versions_keys_are_strings(self):
        """Test that all keys in SLURM_VERSIONS are strings."""
        for key in SLURM_VERSIONS.keys():
            assert isinstance(key, str)
    
    def test_slurm_versions_values_are_strings(self):
        """Test that all values in SLURM_VERSIONS are strings."""
        for value in SLURM_VERSIONS.values():
            assert isinstance(value, str)


class TestSlurmVersionEnum:
    """Test SlurmVersion enum."""
    
    def test_slurm_version_enum_values(self):
        """Test that SlurmVersion enum has correct values."""
        assert SlurmVersion.v25_05 == "25.05"
        assert SlurmVersion.v24_11 == "24.11"
        assert SlurmVersion.v23_11 == "23.11"
        assert SlurmVersion.v23_02 == "23.02"
    
    def test_slurm_version_enum_consistency_with_mapping(self):
        """Test that enum values match keys in SLURM_VERSIONS."""
        enum_values = {v.value for v in SlurmVersion}
        mapping_keys = set(SLURM_VERSIONS.keys())
        assert enum_values == mapping_keys


class TestBuildTypeEnum:
    """Test BuildType enum."""
    
    def test_build_type_enum_values(self):
        """Test that BuildType enum has correct values."""
        assert BuildType.cpu == "cpu"
        assert BuildType.gpu == "gpu"
        assert BuildType.minimal == "minimal"
    
    def test_build_type_enum_completeness(self):
        """Test that all expected build types are present."""
        expected_types = {"cpu", "gpu", "minimal"}
        actual_types = {bt.value for bt in BuildType}
        assert actual_types == expected_types


class TestContainerPaths:
    """Test container path constants."""
    
    def test_container_paths_are_absolute(self):
        """Test that all container paths are absolute paths."""
        paths = [
            CONTAINER_CACHE_DIR,
            CONTAINER_PATCHES_DIR,
            CONTAINER_SPACK_PROJECT_DIR,
            CONTAINER_SLURM_DIR,
            CONTAINER_BUILD_OUTPUT_DIR,
            CONTAINER_ROOT_DIR,
            CONTAINER_SPACK_CACHE_DIR,
        ]
        for path in paths:
            assert path.startswith("/"), f"Path {path} is not absolute"
    
    def test_container_build_output_dir_derivation(self):
        """Test that CONTAINER_BUILD_OUTPUT_DIR is correctly derived."""
        expected = f"{CONTAINER_CACHE_DIR}/builds"
        assert CONTAINER_BUILD_OUTPUT_DIR == expected
    
    def test_cache_subdirs_list(self):
        """Test that CACHE_SUBDIRS contains expected directories."""
        expected_subdirs = ["spack-buildcache", "spack-sourcecache", "builds"]
        assert CACHE_SUBDIRS == expected_subdirs


class TestGetMkdirCommands:
    """Test get_mkdir_commands function."""
    
    def test_get_mkdir_commands_basic(self):
        """Test basic functionality of get_mkdir_commands."""
        base_dir = "/opt/test"
        subdirs = ["dir1", "dir2", "dir3"]
        result = get_mkdir_commands(base_dir, subdirs)
        
        expected_lines = [
            "mkdir -p /opt/test/dir1",
            "mkdir -p /opt/test/dir2", 
            "mkdir -p /opt/test/dir3"
        ]
        assert result == "\n".join(expected_lines)
    
    def test_get_mkdir_commands_empty_subdirs(self):
        """Test get_mkdir_commands with empty subdirs list."""
        result = get_mkdir_commands("/opt/test", [])
        assert result == ""
    
    def test_get_mkdir_commands_single_subdir(self):
        """Test get_mkdir_commands with single subdir."""
        result = get_mkdir_commands("/opt/test", ["single"])
        assert result == "mkdir -p /opt/test/single"
    
    def test_get_mkdir_commands_with_cache_subdirs(self):
        """Test get_mkdir_commands with actual CACHE_SUBDIRS."""
        base_dir = "/opt/cache"
        result = get_mkdir_commands(base_dir, CACHE_SUBDIRS)
        
        expected_lines = [
            "mkdir -p /opt/cache/spack-buildcache",
            "mkdir -p /opt/cache/spack-sourcecache",
            "mkdir -p /opt/cache/builds"
        ]
        assert result == "\n".join(expected_lines)


class TestLXDConfiguration:
    """Test LXD-related constants."""
    
    def test_lxd_image_constants(self):
        """Test LXD image constants."""
        assert LXD_IMAGE == "24.04"
        assert LXD_IMAGE_REMOTE == "ubuntu"
    
    def test_instance_prefixes(self):
        """Test instance name prefixes."""
        assert BASE_INSTANCE_PREFIX == "slurm-factory-base"
        assert INSTANCE_NAME_PREFIX == "slurm-factory"
    
    def test_timeouts_and_expiry(self):
        """Test timeout and expiry values."""
        assert BASE_INSTANCE_EXPIRY_DAYS == 90
        assert CLOUD_INIT_TIMEOUT == 300


class TestSpackConfiguration:
    """Test Spack-related constants."""
    
    def test_spack_paths(self):
        """Test Spack path constants."""
        assert SPACK_SETUP_SCRIPT == "/opt/spack/share/spack/setup-env.sh"
        assert SPACK_REPO_PATH == "./.spack-env/repos/builtin/spack_repo/builtin/packages/slurm/"
    
    def test_patch_files(self):
        """Test patch files list."""
        expected_files = ["slurm_prefix.patch", "package.py"]
        assert SLURM_PATCH_FILES == expected_files


class TestBashConfiguration:
    """Test Bash-related constants."""
    
    def test_bash_header(self):
        """Test BASH_HEADER constant."""
        assert BASH_HEADER == ["bash", "-c"]
    
    def test_bash_preamble(self):
        """Test BASH_PREAMBLE constant."""
        assert BASH_PREAMBLE.strip() == "set -e"


class TestTemplates:
    """Test script template constants."""
    
    def test_templates_are_template_objects(self):
        """Test that script templates are Template objects."""
        templates = [
            CACHE_SETUP_SCRIPT,
            PATCH_COPY_SCRIPT,
            SPACK_PROJECT_SETUP_SCRIPT,
            SPACK_BUILD_CACHE_SCRIPT,
            SPACK_INSTALL_SCRIPT,
            PACKAGE_CREATION_SCRIPT,
            COPY_OUTPUT_SCRIPT,
        ]
        for template in templates:
            assert isinstance(template, Template)
    
    def test_cache_setup_script_template(self):
        """Test CACHE_SETUP_SCRIPT template substitution."""
        result = CACHE_SETUP_SCRIPT.substitute(
            create_cache_dirs="mkdir -p /test/dir1\nmkdir -p /test/dir2",
            cache_dir="/test/cache"
        )
        assert "mkdir -p /test/dir1" in result
        assert "chmod -R 777 /test/cache/" in result
        assert "ls -la /test/cache/" in result
    
    def test_patch_copy_script_template(self):
        """Test PATCH_COPY_SCRIPT template substitution."""
        result = PATCH_COPY_SCRIPT.substitute(
            patches_dir="/opt/patches",
            patch_name="test.patch",
            patch_content="diff content here"
        )
        assert "mkdir -p /opt/patches" in result
        assert "cat > /opt/patches/test.patch" in result
        assert "diff content here" in result
        assert "Copied test.patch to container" in result
    
    def test_spack_project_setup_script_template(self):
        """Test SPACK_PROJECT_SETUP_SCRIPT template substitution."""
        result = SPACK_PROJECT_SETUP_SCRIPT.substitute(
            project_dir="/root/spack-project",
            spack_config="spack:\n  specs: [slurm]"
        )
        assert "mkdir -p /root/spack-project" in result
        assert "cat > /root/spack-project/spack.yaml" in result
        assert "spack:\n  specs: [slurm]" in result
    
    def test_spack_build_cache_script_template(self):
        """Test SPACK_BUILD_CACHE_SCRIPT template substitution."""
        result = SPACK_BUILD_CACHE_SCRIPT.substitute(
            project_dir="/root/spack-project",
            spack_config="spack:\n  specs: [slurm]",
            spack_setup="/opt/spack/share/spack/setup-env.sh",
            version="25.05",
            gpu_support="False",
            patches_dir="/srv/global-patches",
            spack_repo_path="./.spack-env/repos/builtin/spack_repo/builtin/packages/slurm/"
        )
        assert "mkdir -p /root/spack-project" in result
        assert "source /opt/spack/share/spack/setup-env.sh" in result
        assert "spack env activate ." in result
        assert "spack concretize -f" in result
        assert "spack install -j$(nproc)" in result
        assert "Generated dynamic Spack configuration for version 25.05 (GPU: False)" in result
    
    def test_spack_install_script_template(self):
        """Test SPACK_INSTALL_SCRIPT template substitution."""
        result = SPACK_INSTALL_SCRIPT.substitute(
            project_dir="/root/spack-project",
            spack_setup="/opt/spack/share/spack/setup-env.sh"
        )
        assert "cd /root/spack-project" in result
        assert "source /opt/spack/share/spack/setup-env.sh" in result
        assert "spack env activate ." in result
        assert "spack install --cache-only" in result
    
    def test_package_creation_script_template(self):
        """Test PACKAGE_CREATION_SCRIPT template substitution."""
        result = PACKAGE_CREATION_SCRIPT.substitute(
            project_dir="/root/spack-project",
            spack_setup="/opt/spack/share/spack/setup-env.sh",
            slurm_dir="/opt/slurm",
            version="25.05",
            slurm_spec_version="25-05-1-1"
        )
        assert "Creating redistributable package structure" in result
        assert "tar -czf /opt/slurm/redistributable/slurm-25.05-software.tar.gz" in result
        assert "tar -czf /opt/slurm/redistributable/slurm-25.05-module.tar.gz" in result
        assert "SLURM_SPEC=\"slurm@25-05-1-1\"" in result
    
    def test_copy_output_script_template(self):
        """Test COPY_OUTPUT_SCRIPT template substitution."""
        result = COPY_OUTPUT_SCRIPT.substitute(
            slurm_dir="/opt/slurm",
            version="25.05",
            output_dir="/opt/output"
        )
        assert "cp /opt/slurm/redistributable/slurm-25.05-module.tar.gz /opt/output/" in result
        assert "cp /opt/slurm/redistributable/slurm-25.05-software.tar.gz /opt/output/" in result
        assert "ls -la /opt/output/" in result


class TestTemplateRequiredVariables:
    """Test that templates require expected variables."""
    
    def test_cache_setup_script_required_vars(self):
        """Test required variables for CACHE_SETUP_SCRIPT."""
        with pytest.raises(KeyError):
            CACHE_SETUP_SCRIPT.substitute()  # Missing required variables
    
    def test_patch_copy_script_required_vars(self):
        """Test required variables for PATCH_COPY_SCRIPT."""
        with pytest.raises(KeyError):
            PATCH_COPY_SCRIPT.substitute()  # Missing required variables
    
    def test_spack_build_cache_script_required_vars(self):
        """Test required variables for SPACK_BUILD_CACHE_SCRIPT."""
        with pytest.raises(KeyError):
            SPACK_BUILD_CACHE_SCRIPT.substitute()  # Missing required variables


class TestStringTemplateIntegration:
    """Test integration between constants and string templating."""
    
    def test_template_with_container_paths(self):
        """Test using container path constants in templates."""
        # Create a simple template using our constants
        test_template = Template("Cache dir: ${cache_dir}, Patches: ${patches_dir}")
        result = test_template.substitute(
            cache_dir=CONTAINER_CACHE_DIR,
            patches_dir=CONTAINER_PATCHES_DIR
        )
        assert CONTAINER_CACHE_DIR in result
        assert CONTAINER_PATCHES_DIR in result
    
    def test_mkdir_commands_with_cache_setup(self):
        """Test integrating get_mkdir_commands with CACHE_SETUP_SCRIPT."""
        mkdir_commands = get_mkdir_commands("/opt/test", CACHE_SUBDIRS)
        result = CACHE_SETUP_SCRIPT.substitute(
            create_cache_dirs=mkdir_commands,
            cache_dir="/opt/test"
        )
        assert "mkdir -p /opt/test/spack-buildcache" in result
        assert "mkdir -p /opt/test/spack-sourcecache" in result
        assert "mkdir -p /opt/test/builds" in result
