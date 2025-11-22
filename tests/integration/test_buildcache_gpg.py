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

"""Unit tests for GPG key import functionality in buildcache operations."""

import base64
import os
from unittest.mock import Mock, patch

import pytest

from slurm_factory.exceptions import SlurmFactoryError
from slurm_factory.builders.slurm_builder import _push_slurm_to_buildcache

# Create alias for the test
push_to_buildcache = _push_slurm_to_buildcache


class TestGPGKeyImport:
    """Test GPG key import functionality for buildcache operations."""

    @pytest.fixture
    def mock_gpg_key(self):
        """Create a mock GPG private key (base64 encoded)."""
        # This is a fake key for testing purposes only
        fake_key = "-----BEGIN PGP PRIVATE KEY BLOCK-----\nFAKE KEY DATA\n-----END PGP PRIVATE KEY BLOCK-----"
        return base64.b64encode(fake_key.encode()).decode()

    @pytest.fixture
    def mock_gpg_passphrase(self):
        """Create a mock GPG passphrase."""
        return "test_passphrase"

    @pytest.fixture
    def mock_aws_env(self):
        """Create mock AWS environment variables."""
        return {
            "AWS_ACCESS_KEY_ID": "test_key_id",
            "AWS_SECRET_ACCESS_KEY": "test_secret_key",
            "AWS_SESSION_TOKEN": "test_session_token",
            "AWS_DEFAULT_REGION": "us-east-1",
        }

    def test_push_to_buildcache_gpg_configuration(self, mock_gpg_key, mock_gpg_passphrase, mock_aws_env):
        """Test that push_to_buildcache configures GPG correctly for non-interactive use."""
        with patch.dict(os.environ, mock_aws_env), patch("subprocess.run") as mock_run:
            # Mock successful subprocess run
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            # Call the function with GPG key
            push_to_buildcache(
                image_tag="test:latest",
                slurm_version="25.11",
                toolchain="noble",
                publish_mode="all",
                signing_key="0xTESTKEY",
                gpg_private_key=mock_gpg_key,
                gpg_passphrase=mock_gpg_passphrase,
            )

            # Verify subprocess.run was called
            assert mock_run.called

            # Get the command that was executed
            call_args = mock_run.call_args
            cmd = call_args[0][0]

            # Verify docker run command structure
            assert "docker" in cmd
            assert "run" in cmd
            assert "--rm" in cmd

            # Verify GPG key is passed as environment variable
            assert any("GPG_PRIVATE_KEY" in arg for arg in cmd)

            # Verify the bash script contains GPG configuration
            bash_script = cmd[-1]  # Last argument should be the bash script

            # Check for GPG configuration commands (updated for new implementation)
            assert "allow-loopback-pinentry" in bash_script
            assert "gpg-agent.conf" in bash_script
            assert "gpg.conf" in bash_script
            # New implementation uses spack gpg trust instead of manual import
            assert "spack gpg trust" in bash_script
            assert "/tmp/gpg-key.asc" in bash_script
            assert "--pinentry-mode loopback" in bash_script
            # GPG wrapper for non-interactive signing
            assert "gpg-real" in bash_script
            assert "/tmp/gpg-passphrase.txt" in bash_script

    def test_push_to_buildcache_without_gpg_key(self, mock_aws_env):
        """Test that push_to_buildcache works without GPG key (unsigned mode)."""
        with patch.dict(os.environ, mock_aws_env), patch("subprocess.run") as mock_run:
            # Mock successful subprocess run
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            # Call the function without GPG key
            push_to_buildcache(
                image_tag="test:latest",
                slurm_version="25.11",
                toolchain="noble",
                publish_mode="all",
                signing_key=None,
                gpg_private_key=None,
                gpg_passphrase=None,
            )

            # Get the bash script
            call_args = mock_run.call_args
            cmd = call_args[0][0]
            bash_script = cmd[-1]

            # Verify no GPG configuration when key is not provided
            assert "GPG_TTY" not in bash_script
            assert "allow-loopback-pinentry" not in bash_script
            assert "--unsigned" in bash_script

    def test_gpg_agent_kill_and_restart(self, mock_gpg_key, mock_gpg_passphrase, mock_aws_env):
        """Test that GPG agent is killed and restarted to ensure clean configuration state."""
        with patch.dict(os.environ, mock_aws_env), patch("subprocess.run") as mock_run:
            # Mock successful subprocess run
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            # Call the function with GPG key
            push_to_buildcache(
                image_tag="test:latest",
                slurm_version="25.11",
                toolchain="noble",
                publish_mode="all",
                signing_key="0xTESTKEY",
                gpg_private_key=mock_gpg_key,
                gpg_passphrase=mock_gpg_passphrase,
            )

            # Get the bash script
            call_args = mock_run.call_args
            cmd = call_args[0][0]
            bash_script = cmd[-1]

            # Verify gpgconf --kill is present to ensure clean agent state
            assert "gpgconf" in bash_script
            assert "--kill gpg-agent" in bash_script
            # Verify gpg-connect-agent starts fresh agent
            assert "gpg-connect-agent" in bash_script
            # Should have '|| true' to prevent failure if agent is not running
            assert "|| true" in bash_script

    def test_signing_key_parameter_used(self, mock_gpg_key, mock_gpg_passphrase, mock_aws_env):
        """Test that signing key parameter is properly used in buildcache push command."""
        with patch.dict(os.environ, mock_aws_env), patch("subprocess.run") as mock_run:
            # Mock successful subprocess run
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            test_signing_key = "0xABCD1234"

            # Call the function with specific signing key
            push_to_buildcache(
                image_tag="test:latest",
                slurm_version="25.11",
                toolchain="noble",
                publish_mode="all",
                signing_key=test_signing_key,
                gpg_private_key=mock_gpg_key,
                gpg_passphrase=mock_gpg_passphrase,
            )

            # Get the bash script
            call_args = mock_run.call_args
            cmd = call_args[0][0]
            bash_script = cmd[-1]

            # Verify signing key is used in push command
            assert f"--key {test_signing_key}" in bash_script

    def test_gpg_homedir_consistency(self, mock_gpg_key, mock_gpg_passphrase, mock_aws_env):
        """Test that GPG homedir is consistent throughout the script."""
        with patch.dict(os.environ, mock_aws_env), patch("subprocess.run") as mock_run:
            # Mock successful subprocess run
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            # Call the function with GPG key
            push_to_buildcache(
                image_tag="test:latest",
                slurm_version="25.11",
                toolchain="noble",
                publish_mode="all",
                signing_key="0xTESTKEY",
                gpg_private_key=mock_gpg_key,
                gpg_passphrase=mock_gpg_passphrase,
            )

            # Get the bash script
            call_args = mock_run.call_args
            cmd = call_args[0][0]
            bash_script = cmd[-1]

            # Expected GPG homedir used by Spack (updated to match actual implementation)
            expected_homedir = "/opt/spack/opt/spack/gpg"

            # Verify homedir is used consistently
            script_lines = bash_script.split(" && ")
            gpg_commands = [line for line in script_lines if "gpg" in line and "homedir" in line]

            # All GPG commands should use the same homedir
            for cmd in gpg_commands:
                if "--homedir" in cmd or "homedir" in cmd:
                    assert expected_homedir in cmd


