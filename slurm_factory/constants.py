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

"""Constants of slurm-factory."""

import textwrap
from enum import Enum
from pathlib import Path

# Mapping of user-facing version strings to Spack package versions
SLURM_VERSIONS = {
    "25.11": "25-11-0-1",
    "24.11": "24-11-6-1",
    "23.11": "23-11-11-1",
}

# Supported compiler versions for building
# Key: user-facing version, Value: (gcc_version, glibc_version, description)
# Latest stable minor versions for each major GCC version from Spack
COMPILER_TOOLCHAINS = {
    "15.2.0": ("15.2.0", "2.40", "GCC 15.2 (latest) - glibc 2.40"),
    "14.2.0": ("14.2.0", "2.39", "GCC 14.2 (latest stable) - glibc 2.39"),
    "13.4.0": ("13.4.0", "2.39", "GCC 13.4 / Ubuntu 24.04 (default) - glibc 2.39"),
    "12.5.0": ("12.5.0", "2.35", "GCC 12.5 (latest stable) - glibc 2.35"),
    "11.5.0": ("11.5.0", "2.35", "GCC 11.5 / Ubuntu 22.04 - glibc 2.35"),
    "10.5.0": ("10.5.0", "2.31", "GCC 10.5 / RHEL 8 / Ubuntu 20.04 - glibc 2.31"),
    "9.5.0": ("9.5.0", "2.28", "GCC 9.5 (latest stable) - glibc 2.28"),
    "8.5.0": ("8.5.0", "2.28", "GCC 8.5 / RHEL 8 minimum - glibc 2.28"),
    "7.5.0": ("7.5.0", "2.17", "GCC 7.5 / RHEL 7 compatible - glibc 2.17"),
}


class SlurmVersion(str, Enum):
    """Available Slurm versions for building."""

    v25_11 = "25.11"
    v24_11 = "24.11"
    v23_11 = "23.11"


class BuildType(str, Enum):
    """Build type options for Slurm."""

    cpu = "cpu"
    gpu = "gpu"


# Docker configuration
INSTANCE_NAME_PREFIX = "slurm-factory"

# Timeouts (in seconds)
BUILD_TIMEOUT = 3600  # 1 hour for full build
DOCKER_BUILD_TIMEOUT = 600  # 10 minutes for image build

# Spack buildcache configuration
SLURM_FACTORY_SPACK_CACHE_BASE_URL = "https://slurm-factory-spack-binary-cache.vantagecompute.ai"
SLURM_FACTORY_GPG_PUBLIC_KEY_URL = f"{SLURM_FACTORY_SPACK_CACHE_BASE_URL}/keys/vantage-slurm-factory.pub"

# Spack repository paths
SPACK_SETUP_SCRIPT = "/opt/spack/share/spack/setup-env.sh"

# Container paths
CONTAINER_CACHE_DIR = "/opt/slurm-factory-cache"
CONTAINER_SPACK_TEMPLATES_DIR = "/opt/spack/share/spack/templates"
CONTAINER_SPACK_PROJECT_DIR = "/root/spack-project"
CONTAINER_SLURM_DIR = "/opt/slurm"
CONTAINER_BUILD_OUTPUT_DIR = f"{CONTAINER_SLURM_DIR}/build_output"
CONTAINER_ROOT_DIR = "/root"
# NOTE: We do NOT create/use SPACK_CACHE_DIR to avoid cross-build contamination
# Each container build should start fresh without cached compiler metadata

# Patch files
SLURM_PATCH_FILES = ["slurm_prefix.patch", "package.py"]

# Shell script templates
BASH_HEADER = ["bash", "-c"]


def get_compiler_tarball_name(compiler_version: str) -> str:
    """
    Generate the standard compiler tarball name for a given version.

    Args:
        compiler_version: GCC compiler version (e.g., "13.4.0")

    Returns:
        Tarball filename (e.g., "gcc-13.4.0-compiler.tar.gz")

    """
    return f"gcc-{compiler_version}-compiler.tar.gz"


