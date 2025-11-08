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
Integration test for GCC buildcache installation with signature verification.

This test builds a Docker container to verify that:
1. GCC can be installed from buildcache without --cache-only flag
2. GPG signature verification works correctly
3. Missing dependencies can fall back to source builds
"""

import subprocess
import pytest


class TestGCCBuildcacheInstallation:
    """Integration tests for GCC buildcache installation with signature verification."""

    @pytest.mark.slow
    def test_gcc_buildcache_install_with_signature_verification(self):
        """
        Test that GCC can be installed from buildcache with signature verification enabled.
        
        This test verifies the fix for the issue where --cache-only prevented fallback
        to source builds and --no-check-signature disabled signature verification.
        
        The test builds a minimal Docker container that:
        1. Sets up Spack v1.0.0
        2. Trusts the buildcache GPG keys
        3. Installs GCC@12.5.0 from buildcache with signature verification
        4. Verifies GCC is functional
        """
        dockerfile_content = """
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

# Install basic dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    ca-certificates \\
    curl \\
    git \\
    python3 \\
    wget \\
    && rm -rf /var/lib/apt/lists/*

# Clone Spack v1.0.0
RUN git clone --depth 1 --branch v1.0.0 https://github.com/spack/spack.git /opt/spack && \\
    chown -R root:root /opt/spack && \\
    chmod -R a+rX /opt/spack

# Setup Spack environment
RUN echo 'source /opt/spack/share/spack/setup-env.sh' >> /etc/profile.d/spack.sh && \\
    chmod 644 /etc/profile.d/spack.sh

# Test installing GCC from buildcache WITH signature verification and source fallback
RUN bash -c '\\
    source /opt/spack/share/spack/setup-env.sh && \\
    echo "==> Installing buildcache keys and trusting them..." && \\
    spack buildcache keys --install --trust && \\
    echo "==> Creating temporary environment to install GCC compiler..." && \\
    mkdir -p /tmp/compiler-install && \\
    cd /tmp/compiler-install && \\
    cat > spack.yaml << "COMPILER_ENV_EOF"
spack:
  specs:
  - gcc@12.5.0 languages=c,c++,fortran
  view: /opt/spack-compiler-view
  concretizer:
    unify: false
    reuse:
      roots: true
      from:
      - type: buildcache
        path: https://slurm-factory-spack-binary-cache.vantagecompute.ai/compilers/12.5.0/buildcache
COMPILER_ENV_EOF
    echo "==> Concretizing GCC environment..." && \\
    spack -e . concretize -f && \\
    echo "==> Installing GCC compiler from buildcache (with source fallback and signature verification)..." && \\
    spack -e . install && \\
    echo "==> Verifying GCC installation..." && \\
    test -f /opt/spack-compiler-view/bin/gcc && \\
    /opt/spack-compiler-view/bin/gcc --version && \\
    echo "==> SUCCESS: GCC installed with signature verification enabled" \\
    '
"""
        
        # Write Dockerfile to temporary location
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            dockerfile_path = os.path.join(tmpdir, "Dockerfile")
            with open(dockerfile_path, "w") as f:
                f.write(dockerfile_content)
            
            # Build the Docker image
            build_cmd = [
                "docker", "build",
                "-t", "test-gcc-buildcache:latest",
                "-f", dockerfile_path,
                tmpdir
            ]
            
            print("\n==> Building Docker image to test GCC buildcache installation...")
            result = subprocess.run(
                build_cmd,
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minutes max
            )
            
            # Print output for debugging
            if result.stdout:
                print("STDOUT:", result.stdout[-2000:])  # Last 2000 chars
            if result.stderr:
                print("STDERR:", result.stderr[-2000:])  # Last 2000 chars
            
            # Verify the build succeeded
            assert result.returncode == 0, f"Docker build failed with exit code {result.returncode}"
            
            # Verify key messages in output
            assert "Installing buildcache keys and trusting them" in result.stdout or "Installing buildcache keys and trusting them" in result.stderr
            assert "Installing GCC compiler from buildcache" in result.stdout or "Installing GCC compiler from buildcache" in result.stderr
            assert "SUCCESS: GCC installed with signature verification enabled" in result.stdout or "SUCCESS: GCC installed with signature verification enabled" in result.stderr
            
            # Clean up the Docker image
            subprocess.run(
                ["docker", "rmi", "-f", "test-gcc-buildcache:latest"],
                capture_output=True,
                timeout=30
            )

    @pytest.mark.slow
    def test_gcc_install_verifies_signatures(self):
        """
        Test that signature verification is actually enabled (not using --no-check-signature).
        
        This test creates a scenario where we can verify that signature checking is active
        by ensuring the buildcache keys are trusted before installation.
        """
        test_script = """
set -e

# Install Spack
git clone --depth 1 --branch v1.0.0 https://github.com/spack/spack.git /tmp/spack
source /tmp/spack/share/spack/setup-env.sh

# Trust the buildcache keys FIRST
echo "==> Trusting buildcache keys..."
spack buildcache keys --install --trust

# List trusted keys to verify
echo "==> Listing trusted GPG keys:"
spack gpg list

# Create environment for GCC installation
mkdir -p /tmp/gcc-test
cd /tmp/gcc-test
cat > spack.yaml << 'EOF'
spack:
  specs:
  - gcc@12.5.0 languages=c,c++,fortran
  view: /tmp/gcc-view
  concretizer:
    unify: false
    reuse:
      roots: true
      from:
      - type: buildcache
        path: https://slurm-factory-spack-binary-cache.vantagecompute.ai/compilers/12.5.0/buildcache
EOF

# Install with signature verification (no --no-check-signature flag)
echo "==> Installing with signature verification enabled..."
spack -e . concretize -f
spack -e . install 2>&1 | tee /tmp/install.log

# Verify installation succeeded
if [ -f /tmp/gcc-view/bin/gcc ]; then
    echo "SUCCESS: GCC installed successfully"
    /tmp/gcc-view/bin/gcc --version
    
    # Check if any signature warnings/errors occurred
    if grep -qi "signature" /tmp/install.log; then
        echo "Signature verification was active during installation"
    fi
else
    echo "ERROR: GCC not installed"
    exit 1
fi
"""
        
        result = subprocess.run(
            ["docker", "run", "--rm", "ubuntu:24.04", "bash", "-c", 
             "apt-get update -qq && apt-get install -y -qq git ca-certificates wget build-essential > /dev/null 2>&1 && " + test_script],
            capture_output=True,
            text=True,
            timeout=1800,  # 30 minutes
        )
        
        # Print output for debugging
        print("\nTest output:")
        print(result.stdout[-3000:] if result.stdout else "No stdout")
        if result.stderr:
            print("\nStderr:")
            print(result.stderr[-1000:])
        
        # Verify the test succeeded
        assert result.returncode == 0, f"Signature verification test failed: {result.stderr}"
        assert "SUCCESS: GCC installed successfully" in result.stdout
        assert "gcc (Spack GCC)" in result.stdout or "gcc version" in result.stdout

    @pytest.mark.slow  
    def test_gcc_install_allows_source_fallback(self):
        """
        Test that installation allows source builds as fallback (no --cache-only flag).
        
        This verifies that if a package is missing from the buildcache, Spack can
        build it from source instead of failing.
        """
        test_script = """
set -e

# Install Spack
git clone --depth 1 --branch v1.0.0 https://github.com/spack/spack.git /tmp/spack
source /tmp/spack/share/spack/setup-env.sh

# Create a simple environment that uses buildcache preference but allows source builds
mkdir -p /tmp/test-fallback
cd /tmp/test-fallback
cat > spack.yaml << 'EOF'
spack:
  specs:
  - zlib@1.2.13
  concretizer:
    unify: false
    reuse:
      roots: true
      from:
      - type: buildcache
        path: https://slurm-factory-spack-binary-cache.vantagecompute.ai/compilers/12.5.0/buildcache
EOF

# Install WITHOUT --cache-only flag
# This should prefer buildcache but allow source builds
echo "==> Installing with buildcache preference and source fallback..."
spack -e . concretize -f
# Note: Not using --cache-only, so source builds are allowed
spack -e . install

# Verify installation succeeded (from buildcache OR source)
spack -e . find zlib
echo "SUCCESS: Installation completed (buildcache or source build)"
"""
        
        result = subprocess.run(
            ["docker", "run", "--rm", "ubuntu:24.04", "bash", "-c",
             "apt-get update -qq && apt-get install -y -qq git ca-certificates wget build-essential > /dev/null 2>&1 && " + test_script],
            capture_output=True,
            text=True,
            timeout=600,  # 10 minutes
        )
        
        print("\nFallback test output:")
        print(result.stdout[-2000:] if result.stdout else "No stdout")
        
        # Verify success
        assert result.returncode == 0, f"Source fallback test failed: {result.stderr}"
        assert "SUCCESS: Installation completed" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
