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

"""Unit tests for slurm_factory.builders module."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from slurm_factory.builders import slurm_builder
from slurm_factory.config import Settings
from slurm_factory.exceptions import SlurmFactoryError


class TestSlurmBuilderModule:
    """Test the slurm_builder module structure and exports."""

    def test_module_imports(self):
        """Test that the slurm_builder module imports successfully."""
        assert hasattr(slurm_builder, 'create_slurm_package')
        assert callable(slurm_builder.create_slurm_package)

    def test_module_docstring(self):
        """Test that the module has a docstring."""
        assert slurm_builder.__doc__ is not None
        assert len(slurm_builder.__doc__) > 0

    def test_create_slurm_package_function_exists(self):
        """Test that the create_slurm_package function exists and is callable."""
        assert hasattr(slurm_builder, 'create_slurm_package')
        assert callable(slurm_builder.create_slurm_package)

    def test_get_module_template_content_exists(self):
        """Test that helper functions exist."""
        assert hasattr(slurm_builder, 'get_module_template_content')
        assert callable(slurm_builder.get_module_template_content)

    def test_sanitize_build_namespace(self):
        """Build namespaces should be safe for filesystem and container paths."""
        namespace = slurm_builder._sanitize_build_namespace("registry.local/slurm-factory:build 26.05")

        assert namespace == "registry.local-slurm-factory-build-26.05"

    def test_build_script_uses_configured_lmod_root(self):
        """Generated build script should read modules from the configured writable Lmod root."""
        script = slurm_builder.get_slurm_build_script(
            "noble",
            "26.05",
            lmod_root="/opt/slurm/builds/build-123/lmod",
        )

        assert "find /opt/slurm/builds/build-123/lmod -type f -name '*.lua'" in script
        assert 'basename "$(dirname "$f")"' in script
        assert '" = "slurm"' in script
        assert "case $f in *slurm*)" not in script
        assert 'spack -e . install -j "$JOBS" --reuse-deps --verbose' in script
        assert "spack -e . install -j $(nproc)" not in script
        assert "share/spack/lmod" not in script

    def test_build_script_removes_dependency_loads_from_redistributable_modules(self):
        """Tarball modulefiles should not require dependency modulefiles absent from the tarball."""
        script = slurm_builder.get_slurm_build_script("noble", "26.05")

        assert "depends_on|prereq|always_load|load" in script
        assert "sed -i.bak -E" in script
        assert 'rm -f "$module_file.bak"' in script

    @patch("slurm_factory.builders.slurm_builder.subprocess.run")
    @patch("slurm_factory.builders.slurm_builder.remove_old_docker_image")
    @patch("slurm_factory.builders.slurm_builder.build_docker_image")
    @patch("slurm_factory.builders.slurm_builder._run_spack_build_in_container")
    @patch("slurm_factory.builders.slurm_builder.generate_yaml_string", return_value="spack:\n  specs: []\n")
    def test_create_slurm_package_generates_namespaced_spack_roots(
        self,
        mock_generate_yaml_string,
        mock_run_spack_build,
        mock_build_docker_image,
        mock_remove_old_docker_image,
        mock_subprocess_run,
        tmp_path: Path,
    ):
        """The mounted spack.yaml should use paths unique to the generated container name."""
        mock_subprocess_run.return_value = Mock(returncode=0, stdout="", stderr="")

        with patch.dict("os.environ", {"SLURM_FACTORY_CACHE_DIR": str(tmp_path)}):
            settings = Settings(project_name="test")
            slurm_builder.create_slurm_package(
                image_tag="slurm-factory:build-26-05-abc12345",
                settings=settings,
                slurm_version="26.05",
                toolchain="noble",
            )

        expected_namespace = "slurm-factory-build-26-05-abc12345"
        expected_build_root = f"/opt/slurm/builds/{expected_namespace}"

        mock_generate_yaml_string.assert_called_once()
        yaml_kwargs = mock_generate_yaml_string.call_args.kwargs

        assert yaml_kwargs["install_tree_root"] == f"{expected_build_root}/software"
        assert yaml_kwargs["view_root"] == f"{expected_build_root}/view"
        assert yaml_kwargs["build_stage_root"] == f"/opt/spack-stage/{expected_namespace}"
        assert yaml_kwargs["source_cache_root"] == f"/opt/spack-stage/{expected_namespace}/source-cache"
        assert yaml_kwargs["misc_cache_root"] == f"/opt/slurm-factory-cache/source/misc/{expected_namespace}"
        assert yaml_kwargs["lmod_root"] == f"{expected_build_root}/lmod"
        assert yaml_kwargs["architecture"] == slurm_builder._get_normalized_architecture()

        mock_build_docker_image.assert_called_once()
        mock_run_spack_build.assert_called_once()
        mock_remove_old_docker_image.assert_any_call("slurm-factory:build-26-05-abc12345")
        mock_remove_old_docker_image.assert_any_call("slurm-factory:build-26-05-abc12345-base")

    @patch("slurm_factory.builders.slurm_builder.get_module_template_content", return_value="template")
    @patch("slurm_factory.builders.slurm_builder.subprocess.run")
    def test_run_spack_build_mounts_namespaced_stage_and_cache_env(
        self,
        mock_subprocess_run,
        mock_get_module_template,
        tmp_path: Path,
    ):
        """The live Docker container should receive per-build Spack stage/cache paths."""
        mock_subprocess_run.side_effect = [
            Mock(returncode=0, stdout="", stderr=""),
            Mock(returncode=1, stdout="", stderr=""),
        ]

        with patch.dict("os.environ", {"SLURM_FACTORY_CACHE_DIR": str(tmp_path)}):
            settings = Settings(project_name="test")

            with pytest.raises(SlurmFactoryError):
                slurm_builder._run_spack_build_in_container(
                    container_name="slurm-factory-build-26-05-abc12345",
                    base_image="slurm-factory:build-26-05-abc12345-base",
                    settings=settings,
                    spack_yaml="spack:\n  specs: []\n",
                    toolchain="noble",
                    slurm_version="26.05",
                    gpu_support=False,
                )

        docker_run_cmd = mock_subprocess_run.call_args_list[0].args[0]
        exec_build_cmd = mock_subprocess_run.call_args_list[1].args[0]
        expected_namespace = "slurm-factory-build-26-05-abc12345"
        expected_stage_mount = f"{tmp_path}/spack-stage/noble/26.05:/opt/spack-stage"
        expected_inputs_dir = f"{tmp_path}/container-inputs/{expected_namespace}"

        assert expected_stage_mount in docker_run_cmd
        assert f"{expected_inputs_dir}/spack.yaml:/root/spack-project/spack.yaml.mount:ro" in docker_run_cmd
        assert (
            f"{expected_inputs_dir}/build-script.sh:/root/spack-project/build-script.sh:ro"
            in docker_run_cmd
        )
        for dns_server in slurm_builder.DOCKER_DNS_SERVERS:
            dns_server_index = docker_run_cmd.index(dns_server)
            assert docker_run_cmd[dns_server_index - 1] == "--dns"
        assert "/root/spack-project/build-script.sh" in exec_build_cmd
        assert f"SPACK_USER_CACHE_PATH=/opt/spack-stage/{expected_namespace}/user-cache" in docker_run_cmd
        assert f"TMPDIR=/opt/spack-stage/{expected_namespace}/tmp" in docker_run_cmd
        assert f"TMP=/opt/spack-stage/{expected_namespace}/tmp" in docker_run_cmd
        assert f"TEMP=/opt/spack-stage/{expected_namespace}/tmp" in docker_run_cmd