def get_compiler_tarball_path(cache_dir: str, compiler_version: str) -> str:
    """
    Generate the full path to a compiler tarball in the cache directory.

    Args:
        cache_dir: Base cache directory path
        compiler_version: GCC compiler version (e.g., "13.4.0")

    Returns:
        Full path to compiler tarball (e.g., "/path/to/cache/compilers/13.4.0/gcc-13.4.0-compiler.tar.gz")

    """
    from pathlib import Path

    return str(Path(cache_dir) / "compilers" / compiler_version / get_compiler_tarball_name(compiler_version))


def get_module_template_content() -> str:
    """Return the embedded Lmod module template content."""
    template_path = Path(__file__).parent.parent / "data" / "templates" / "relocatable_modulefile.lua"
    return template_path.read_text()


def get_modulerc_creation_script(module_dir: str, modulerc_path: str) -> str:
    """
    Generate bash script to create the .modulerc.lua file.

    Args:
        module_dir: Directory containing the .lua module files
        modulerc_path: Full path where .modulerc.lua should be created

    Returns:
        Single-line bash script as a string

    """
    # Use printf with %s for proper escaping, avoiding single quotes in echo
    # This avoids issues when embedded in complex shell scripts
    return (
        f"MODULE_LUA_FILE=$(ls {module_dir}/*.lua | head -1) && "
        f'[ -n "$MODULE_LUA_FILE" ] && '
        f'MODULE_VERSION=$(basename "$MODULE_LUA_FILE" .lua) && '
        f'printf "module_version(\\"%s\\",\\"default\\")\\n" "$MODULE_VERSION" > {modulerc_path}'
    )


def get_install_system_deps_script() -> str:
    """Generate script to install system dependencies for Spack."""
    return textwrap.dedent("""\
        apt-get update && apt-get upgrade -y && \\
        apt-get install -y \\
        git \\
        python3 \\
        python3-pip \\
        unzip \\
        bison \\
        flex \\
        libfl-dev \\
        cmake \\
        make \\
        m4 \\
        pkg-config \\
        ccache \\
        findutils \\
        diffutils \\
        tar \\
        gawk \\
        gettext \\
        libmd-dev \\
        libbsd-dev \\
        libsigsegv-dev \\
        file \\
        lmod \\
        ca-certificates \\
        wget && \\
        python3 -m pip install --break-system-packages boto3 pyyaml && \\
        apt-get clean && rm -rf /var/lib/apt/lists/*
    """).strip()


def get_install_spack_script() -> str:
    """Generate script to install Spack."""
    return textwrap.dedent(
        """\
        git clone --depth 1 --branch v1.0.0 https://github.com/spack/spack.git /opt/spack && \\
        chown -R root:root /opt/spack && chmod -R a+rX /opt/spack
    """
    ).strip()


def get_spack_profile_script() -> str:
    """Generate script to set up Spack profile."""
    return textwrap.dedent("""\
        echo 'source /opt/spack/share/spack/setup-env.sh' >> /etc/profile.d/spack.sh && \\
        chmod 644 /etc/profile.d/spack.sh
    """).strip()


def get_create_directories_script() -> str:
    """Generate script to create required directories."""
    return textwrap.dedent(f"""\
        mkdir -p {CONTAINER_SPACK_PROJECT_DIR} \\
                 {CONTAINER_SPACK_TEMPLATES_DIR} \\
                 {CONTAINER_SLURM_DIR}
    """).strip()


