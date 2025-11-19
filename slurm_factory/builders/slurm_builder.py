#!/usr/bin/env python3
# Copyright (c) Vantage Compute Inc. All rights reserved.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Slurm build process management."""
import logging
import os
import subprocess
import sys
import textwrap
from pathlib import Path

from rich.console import Console
from rich.markup import escape

from slurm_factory.constants import (
    CONTAINER_BUILD_OUTPUT_DIR,
    CONTAINER_CACHE_DIR,
    CONTAINER_SLURM_DIR,
    CONTAINER_SPACK_PROJECT_DIR,
    CONTAINER_SPACK_TEMPLATES_DIR,
    S3_BUILDCACHE_BUCKET,
    SPACK_SETUP_SCRIPT,
)
from slurm_factory.exceptions import SlurmFactoryError, SlurmFactoryStreamExecError
from slurm_factory.spack_yaml import generate_yaml_string
from slurm_factory.utils import (
    build_docker_image,
    get_create_spack_profile_script,
    get_data_dir,
    get_install_spack_script,
    get_install_system_deps_script,
    remove_old_docker_image,
)

logger = logging.getLogger(__name__)
console = Console()


def get_module_template_content() -> str:
    """Return the embedded Lmod module template content."""
    # Try installed location first (share/slurm-factory/templates/)
    installed_path = Path(sys.prefix) / "share" / "slurm-factory" / "templates" / "relocatable_modulefile.lua"
    if installed_path.exists():
        return installed_path.read_text()

    # Fall back to development location (project root data/templates/)
    dev_path = Path(__file__).parent.parent.parent / "data" / "templates" / "relocatable_modulefile.lua"
    if dev_path.exists():
        return dev_path.read_text()

    raise FileNotFoundError(
        f"Could not find relocatable_modulefile.lua in installed location ({installed_path}) "
        f"or development location ({dev_path})"
    )


def get_move_slurm_assets_to_container_str() -> str:
    """
    Generate Dockerfile commands to add slurm_assets files by embedding their content.

    Iterates over all files and directories in slurm_assets and generates shell commands
    that create the files in the container using base64 encoding to avoid escaping issues.

    Returns
    -------
        Multi-line string with shell commands to create directories and files

    """
    import base64

    data_dir = get_data_dir()
    slurm_assets_dir = data_dir / "slurm_assets"

    if not slurm_assets_dir.exists():
        raise FileNotFoundError(f"slurm_assets directory not found at {slurm_assets_dir}")

    commands = []

    # Base directory to copy assets into
    container_base_dir = f"{CONTAINER_SLURM_DIR}/slurm_assets"

    # First, create the base directory
    commands.append(f"mkdir -p {container_base_dir}")

    # Walk through all files and directories
    for root, dirs, files in os.walk(slurm_assets_dir):
        root_path = Path(root)
        # Get relative path from slurm_assets_dir
        rel_path = root_path.relative_to(slurm_assets_dir)

        # Create subdirectories in container
        for dir_name in sorted(dirs):
            if rel_path != Path("."):
                container_dir = f"{container_base_dir}/{rel_path}/{dir_name}"
            else:
                container_dir = f"{container_base_dir}/{dir_name}"
            commands.append(f"mkdir -p {container_dir}")

        # Create files in container using base64 encoding
        for file_name in sorted(files):
            source_file = root_path / file_name
            if rel_path != Path("."):
                container_file = f"{container_base_dir}/{rel_path}/{file_name}"
            else:
                container_file = f"{container_base_dir}/{file_name}"

            # Read file content and base64 encode it
            try:
                content_bytes = source_file.read_bytes()
                encoded_content = base64.b64encode(content_bytes).decode('ascii')

                # Use base64 decode to recreate the file
                commands.append(f"echo '{encoded_content}' | base64 -d > {container_file}")

                # Make scripts executable if they have .sh extension
                if file_name.endswith(".sh"):
                    commands.append(f"chmod +x {container_file}")

            except Exception as e:
                logger.warning(f"Failed to read {source_file}: {e}")
                continue

    # Join all commands with && for a single RUN statement
    return " && \\\n    ".join(commands)



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


