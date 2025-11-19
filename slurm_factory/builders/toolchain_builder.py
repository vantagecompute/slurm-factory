#!/usr/bin/env python3
# Copyright 2024 Vantage Compute, Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""GCC compiler build process management."""

import logging
import subprocess
import textwrap
import uuid
from pathlib import Path

import typer
from rich.console import Console
from rich.markup import escape

from slurm_factory.constants import (
    CONTAINER_CACHE_DIR,
    INSTANCE_NAME_PREFIX,
    S3_BUILDCACHE_BUCKET,
)
from slurm_factory.exceptions import SlurmFactoryError, SlurmFactoryStreamExecError
from slurm_factory.spack_yaml import generate_compiler_bootstrap_yaml
from slurm_factory.utils import (
    build_docker_image,
    get_create_spack_profile_script,
    get_install_spack_script,
    get_install_system_deps_script,
    remove_old_docker_image,
)

logger = logging.getLogger(__name__)
console = Console()


def build_compiler(
    ctx: typer.Context,
    compiler_version: str = "13.4.0",
    no_cache: bool = False,
    publish: str = "none",
    signing_key: str | None = None,
    gpg_private_key: str | None = None,
    gpg_passphrase: str | None = None,
):
    """Build a GCC compiler toolchain in a Docker container."""
    console = Console()

    # Initialize settings and ensure cache directories exist
    settings = ctx.obj.settings

    logger.debug(
        f"Starting compiler build with parameters: compiler_version={compiler_version}, "
        f"no_cache={no_cache}, publish={publish}, has_gpg_key={gpg_private_key is not None}"
    )
    settings.ensure_cache_dirs()
    logger.debug(f"Ensured cache directories exist at {settings.home_cache_dir}")

    # Check if Docker is available
    try:
        result = subprocess.run(
            ["docker", "version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            console.print("[bold red]Docker is not running or not accessible[/bold red]")
            logger.error("Docker version check failed")
            raise SlurmFactoryError("Docker is not available. Please ensure Docker is installed and running.")
    except FileNotFoundError:
        console.print("[bold red]Docker is not installed[/bold red]")
        logger.error("Docker command not found")
        raise SlurmFactoryError("Docker is not installed. Please install Docker first.")
    except subprocess.TimeoutExpired:
        console.print("[bold red]Docker check timed out[/bold red]")
        logger.error("Docker version check timed out")
        raise SlurmFactoryError("Docker is not responding. Please check your Docker installation.")

    console.print(f"Starting compiler build process for GCC {compiler_version}")
    logger.debug(f"Building compiler version {compiler_version}")

    # Generate unique container name for this build
    short_uuid = f"{uuid.uuid4()}"[:8]
    safe_version = compiler_version.replace(".", "-")
    container_name = f"{INSTANCE_NAME_PREFIX}-compiler-{safe_version}-{short_uuid}"
    image_tag = f"{INSTANCE_NAME_PREFIX}:compiler-{safe_version}-{short_uuid}"
    logger.debug(f"Generated container name: {container_name}")
    logger.debug(f"Generated image tag: {image_tag}")

    console.print(f"[bold blue]Building Docker image for compiler {container_name}...[/bold blue]")

    try:
        # Build the compiler package
        _compiler_builder(
            image_tag=image_tag,
            compiler_version=compiler_version,
            no_cache=no_cache,
            publish=publish,
            signing_key=signing_key,
            gpg_private_key=gpg_private_key,
            gpg_passphrase=gpg_passphrase,
        )
        logger.debug("Compiler package creation completed")
        console.print("[bold green]✓ Compiler package created successfully[/bold green]")
    except SlurmFactoryError as e:
        logger.error(f"Failed to create compiler package: {e}")
        console.print(f"[bold red]Failed to create compiler package:[/bold red] {escape(str(e))}")
        console.print(f"[yellow]Build container {container_name} may be left running for debugging[/yellow]")
        raise

    logger.info(f"Compiler build process completed successfully for GCC {compiler_version}")
    console.print("[bold green]Compiler build completed successfully![/bold green]")


def _get_compiler_builder_dockerfile(compiler_version: str) -> str:
    """
    Generate a Dockerfile for building only the compiler toolchain.

    This creates a standalone build for the compiler that can be published
    to the buildcache and reused across multiple Slurm builds.

    Args:
        compiler_version: GCC compiler version to build

    Returns:
        A complete Dockerfile as a string for building the compiler

    """
    # Generate all script components
    install_deps_script = get_install_system_deps_script()
    install_spack_script = get_install_spack_script()
    create_spack_profile_script = get_create_spack_profile_script()

    # Generate bootstrap spack.yaml for building the compiler

    bootstrap_yaml = generate_compiler_bootstrap_yaml(
        compiler_version=compiler_version,
        buildcache_root=f"{CONTAINER_CACHE_DIR}/buildcache",
        sourcecache_root=f"{CONTAINER_CACHE_DIR}/source",
    )

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
RUN {create_spack_profile_script}

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
# The packages config sets gcc externals to empty list, but we need to ensure
# Spack doesn't auto-detect gcc as an external package during concretization.
# Remove any cached Spack state first to ensure truly clean build
RUN rm -rf /opt/spack/var/spack/cache/* \
           /opt/spack/var/spack/junit-report/* \
           /opt/spack-compiler-install/.spack-db \
           /opt/spack-compiler-install/.spack-empty \
           2>/dev/null || true

RUN bash << 'BASH_EOF'
set -e
source /opt/spack/share/spack/setup-env.sh
eval $(spack env activate --sh .)

# Show environment info for debugging
echo "==> Spack environment info:"
spack env status
spack compiler list

# Concretize with explicit preference to build from source
echo "==> Starting concretization..."
spack -e . concretize -j $(nproc) -f

# Install
echo "==> Starting installation..."
spack -e . install -j $(nproc) --verbose

echo "==> Installation complete"
BASH_EOF

# Register the newly built compiler with Spack at site scope
# The view at /opt/spack-compiler is automatically created by the environment configuration
# Use --scope site to make compiler available globally (not just in the environment)
# Use explicit path to ensure compiler is found correctly
RUN bash -c 'source /opt/spack/share/spack/setup-env.sh && \\
    spack compiler find --scope site /opt/spack-compiler'

# NOTE: gcc-runtime is built automatically as a dependency of gcc and
# is pushed to the buildcache to ensure completeness. This allows users
# to install the compiler from buildcache with --cache-only.

# Verify compiler installation
RUN /opt/spack-compiler/bin/gcc --version && \\
    /opt/spack-compiler/bin/g++ --version && \\
    /opt/spack-compiler/bin/gfortran --version

CMD ["/bin/bash"]
"""
    )


def _publish_compiler_to_buildcache(
    image_tag: str,
    compiler_version: str,
    signing_key: str | None = None,
    gpg_private_key: str | None = None,
    gpg_passphrase: str | None = None,
) -> None:
    """
    Publish compiler binaries to S3 buildcache using spack buildcache push.

    This runs `spack buildcache push` inside the Docker container with AWS
    credentials/role passed as environment variables.

    Args:
        image_tag: Tag of the compiler Docker image
        compiler_version: GCC compiler version
        signing_key: Optional GPG key ID for signing packages (e.g., "0xKEYID")
        gpg_private_key: Optional GPG private key (base64 encoded) to import into container
        gpg_passphrase: Optional GPG key passphrase for signing packages

    """
    console.print("[bold blue]Publishing compiler to S3 buildcache...[/bold blue]")

    s3_mirror_url = f"{S3_BUILDCACHE_BUCKET}/compilers/{compiler_version}"

    logger.debug(f"Publishing compiler {compiler_version} to {s3_mirror_url}")

    # Check for AWS credentials - support both direct credentials and OIDC role
    import os

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
        console.print(f"[dim]Pushing packages to {s3_mirror_url} using spack buildcache push...[/dim]")

        # Determine signing flags
        if signing_key:
            signing_flags = f"--key {signing_key}"
            logger.debug(f"Using GPG signing key: {signing_key}")
        else:
            signing_flags = "--unsigned"
            logger.debug("Publishing unsigned packages")

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

        # Push toolchain packages to S3 buildcache
        bash_script_parts.extend(
            [
                "cd /root/compiler-bootstrap",
                # Activate the environment
                "source /opt/spack/share/spack/setup-env.sh",
                "spack env activate .",
                # List what we're about to push for debugging
                "echo '==> Packages in environment:'",
                "spack find",
                # Add the mirror
                f"spack mirror add --scope site s3-buildcache {s3_mirror_url}",
                # Push ALL installed packages from the environment, including dependencies
                # This ensures gcc-runtime and other dependencies are available in buildcache
                # Use --force to overwrite existing packages
                # Use --update-index to regenerate index after pushing
                # Note: --verbose doesn't exist in Spack v1.0.0
                # Use --fail-fast to stop on first failure
                f"spack buildcache push {signing_flags} --force --update-index --fail-fast s3-buildcache",
                # Verify upload succeeded
                "echo '==> Buildcache contents:'",
                "spack buildcache list --allarch",
            ]
        )

        # Join the script parts with &&
        # Use && to ensure each step succeeds before continuing
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

        console.print(f"[bold green]✓ Published compiler to {s3_mirror_url}[/bold green]")
        logger.debug(f"Successfully published compiler to {s3_mirror_url}")

    except subprocess.TimeoutExpired:
        msg = "Publishing timed out (>120 minutes)"
        logger.error(msg)
        console.print(f"[bold red]{msg}[/bold red]")
        raise SlurmFactoryError(msg)
    except Exception as e:
        msg = f"Failed to publish compiler to buildcache: {e}"
        logger.error(msg)
        console.print(f"[bold red]{escape(msg)}[/bold red]")
        raise SlurmFactoryError(msg)


def _compiler_builder(
    image_tag: str,
    compiler_version: str = "13.4.0",
    no_cache: bool = False,
    publish: str = "none",
    signing_key: str | None = None,
    gpg_private_key: str | None = None,
    gpg_passphrase: str | None = None,
) -> None:
    """Create compiler package in a Docker container."""
    console.print("[bold blue]Creating compiler package in Docker container...[/bold blue]")

    logger.debug(
        f"Building compiler package: compiler_version={compiler_version}, "
        f"no_cache={no_cache}, publish={publish}, has_gpg_key={gpg_private_key is not None}"
    )

    try:
        # Generate Dockerfile for compiler-only build
        logger.debug("Removing old compiler Docker image if it exists")
        remove_old_docker_image(image_tag)

        logger.debug("Generating compiler Dockerfile")
        compiler_builder_dockerfile_content = _get_compiler_builder_dockerfile(
            compiler_version=compiler_version
        )
        logger.debug(f"Generated Dockerfile ({len(compiler_builder_dockerfile_content)} chars)")

        # Build the compiler image
        console.print("[bold cyan]Building compiler Docker image...[/bold cyan]")
        build_docker_image(
            image_tag,
            compiler_builder_dockerfile_content,
            target="compiler-packager",  # Build up to the packager stage
        )

        console.print("[bold green]✓ Compiler build complete[/bold green]")

        # If publish is enabled, push to S3 buildcache using spack
        if publish != "none":
            console.print(f"[bold cyan]Publishing compiler to S3 buildcache ({publish})...[/bold cyan]")
            _publish_compiler_to_buildcache(
                image_tag=image_tag,
                compiler_version=compiler_version,
                signing_key=signing_key,
                gpg_private_key=gpg_private_key,
                gpg_passphrase=gpg_passphrase,
            )

        console.print("[bold green]✓ Compiler package built successfully[/bold green]")

    except SlurmFactoryStreamExecError as e:
        msg = f"Compiler build failed: {e}"
        logger.error(msg)
        console.print(f"[bold red]{escape(msg)}[/bold red]")
        raise SlurmFactoryError(msg)
    except Exception as e:
        msg = f"Failed to create compiler package: {e}"
        logger.error(msg)
        console.print(f"[bold red]{escape(msg)}[/bold red]")
        raise SlurmFactoryError(msg)