def get_spack_build_script(compiler_version: str) -> str:
    """
    Generate script to build Slurm with Spack using a bootstrap compiler.

    This implements a two-stage build process:

    Stage 1: Compiler Bootstrap (lines 1-25)
    - Create temporary environment at /tmp/compiler-install
    - Install GCC from buildcache with view at /opt/spack-compiler-view
    - Register compiler globally with `spack compiler find --scope site`
    - This makes the compiler available to ALL Spack environments

    Stage 2: Slurm Build (lines 26-end)
    - Switch to Slurm project environment at {CONTAINER_SPACK_PROJECT_DIR}
    - Activate the Slurm environment (which has spack.yaml with Slurm specs)
    - Concretize and install Slurm using the registered compiler

    Key insight from Spack docs: Compilers registered at 'site' scope are global.
    See: https://spack.readthedocs.io/en/latest/configuring_compilers.html

    Args:
        compiler_version: GCC version to install and use (e.g., "13.4.0")

    Returns:
        Complete bash script for compiler bootstrap and Slurm build

    """
    buildcache_url = (
        f"https://slurm-factory-spack-binary-cache.vantagecompute.ai/compilers/{compiler_version}/buildcache"
    )
    return textwrap.dedent(f"""        source {SPACK_SETUP_SCRIPT}
        echo '==> Configuring buildcache mirror globally for compiler installation...'
        spack mirror add --scope site slurm-factory-buildcache {buildcache_url} || true
        echo '==> Installing buildcache keys...'
        spack buildcache keys --install --trust
        echo '==> Creating temporary environment to install GCC compiler from buildcache...'
        mkdir -p /tmp/compiler-install
        cd /tmp/compiler-install
        cat > spack.yaml << 'COMPILER_ENV_EOF'
spack:
  specs:
  - gcc@{compiler_version}
  view: /opt/spack-compiler-view
  concretizer:
    unify: false
    reuse:
      roots: true
      from:
      - type: buildcache
        path: https://slurm-factory-spack-binary-cache.vantagecompute.ai/compilers/{compiler_version}/buildcache
COMPILER_ENV_EOF
        echo '==> Concretizing GCC environment...'
        spack -e . concretize -f
        echo '==> Installing GCC compiler from buildcache in dedicated environment...'
        spack -e . install --cache-only --no-check-signature
        echo '==> Hiding system gcc binaries to prevent auto-detection...'
        for f in gcc g++ c++ gfortran gcc-13 g++-13 gfortran-13 gcc-14 g++-14 gfortran-14; do
            [ -f /usr/bin/$f ] && mv /usr/bin/$f /usr/bin/$f.hidden || true
        done
        echo '==> Verifying GCC installation in compiler view...'
        ls -la /opt/spack-compiler-view/bin/gcc* || echo 'WARNING: GCC binaries not found'
        /opt/spack-compiler-view/bin/gcc --version || echo 'ERROR: GCC not executable'
        echo '==> Setting up compiler runtime library path...'
        export LD_LIBRARY_PATH=/opt/spack-compiler-view/lib64:/opt/spack-compiler-view/lib:${{LD_LIBRARY_PATH:-}}
        echo "LD_LIBRARY_PATH=$LD_LIBRARY_PATH"
        echo '==> Detecting newly installed GCC compiler...'
        spack compiler find --scope site /opt/spack-compiler-view
        echo '==> Removing any auto-detected system compilers...'
        for compiler in $(spack compiler list | grep -v gcc@{compiler_version} | \
                grep gcc@ | awk '{{print $1}}'); do
            echo "Removing $compiler"
            spack compiler rm --scope site $compiler 2>/dev/null || true
        done
        echo '==> Verifying gcc@{compiler_version} is available...'
        if ! spack compiler list | grep -q "gcc@{compiler_version}"; then
            echo 'ERROR: gcc@{compiler_version} compiler not found:'
            spack compiler list
            exit 1
        fi
        echo '==> Configured compilers:'
        spack compiler list
        echo '==> Compiler info for gcc@{compiler_version}:'
        spack compiler info gcc@{compiler_version}
        echo '==> Testing compiler with simple program...'
        cat > /tmp/test.c << 'CEOF'
#include <stdio.h>
int main() {{ printf("Compiler test OK
"); return 0; }}
CEOF
        /opt/spack-compiler-view/bin/gcc /tmp/test.c -o /tmp/test && /tmp/test || {{
            echo 'ERROR: Compiler test failed'
            /opt/spack-compiler-view/bin/gcc -v /tmp/test.c -o /tmp/test 2>&1 || true
            ldd /tmp/test 2>&1 || true
            exit 1
        }}
        echo '==> Switching to Slurm project environment...'
        cd {CONTAINER_SPACK_PROJECT_DIR}
        spack env activate .
        echo '==> Verifying compiler is still available in environment...'
        spack compiler list || {{
            echo 'ERROR: No compilers found in environment'
            exit 1
        }}
        spack compiler info gcc@{compiler_version} || {{
            echo 'ERROR: gcc@{compiler_version} not found in environment scope'
            echo 'Available compilers:'
            spack compiler list
            exit 1
        }}
        rm -f spack.lock
        echo '==> Concretizing Slurm packages with gcc@{compiler_version}...'
        spack concretize -j $(nproc) -f --fresh
        echo '==> Installing Slurm and dependencies...'
        spack install -j$(nproc) -f || {{
            echo 'ERROR: spack install failed'
            echo 'Checking view status:'
            ls -la {CONTAINER_SLURM_DIR}/view 2>&1 || echo 'View directory does not exist'
            echo 'Installed specs:'
            spack find -v 2>&1 || true
            exit 1
        }}
        echo 'Verifying view was created...'
        ls -la {CONTAINER_SLURM_DIR}/view || {{
            echo 'ERROR: View was not created at {CONTAINER_SLURM_DIR}/view'
            echo 'Environment status:'
            spack env status
            echo 'spack.yaml content:'
            cat spack.yaml
            exit 1
        }}
        spack module lmod refresh --delete-tree -y
        spack module lmod refresh -y
        mkdir -p {CONTAINER_SLURM_DIR}/modules
        SPACK_ROOT_PATH=$(spack location -r)
        for f in $(find $SPACK_ROOT_PATH/share/spack/lmod -type f -name '*.lua'); do
            case $f in *slurm*) cp "$f" {CONTAINER_SLURM_DIR}/modules/;; esac
        done
    """).strip()


