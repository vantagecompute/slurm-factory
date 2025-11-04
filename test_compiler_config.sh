#!/bin/bash
set -e

# Test script to verify compiler configuration fix
# This mimics the actual build environment to test the sed-based compiler config

echo "==> Building test container..."
docker build --no-cache -t slurm-factory-compiler-test -f - . << 'DOCKERFILE'
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    gpg \
    python3 \
    python3-pip \
    file \
    unzip \
    gawk \
    sed \
    && rm -rf /var/lib/apt/lists/*

# Install Spack
RUN git clone -c feature.manyFiles=true --depth=1 --branch=v1.0.0 \
    https://github.com/spack/spack.git /opt/spack

ENV SPACK_ROOT=/opt/spack
ENV PATH="${SPACK_ROOT}/bin:${PATH}"

# Initialize Spack
RUN . /opt/spack/share/spack/setup-env.sh && \
    spack compiler find --scope site && \
    for compiler in $(spack compiler list | grep gcc@ | awk '{print $1}'); do \
        spack compiler rm --scope site $compiler 2>/dev/null || true; \
    done

WORKDIR /test
DOCKERFILE

echo ""
echo "==> Running compiler configuration test..."
docker run --rm slurm-factory-compiler-test bash -c '
set -e

# Source Spack
. /opt/spack/share/spack/setup-env.sh

echo "==> Creating compiler bootstrap environment..."
cat > /tmp/compiler-env.yaml << "EOF"
spack:
  specs:
  - gcc@9.5.0 +binutils +piclibs languages=c,c++,fortran ^binutils@2.44
  view:
    /opt/spack-compiler-view:
      root: /opt/spack-compiler-view
      select: [gcc@9.5.0]
      link: all
      link_type: symlink
  mirrors:
    slurm-factory-buildcache:
      url: https://slurm-factory-spack-binary-cache.vantagecompute.ai/compilers/9.5.0/buildcache
      signed: false
  concretizer:
    unify: false
    reuse:
      roots: true
      from:
      - type: buildcache
EOF

spack env create compiler-test /tmp/compiler-env.yaml
spack env activate compiler-test

echo "==> Installing GCC from buildcache..."
spack install --cache-only --no-check-signature

echo "==> Verifying GCC installation..."
ls -la /opt/spack-compiler-view/bin/gcc*
/opt/spack-compiler-view/bin/gcc --version

echo "==> Detecting compiler..."
spack compiler find --scope site /opt/spack-compiler-view

echo "==> Initial compiler info:"
spack compiler info gcc@9.5.0

echo ""
echo "==> Applying sed-based compiler configuration fix..."

# Find Spack root
SPACK_ROOT=$(spack location -r)
echo "Spack root: $SPACK_ROOT"

COMPILERS_FILE="$SPACK_ROOT/etc/spack/packages.yaml"
echo "Editing: $COMPILERS_FILE"

# Show the file before modification
echo "==> File content before modification:"
cat "$COMPILERS_FILE"

# Backup original
cp "$COMPILERS_FILE" "${COMPILERS_FILE}.bak"

# Create the YAML additions (8 spaces indentation for extra_attributes content)
cat > /tmp/compiler_additions.yaml << "ADDEOF"
        environment:
          prepend_path:
            LD_LIBRARY_PATH: /opt/spack-compiler-view/lib64:/opt/spack-compiler-view/lib
        extra_rpaths:
        - /opt/spack-compiler-view/lib64
        - /opt/spack-compiler-view/lib
        flags:
          cflags: -L/opt/spack-compiler-view/lib64 -L/opt/spack-compiler-view/lib
          cxxflags: -L/opt/spack-compiler-view/lib64 -L/opt/spack-compiler-view/lib
          fflags: -L/opt/spack-compiler-view/lib64 -L/opt/spack-compiler-view/lib
          ldflags: -L/opt/spack-compiler-view/lib64 -L/opt/spack-compiler-view/lib -Wl,-rpath,/opt/spack-compiler-view/lib64 -Wl,-rpath,/opt/spack-compiler-view/lib
ADDEOF

echo "==> YAML additions to insert:"
cat /tmp/compiler_additions.yaml

# Insert after the fortran line (within extra_attributes) so the new sections are part of extra_attributes
sed -i "/fortran: \/opt\/spack-compiler-view\/bin\/gfortran/r /tmp/compiler_additions.yaml" "$COMPILERS_FILE"

echo "==> File content after modification:"
grep -A 25 "gcc@9.5.0" "$COMPILERS_FILE" || echo "Could not find gcc@9.5.0"

echo ""
echo "==> Updated compiler info:"
spack compiler info gcc@9.5.0

echo ""
echo "==> Verifying configuration sections..."
if spack compiler info gcc@9.5.0 | grep -q "environment:"; then
    echo "✓ environment section found"
else
    echo "✗ environment section MISSING"
    exit 1
fi

if spack compiler info gcc@9.5.0 | grep -q "extra_rpaths:"; then
    echo "✓ extra_rpaths section found"
else
    echo "✗ extra_rpaths section MISSING"
    exit 1
fi

if spack compiler info gcc@9.5.0 | grep -q "flags:"; then
    echo "✓ flags section found"
else
    echo "✗ flags section MISSING"
    exit 1
fi

echo ""
echo "==> Testing compiler with library paths..."
export LD_LIBRARY_PATH=/opt/spack-compiler-view/lib64:/opt/spack-compiler-view/lib:${LD_LIBRARY_PATH:-}

cat > /tmp/test.c << "CEOF"
#include <stdio.h>
int main() { printf("Compiler test OK\n"); return 0; }
CEOF

/opt/spack-compiler-view/bin/gcc /tmp/test.c -o /tmp/test
/tmp/test

echo ""
echo "==> Testing simple package build with configured compiler..."
spack env deactivate
cat > /tmp/test-env.yaml << "TESTEOF"
spack:
  specs:
  - zlib@1.3.1 %gcc@9.5.0
  packages:
    all:
      target: [x86_64_v3]
TESTEOF

spack env create test-build /tmp/test-env.yaml
spack env activate test-build

echo "==> Concretizing test package..."
spack concretize -f

echo "==> Installing test package (this will fail if compiler wrapper has issues)..."
spack install --no-check-signature

echo ""
echo "==> ✓ SUCCESS: Compiler configuration test passed!"
echo "==> The sed-based fix correctly configures the compiler"
'

TEST_EXIT=$?

if [ $TEST_EXIT -eq 0 ]; then
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "✓ TEST PASSED: Compiler configuration works correctly!"
    echo "════════════════════════════════════════════════════════════"
else
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "✗ TEST FAILED: Compiler configuration has issues"
    echo "════════════════════════════════════════════════════════════"
fi

echo ""
echo "==> Cleaning up test container..."
docker rmi slurm-factory-compiler-test 2>/dev/null || true

exit $TEST_EXIT