class TestGPGErrorHandling:
    """Test error handling for GPG operations."""

    @pytest.fixture
    def mock_gpg_key(self):
        """Create a mock GPG private key (base64 encoded)."""
        fake_key = "-----BEGIN PGP PRIVATE KEY BLOCK-----\nFAKE KEY DATA\n-----END PGP PRIVATE KEY BLOCK-----"
        return base64.b64encode(fake_key.encode()).decode()

    @pytest.fixture
    def mock_gpg_passphrase(self):
        """Create a mock GPG passphrase."""
        return "test_passphrase"

    @pytest.fixture
    def mock_aws_env(self):
        """Create mock AWS environment variables."""
        return {
            "AWS_ACCESS_KEY_ID": "test_key_id",
            "AWS_SECRET_ACCESS_KEY": "test_secret_key",
        }

    def test_push_to_buildcache_subprocess_error(self, mock_gpg_key, mock_gpg_passphrase, mock_aws_env):
        """Test that subprocess errors are properly handled and reported."""
        with patch.dict(os.environ, mock_aws_env), patch("subprocess.run") as mock_run:
            # Mock subprocess error with GPG failure
            mock_run.return_value = Mock(
                returncode=1,
                stdout="Some output",
                stderr="gpg: signing failed: Inappropriate ioctl for device",
            )

            # Should raise SlurmFactoryError with appropriate message
            with pytest.raises(SlurmFactoryError) as exc_info:
                push_to_buildcache(
                    image_tag="test:latest",
                    slurm_version="25.11",
                    toolchain="noble",
                    publish_mode="all",
                    signing_key="0xTESTKEY",
                    gpg_private_key=mock_gpg_key,
                    gpg_passphrase=mock_gpg_passphrase,
                )

            # Verify error message contains information about the failure
            assert "Failed to push to buildcache" in str(exc_info.value)

    def test_missing_aws_credentials(self, mock_gpg_key, mock_gpg_passphrase):
        """Test that missing AWS credentials are properly detected."""
        with patch.dict(os.environ, {}, clear=True), patch("pathlib.Path.exists") as mock_exists:
            # Mock that ~/.aws directory doesn't exist
            mock_exists.return_value = False

            # Should raise SlurmFactoryError about missing credentials
            with pytest.raises(SlurmFactoryError) as exc_info:
                push_to_buildcache(
                    image_tag="test:latest",
                    slurm_version="25.11",
                    toolchain="noble",
                    publish_mode="all",
                    signing_key="0xTESTKEY",
                    gpg_private_key=mock_gpg_key,
                    gpg_passphrase=mock_gpg_passphrase,
                )

            # Verify error message mentions AWS credentials
            assert "AWS credentials not found" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
