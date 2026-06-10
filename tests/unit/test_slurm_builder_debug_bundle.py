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

"""Unit tests for Slurm build debug bundle helpers."""

from pathlib import Path
from unittest.mock import patch

from slurm_factory.builders.slurm_builder import (
    _collect_spack_failure_debug_bundle,
    _prepare_build_debug_bundle,
)
from slurm_factory.config import Settings


class TestSlurmBuilderDebugBundle:
    """Test stable debug bundle helpers."""

    def test_prepare_build_debug_bundle_writes_generated_inputs(self, tmp_path: Path):
        """Generated inputs should be written to the stable debug bundle path."""
        with patch("pathlib.Path.home", return_value=tmp_path):
            settings = Settings(project_name="test")

            debug_dir = _prepare_build_debug_bundle(
                settings=settings,
                toolchain="resolute",
                slurm_version="26.05",
                spack_yaml="spack:\n  specs: []\n",
                build_script="echo building\n",
            )

        expected_dir = tmp_path / ".slurm-factory" / "build-debug" / "resolute" / "26.05"

        assert debug_dir == expected_dir
        assert (debug_dir / "spack.yaml").read_text() == "spack:\n  specs: []\n"
        assert (debug_dir / "build-script.sh").read_text() == "echo building\n"

    def test_collect_spack_failure_debug_bundle_copies_curated_logs(self, tmp_path: Path):
        """Only curated Spack diagnostic files should be copied into the bundle."""
        stage_dir = tmp_path / "spack-stage"
        package_dir = stage_dir / "root" / "spack-stage-abc123" / "slurm-26.05"
        package_dir.mkdir(parents=True)
        (package_dir / "spack-build-out.txt").write_text("build output")
        (package_dir / "spack-build-env.txt").write_text("build env")
        (package_dir / "config.log").write_text("configure log")
        (package_dir / "ignored.txt").write_text("ignore me")

        debug_dir = tmp_path / "build-debug" / "resolute" / "26.05"

        copied_files = _collect_spack_failure_debug_bundle(stage_dir, debug_dir)

        assert copied_files == 3
        copied_dir = debug_dir / "spack-stage" / "root" / "spack-stage-abc123" / "slurm-26.05"

        assert (copied_dir / "spack-build-out.txt").read_text() == "build output"
        assert (copied_dir / "spack-build-env.txt").read_text() == "build env"
        assert (copied_dir / "config.log").read_text() == "configure log"
        assert not (copied_dir / "ignored.txt").exists()

    def test_collect_spack_failure_debug_bundle_tolerates_missing_stage_dir(self, tmp_path: Path):
        """Missing stage directories should not raise an exception."""
        copied_files = _collect_spack_failure_debug_bundle(
            tmp_path / "missing-stage",
            tmp_path / "build-debug" / "resolute" / "26.05",
        )

        assert copied_files == 0
