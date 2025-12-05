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

import base64
import logging
import os
import subprocess
import sys
import textwrap
from pathlib import Path

from rich.console import Console
from rich.markup import escape

from slurm_factory.config import Settings
from slurm_factory.constants import (
    COMPILER_TOOLCHAINS,
    CONTAINER_BUILD_OUTPUT_DIR,
    CONTAINER_CACHE_DIR,
    CONTAINER_SLURM_DIR,
    CONTAINER_SPACK_PROJECT_DIR,
    CONTAINER_SPACK_TEMPLATES_DIR,
    DOCKER_COMMIT_TIMEOUT,
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
                encoded_content = base64.b64encode(content_bytes).decode("ascii")

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


def get_slurm_build_script(toolchain: str) -> str:
    """
    Generate script to build Slurm with Spack using the OS-provided system compiler.

    Since we're using OS-based toolchains (noble, jammy, etc.), we use the GCC compiler
    that's already installed in the Docker base image instead of downloading a custom-built
    GCC from buildcache.

    Args:
        toolchain: OS toolchain identifier (e.g., "noble", "jammy", "rockylinux9")

    Returns:
        Complete bash script for Slurm build using system compiler

    """
    # Get GCC version for this toolchain
    _, gcc_version, _, _, _ = COMPILER_TOOLCHAINS[toolchain]

    return textwrap.dedent(f"""\
        mkdir -p /opt/spack-stage/tmp
        export TMPDIR=/opt/spack-stage/tmp
        export TMP=/opt/spack-stage/tmp
        export TEMP=/opt/spack-stage/tmp
        # Copy spack.yaml from mount point to spack project (so it's in container filesystem)
        mkdir -p {CONTAINER_SPACK_PROJECT_DIR}
        cp /tmp/spack.yaml.mount {CONTAINER_SPACK_PROJECT_DIR}/spack.yaml
        source {SPACK_SETUP_SCRIPT}
        cd {CONTAINER_SPACK_PROJECT_DIR}
        spack env activate .
        echo '==> Installing GPG keys from keyserver...'
        gpg --batch --keyserver hkps://keyserver.ubuntu.com \\
            --recv-keys FDEA90667641505264EFD114DFB92630BCA5AB71 || {{
            echo 'WARNING: Failed to retrieve GPG key from keyserver'
            echo 'Will continue but may not be able to use binary packages'
        }}
        gpg --armor --export FDEA90667641505264EFD114DFB92630BCA5AB71 > /tmp/vantage-spack.pub
        spack gpg trust /tmp/vantage-spack.pub || {{
            echo 'WARNING: Failed to trust GPG keys'
            echo 'Will continue but may not be able to use binary packages'
        }}
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
        echo '==> Detecting system compilers...'
        spack compiler find --scope site
        echo '==> Available compilers:'
        spack compiler list
        echo '==> Verifying gcc@{gcc_version} is available...'
        if ! spack compiler list | grep -q "gcc@{gcc_version}"; then
            echo 'ERROR: gcc@{gcc_version} compiler not found'
            echo 'Available compilers:'
            spack compiler list
            echo 'Trying to find GCC in standard locations...'
            which gcc g++ gfortran || true
            gcc --version || true
            exit 1
        fi
        echo '✓ gcc@{gcc_version} available'
        spack compiler info gcc@{gcc_version}
        rm -f spack.lock

        echo '==> Concretizing Slurm packages with gcc@{gcc_version}...'
        spack -e . concretize -j $(nproc) -f --fresh

        # Clean up any stale locks before installation
        echo '==> Cleaning stale locks...'
        find /opt/spack-stage -name "*.lock" -mmin +60 -delete 2>/dev/null || true

        # Use limited parallelism to avoid lock contention (max 8 jobs)
        JOBS=$(( $(nproc) < 8 ? $(nproc) : 8 ))
        echo "==> Installing Slurm and all dependencies with $JOBS parallel jobs..."
        spack -e . install -j $(nproc) --reuse-deps --verbose || {{
            echo 'ERROR: spack install failed'
            echo 'Checking view status:'
            ls -la {CONTAINER_SLURM_DIR}/view 2>&1 || echo 'View directory does not exist'
            echo 'Installed specs:'
            spack find -v 2>&1 || true
            exit 1
        }}
        echo '==> Regenerating view to ensure all packages are properly linked...'
        spack -e . env view regenerate 2>&1 || {{
            echo 'ERROR: Failed to regenerate environment view'
            echo 'Last error output should be above'
            echo 'Checking view status:'
            ls -la {CONTAINER_SLURM_DIR}/view 2>&1 || echo 'View directory does not exist'
            echo 'Checking for conflicting files:'
            spack -e . env status -v
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
    toolchain: str = "noble",
    gpu_support: bool = False,
) -> str:
    """
    Generate script to package everything into a tarball.

    Args:
        modulerc_script: The script to create .modulerc.lua file
        version: Slurm version (e.g., "25.11") for the tarball filename
        toolchain: OS toolchain identifier (e.g., "noble", "jammy", "rockylinux9")
        gpu_support: Whether GPU support is enabled (affects CUDA/ROCm handling)

    """
    tarball_base = f"slurm-{version}-{toolchain}-software"

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


def _get_slurm_base_dockerfile(
    operating_system: str,
) -> str:
    """
    Generate a base Dockerfile with all dependencies for building Slurm packages.

    This creates a reusable base image with:
    - Ubuntu/Rocky + system dependencies
    - Spack installation
    - Required directories

    The actual Spack build is executed via `docker run` on a container from this base image,
    which allows for better debugging and inspection of build failures.

    Args:
        operating_system: Operating system identifier for setup script

    Returns:
        A complete Dockerfile as a string for the base build image

    """
    # Generate all script components
    install_deps_script = COMPILER_TOOLCHAINS[operating_system][4]
    container_image = COMPILER_TOOLCHAINS[operating_system][3]

    install_spack_script = get_install_spack_script()
    create_spack_profile_script = get_create_spack_profile_script()

    return textwrap.dedent(
        f"""\
# syntax=docker/dockerfile:1
# Slurm Factory Base Build Container
# Generated by slurm-factory - DO NOT EDIT MANUALLY
#
# This image provides the base environment for building Slurm packages.
# The actual build is executed via `docker run` on a container from this image.
#
# ========================================================================
# Base Image - Install build deps and init base system with Spack
# ========================================================================
FROM {container_image}

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

RUN bash << 'SETUP_EOF'
{install_deps_script}
SETUP_EOF

# Install Spack v1.0.0
RUN {install_spack_script}

ENV SPACK_ROOT=/opt/spack
ENV PATH=$SPACK_ROOT/bin:$PATH
RUN {create_spack_profile_script}

# Create required directories including cache directories
RUN mkdir -p \
    {CONTAINER_SPACK_PROJECT_DIR} \
    {CONTAINER_SPACK_TEMPLATES_DIR}/modules \
    {CONTAINER_SLURM_DIR} && \
        mkdir -p {CONTAINER_CACHE_DIR}/buildcache {CONTAINER_CACHE_DIR}/source

WORKDIR {CONTAINER_SPACK_PROJECT_DIR}

CMD ["/bin/bash"]
"""
    )


def _extract_slurm_tarball_from_image(
    image_tag: str,
    output_dir: str,
    slurm_version: str,
    toolchain: str,
) -> None:
    """
    Extract the Slurm package tarball from a packager Docker image.

    Args:
        image_tag: Tag of the packager Docker image
        output_dir: Directory to extract the tarball to (will be appended with version/toolchain)
        slurm_version: Slurm version (for finding the correct tarball)
        toolchain: OS toolchain identifier used for the build

    """
    console.print(f"[bold blue]Extracting Slurm package from image {image_tag}...[/bold blue]")

    # Create slurm_version-specific output directory: ~/.slurm-factory/slurm_version/toolchain/
    base_path = Path(output_dir)
    output_path = base_path / slurm_version / toolchain
    output_path.mkdir(parents=True, exist_ok=True)

    logger.debug(f"Extracting package from image {image_tag} to {output_path}")

    container_name = f"slurm-factory-extract-{slurm_version.replace('.', '-')}"

    # Get GCC version from toolchain for tarball naming
    tarball_name = f"slurm-{slurm_version}-{toolchain}-software.tar.gz"

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


def sign_and_push_tarball_to_buildcache(
    tarball_path: Path,
    slurm_version: str,
    toolchain: str,
    gpg_private_key: str,
    gpg_passphrase: str,
    gpg_key_id: str,
) -> None:
    """
    Sign a tarball with GPG and upload both tarball and signature to S3.

    Creates a Docker container to handle GPG signing and S3 upload operations.

    Args:
        tarball_path: Path to the tarball file to sign and upload
        slurm_version: Slurm version (e.g., "25.11")
        toolchain: OS toolchain identifier (e.g., "noble")
        gpg_private_key: GPG private key (base64 encoded)
        gpg_passphrase: GPG key passphrase
        gpg_key_id: GPG key ID for signing

    Raises:
        SlurmFactoryError: If signing or upload fails

    """
    console.print("[bold blue]Signing and uploading tarball to buildcache...[/bold blue]")

    if not tarball_path.exists():
        msg = f"Tarball not found at {tarball_path}"
        logger.error(msg)
        console.print(f"[bold red]{escape(msg)}[/bold red]")
        raise SlurmFactoryError(msg)

    # Check for AWS credentials
    aws_env = {}
    if "AWS_ACCESS_KEY_ID" in os.environ:
        aws_env["AWS_ACCESS_KEY_ID"] = os.environ["AWS_ACCESS_KEY_ID"]
        aws_env["AWS_SECRET_ACCESS_KEY"] = os.environ["AWS_SECRET_ACCESS_KEY"]
        if "AWS_SESSION_TOKEN" in os.environ:
            aws_env["AWS_SESSION_TOKEN"] = os.environ["AWS_SESSION_TOKEN"]
        if "AWS_DEFAULT_REGION" in os.environ:
            aws_env["AWS_DEFAULT_REGION"] = os.environ["AWS_DEFAULT_REGION"]
        if "AWS_REGION" in os.environ:
            aws_env["AWS_REGION"] = os.environ["AWS_REGION"]
        logger.debug("Using AWS credentials from environment")
    else:
        aws_dir = Path.home() / ".aws"
        if not aws_dir.exists():
            msg = "AWS credentials not found. Set AWS_ACCESS_KEY_ID or configure ~/.aws/"
            logger.error(msg)
            console.print(f"[bold red]{escape(msg)}[/bold red]")
            raise SlurmFactoryError(msg)
        logger.debug("Using AWS credentials from ~/.aws/")

    tarball_name = tarball_path.name
    # S3_BUILDCACHE_BUCKET already includes s3:// prefix
    # Extract just the bucket name for AWS CLI
    s3_bucket_name = S3_BUILDCACHE_BUCKET.replace("s3://", "")
    s3_base_path = f"{toolchain}/{slurm_version}"

    try:
        # Create temporary directory for Dockerfile
        import tempfile

        sign_dir = Path(tempfile.mkdtemp(prefix="slurm-factory-sign-"))
        logger.debug(f"Created temporary signing directory: {sign_dir}")

        # Create Dockerfile that handles signing and uploading in one container
        dockerfile_content = textwrap.dedent("""
            FROM ubuntu:26.04

            RUN apt-get update && \\
                apt-get install -y gnupg python3 python3-pip && \\
                    apt-get clean -y && rm -rf /var/lib/apt/lists/* && \\
                        python3 -m pip install awscli --break-system-packages

            # Import GPG key
            ARG GPG_PRIVATE_KEY
            ARG GPG_PASSPHRASE
            ARG GPG_KEY_ID

            RUN echo "$GPG_PRIVATE_KEY" | base64 -d | \\
                gpg --batch --yes --passphrase "$GPG_PASSPHRASE" \\
                    --pinentry-mode loopback --import

            WORKDIR /workspace

            # Set up the entrypoint script
            COPY entrypoint.sh /entrypoint.sh
            RUN chmod +x /entrypoint.sh

            ENTRYPOINT ["/entrypoint.sh"]
        """).strip()

        # Create entrypoint script that signs and uploads
        entrypoint_content = textwrap.dedent(f"""
            #!/bin/bash
            set -e

            TARBALL_NAME="{tarball_name}"
            S3_BUCKET="{s3_bucket_name}"
            S3_PATH="{s3_base_path}"

            echo "🔐 Signing tarball with GPG key $GPG_KEY_ID..."
            echo "$GPG_PASSPHRASE" | gpg --batch --yes --passphrase-fd 0 \\
                --pinentry-mode loopback \\
                --local-user "$GPG_KEY_ID" \\
                --detach-sign \\
                --armor \\
                --output /workspace/$TARBALL_NAME.asc \\
                /workspace/$TARBALL_NAME

            echo "✓ Tarball signed successfully"

            echo "📦 Uploading tarball to S3..."
            aws s3 cp /workspace/$TARBALL_NAME \\
                s3://$S3_BUCKET/$S3_PATH/$TARBALL_NAME

            echo "✓ Tarball uploaded successfully"

            echo "📦 Uploading signature to S3..."
            aws s3 cp /workspace/$TARBALL_NAME.asc \\
                s3://$S3_BUCKET/$S3_PATH/$TARBALL_NAME.asc

            echo "✓ Signature uploaded successfully"
            echo "✅ Tarball and signature published to s3://$S3_BUCKET/$S3_PATH/"
        """).strip()

        dockerfile_path = sign_dir / "Dockerfile.sign"
        dockerfile_path.write_text(dockerfile_content)
        entrypoint_path = sign_dir / "entrypoint.sh"
        entrypoint_path.write_text(entrypoint_content)
        logger.debug(f"Created Dockerfile at {dockerfile_path}")
        logger.debug(f"Created entrypoint script at {entrypoint_path}")

        # Build signing and upload image
        console.print("[dim]Building GPG signing and upload container...[/dim]")
        build_cmd = [
            "docker",
            "build",
            "--build-arg",
            f"GPG_PRIVATE_KEY={gpg_private_key}",
            "--build-arg",
            f"GPG_PASSPHRASE={gpg_passphrase}",
            "--build-arg",
            f"GPG_KEY_ID={gpg_key_id}",
            "-f",
            str(dockerfile_path),
            "-t",
            "tarball-signer-uploader",
            str(sign_dir),
        ]

        result = subprocess.run(
            build_cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode != 0:
            msg = f"Failed to build signing container: {result.stderr}"
            logger.error(msg)
            console.print(f"[bold red]{escape(msg)}[/bold red]")
            raise SlurmFactoryError(msg)

        # Run signing and upload container
        console.print(f"[dim]Signing tarball with GPG key {gpg_key_id} and uploading to S3...[/dim]")
        # Build docker run command with environment variables
        run_cmd = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{tarball_path}:/workspace/{tarball_name}:ro",
            "-e",
            f"GPG_PASSPHRASE={gpg_passphrase}",
            "-e",
            f"GPG_KEY_ID={gpg_key_id}",
        ]
        # Add AWS credentials to container
        for key, value in aws_env.items():
            run_cmd.extend(["-e", f"{key}={value}"])

        # Mount AWS credentials directory if not using environment credentials
        if "AWS_ACCESS_KEY_ID" not in aws_env:
            run_cmd.extend(["-v", f"{Path.home() / '.aws'}:/root/.aws:ro"])

        run_cmd.append("tarball-signer-uploader")

        result = subprocess.run(
            run_cmd,
            capture_output=True,
            text=True,
            timeout=1800,  # 30 minutes for large uploads
        )

        if result.returncode != 0:
            msg = f"Failed to sign and upload tarball: {result.stderr}"
            logger.error(msg)
            console.print(f"[bold red]{escape(msg)}[/bold red]")
            raise SlurmFactoryError(msg)

        console.print(f"[bold green]{escape(result.stdout.strip())}[/bold green]")
        logger.debug(result.stdout)

        # Cleanup Docker image
        subprocess.run(
            ["docker", "rmi", "tarball-signer-uploader"],
            capture_output=True,
            timeout=30,
        )

        # Cleanup temporary directory
        import shutil

        shutil.rmtree(sign_dir, ignore_errors=True)
        logger.debug(f"Cleaned up temporary signing directory: {sign_dir}")

        console.print("[bold green]✓ Tarball and signature published successfully[/bold green]")

    except subprocess.TimeoutExpired:
        msg = "Signing or upload timed out"
        logger.error(msg)
        console.print(f"[bold red]{msg}[/bold red]")
        raise SlurmFactoryError(msg)
    except Exception as e:
        msg = f"Failed to sign and upload tarball: {e}"
        logger.error(msg)
        console.print(f"[bold red]{escape(msg)}[/bold red]")
        raise SlurmFactoryError(msg)


def _push_slurm_to_buildcache(
    image_tag: str,
    slurm_version: str,
    toolchain: str,
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
        toolchain: OS toolchain identifier
        publish_mode: What to publish - "slurm", "deps", or "all"
        signing_key: GPG key ID for signing packages (e.g., "0xKEYID")
        gpg_private_key: GPG private key (base64 encoded) to import into container
        gpg_passphrase: GPG key passphrase for non-interactive signing

    """
    console.print(f"[bold blue]Publishing to buildcache (mode: {publish_mode})...[/bold blue]")

    # NOTE: Spack adds build_cache/ subdirectory automatically - do NOT append /buildcache here
    s3_mirror_url = f"{S3_BUILDCACHE_BUCKET}/{toolchain}/slurm/{slurm_version}"

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
            s3_mirror_url = f"{S3_BUILDCACHE_BUCKET}/{toolchain}/slurm/deps"
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
                    # Ensure GPG home directory exists
                    "mkdir -p /opt/spack/opt/spack/gpg",
                    # Configure GPG with loopback pinentry BEFORE importing keys
                    'echo "pinentry-mode loopback" > /opt/spack/opt/spack/gpg/gpg.conf',
                    (
                        'echo -e "allow-loopback-pinentry\\ndefault-cache-ttl 34560000\\n'
                        'max-cache-ttl 34560000" > /opt/spack/opt/spack/gpg/gpg-agent.conf'
                    ),
                    # Store passphrase for GPG wrapper to use
                    'echo "${GPG_PASSPHRASE}" > /tmp/gpg-passphrase.txt',
                    # Create GPG wrapper to inject passphrase when Spack calls gpg for signing
                    "mv /usr/bin/gpg /usr/bin/gpg-real",
                    (
                        r"""printf '#!/bin/bash\n# Wrapper to add passphrase for non-interactive signing\n"""
                        r"""if [[ "$*" == *"--clearsign"* ]] || [[ "$*" == *"--detach-sign"* ]]; then\n"""
                        r"""  exec /usr/bin/gpg-real --pinentry-mode loopback """
                        r"""--passphrase-file /tmp/gpg-passphrase.txt "$@"\n"""
                        r"""else\n  exec /usr/bin/gpg-real "$@"\nfi\n' > /usr/bin/gpg"""
                    ),
                    "chmod +x /usr/bin/gpg",
                    # Import GPG key using Spack's gpg trust command (imports to /opt/spack/opt/spack/gpg)
                    'echo "$GPG_PRIVATE_KEY" | base64 -d > /tmp/gpg-key.asc',
                    "spack gpg trust /tmp/gpg-key.asc",
                    # Extract and import the public key separately to ensure it's registered
                    'echo "$GPG_PRIVATE_KEY" | base64 -d | gpg --homedir /opt/spack/opt/spack/gpg --import',
                    # Export public key and re-import to ensure it's in the keyring
                    (
                        f"gpg --homedir /opt/spack/opt/spack/gpg --armor "
                        f"--export {signing_key} > /tmp/pubkey.asc"
                    ),
                    "gpg --homedir /opt/spack/opt/spack/gpg --import /tmp/pubkey.asc",
                    # Start GPG agent with our configuration
                    "gpgconf --homedir /opt/spack/opt/spack/gpg --kill gpg-agent 2>/dev/null || true",
                    "gpg-connect-agent --homedir /opt/spack/opt/spack/gpg /bye",
                    # Verify the key is present
                    'echo "Verifying GPG keys are available:"',
                    "spack gpg list",
                    "gpg --homedir /opt/spack/opt/spack/gpg --list-keys",
                ]
            )

        # Add spack environment and buildcache commands
        bash_script_parts.extend(
            [
                "cd /root/spack-project",
                "spack env activate .",
                f"spack mirror add --scope site s3-buildcache {s3_mirror_url}",
                # Don't install/trust keys or update index before push - buildcache may be empty
                # The push command with --update-index will create the index after pushing
                push_cmd,
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
            console.print(f"[dim]stdout: {escape(result.stdout)}[/dim]")
            console.print(f"[bold red]{escape(msg)}[/bold red]")
            raise SlurmFactoryError(msg)

        # Always show buildcache push output for transparency
        if result.stdout:
            console.print(f"[dim]Buildcache push output:\n{escape(result.stdout)}[/dim]")
        else:
            console.print("[dim]No buildcache push output (command may have failed silently)[/dim]")

        if result.stderr:
            console.print(f"[yellow]Buildcache push stderr:\n{escape(result.stderr)}[/yellow]")

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


def _run_spack_build_in_container(
    container_name: str,
    base_image: str,
    settings: Settings,
    spack_yaml: str,
    toolchain: str,
    slurm_version: str,
    gpu_support: bool,
    keep_container: bool = False,
) -> None:
    """
    Run the Spack build process inside a Docker container with mounted volumes.

    This approach allows better debugging and inspection compared to building everything
    in the Dockerfile. The container persists after build failures for inspection.

    Args:
        container_name: Name for the build container
        base_image: Tag of the base Docker image to use
        settings: Application settings with cache directories
        spack_yaml: Spack environment configuration
        toolchain: OS toolchain identifier
        slurm_version: Slurm version being built
        gpu_support: Whether GPU support is enabled
        keep_container: If True, don't remove container after build (for publishing)

    """
    console.print(f"[bold cyan]Running Spack build in container {container_name}...[/bold cyan]")
    logger.debug(f"Starting build container: {container_name}")

    # Prepare directories for mounting
    spack_stage_dir: Path = settings.spack_stage_dir / toolchain / slurm_version
    spack_buildcache_dir: Path = settings.spack_buildcache_dir
    spack_sourcecache_dir: Path = settings.spack_sourcecache_dir
    tarball_build_output_dir: Path = settings.builds_dir / toolchain / slurm_version

    for dir_path in [spack_stage_dir, spack_buildcache_dir, spack_sourcecache_dir, tarball_build_output_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {dir_path}")

    # Generate build scripts
    module_template_content = get_module_template_content()
    slurm_build_script = get_slurm_build_script(toolchain)
    modulerc_script = get_modulerc_creation_script(
        module_dir=f"{CONTAINER_SLURM_DIR}/view/assets/modules/slurm",
        modulerc_path=f"{CONTAINER_SLURM_DIR}/view/assets/modules/slurm/.modulerc.lua",
    )
    create_slurm_tarball_script = get_create_slurm_tarball_script(
        modulerc_script, slurm_version, toolchain, gpu_support
    )
    move_assets_script = get_move_slurm_assets_to_container_str()

    try:
        # Write spack.yaml to a temp file for mounting
        console.print("[dim]Preparing configuration files...[/dim]")
        spack_yaml_file = Path(f"/tmp/spack-{container_name}.yaml")
        spack_yaml_file.write_text(spack_yaml)

        # Write module template to a temp file for mounting
        module_template_file = Path(f"/tmp/module-{container_name}.lua")
        module_template_file.write_text(module_template_content)

        # Write build script to a temp file for mounting
        build_script_file = Path(f"/tmp/build-script-{container_name}.sh")
        build_script_file.write_text(slurm_build_script)

        # Execute the Spack build script using docker run
        console.print("[bold cyan]Executing Spack build in container...[/bold cyan]")
        console.print("[yellow]This may take 30-60 minutes depending on cache availability...[/yellow]")

        # Start container in detached mode with sleep to keep it alive
        build_script_cmd = [
            "docker",
            "run",
            "-dt",  # Detached mode with TTY for CUDA installer
            "--name",
            container_name,
            "-v",
            f"{spack_stage_dir}:/opt/spack-stage",
            "-v",
            f"{spack_buildcache_dir}:{CONTAINER_CACHE_DIR}/buildcache",
            "-v",
            f"{spack_sourcecache_dir}:{CONTAINER_CACHE_DIR}/source",
            "-v",
            f"{tarball_build_output_dir}:{CONTAINER_BUILD_OUTPUT_DIR}",
            "-v",
            f"{spack_yaml_file}:/tmp/spack.yaml.mount:ro",
            "-v",
            f"{module_template_file}:{CONTAINER_SPACK_TEMPLATES_DIR}/modules/relocatable_modulefile.lua",
            "-v",
            f"{build_script_file}:/tmp/build-script.sh:ro",
            "-e",
            "SPACK_USER_CACHE_PATH=/opt/spack-stage",
            "-e",
            "TMPDIR=/opt/spack-stage/tmp",
            "-e",
            "TMP=/opt/spack-stage/tmp",
            "-e",
            "TEMP=/opt/spack-stage/tmp",
            base_image,
            "sleep",
            "infinity",
        ]

        logger.debug(f"Starting container: {' '.join(build_script_cmd)}")

        subprocess.run(build_script_cmd, check=True, capture_output=True)

        # Execute the build script in the running container
        exec_build_cmd = [
            "docker",
            "exec",
            container_name,
            "/bin/bash",
            "/tmp/build-script.sh",
        ]

        result = subprocess.run(
            exec_build_cmd,
            check=False,  # Don't raise exception on non-zero exit
        )

        # Clean up temp files
        spack_yaml_file.unlink()
        module_template_file.unlink()
        build_script_file.unlink()

        if result.returncode != 0:
            console.print("[bold red]Spack build failed![/bold red]")
            console.print(f"[yellow]Container {container_name} has exited with errors[/yellow]")
            console.print(
                f"[dim]Check logs at: {spack_stage_dir}/root/spack-stage-*/spack-build-out.txt[/dim]"
            )
            raise SlurmFactoryError("Spack build failed")

        console.print("[green]✓ Spack build completed successfully[/green]")

        # Copy assets and create tarball in the build container
        console.print("[bold cyan]Creating tarball package...[/bold cyan]")

        # Execute asset moving script in the build container
        asset_exec_cmd = [
            "docker",
            "exec",
            "-i",
            container_name,
            "/bin/bash",
        ]

        process = subprocess.Popen(
            asset_exec_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        stdout, _ = process.communicate(input=move_assets_script)
        console.print(escape(stdout), end="")

        if process.returncode != 0:
            raise SlurmFactoryError("Failed to move assets")

        # Execute tarball creation script in the build container
        tarball_exec_cmd = [
            "docker",
            "exec",
            "-i",
            container_name,
            "/bin/bash",
        ]

        process = subprocess.Popen(
            tarball_exec_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        stdout, _ = process.communicate(input=create_slurm_tarball_script)
        console.print(escape(stdout), end="")

        if process.returncode != 0:
            raise SlurmFactoryError("Failed to create tarball")

        console.print("[green]✓ Tarball created successfully[/green]")

        # Clean up the build container (unless we need it for publishing)
        if not keep_container:
            subprocess.run(
                ["docker", "rm", "-f", container_name],
                capture_output=True,
                text=True,
                timeout=30,
            )
        else:
            console.print(f"[dim]Keeping container {container_name} for publishing...[/dim]")

        # Tarball is already in the mounted directory, no need to copy
        tarball_name = f"slurm-{slurm_version}-{toolchain}-software.tar.gz"
        console.print(
            f"[bold green]✓ Tarball {tarball_name} available at {tarball_build_output_dir}[/bold green]"
        )

    except subprocess.TimeoutExpired:
        console.print("[bold red]Container operation timed out[/bold red]")
        console.print(f"[yellow]Container {container_name} may still be running[/yellow]")
        console.print(f"[dim]Access it with: docker exec -it {container_name} bash[/dim]")
        raise SlurmFactoryError("Container operation timed out")
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Container operation failed: {e}[/bold red]")
        console.print(f"[yellow]Container {container_name} is still running for debugging[/yellow]")
        console.print(f"[dim]Access it with: docker exec -it {container_name} bash[/dim]")
        raise SlurmFactoryError(f"Container operation failed: {e}")
    except Exception as e:
        console.print(f"[bold red]Build failed: {e}[/bold red]")
        console.print(f"[yellow]Container {container_name} is still running for debugging[/yellow]")
        console.print(f"[dim]Access it with: docker exec -it {container_name} bash[/dim]")
        raise


def create_slurm_package(
    image_tag: str,
    settings: Settings,
    slurm_version: str = "25.11",
    toolchain: str = "noble",
    gpu_support: bool = False,
    no_cache: bool = False,
    publish: str = "none",
    buildcache: str = "none",
    enable_hierarchy: bool = False,
    signing_key: str | None = None,
    gpg_private_key: str | None = None,
    gpg_passphrase: str | None = None,
) -> None:
    """Create slurm package in a Docker container using a multi-stage build."""
    console.print("[bold blue]Creating slurm package in Docker container...[/bold blue]")

    logger.debug(
        f"Building Slurm package: slurm_version={slurm_version}, toolchain={toolchain}, "
        f"gpu={gpu_support}, no_cache={no_cache}, cache_dir={settings.home_cache_dir}, "
        f"publish={publish}, enable_hierarchy={enable_hierarchy}"
    )

    # Generate container and image names
    container_name = image_tag.replace(":", "-")  # Docker container names can't have ':'
    base_image_tag = f"{image_tag}-base"

    try:
        console.print(
            "[bold yellow]🗑️  Performing fresh build - cleaning old containers/images...[/bold yellow]"
        )

        # Remove old container if it exists
        subprocess.run(
            ["docker", "rm", "-f", container_name],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Remove old Docker images
        remove_old_docker_image(image_tag)
        remove_old_docker_image(base_image_tag)

        # Always use Spack-built compiler for consistency and relocatability
        spack_yaml = generate_yaml_string(
            slurm_version=slurm_version,
            toolchain=toolchain,
            buildcache=buildcache,
            gpu_support=gpu_support,
            enable_hierarchy=enable_hierarchy,
        )
        logger.debug(f"Generated Spack YAML configuration ({len(spack_yaml)} chars)")

        # Generate base Dockerfile (just dependencies + Spack, no build steps)
        logger.debug("Generating base Dockerfile")
        base_dockerfile_content = _get_slurm_base_dockerfile(
            operating_system=toolchain,
        )
        logger.debug(f"Generated Dockerfile ({len(base_dockerfile_content)} chars)")

        # Build the base image
        console.print("[bold cyan]Building base Docker image (Ubuntu + Spack)...[/bold cyan]")
        build_docker_image(
            base_image_tag,
            settings=settings,
            dockerfile_content=base_dockerfile_content,
            slurm_version=slurm_version,
            toolchain=toolchain,
            target="",  # No target for single-stage build
            use_cache=False,  # Fresh build
        )
        console.print(f"[bold green]✓ Base image complete (tagged as {base_image_tag})[/bold green]")

        # Check if we need to keep the container for publishing
        needs_publish = bool(
            gpg_private_key and gpg_passphrase and signing_key
            and (publish == "slurm" or publish == "deps")
        )

        # Run the Spack build inside a container with mounted volumes
        _run_spack_build_in_container(
            container_name=container_name,
            base_image=base_image_tag,
            settings=settings,
            spack_yaml=spack_yaml,
            toolchain=toolchain,
            slurm_version=slurm_version,
            gpu_support=gpu_support,
            keep_container=needs_publish,
        )

        # Calculate tarball output directory for publishing
        tarball_build_output_dir = settings.builds_dir / toolchain / slurm_version

        # If publish is enabled, push to buildcache
        if (gpg_private_key and gpg_passphrase and signing_key) and (publish == "slurm" or publish == "deps"):
            console.print(f"[bold cyan]Publishing to buildcache ({publish})...[/bold cyan]")

            # Commit the container to an image so we can use it with _push_slurm_to_buildcache
            # Note: spack.yaml was copied into the container filesystem at build start,
            # so it will be included in the committed image.
            temp_image_tag = f"{image_tag}-temp"
            console.print(
                f"[dim]Committing container {container_name} to temporary image {temp_image_tag}...[/dim]"
            )
            commit_result = subprocess.run(
                ["docker", "commit", container_name, temp_image_tag],
                capture_output=True,
                text=True,
                timeout=DOCKER_COMMIT_TIMEOUT,
            )
            if commit_result.returncode != 0:
                error_msg = commit_result.stderr.strip() or commit_result.stdout.strip() or "Unknown error"
                raise SlurmFactoryError(f"Failed to commit container {container_name}: {error_msg}")

            try:
                _push_slurm_to_buildcache(
                    image_tag=temp_image_tag,
                    slurm_version=slurm_version,
                    toolchain=toolchain,
                    publish_mode=publish,
                    signing_key=signing_key,
                    gpg_private_key=gpg_private_key,
                    gpg_passphrase=gpg_passphrase,
                )

                # Sign and upload the tarball if publishing slurm
                if publish == "slurm":
                    console.print("[bold cyan]Signing and uploading tarball...[/bold cyan]")
                    tarball_name = f"slurm-{slurm_version}-{toolchain}-software.tar.gz"
                    tarball_path = tarball_build_output_dir / tarball_name
                    sign_and_push_tarball_to_buildcache(
                        tarball_path=tarball_path,
                        slurm_version=slurm_version,
                        toolchain=toolchain,
                        gpg_private_key=gpg_private_key,
                        gpg_passphrase=gpg_passphrase,
                        gpg_key_id=signing_key,
                    )
            finally:
                # Clean up temporary image
                console.print(f"[dim]Removing temporary image {temp_image_tag}...[/dim]")
                remove_old_docker_image(temp_image_tag)
                # Clean up the build container now that publishing is done
                console.print(f"[dim]Removing build container {container_name}...[/dim]")
                subprocess.run(
                    ["docker", "rm", "-f", container_name],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

        console.print("[bold green]✓ Slurm package built successfully[/bold green]")

        # Provide instructions for accessing the build container
        console.print("\n[cyan]💡 To inspect build artifacts and logs:[/cyan]")
        console.print("[dim]  # Access the build container:[/dim]")
        console.print(f"[dim]  docker exec -it {container_name} bash[/dim]")
        console.print("\n[dim]  # Inside container:[/dim]")
        console.print("[dim]  ls -la /opt/spack-stage  # Spack build logs and stage directory[/dim]")
        console.print(f"[dim]  ls -la {escape(CONTAINER_SLURM_DIR)}/view  # Built Slurm installation[/dim]")
        console.print("\n[dim]  # Stop and remove container when done:[/dim]")
        console.print(f"[dim]  docker stop {container_name} && docker rm {container_name}[/dim]")

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
