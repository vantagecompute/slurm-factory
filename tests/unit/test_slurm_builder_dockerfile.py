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

"""Tests for generated Slurm build Dockerfiles."""

from slurm_factory.builders.slurm_builder import _get_slurm_base_dockerfile


class TestSlurmBaseDockerfile:
    """Test generated base Dockerfile content."""

    def test_resolute_spack_python_has_boto3(self):
        """Resolute uses a Python 3.12 venv with boto3 for Spack S3 buildcache support."""
        dockerfile = _get_slurm_base_dockerfile("resolute")

        assert "apt-get install -y python3.12 python3.12-venv" in dockerfile
        assert "ENV SPACK_PYTHON=/opt/spack-python/bin/python" in dockerfile
        assert "/usr/bin/python3.12 -m venv /opt/spack-python" in dockerfile
        assert "/opt/spack-python/bin/python -m pip install boto3" in dockerfile
        assert "/opt/spack-python/bin/python -c \"import boto3\"" in dockerfile

    def test_non_resolute_spack_python_has_boto3(self):
        """Non-Resolute images install boto3 through the interpreter Spack will run."""
        dockerfile = _get_slurm_base_dockerfile("noble")

        assert "ENV SPACK_PYTHON" not in dockerfile
        assert 'python_for_spack="${SPACK_PYTHON:-$(command -v python3)}"' in dockerfile
        assert 'PIP_BREAK_SYSTEM_PACKAGES=1 "$python_for_spack" -m pip install boto3' in dockerfile
        assert '"$python_for_spack" -c "import boto3"' in dockerfile