def get_package_tarball_script(
    modulerc_script: str,
    version: str,
    compiler_version: str = "13.4.0",
    gpu_support: bool = False,
) -> str:
    """
    Generate script to package everything into a tarball.

    Args:
        modulerc_script: The script to create .modulerc.lua file
        version: Slurm version (e.g., "25.11") for the tarball filename
        compiler_version: GCC compiler version used for the build (e.g., "7.5.0")
        gpu_support: Whether GPU support is enabled (affects CUDA/ROCm handling)

    """
    tarball_base = f"slurm-{version}-gcc{compiler_version}-software"

    # When GPU support is enabled, we need to copy specific GPU .so files from install tree
    # since CUDA and ROCm packages are excluded from the view
    gpu_handling_script = ""
    if gpu_support:
        gpu_handling_script = textwrap.dedent(f"""\
            echo "DEBUG: Copying GPU libraries from Spack install tree..." && \\
            mkdir -p {CONTAINER_SLURM_DIR}/view/lib/gpu && \\
            for lib in libnvidia-ml.so librocm_smi64.so librocm-core.so; do \\
                find /opt/slurm/software -name "$lib*" \\
                    \\( -type f -o -type l \\) 2>/dev/null | while read -r libfile; do \\
                    echo "DEBUG: Copying GPU library: $libfile" && \\
                    cp -P "$libfile" {CONTAINER_SLURM_DIR}/view/lib/gpu/ || true; \\
                done; \\
            done && \\
        """).strip()

    return textwrap.dedent(f"""\
        set -e && \\
        [ -d "{CONTAINER_SLURM_DIR}/view" ] || {{ \\
            echo "ERROR: Spack view was not created at {CONTAINER_SLURM_DIR}/view"; \\
            exit 1; \\
        }} && \\
        MISSING_LIBS="" && \\
        for lib in libmunge.so libjwt.so libjansson.so; do \\
            if ! find {CONTAINER_SLURM_DIR}/view/lib* -name "$lib*" 2>/dev/null | grep -q .; then \\
                echo "WARNING: $lib not found in view" && \\
                MISSING_LIBS="$MISSING_LIBS $lib"; \\
            fi; \\
        done && \\
        if [ -n "$MISSING_LIBS" ]; then \\
            echo "WARNING: Some expected libraries/binaries are missing: $MISSING_LIBS" && \\
            echo "Continuing anyway - they may not be required for this configuration"; \\
        else \\
            echo "DEBUG: All critical libraries verified in view"; \\
        fi && \\
        echo "DEBUG: Packaging view directly (projections create FHS layout)..." && \\
        cd {CONTAINER_SLURM_DIR}/view && \\
        {gpu_handling_script}
        find . -name "include" -type d -exec rm -rf {{}} + 2>/dev/null || true && \\
        find . -path "*/lib/pkgconfig" -type d -exec rm -rf {{}} + 2>/dev/null || true && \\
        find . -path "*/share/doc" -type d -exec rm -rf {{}} + 2>/dev/null || true && \\
        find . -path "*/share/man" -type d -exec rm -rf {{}} + 2>/dev/null || true && \\
        find . -path "*/share/info" -type d -exec rm -rf {{}} + 2>/dev/null || true && \\
        find . -name "__pycache__" -type d -exec rm -rf {{}} + 2>/dev/null || true && \\
        find . -name "*.pyc" -delete 2>/dev/null || true && \\
        find . -name "*.a" -delete 2>/dev/null || true && \\
        mkdir -p assets && \\
        cp -r {CONTAINER_SLURM_DIR}/slurm_assets assets/ && \\
        mkdir -p assets/modules/slurm && \\
        cp {CONTAINER_SLURM_DIR}/modules/*.lua assets/modules/slurm/ && \\
        {modulerc_script} && \\
        cd {CONTAINER_SLURM_DIR} && \\
        mkdir -p {CONTAINER_SLURM_DIR}/redistributable && \\
        tar -chzf {CONTAINER_SLURM_DIR}/redistributable/{tarball_base}.tar.gz view && \\
        mkdir -p {CONTAINER_BUILD_OUTPUT_DIR} && \\
        cp {CONTAINER_SLURM_DIR}/redistributable/{tarball_base}.tar.gz {CONTAINER_BUILD_OUTPUT_DIR}/
    """).strip()