def get_slurm_build_script(compiler_version: str) -> str:
    """
    Generate script to build Slurm with Spack using a bootstrap compiler.

    This implements a two-stage build process:

    Stage 1: Compiler Bootstrap
    - Create temporary environment at /tmp/compiler-install
    - Install GCC from buildcache with view at /opt/spack-compiler-view
    - Register compiler globally with `spack compiler find --scope site`
    - This makes the compiler available to ALL Spack environments

    Stage 2: Slurm Build
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
    # NOTE: Spack adds build_cache/ subdirectory automatically - do NOT append /buildcache here
    compiler_buildcache_url = (
        f"https://slurm-factory-spack-binary-cache.vantagecompute.ai/compilers/{compiler_version}"
    )
    return textwrap.dedent(f"""        source {SPACK_SETUP_SCRIPT}
        echo '==> Configuring buildcache mirror globally for compiler installation...'
        spack mirror add --scope site slurm-factory-compiler-buildcache {compiler_buildcache_url} || true
        echo '==> Trusting Slurm Factory GPG public key for signed compiler packages...'
        spack buildcache keys --install --trust
        echo '==> Creating temporary environment to install GCC compiler from buildcache...'
        mkdir -p /tmp/compiler-install
        cd /tmp/compiler-install
        printf '%s\\n' \\
          'spack:' \\
          '  specs:' \\
          '  - gcc@{compiler_version} languages=c,c++,fortran' \\
          '  view:' \\
          '    default:' \\
          '      root: /opt/spack-compiler-view' \\
          '      link_type: symlink' \\
          '  concretizer:' \\
          '    unify: false' \\
          '    reuse:' \\
          '      roots: true' \\
          '      from:' \\
          '      - type: buildcache' \\
          '        path: {compiler_buildcache_url}' \\
          > spack.yaml
        echo '==> Checking if GCC is available in buildcache...'
        if ! spack buildcache list --allarch | grep -q "gcc@{compiler_version}"; then
            echo 'ERROR: gcc@{compiler_version} not found in buildcache!'
            echo 'Available packages in buildcache:'
            spack buildcache list --allarch | head -50
            exit 1
        fi
        echo '✓ gcc@{compiler_version} found in buildcache'
        echo '==> Concretizing GCC environment...'
        spack -e . concretize -f
        echo '==> Installing GCC compiler from buildcache...'
        # The concretizer is configured to prefer buildcache (via reuse:roots + from:buildcache)
        # This will use gcc from buildcache while allowing dependencies to build from source if needed
        # GPG signature verification is automatic since we've trusted the key
        spack -e . install
        echo '==> Verifying GCC was installed from buildcache (not built from source)...'
        if spack find -v gcc@{compiler_version} | grep -q 'installed from binary cache'; then
            echo '✓ GCC was installed from buildcache'
        else
            # Check the build stage to confirm it came from cache
            echo 'Checking installation method...'
            spack find -vl gcc@{compiler_version} || true
        fi
        echo '==> Hiding system gcc binaries to prevent auto-detection...'
        for f in gcc g++ c++ gfortran gcc-13 g++-13 gfortran-13 gcc-14 g++-14 gfortran-14; do
            [ -f /usr/bin/$f ] && mv /usr/bin/$f /usr/bin/$f.hidden || true
        done
        echo '==> Verifying GCC installation in compiler view...'
        ls -la /opt/spack-compiler-view/bin/gcc* || echo 'WARNING: GCC binaries not found'
        /opt/spack-compiler-view/bin/gcc --version || echo 'ERROR: GCC not executable'
        echo '==> Setting up compiler runtime library path...'
        export \
            LD_LIBRARY_PATH=/opt/spack-compiler-view/lib64:/opt/spack-compiler-view/lib:${{LD_LIBRARY_PATH:-}}
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
        printf '%s\\n' \\
          '#include <stdio.h>' \\
          'int main() {{ printf("Compiler test OK\\\\n"); return 0; }}' \\
          > /tmp/test.c
        /opt/spack-compiler-view/bin/gcc /tmp/test.c -o /tmp/test && /tmp/test || {{
            echo 'ERROR: Compiler test failed'
            /opt/spack-compiler-view/bin/gcc -v /tmp/test.c -o /tmp/test 2>&1 || true
            ldd /tmp/test 2>&1 || true
            exit 1
        }}
        echo '==> Switching to Slurm project environment...'
        cd {CONTAINER_SPACK_PROJECT_DIR}
        spack env activate .
        echo '==> Checking custom Spack repositories...'
        spack repo list || true
        spack env status
        echo '==> Verifying slurm_factory namespace is available...'
        spack list slurm_factory.slurm || {{
            echo 'WARNING: slurm_factory.slurm not found in repo list'
            echo 'Available repos:'
            spack repo list
            exit 1
        }}
        # Check for compiler in site scope (where it was registered)
        if ! spack compiler list --scope site | grep -q "gcc@{compiler_version}"; then
            echo 'ERROR: gcc@{compiler_version} not found in site scope'
            echo 'Site compilers:'
            spack compiler list --scope site
            echo 'All compilers:'
            spack compiler list
            exit 1
        fi
        echo '✓ gcc@{compiler_version} available in site scope'
        spack compiler info gcc@{compiler_version} || {{
            echo 'WARNING: Could not get compiler info, but compiler is registered'
            echo 'Available compilers:'
            spack compiler list
        }}
        rm -f spack.lock
        echo '==> Concretizing Slurm packages with gcc@{compiler_version}...'
        spack -e . concretize -j $(nproc) -f --fresh
        echo '==> Installing Slurm and dependencies...'
        spack -e . install -j $(nproc) -f slurm || {{
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


def get_create_slurm_tarball_script(
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
        {gpu_handling_script if gpu_handling_script else ""}find . -name "include" -type d \\
            -exec rm -rf {{}} + 2>/dev/null || true && \\
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


def _get_slurm_builder_dockerfile(
    spack_yaml_content: str,
    slurm_version: str = "25.11",
    compiler_version: str = "13.4.0",
    gpu_support: bool = False,
) -> str:
    """
    Generate a multi-stage Dockerfile for building Slurm packages.

    Stage 0 (init): Ubuntu + system deps + Spack (heavily cached)
    Stage 1 (builder): Runs spack install, creates view, generates modules (cached on spack.yaml)
    Stage 2 (packager): Embeds slurm_assets content and creates tarball (invalidates on asset changes)

    The compiler is downloaded from the remote Spack buildcache mirror automatically.
    No separate compiler bootstrap stage is needed.

    Args:
        spack_yaml_content: The complete spack.yaml content as a string
        slurm_version: Slurm version (e.g., "25.11") for the tarball filename
        compiler_version: GCC compiler version to use (downloaded from buildcache)
        gpu_support: Whether GPU support is enabled

    Returns:
        A complete multi-stage Dockerfile as a string

    """
    # Generate all script components
    install_deps_script = get_install_system_deps_script()
    install_spack_script = get_install_spack_script()
    create_spack_profile_script = get_create_spack_profile_script()
    module_template_content = get_module_template_content()
    slurm_build_script = get_slurm_build_script(compiler_version)

    # Generate the modulerc creation script
    modulerc_script = get_modulerc_creation_script(
        module_dir=f"{CONTAINER_SLURM_DIR}/view/assets/modules/slurm",
        modulerc_path=f"{CONTAINER_SLURM_DIR}/view/assets/modules/slurm/.modulerc.lua",
    )

    # Generate the packaging script
    create_slurm_tarball_script = get_create_slurm_tarball_script(
        modulerc_script, slurm_version, compiler_version, gpu_support
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
#
# ========================================================================
# Stage 0 Init - Install build deps and init base system with Spack
# ========================================================================
FROM ubuntu:24.04 AS init

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

RUN {install_deps_script}

# Install Spack v1.0.0
RUN {install_spack_script}

ENV SPACK_ROOT=/opt/spack
ENV PATH=$SPACK_ROOT/bin:$PATH
RUN {create_spack_profile_script}

# Create required directories including cache directories
RUN mkdir -p \
    {CONTAINER_SPACK_PROJECT_DIR} \
    {CONTAINER_SPACK_TEMPLATES_DIR} \
    {CONTAINER_SLURM_DIR} && \
        mkdir -p {CONTAINER_CACHE_DIR}/buildcache {CONTAINER_CACHE_DIR}/source

# ========================================================================
# Stage 1 Build - Build Slurm
# ========================================================================
FROM init AS builder

# Add spack.yaml
RUN cat > {CONTAINER_SPACK_PROJECT_DIR}/spack.yaml << 'SPACK_YAML_EOF'
{spack_yaml_content}
SPACK_YAML_EOF

# Copy module template (Spack expects it in modules/ subdirectory)
RUN mkdir -p {CONTAINER_SPACK_TEMPLATES_DIR}/modules
RUN cat > {CONTAINER_SPACK_TEMPLATES_DIR}/modules/relocatable_modulefile.lua << 'MODULE_TEMPLATE_EOF'
{module_template_content}
MODULE_TEMPLATE_EOF

WORKDIR {CONTAINER_SPACK_PROJECT_DIR}

# Build Slurm: install + create view + generate modules
RUN /bin/bash <<'EOFBASH'
{slurm_build_script}
EOFBASH

# ========================================================================
# Stage 2 Packager - Create tarball
# ========================================================================
FROM builder AS packager

# Use bash as the shell for RUN commands in this stage
SHELL ["/bin/bash", "-c"]

# Add configuration assets by catting their content (invalidates cache when they change)
RUN {get_move_slurm_assets_to_container_str()}

# Package everything into single tarball
RUN {create_slurm_tarball_script}

CMD ["/bin/bash"]
"""
    )


def _extract_slurm_tarball_from_image(
    image_tag: str,
    output_dir: str,
    slurm_version: str,
    compiler_version: str,
) -> None:
    """
    Extract the Slurm package tarball from a packager Docker image.

    Args:
        image_tag: Tag of the packager Docker image
        output_dir: Directory to extract the tarball to (will be appended with version/compiler_version)
        slurm_version: Slurm version (for finding the correct tarball)
        compiler_version: GCC compiler version used for the build

    """
    console.print(f"[bold blue]Extracting Slurm package from image {image_tag}...[/bold blue]")

    # Create slurm_version-specific output directory: ~/.slurm-factory/slurm_version/compiler_version/
    base_path = Path(output_dir)
    output_path = base_path / slurm_version / compiler_version
    output_path.mkdir(parents=True, exist_ok=True)

    logger.debug(f"Extracting package from image {image_tag} to {output_path}")

    container_name = f"slurm-factory-extract-{slurm_version.replace('.', '-')}"

    # Tarball name always includes compiler version for consistency
    tarball_name = f"slurm-{slurm_version}-gcc{compiler_version}-software.tar.gz"

    container_tarball_path = f"/opt/slurm/build_output/{tarball_name}"

    try:
        # Create a temporary container from the image
        logger.debug(f"Creating temporary container {container_name}")
        result = subprocess.run(
            ["docker", "create", "--name", container_name, image_tag],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            msg = f"Failed to create container for extraction: {result.stderr}"
            logger.error(msg)
            console.print(f"[bold red]{escape(msg)}[/bold red]")
            raise SlurmFactoryError(msg)

        # Copy the tarball from the container
        logger.debug(f"Copying {container_tarball_path} from container to {output_path}")
        console.print(f"[dim]Copying tarball to {output_path}...[/dim]")

        result = subprocess.run(
            ["docker", "cp", f"{container_name}:{container_tarball_path}", str(output_path)],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            msg = f"Failed to copy tarball from container: {result.stderr}"
            logger.error(msg)
            console.print(f"[bold red]{escape(msg)}[/bold red]")
            raise SlurmFactoryError(msg)

        console.print(f"[bold green]✓ Extracted {tarball_name} to {output_path}[/bold green]")
        logger.debug(f"Successfully extracted package to {output_path}/{tarball_name}")

    except subprocess.TimeoutExpired:
        msg = "Extraction timed out"
        logger.error(msg)
        console.print(f"[bold red]{msg}[/bold red]")
        raise SlurmFactoryError(msg)
    except Exception as e:
        msg = f"Failed to extract package: {e}"
        logger.error(msg)
        console.print(f"[bold red]{escape(msg)}[/bold red]")
        raise SlurmFactoryError(msg)
    finally:
        # Clean up the temporary container
        try:
            subprocess.run(
                ["docker", "rm", container_name],
                capture_output=True,
                text=True,
                timeout=30,
            )
            logger.debug(f"Removed temporary container {container_name}")
        except Exception as e:
            logger.warning(f"Failed to remove temporary container: {e}")


def _push_slurm_to_buildcache(
    image_tag: str,
    slurm_version: str,
    compiler_version: str,
    publish_mode: str = "all",
    signing_key: str | None = None,
    gpg_private_key: str | None = None,
    gpg_passphrase: str | None = None,
) -> None:
    """
    Push Slurm specs to buildcache using spack buildcache push.

    This runs `spack buildcache push` inside the Docker container with AWS
    credentials/role passed as environment variables.

    Args:
        image_tag: Tag of the build Docker image
        slurm_version: Slurm version
        compiler_version: GCC compiler version
        publish_mode: What to publish - "slurm", "deps", or "all"
        signing_key: GPG key ID for signing packages (e.g., "0xKEYID")
        gpg_private_key: GPG private key (base64 encoded) to import into container
        gpg_passphrase: GPG key passphrase for non-interactive signing

    """
    console.print(f"[bold blue]Publishing to buildcache (mode: {publish_mode})...[/bold blue]")

    # NOTE: Spack adds build_cache/ subdirectory automatically - do NOT append /buildcache here
    s3_mirror_url = f"{S3_BUILDCACHE_BUCKET}/slurm/{slurm_version}/{compiler_version}"

    logger.debug(f"Publishing Slurm {slurm_version} to {S3_BUILDCACHE_BUCKET} (mode: {publish_mode})")

    # Check for AWS credentials - support both direct credentials and OIDC role

    aws_env = {}

    # Check for AWS credentials (GitHub Actions OIDC or static credentials)
    # The configure-aws-credentials action sets these environment variables
    if "AWS_ACCESS_KEY_ID" in os.environ:
        # Use temporary credentials from configure-aws-credentials action
        aws_env["AWS_ACCESS_KEY_ID"] = os.environ["AWS_ACCESS_KEY_ID"]
        aws_env["AWS_SECRET_ACCESS_KEY"] = os.environ["AWS_SECRET_ACCESS_KEY"]
        if "AWS_SESSION_TOKEN" in os.environ:
            aws_env["AWS_SESSION_TOKEN"] = os.environ["AWS_SESSION_TOKEN"]
        if "AWS_DEFAULT_REGION" in os.environ:
            aws_env["AWS_DEFAULT_REGION"] = os.environ["AWS_DEFAULT_REGION"]
        if "AWS_REGION" in os.environ:
            aws_env["AWS_REGION"] = os.environ["AWS_REGION"]
        logger.debug("Using AWS credentials from environment (GitHub Actions OIDC or configured credentials)")
    else:
        # Fall back to checking for credentials file
        aws_dir = Path.home() / ".aws"
        if not aws_dir.exists():
            msg = "AWS credentials not found. Set AWS_ACCESS_KEY_ID or configure ~/.aws/ credentials."
            logger.error(msg)
            console.print(f"[bold red]{escape(msg)}[/bold red]")
            raise SlurmFactoryError(msg)
        logger.debug("Using AWS credentials from ~/.aws/")

    try:
        # Determine signing flags
        if signing_key:
            signing_flags = f"--key {signing_key}"
            logger.debug(f"Using GPG signing key: {signing_key}")
        else:
            signing_flags = "--unsigned"
            logger.debug("Publishing unsigned packages")

        # Determine what to push based on publish_mode
        if publish_mode == "slurm":
            # Push only slurm package
            push_cmd = (
                f"spack buildcache push {signing_flags} --force --update-index "
                "--only=package s3-buildcache slurm"
            )
        elif publish_mode == "deps":
            # Push only dependencies (everything except slurm)
            s3_mirror_url = f"{S3_BUILDCACHE_BUCKET}/deps/{compiler_version}"
            push_cmd = (
                f"spack -e . buildcache push {signing_flags} --force --update-index "
                "--only=dependencies --with-build-dependencies s3-buildcache slurm"
            )
        else:  # all
            push_cmd = f"spack -e . buildcache push {signing_flags} --force --update-index s3-buildcache"

        console.print(f"[dim]Pushing packages to {s3_mirror_url}...[/dim]")
        # Build docker run command with AWS environment variables
        cmd = ["docker", "run", "--rm"]

        # Add AWS environment variables
        for key, value in aws_env.items():
            cmd.extend(["-e", f"{key}={value}"])

        # If GPG private key is provided, pass it as an environment variable
        if gpg_private_key:
            cmd.extend(["-e", f"GPG_PRIVATE_KEY={gpg_private_key}"])
            logger.debug("GPG private key will be imported into container")

        # If GPG passphrase is provided, pass it as an environment variable
        if gpg_passphrase:
            cmd.extend(["-e", f"GPG_PASSPHRASE={gpg_passphrase}"])
            logger.debug("GPG passphrase will be available in container")

        # Mount AWS credentials directory if not using environment credentials
        if "AWS_ACCESS_KEY_ID" not in aws_env:
            cmd.extend(["-v", f"{Path.home() / '.aws'}:/root/.aws:ro"])

        # Build the bash script to run in the container
        bash_script_parts = ["source /opt/spack/share/spack/setup-env.sh"]

        # If GPG private key is provided, import it before running buildcache commands
        if gpg_private_key:
            bash_script_parts.extend(
                [
                    # Import GPG key using Spack's gpg trust command (imports to /opt/spack/opt/spack/gpg)
                    'echo "$GPG_PRIVATE_KEY" | base64 -d > /tmp/gpg-key.asc',
                    "spack gpg trust /tmp/gpg-key.asc",
                    # Store passphrase for GPG wrapper to use
                    'echo "${GPG_PASSPHRASE}" > /tmp/gpg-passphrase.txt',
                    # Configure GPG with loopback pinentry
                    "mkdir -p /opt/spack/opt/spack/gpg",
                    'echo "pinentry-mode loopback" > /opt/spack/opt/spack/gpg/gpg.conf',
                    (
                        'echo -e "allow-loopback-pinentry\\ndefault-cache-ttl 34560000\\n'
                        'max-cache-ttl 34560000" > /opt/spack/opt/spack/gpg/gpg-agent.conf'
                    ),
                    # Kill and restart agent
                    "gpgconf --homedir /opt/spack/opt/spack/gpg --kill gpg-agent 2>/dev/null || true",
                    "gpg-connect-agent --homedir /opt/spack/opt/spack/gpg /bye",
                    # Create GPG wrapper to inject passphrase when Spack calls gpg for signing
                    "mv /usr/bin/gpg /usr/bin/gpg-real",
                    (
                        r"""printf '#!/bin/bash\n# Wrapper to add passphrase for non-interactive signing\n"""
                        r"""if [[ "$*" == *"--clearsign"* ]]; then\n  exec /usr/bin/gpg-real """
                        r"""--pinentry-mode loopback --passphrase-file /tmp/gpg-passphrase.txt "$@"\n"""
                        r"""else\n  exec /usr/bin/gpg-real "$@"\nfi\n' > /usr/bin/gpg"""
                    ),
                    "chmod +x /usr/bin/gpg",
                ]
            )

        # Add spack environment and buildcache commands
        bash_script_parts.extend(
            [
                "cd /root/spack-project",
                "spack env activate .",
                f"spack mirror add --scope site s3-buildcache {s3_mirror_url}",
                push_cmd,
                # Update buildcache index after pushing (Spack 1.0+ requirement)
                #update_index_cmd,
            ]
        )

        # Join the script parts with &&
        bash_script = " && ".join(bash_script_parts)

        # Add image and command
        cmd.extend([image_tag, "bash", "-c", bash_script])

        console.print(f"[dim]Running spack buildcache push in {image_tag} with AWS credentials[/dim]")
        logger.debug(f"Running: {' '.join(cmd[:10])}...")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=7200,  # 120 minutes for large uploads
        )

        if result.returncode != 0:
            msg = f"Failed to push to buildcache: {result.stderr}"
            logger.error(msg)
            console.print(f"[dim]stdout: {result.stdout}[/dim]")
            console.print(f"[bold red]{escape(msg)}[/bold red]")
            raise SlurmFactoryError(msg)

        # Always show buildcache push output for transparency
        if result.stdout:
            console.print(f"[dim]Buildcache push output:\n{result.stdout}[/dim]")
        else:
            console.print("[dim]No buildcache push output (command may have failed silently)[/dim]")

        if result.stderr:
            console.print(f"[yellow]Buildcache push stderr:\n{result.stderr}[/yellow]")

        console.print(f"[bold green]✓ Published to buildcache ({publish_mode})[/bold green]")
        logger.debug(f"Successfully published to {s3_mirror_url}")

    except subprocess.TimeoutExpired:
        msg = "Publishing timed out (>120 minutes)"
        logger.error(msg)
        console.print(f"[bold red]{msg}[/bold red]")
        raise SlurmFactoryError(msg)
    except Exception as e:
        msg = f"Failed to push to buildcache: {e}"
        logger.error(msg)
        console.print(f"[bold red]{escape(msg)}[/bold red]")
        raise SlurmFactoryError(msg)


