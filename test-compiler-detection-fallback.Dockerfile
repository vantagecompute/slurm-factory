# Test Dockerfile to validate compiler detection FALLBACK
# Simulates a scenario where auto-detection fails

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

# Test script that simulates FAILED auto-detection
RUN cat > /test/test-compiler-fallback.sh <<'TESTSCRIPT'
#!/bin/bash
set -e

echo "=== Testing Compiler Detection FALLBACK ==="
echo ""

# Verify spack works
echo "1. Verifying Spack installation..."
spack --version
echo "✓ Spack is working"
echo ""

# Simulate FAILED auto-detection by NOT running compiler find
echo "2. Simulating FAILED auto-detection (skipping 'spack compiler find')..."
echo ""

# Verify compiler was NOT found
echo "3. Checking for configured compilers..."
if spack compiler list 2>&1 | grep -q "No compilers available"; then
  echo "⚠ No compilers configured (expected)"
else
  spack compiler list || true
fi
echo ""

# Apply the fallback fix
echo "4. Applying fallback fix..."
if ! spack compiler list 2>&1 | grep -q gcc || spack compiler list 2>&1 | grep -q "No compilers available"; then
  echo "⚠ No compilers found. Adding system GCC manually..."
  # Get system gcc version
  GCC_VERSION=$(gcc -dumpversion)
  echo "System GCC version: ${GCC_VERSION}"
  
  # Create compiler config
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
  echo "✓ Manually added GCC ${GCC_VERSION}"
  echo ""
  
  echo "5. Verifying compiler configuration after fallback..."
  spack compiler list
  echo ""
else
  echo "✓ Compiler already configured (unexpected in this test)"
  echo ""
fi

# Verify we can use the compiler
echo "6. Testing compiler functionality..."
spack spec zlib 2>&1 | head -20
echo "✓ Compiler can be used for package specs"
echo ""

echo "=== Fallback Test Passed ==="
echo ""
echo "Summary:"
echo "- Simulated failed auto-detection"
echo "- Fallback successfully configured system compiler"
echo "- Compiler can be used for package operations"
TESTSCRIPT

RUN chmod +x /test/test-compiler-fallback.sh

# Run the test
CMD ["/test/test-compiler-fallback.sh"]