def get_compiler_dockerfile(
    compiler_version: str = "13.4.0",
    cache_dir: str = "",
) -> str:
    """
    Generate a Dockerfile for building only the compiler toolchain.

    This creates a standalone build for the compiler that can be published
    to the buildcache and reused across multiple Slurm builds.

    Args:
        compiler_version: GCC compiler version to build
        cache_dir: Host cache directory for mounting buildcache and source cache

    Returns:
        A complete Dockerfile as a string for building the compiler

    """
    # Generate all script components
    install_deps_script = get_install_system_deps_script()
    install_spack_script = get_install_spack_script()
    spack_profile_script = get_spack_profile_script()

    # Generate bootstrap spack.yaml for building the compiler
    from .spack_yaml import generate_compiler_bootstrap_yaml

    bootstrap_yaml = generate_compiler_bootstrap_yaml(
        compiler_version=compiler_version,
        buildcache_root=f"{CONTAINER_CACHE_DIR}/buildcache",
        sourcecache_root=f"{CONTAINER_CACHE_DIR}/source",
    )

    gcc_ver = compiler_version

    return textwrap.dedent(
        f"""\
# syntax=docker/dockerfile:1
# Compiler Toolchain Build Container
# Generated by slurm-factory - DO NOT EDIT MANUALLY
#
# This Dockerfile uses BuildKit for enhanced caching.
# Cache directories are configured in spack.yaml to use:
# - {CONTAINER_CACHE_DIR}/buildcache for binary packages
# - {CONTAINER_CACHE_DIR}/source for source archives

# ========================================================================
# Stage 0: Compiler Bootstrap - Build custom GCC toolchain
# ========================================================================
FROM ubuntu:24.04 AS compiler-bootstrap

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install minimal system dependencies for Spack
RUN {install_deps_script}

# Install Spack v1.0.0
RUN {install_spack_script}

ENV SPACK_ROOT=/opt/spack
ENV PATH=$SPACK_ROOT/bin:$PATH
RUN {spack_profile_script}

# Create directories for cache (will be populated by Spack during build)
RUN mkdir -p {CONTAINER_CACHE_DIR}/buildcache {CONTAINER_CACHE_DIR}/source

# Create compiler bootstrap project directory
RUN mkdir -p /root/compiler-bootstrap

# Copy compiler bootstrap spack.yaml
RUN cat > /root/compiler-bootstrap/spack.yaml << 'BOOTSTRAP_YAML_EOF'
{bootstrap_yaml}
BOOTSTRAP_YAML_EOF

WORKDIR /root/compiler-bootstrap

# Build the compiler toolchain
# CRITICAL: Hide system gcc binaries ONLY during Spack environment activation
# This prevents Spack v1.0.0 from auto-detecting and adding gcc as external
# But we restore them before concretization so gcc can be used to BUILD gcc@11.4.0
RUN bash -c 'for f in gcc g++ c++ gfortran gcc-13 g++-13 gfortran-13; do \\
        [ -f /usr/bin/$f ] && mv /usr/bin/$f /usr/bin/$f.hidden || true; \\
    done && \\
    source /opt/spack/share/spack/setup-env.sh && \\
    eval $(spack env activate --sh .) && \\
    for f in gcc g++ c++ gfortran gcc-13 g++-13 gfortran-13; do \\
        [ -f /usr/bin/$f.hidden ] && mv /usr/bin/$f.hidden /usr/bin/$f || true; \\
    done && \\
    spack -e . concretize -j $(( $(nproc) - 1 )) -f && \\
    spack -e . install -j $(( $(nproc) - 1 )) --verbose

# Register the newly built compiler with Spack at site scope
# The view at /opt/spack-compiler is automatically created by the environment configuration
# Use --scope site to make compiler available globally (not just in the environment)
# Use explicit path to ensure compiler is found correctly
RUN bash -c 'source /opt/spack/share/spack/setup-env.sh && \\
    spack compiler find --scope site /opt/spack-compiler'

# NOTE: We do NOT build gcc-runtime or compiler-wrapper here!
# They MUST be built during the Slurm build phase with the target compiler,
# otherwise they will be built with the system compiler and have wrong linkage.
# Spack will automatically build them as dependencies when needed.

# Verify compiler installation
RUN /opt/spack-compiler/bin/gcc --version && \\
    /opt/spack-compiler/bin/g++ --version && \\
    /opt/spack-compiler/bin/gfortran --version

# ========================================================================
# Stage 1: Compiler Packager - Create tarball and buildcache output
# ========================================================================
FROM compiler-bootstrap AS compiler-packager

SHELL ["/bin/bash", "-c"]

# Package the compiler into a tarball
# Use -h flag to dereference symlinks and include actual files from Spack store
RUN mkdir -p /opt/compiler-output && \\
    cd /opt && \\
    tar -chzf /opt/compiler-output/{get_compiler_tarball_name(gcc_ver)} spack-compiler

# Export buildcache binaries (Spack build cache from {CONTAINER_CACHE_DIR}/buildcache)
# This will be copied from the image after build completes

CMD ["/bin/bash"]
"""
    )