def create_slurm_package(
    image_tag: str,
    slurm_version: str = "25.11",
    compiler_version: str = "13.4.0",
    gpu_support: bool = False,
    cache_dir: str = "",
    no_cache: bool = False,
    use_local_buildcache: bool = False,
    publish: str = "none",
    enable_hierarchy: bool = False,
    signing_key: str | None = None,
    gpg_private_key: str | None = None,
    gpg_passphrase: str | None = None,
) -> None:
    """Create slurm package in a Docker container using a multi-stage build."""
    console.print("[bold blue]Creating slurm package in Docker container...[/bold blue]")

    logger.debug(
        f"Building Slurm package: slurm_version={slurm_version}, compiler_version={compiler_version}, "
        f"gpu={gpu_support}, no_cache={no_cache}, use_local_buildcache={use_local_buildcache}, "
        f"publish={publish}, enable_hierarchy={enable_hierarchy}"
    )

    try:
        console.print("[bold yellow]🗑️  Performing fresh build - cleaning all caches...[/bold yellow]")

        # Remove old Docker images
        remove_old_docker_image(image_tag)

        # Always use Spack-built compiler for consistency and relocatability
        spack_yaml = generate_yaml_string(
            slurm_version=slurm_version,
            compiler_version=compiler_version,
            gpu_support=gpu_support,
            enable_hierarchy=enable_hierarchy,
        )
        logger.debug(f"Generated Spack YAML configuration ({len(spack_yaml)} chars)")

        # Generate multi-stage Dockerfile with embedded spack.yaml
        # This creates 3 stages:
        # 0. compiler-bootstrap: Build custom GCC toolchain (or reuse from buildcache)
        # 1. init: Ubuntu + deps + Spack (heavily cached)
        # 2. builder: Spack install + view + modules (cached on spack.yaml changes)
        # 3. packager: Copy assets + create tarball (invalidates on asset changes)
        logger.debug("Generating multi-stage Dockerfile")
        slurm_builder_dockerfile_content = _get_slurm_builder_dockerfile(
            spack_yaml,
            slurm_version,
            compiler_version=compiler_version,
            gpu_support=gpu_support,
        )
        logger.debug(f"Generated Dockerfile ({len(slurm_builder_dockerfile_content)} chars)")

        # Build all stages up to packager (the final stage)
        console.print(
            "[bold cyan]Building multi-stage Docker image (init → builder → packager)...[/bold cyan]"
        )
        build_docker_image(
            image_tag,
            slurm_builder_dockerfile_content,
            target="packager",  # Build all stages up to packager
        )

        console.print("[bold green]✓ Multi-stage build complete[/bold green]")

        _extract_slurm_tarball_from_image(
            image_tag=image_tag,
            output_dir=cache_dir,
            slurm_version=slurm_version,
            compiler_version=compiler_version,
        )

        # If publish is enabled, push to buildcache
        if publish != "none":
            console.print(f"[bold cyan]Publishing to buildcache ({publish})...[/bold cyan]")
            _push_slurm_to_buildcache(
                image_tag=image_tag,
                slurm_version=slurm_version,
                compiler_version=compiler_version,
                publish_mode=publish,
                signing_key=signing_key,
                gpg_private_key=gpg_private_key,
                gpg_passphrase=gpg_passphrase,
            )

        console.print("[bold green]✓ Slurm package built successfully[/bold green]")

    except SlurmFactoryStreamExecError as e:
        msg = f"Build failed: {e}"
        logger.error(msg)
        console.print(f"[bold red]{escape(msg)}[/bold red]")
        raise SlurmFactoryError(msg)
    except Exception as e:
        msg = f"Failed to create slurm package: {e}"
        logger.error(msg)
        console.print(f"[bold red]{escape(msg)}[/bold red]")
        raise SlurmFactoryError(msg)
