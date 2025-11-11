# Test Dockerfile to validate compiler detection fix
# This simulates the GitHub Actions Ubuntu environment

FROM ubuntu:24.04

# Install system dependencies (similar to GitHub Actions runner)
RUN apt-get update && apt-get install -y \
    build-essential \
    gfortran \
    git \
    curl \
    python3 \
    python3-pip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set up test environment
WORKDIR /test

# Clone Spack v1.0.0 (same as workflow)
RUN git clone --depth 1 --branch v1.0.0 https://github.com/spack/spack.git

# Set up Spack environment variables
ENV SPACK_ROOT=/test/spack
ENV PATH="${SPACK_ROOT}/bin:${PATH}"
ENV SPACK_USER_CACHE_PATH=/test/spack-cache
ENV SPACK_USER_CONFIG_PATH=/test/spack-config

RUN mkdir -p "${SPACK_USER_CACHE_PATH}" "${SPACK_USER_CONFIG_PATH}"

# Test script that mimics the workflow steps
RUN cat > /test/test-compiler-detection.sh <<'TESTSCRIPT'
#!/bin/bash
set -e

echo "=== Testing Compiler Detection Fix ==="
echo ""

# Verify spack works
echo "1. Verifying Spack installation..."
spack --version
echo "✓ Spack is working"
echo ""

# Configure system compiler directly (skip auto-detection for reliability)
echo "2. Configuring system compiler..."
GCC_VERSION=$(gcc -dumpversion)
echo "Detected system GCC version: ${GCC_VERSION}"

# Create compiler configuration
mkdir -p "$SPACK_USER_CONFIG_PATH/linux"
cat > "$SPACK_USER_CONFIG_PATH/linux/compilers.yaml" <<EOF
compilers:
- compiler:
    spec: gcc@${GCC_VERSION}
    paths:
      cc: /usr/bin/gcc
      cxx: /usr/bin/g++
      f77: /usr/bin/gfortran
      fc: /usr/bin/gfortran
    flags: {}
    operating_system: ubuntu24.04
    target: x86_64
    modules: []
    environment: {}
    extra_rpaths: []
EOF

echo "✓ Configured GCC ${GCC_VERSION}"
echo ""

# Verify compiler configuration
echo "3. Checking for configured compilers..."
spack compiler list
echo ""

# Verify we can use the compiler
echo "4. Testing compiler functionality..."
spack spec zlib
echo "✓ Compiler can be used for package specs"
echo ""

echo "=== All Tests Passed ==="
echo ""
echo "Summary:"
echo "- Spack v1.0.0 installed and working"
echo "- System compiler configured successfully (hardcoded)"
echo "- Compiler can be used for package operations"
TESTSCRIPT

RUN chmod +x /test/test-compiler-detection.sh

# Run the test
CMD ["/test/test-compiler-detection.sh"]
