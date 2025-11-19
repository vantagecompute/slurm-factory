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

"""Build Slurm package command."""
import logging
import subprocess
import uuid

import typer
from rich.console import Console
from rich.markup import escape
from typing_extensions import Annotated

from slurm_factory.builders.slurm_builder import create_slurm_package
from slurm_factory.constants import COMPILER_TOOLCHAINS, INSTANCE_NAME_PREFIX, SlurmVersion
from slurm_factory.exceptions import SlurmFactoryError

logger = logging.getLogger(__name__)


def build_slurm(
    ctx: typer.Context,
    slurm_version: Annotated[
        SlurmVersion, typer.Option("--slurm-version", help="Slurm version to build")
    ] = SlurmVersion.v25_11,
    compiler_version: str = "13.4.0",
    gpu: bool = False,
    verify: bool = False,
    no_cache: bool = False,
    publish: str = "none",
    enable_hierarchy: Annotated[
        bool, typer.Option("--enable-hierarchy", help="Enable Core/Compiler/MPI module hierarchy")
    ] = False,
    signing_key: str | None = None,
    gpg_private_key: str | None = None,
    gpg_passphrase: str | None = None,
):
    """Build a specific Slurm version in a Docker container."""
    console = Console()

    # Initialize settings and ensure cache directories exist
    settings = ctx.obj["settings"]

    logger.debug(
        f"Starting build with parameters: slurm_version={slurm_version.value}, "
        f"compiler_version={compiler_version}, gpu={gpu}, verify={verify}, "
        f"publish={publish}, enable_hierarchy={enable_hierarchy}"
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

    version = slurm_version.value
    console.print(f"Starting Slurm build process for version {version}")
    logger.debug(f"Building Slurm version {slurm_version.value}")

    # Generate unique container name for this build
    short_uuid = f"{uuid.uuid4()}"[:8]
    safe_version = version.replace(".", "-")
    container_name = f"{INSTANCE_NAME_PREFIX}-{safe_version}-{short_uuid}"
    image_tag = f"{INSTANCE_NAME_PREFIX}:build-{safe_version}-{short_uuid}"
    logger.debug(f"Generated container name: {container_name}")
    logger.debug(f"Generated image tag: {image_tag}")

    console.print(f"[bold blue]Building Docker image and container {container_name}...[/bold blue]")

    try:
        # Build and run the container - this will handle everything
        create_slurm_package(
            image_tag=image_tag,
            slurm_version=version,
            compiler_version=compiler_version,
            gpu_support=gpu,
            cache_dir=f"{settings.home_cache_dir}",
            no_cache=no_cache,
            publish=publish,
            enable_hierarchy=enable_hierarchy,
            signing_key=signing_key,
            gpg_private_key=gpg_private_key,
            gpg_passphrase=gpg_passphrase,
        )
        logger.debug("Slurm package creation completed")
        console.print("[bold green]✓ Slurm package created successfully[/bold green]")
    except SlurmFactoryError as e:
        logger.error(f"Failed to create Slurm package: {e}")
        console.print(f"[bold red]Failed to create Slurm package:[/bold red] {escape(str(e))}")
        # Container cleanup will be handled in the utils module
        console.print(f"[yellow]Build container {container_name} may be left running for debugging[/yellow]")
        raise

    logger.info(f"Build process completed successfully for Slurm {version}")
    console.print("[bold green]Build completed successfully![/bold green]")


def build_slurm_command(
    ctx: typer.Context,
    slurm_version: Annotated[
        SlurmVersion, typer.Option("--slurm-version", help="Slurm version to build")
    ] = SlurmVersion.v25_11,
    compiler_version: Annotated[
        str,
        typer.Option(
            "--compiler-version",
            help=f"GCC compiler version to use ({', '.join(COMPILER_TOOLCHAINS.keys())})",
        ),
    ] = "13.4.0",
    gpu: Annotated[
        bool, typer.Option("--gpu", help="Enable GPU support (CUDA/ROCm) - creates larger packages")
    ] = False,
    verify: Annotated[
        bool, typer.Option("--verify", help="Enable relocatability verification (for CI/testing)")
    ] = False,
    no_cache: Annotated[
        bool, typer.Option("--no-cache", help="Force a fresh build without using Docker cache")
    ] = False,
    use_local_buildcache: Annotated[
        bool,
        typer.Option(
            "--use-local-buildcache",
            help="Use locally cached compiler tarball instead of building from source",
        ),
    ] = False,
    publish_s3: Annotated[
        bool,
        typer.Option("--publish-s3", help="Upload binaries to S3 (s3://slurm-factory-spack-binary-cache)"),
    ] = False,
    publish: Annotated[
        str,
        typer.Option(
            "--publish",
            help=(
                "Publish to buildcache: none (default), slurm (only Slurm), deps (only dependencies),"
                " all (Slurm + deps)"
            ),
        ),
    ] = "none",
    enable_hierarchy: Annotated[
        bool, typer.Option("--enable-hierarchy", help="Enable Core/Compiler/MPI module hierarchy")
    ] = False,
    signing_key: Annotated[
        str | None,
        typer.Option("--signing-key", help="GPG key ID for signing buildcache packages (e.g., '0xKEYID')"),
    ] = None,
    gpg_private_key: Annotated[
        str | None,
        typer.Option(
            "--gpg-private-key",
            help="Base64-encoded GPG private key to import into Docker container for signing",
        ),
    ] = None,
    gpg_passphrase: Annotated[
        str | None,
        typer.Option(
            "--gpg-passphrase",
            help="Passphrase for the GPG private key (if encrypted)",
        ),
    ] = None,
):
    """
    Build a specific Slurm version.

    Available versions: 25.11 (default), 25.11, 24.11, 23.11

    Compiler toolchains (--compiler-version) - all built with Spack for relocatability:
    - 14.2.0: GCC 14.2, glibc 2.39, latest stable
    - 13.4.0 (default): GCC 13.4, glibc 2.39, Ubuntu 24.04 compatible
    - 12.5.0: GCC 12.5, glibc 2.35, Ubuntu 22.04 compatible
    - 11.5.0: GCC 11.5, glibc 2.35, good compatibility
    - 10.5.0: GCC 10.5, glibc 2.31, RHEL 8/Ubuntu 20.04 compatible
    - 9.5.0: GCC 9.5, glibc 2.28, wide compatibility
    - 8.5.0: GCC 8.5, glibc 2.28, RHEL 8 minimum
    - 7.5.0: GCC 7.5, glibc 2.17, RHEL 7 compatible (maximum compatibility)

    Build types:
    - Default: ~2-5GB, CPU-only with OpenMPI and standard features
    - --gpu: ~15-25GB, includes CUDA/ROCm support for GPU workloads
    - --verify: Enable relocatability verification for CI/testing
    - --no-cache: Force a fresh build without using Docker layer cache
    - --use-local-buildcache: Use locally cached compiler tarball (advanced)

    Buildcache publishing (--publish):
    - none (default): Don't publish to buildcache
    - slurm: Publish only the Slurm package
    - deps: Publish only dependencies (excluding Slurm)
    - all: Publish all packages (Slurm + dependencies)

    Remote Spack buildcache:
    - Always enabled via mirror in spack.yaml
    - Automatically downloads pre-built compiler binaries when available
    - No flag needed - works automatically

    Advanced Spack 1.x features:
    - --enable-hierarchy: Enable Core/Compiler/MPI 3-tier module hierarchy

    Each version includes:
    - Dynamic Spack configuration with relocatability features
    - Explicit compiler toolchains (toolchains)
    - Enhanced RPATH/RUNPATH configuration (Spack 1.x)
    - GCC runtime as separate package for clean ABI compatibility
    - Optional verification checks (--verify for CI)

    - Professional Lmod modules with hierarchy support

    Examples:
        slurm-factory build-slurm                                    # Build default (25.11, gcc 13.4.0)
        slurm-factory build-slurm --slurm-version 24.11             # Build specific version
        slurm-factory build-slurm --compiler-version 14.2.0         # Build with gcc 14.2
        slurm-factory build-slurm --compiler-version 12.5.0         # gcc 12 - Ubuntu 22.04 compat
        slurm-factory build-slurm --compiler-version 10.5.0         # gcc 10.5 - RHEL 8 compat
        slurm-factory build-slurm --compiler-version 7.5.0          # gcc 7.5 - RHEL 7 compat
        slurm-factory build-slurm --gpu                             # Build with GPU support
        slurm-factory build-slurm --verify                          # Build with verification (CI)
        slurm-factory build-slurm --no-cache                        # Build without Docker cache
        slurm-factory build-slurm --enable-hierarchy                # Build with module hierarchy
        slurm-factory build-slurm --publish=all                     # Build and publish all to buildcache
        slurm-factory build-slurm --publish=slurm                   # Build and publish only Slurm
        slurm-factory build-slurm --publish=deps                    # Build and publish only dependencies
        slurm-factory build-slurm --use-local-buildcache            # Use local compiler tarball (advanced)

    """
    console = Console()

    # Validate publish parameter
    valid_publish_options = ["none", "slurm", "deps", "all"]
    if publish not in valid_publish_options:
        console.print(f"[bold red]Error: Invalid --publish value '{publish}'[/bold red]")
        console.print(f"[bold yellow]Valid options: {', '.join(valid_publish_options)}[/bold yellow]")
        raise typer.Exit(1)

    if compiler_version not in COMPILER_TOOLCHAINS:
        console.print(f"[bold red]Error: Invalid compiler version '{compiler_version}'[/bold red]")
        console.print(
            f"[bold yellow]Available versions: {', '.join(sorted(COMPILER_TOOLCHAINS.keys()))}[/bold yellow]"
        )
        raise typer.Exit(1)

    # Show compiler info
    gcc_ver, glibc_ver, description = COMPILER_TOOLCHAINS[compiler_version]
    console.print(
        f"[bold blue]Building with compiler toolchain:[/bold blue] "
        f"GCC {gcc_ver}, glibc {glibc_ver} ({description})"
    )

    console.print(f"[bold green]Starting build for Slurm {slurm_version}[/bold green]")
    if no_cache:
        console.print("[bold yellow]Building with --no-cache (fresh build)[/bold yellow]")

    if use_local_buildcache:
        console.print("[bold yellow]Using locally cached compiler tarball[/bold yellow]")

    if publish_s3:
        console.print(
            "[bold blue]Will upload binaries to S3 (s3://slurm-factory-spack-binary-cache)[/bold blue]"
        )

    if publish != "none":
        console.print(f"[bold cyan]Will publish to buildcache: {publish}[/bold cyan]")
        if signing_key:
            console.print(f"[bold blue]Using GPG signing key: {signing_key}[/bold blue]")

    if enable_hierarchy:
        console.print("[bold cyan]Enabling Core/Compiler/MPI module hierarchy[/bold cyan]")

    build_slurm(
        ctx,
        slurm_version,
        compiler_version,
        gpu,
        verify,
        no_cache,
        publish,
        enable_hierarchy,
        signing_key,
        gpg_private_key,
        gpg_passphrase,
    )
