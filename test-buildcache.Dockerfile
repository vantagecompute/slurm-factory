# Test Dockerfile to verify buildcache installation
# This tests installing GCC from the slurm-factory buildcache

FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install minimal dependencies for Spack
RUN apt-get update && apt-get install -y \
    build-essential \
    ca-certificates \
    curl \
    git \
    gnupg2 \
    python3 \
    python3-pip \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Spack v1.0.2
RUN git clone --depth 1 --branch v1.0.2 https://github.com/spack/spack.git /opt/spack

ENV SPACK_ROOT=/opt/spack
ENV PATH=$SPACK_ROOT/bin:$PATH

# Set up Spack shell integration
RUN echo 'source /opt/spack/share/spack/setup-env.sh' >> /etc/profile.d/spack.sh

# Create test environment directory
RUN mkdir -p /test-buildcache
WORKDIR /test-buildcache

# Create spack.yaml for testing buildcache installation
RUN cat > /test-buildcache/spack.yaml << 'EOF'
spack:
  specs:
    - gcc@15.1.0 +binutils +piclibs languages=c,c++,fortran
  
  concretizer:
    unify: true
    reuse:
      roots: true
      from:
        - type: buildcache
  
  packages:
    all:
      target: [x86_64_v3]
      require: target=x86_64_v3
  
  config:
    install_tree:
      root: /opt/test-install
      padded_length: 128
  
  mirrors:
    slurm-factory-buildcache:
      url: https://slurm-factory-spack-binary-cache.vantagecompute.ai/compilers/15.1.0
      signed: true
      binary: true
      source: false
    spack-public:
      url: https://mirror.spack.io
      signed: false
      binary: false
      source: true
EOF

# Test installation from buildcache
RUN bash -c 'set -ex && \
    source /opt/spack/share/spack/setup-env.sh && \
    cd /test-buildcache && \
    spack env activate . && \
    echo "==> Adding mirrors..." && \
    spack mirror list && \
    echo "==> Installing GPG keys..." && \
    spack buildcache keys --install --trust && \
    echo "==> Updating buildcache index..." && \
    spack buildcache update-index slurm-factory-buildcache || echo "Warning: Could not update index" && \
    echo "==> Listing available packages..." && \
    spack buildcache list --allarch && \
    echo "==> Concretizing..." && \
    spack concretize -f && \
    echo "==> Installing from buildcache (cache-only mode)..." && \
    spack install --cache-only && \
    echo "==> Verifying installation..." && \
    spack find && \
    echo "==> Testing GCC..." && \
    spack load gcc@15.1.0 && \
    gcc --version && \
    g++ --version && \
    gfortran --version && \
    echo "==> SUCCESS: GCC installed from buildcache!"'

CMD ["/bin/bash"]