def get_dockerfile(
    spack_yaml_content: str,
    version: str = "25.11",
    compiler_version: str = "13.4.0",
    gpu_support: bool = False,
    cache_dir: str = "",
    use_local_buildcache: bool = False,
) -> str:
    """
    Generate a multi-stage Dockerfile for building Slurm packages.

    Stage 0 (init): Ubuntu + system deps + Spack (heavily cached)
    Stage 1 (builder): Runs spack install, creates view, generates modules (cached on spack.yaml)
    Stage 2 (packager): Copies slurm_assets and creates tarball (invalidates on asset changes)

    The compiler is downloaded from the remote Spack buildcache mirror automatically.
    No separate compiler bootstrap stage is needed.

    Args:
        spack_yaml_content: The complete spack.yaml content as a string
        version: Slurm version (e.g., "25.11") for the tarball filename
        compiler_version: GCC compiler version to use (downloaded from buildcache)
        gpu_support: Whether GPU support is enabled
        cache_dir: Host cache directory (not used for compiler anymore)
        use_local_buildcache: Whether to use locally cached compiler tarball (legacy support)

    Returns:
        A complete multi-stage Dockerfile as a string

    """
    # Generate all script components
    install_deps_script = get_install_system_deps_script()
    install_spack_script = get_install_spack_script()
    spack_profile_script = get_spack_profile_script()
    create_dirs_script = get_create_directories_script()
    module_template_content = get_module_template_content()
    spack_build_script = get_spack_build_script(compiler_version)

    # Generate the modulerc creation script
    modulerc_script = get_modulerc_creation_script(
        module_dir=f"{CONTAINER_SLURM_DIR}/view/assets/modules/slurm",
        modulerc_path=f"{CONTAINER_SLURM_DIR}/view/assets/modules/slurm/.modulerc.lua",
    )

    # Generate the packaging script
    package_script = get_package_tarball_script(modulerc_script, version, compiler_version, gpu_support)

    # No compiler bootstrap stage needed - Spack will download from remote buildcache
    # Only generate local compiler tarball copy stage if explicitly requested
    compiler_bootstrap_stage = ""
    base_stage = "ubuntu:24.04"

    if use_local_buildcache and cache_dir:
        # Legacy support: use local compiler tarball if explicitly requested and available
        from pathlib import Path

        buildcache_tarball = Path(get_compiler_tarball_path(cache_dir, compiler_version))

        if buildcache_tarball.exists():
            # Use pre-built compiler from local buildcache
            # NOTE: The following is a Python f-string template that generates Dockerfile syntax
            compiler_bootstrap_stage = textwrap.dedent(
                f"""\
# ========================================================================
# Stage 0: Compiler Bootstrap - Use pre-built compiler from local buildcache
# ========================================================================
FROM ubuntu:24.04 AS compiler-bootstrap

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install minimal system dependencies for Spack
RUN {install_deps_script}

# Install Spack v1.0.0
RUN {install_spack_script}

ENV SPACK_ROOT=/opt/spack
ENV PATH=$SPACK_ROOT/bin:$PATH
RUN {spack_profile_script}

# Create directory for compiler
RUN mkdir -p /opt

# Copy pre-built compiler from local buildcache
COPY compilers/{compiler_version}/{get_compiler_tarball_name(compiler_version)} /tmp/
RUN cd /opt && tar -xzf /tmp/{get_compiler_tarball_name(compiler_version)} && \\
    rm /tmp/{get_compiler_tarball_name(compiler_version)}

# Verify compiler installation
RUN /opt/spack-compiler/bin/gcc --version && \\
    /opt/spack-compiler/bin/g++ --version && \\
    /opt/spack-compiler/bin/gfortran --version

# Register the compiler with Spack
RUN bash -c 'source /opt/spack/share/spack/setup-env.sh && \\
    spack compiler add /opt/spack-compiler/bin'

"""
            )
            base_stage = "compiler-bootstrap"
        else:
            # Local buildcache requested but tarball not found
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(
                f"Local buildcache requested but compiler tarball not found at "
                f"{buildcache_tarball}, will use remote Spack buildcache"
            )

    return textwrap.dedent(
        f"""\
# syntax=docker/dockerfile:1
# Slurm Factory Build Container - Multi-Stage Build
# Generated by slurm-factory - DO NOT EDIT MANUALLY
#
# This Dockerfile uses BuildKit for enhanced caching.
# Cache directories are configured in spack.yaml to use:
# - {CONTAINER_CACHE_DIR}/buildcache for binary packages
# - {CONTAINER_CACHE_DIR}/source for source archives

{compiler_bootstrap_stage}# ========================================================================
# Stage {"0" if not compiler_bootstrap_stage else "1"}: Init - Base system with Spack (heavily cached)
# ========================================================================
FROM {base_stage} AS init

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install system dependencies and Spack only if not using local buildcache
# (local buildcache stage already has these installed)
{
            "# System deps and Spack already installed in compiler-bootstrap stage"
            if compiler_bootstrap_stage
            else f'''# Install minimal system dependencies for Spack
RUN {install_deps_script}

# Install Spack v1.0.0
RUN {install_spack_script}

ENV SPACK_ROOT=/opt/spack
ENV PATH=$SPACK_ROOT/bin:$PATH
RUN {spack_profile_script}'''
        }

# Create required directories including cache directories
RUN {create_dirs_script} && \\
    mkdir -p {CONTAINER_CACHE_DIR}/buildcache {CONTAINER_CACHE_DIR}/source

# ========================================================================
# Stage {"1" if not compiler_bootstrap_stage else "2"}: Builder - Compile Slurm (cached on spack.yaml changes)
# ========================================================================
FROM init AS builder

# Copy spack.yaml (invalidates cache when build spec changes)
RUN cat > {CONTAINER_SPACK_PROJECT_DIR}/spack.yaml << 'SPACK_YAML_EOF'
{spack_yaml_content}
SPACK_YAML_EOF

# Copy module template (Spack expects it in modules/ subdirectory)
RUN mkdir -p {CONTAINER_SPACK_TEMPLATES_DIR}/modules
RUN cat > {CONTAINER_SPACK_TEMPLATES_DIR}/modules/relocatable_modulefile.lua << 'MODULE_TEMPLATE_EOF'
{module_template_content}
MODULE_TEMPLATE_EOF

# Trust Slurm Factory GPG public key for verifying signed buildcache packages
RUN bash -c 'source {SPACK_SETUP_SCRIPT} && \\
    wget -q {SLURM_FACTORY_GPG_PUBLIC_KEY_URL} -O /tmp/vantage-slurm-factory.pub && \\
    spack gpg trust /tmp/vantage-slurm-factory.pub && \\
    rm /tmp/vantage-slurm-factory.pub && \\
    echo "Trusted GPG keys:" && \\
    spack gpg list'

WORKDIR {CONTAINER_SPACK_PROJECT_DIR}

# Build Slurm: install + create view + generate modules
RUN /bin/bash <<'EOFBASH'
{spack_build_script}
EOFBASH

# ========================================================================
# Stage {
            "2" if not compiler_bootstrap_stage else "3"
        }: Packager - Create tarball (invalidates on asset changes)
# ========================================================================
FROM builder AS packager

# Use bash as the shell for RUN commands in this stage
SHELL ["/bin/bash", "-c"]

# Copy configuration assets (invalidates cache when they change)
COPY data/slurm_assets/ {CONTAINER_SLURM_DIR}/slurm_assets/

# Package everything into single tarball
RUN {package_script}

CMD ["/bin/bash"]
"""
    )
