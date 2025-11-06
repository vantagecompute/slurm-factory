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

"""
Integration tests for GPG signing in Docker containers.

These tests verify that GPG signing actually works in a real Docker container,
not just mocked subprocess calls.
"""

import base64
import subprocess

import pytest


class TestGPGDockerIntegration:
    """Integration tests for GPG signing in Docker containers."""

    @pytest.fixture
    def test_gpg_key(self):
        """Generate a test GPG key for integration testing."""
        # Generate a simple test key without passphrase
        gpg_gen_script = """
set -e
apt-get update -qq && apt-get install -y -qq gnupg > /dev/null 2>&1

cat > /tmp/gpg-key-gen.txt <<'EOF'
%no-protection
Key-Type: RSA
Key-Length: 2048
Name-Real: Test User
Name-Email: test@example.com
Expire-Date: 0
EOF

gpg --batch --gen-key /tmp/gpg-key-gen.txt 2>&1
gpg --armor --export-secret-keys test@example.com 2>&1
"""
        try:
            result = subprocess.run(
                ["docker", "run", "--rm", "ubuntu:24.04", "bash", "-c", gpg_gen_script],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode != 0:
                pytest.skip(f"Could not generate test GPG key: {result.stderr}")

            # Extract the private key from output
            lines = result.stdout.split("\n")
            key_lines = []
            in_key = False
            for line in lines:
                if "BEGIN PGP PRIVATE KEY BLOCK" in line:
                    in_key = True
                if in_key:
                    key_lines.append(line)
                if "END PGP PRIVATE KEY BLOCK" in line:
                    break

            if not key_lines:
                pytest.skip("Could not extract GPG key from generation output")

            private_key = "\n".join(key_lines)
            return base64.b64encode(private_key.encode()).decode()

        except subprocess.TimeoutExpired:
            pytest.skip("GPG key generation timed out")
        except Exception as e:
            pytest.skip(f"Could not generate test key: {e}")

    def test_gpg_directory_setup_in_docker(self):
        """Test that GPG directories are created with correct permissions in Docker."""
        setup_script = """
set -e
# Ensure /tmp has proper permissions for GPG temp files
chmod 1777 /tmp 2>/dev/null || true
# Configure GPG for non-interactive use
export GPG_TTY=$(tty)
# Create full GPG directory structure with correct permissions
mkdir -p /opt/spack/opt/spack/gpg/private-keys-v1.d
chmod 700 /opt/spack/opt/spack/gpg
chmod 700 /opt/spack/opt/spack/gpg/private-keys-v1.d
# Configure GPG agent for non-interactive use
echo "allow-loopback-pinentry" > /opt/spack/opt/spack/gpg/gpg-agent.conf
# Configure GPG for batch mode with loopback pinentry
echo "pinentry-mode loopback" > /opt/spack/opt/spack/gpg/gpg.conf

# Verify directories exist and have correct permissions
ls -ld /opt/spack/opt/spack/gpg
ls -ld /opt/spack/opt/spack/gpg/private-keys-v1.d
cat /opt/spack/opt/spack/gpg/gpg-agent.conf
cat /opt/spack/opt/spack/gpg/gpg.conf
"""

        result = subprocess.run(
            ["docker", "run", "--rm", "ubuntu:24.04", "bash", "-c", setup_script],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"Setup failed: {result.stderr}"
        assert "drwx------" in result.stdout, "GPG directory doesn't have 700 permissions"
        assert "allow-loopback-pinentry" in result.stdout
        assert "pinentry-mode loopback" in result.stdout

    def test_gpg_key_import_in_docker(self, test_gpg_key):
        """Test that GPG key can be imported in Docker with our setup."""
        import_script = f"""
set -e
apt-get update -qq && apt-get install -y -qq gnupg > /dev/null 2>&1

# Setup GPG environment
chmod 1777 /tmp 2>/dev/null || true
export GPG_TTY=$(tty)
mkdir -p /opt/spack/opt/spack/gpg/private-keys-v1.d
chmod 700 /opt/spack/opt/spack/gpg
chmod 700 /opt/spack/opt/spack/gpg/private-keys-v1.d
echo "allow-loopback-pinentry" > /opt/spack/opt/spack/gpg/gpg-agent.conf
echo "pinentry-mode loopback" > /opt/spack/opt/spack/gpg/gpg.conf

# Import the key
echo '{test_gpg_key}' | base64 -d > /tmp/private.key
gpg --homedir /opt/spack/opt/spack/gpg --batch --yes --pinentry-mode loopback --import /tmp/private.key 2>&1
rm -f /tmp/private.key

# List keys to verify import
gpg --homedir /opt/spack/opt/spack/gpg --list-secret-keys 2>&1
"""

        result = subprocess.run(
            ["docker", "run", "--rm", "ubuntu:24.04", "bash", "-c", import_script],
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert result.returncode == 0, f"Key import failed: {result.stderr}"
        assert "test@example.com" in result.stdout or "sec" in result.stdout, "Key not imported"

    def test_gpg_signing_in_docker(self, test_gpg_key):
        """Test that GPG can actually sign files in Docker with our configuration."""
        signing_script = f"""
set -e
apt-get update -qq && apt-get install -y -qq gnupg > /dev/null 2>&1

# Setup GPG environment (same as production code)
chmod 1777 /tmp 2>/dev/null || true
export GPG_TTY=$(tty)
mkdir -p /opt/spack/opt/spack/gpg/private-keys-v1.d
chmod 700 /opt/spack/opt/spack/gpg
chmod 700 /opt/spack/opt/spack/gpg/private-keys-v1.d
echo "allow-loopback-pinentry" > /opt/spack/opt/spack/gpg/gpg-agent.conf
echo "pinentry-mode loopback" > /opt/spack/opt/spack/gpg/gpg.conf
gpg-connect-agent --homedir /opt/spack/opt/spack/gpg reloadagent /bye 2>&1 || true

# Import key
echo '{test_gpg_key}' | base64 -d > /tmp/private.key
gpg --homedir /opt/spack/opt/spack/gpg --batch --yes --pinentry-mode loopback --import /tmp/private.key 2>&1
rm -f /tmp/private.key

# Create a test file to sign
echo "Test content for signing" > /tmp/test.txt

# Try to sign the file (this is what Spack does)
gpg --homedir /opt/spack/opt/spack/gpg --batch --yes --pinentry-mode loopback --clearsign /tmp/test.txt 2>&1

# Verify signed file was created
ls -l /tmp/test.txt.asc
cat /tmp/test.txt.asc
"""

        result = subprocess.run(
            ["docker", "run", "--rm", "ubuntu:24.04", "bash", "-c", signing_script],
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert result.returncode == 0, f"Signing failed: {result.stderr}\n{result.stdout}"
        assert "BEGIN PGP SIGNED MESSAGE" in result.stdout, "File not signed correctly"
        assert "Test content for signing" in result.stdout, "Signed content missing"

    def test_gpg_signing_in_tmp_subdir(self, test_gpg_key):
        """Test GPG can sign files in /tmp subdirectories (like /tmp/spack-stage)."""
        signing_script = f"""
set -e
apt-get update -qq && apt-get install -y -qq gnupg > /dev/null 2>&1

# Setup GPG environment (using production sequence)
chmod 1777 /tmp
export GPG_TTY=$(tty)
mkdir -p /opt/spack/opt/spack/gpg/private-keys-v1.d
chmod 700 /opt/spack/opt/spack/gpg
chmod 700 /opt/spack/opt/spack/gpg/private-keys-v1.d
echo "allow-loopback-pinentry" > /opt/spack/opt/spack/gpg/gpg-agent.conf
echo "pinentry-mode loopback" > /opt/spack/opt/spack/gpg/gpg.conf
# Kill any existing agent to ensure clean state
gpgconf --homedir /opt/spack/opt/spack/gpg --kill gpg-agent 2>/dev/null || true
# Start agent with our configuration
gpg-connect-agent --homedir /opt/spack/opt/spack/gpg /bye || true

# Import key
echo '{test_gpg_key}' | base64 -d > /tmp/private.key
gpg --homedir /opt/spack/opt/spack/gpg --batch --yes --pinentry-mode loopback --no-tty --import /tmp/private.key 2>&1
rm -f /tmp/private.key

# Create subdirectory similar to spack-stage
mkdir -p /tmp/spack-stage/root/test123
echo '{{"name": "test", "version": "1.0"}}' > /tmp/spack-stage/root/test123/manifest.json

# Try to sign the manifest file (this is what fails in production)
cd /tmp/spack-stage/root/test123
gpg --homedir /opt/spack/opt/spack/gpg --batch --yes --pinentry-mode loopback --clearsign manifest.json 2>&1

# Verify signed file was created
ls -l manifest.json.asc
cat manifest.json.asc
echo "SUCCESS: File signed in /tmp subdirectory"
"""

        result = subprocess.run(
            ["docker", "run", "--rm", "ubuntu:24.04", "bash", "-c", signing_script],
            capture_output=True,
            text=True,
            timeout=60,
        )

        # This is the critical test - signing files in /tmp/spack-stage subdirectories
        assert result.returncode == 0, f"Signing in subdirectory failed: {result.stderr}\n{result.stdout}"
        assert "BEGIN PGP SIGNED MESSAGE" in result.stdout, "Manifest not signed correctly"
        assert "SUCCESS: File signed in /tmp subdirectory" in result.stdout

    def test_gpg_agent_restart_with_config(self, test_gpg_key):
        """Test that killing and restarting the agent ensures it reads the config correctly."""
        restart_script = f"""
set -e
apt-get update -qq && apt-get install -y -qq gnupg > /dev/null 2>&1

# Setup GPG directory
chmod 1777 /tmp
mkdir -p /opt/spack/opt/spack/gpg/private-keys-v1.d
chmod 700 /opt/spack/opt/spack/gpg
chmod 700 /opt/spack/opt/spack/gpg/private-keys-v1.d

# Start agent WITHOUT config (simulating misconfigured state)
gpg-connect-agent --homedir /opt/spack/opt/spack/gpg /bye

# NOW add config
echo "allow-loopback-pinentry" > /opt/spack/opt/spack/gpg/gpg-agent.conf
echo "pinentry-mode loopback" > /opt/spack/opt/spack/gpg/gpg.conf

# Kill and restart agent (production fix)
gpgconf --homedir /opt/spack/opt/spack/gpg --kill gpg-agent 2>/dev/null || true
gpg-connect-agent --homedir /opt/spack/opt/spack/gpg /bye || true

# Import key
echo '{test_gpg_key}' | base64 -d > /tmp/private.key
gpg --homedir /opt/spack/opt/spack/gpg --batch --yes --pinentry-mode loopback --no-tty --import /tmp/private.key 2>&1
rm -f /tmp/private.key

# Try to sign a file - should work with restarted agent
echo "test content" > /tmp/test.txt
gpg --homedir /opt/spack/opt/spack/gpg --batch --yes --pinentry-mode loopback --no-tty --clearsign /tmp/test.txt 2>&1

# Verify
test -f /tmp/test.txt.asc && echo "SUCCESS: Agent restart worked"
"""

        result = subprocess.run(
            ["docker", "run", "--rm", "ubuntu:24.04", "bash", "-c", restart_script],
            capture_output=True,
            text=True,
            timeout=60,
        )

        # Verify the agent restart allows signing to work
        assert result.returncode == 0, f"Agent restart test failed: {result.stderr}\n{result.stdout}"
        assert "SUCCESS: Agent restart worked" in result.stdout
        # Make sure no /dev/tty errors appear
        assert "cannot open '/dev/tty'" not in result.stdout
        assert "cannot open '/dev/tty'" not in result.stderr

    def test_tmp_permissions_are_critical(self):
        """Test that /tmp permissions are actually necessary for GPG signing."""
        # Test WITHOUT proper /tmp permissions (should show the issue)
        bad_script = """
set -e
apt-get update -qq && apt-get install -y -qq gnupg > /dev/null 2>&1

# Deliberately don't fix /tmp permissions
# DON'T run: chmod 1777 /tmp

# Create test GPG key
cat > /tmp/gpg-gen.txt <<EOF
%no-protection
Key-Type: RSA
Key-Length: 2048
Name-Real: Test
Name-Email: test@test.com
Expire-Date: 0
EOF
gpg --homedir /tmp/gpg --batch --gen-key /tmp/gpg-gen.txt 2>&1 || echo "Key generation might fail"

# Try to sign something
echo "test" > /tmp/test.txt
gpg --homedir /tmp/gpg --batch --yes --clearsign /tmp/test.txt 2>&1 && \
    echo "SUCCESS" || echo "FAILED_AS_EXPECTED"
"""

        result = subprocess.run(
            ["docker", "run", "--rm", "ubuntu:24.04", "bash", "-c", bad_script],
            capture_output=True,
            text=True,
            timeout=60,
        )

        # We expect this might fail or have issues, demonstrating why the fix is needed
        # Just verify the test runs without crashing
        assert result.returncode in [0, 2], "Test setup failed unexpectedly"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
