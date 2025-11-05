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

"""Main typer app for slurm-factory."""

import logging
import subprocess
import sys

import typer
from rich.console import Console
from rich.markup import escape
from typing_extensions import Annotated

from slurm_factory.builder import SlurmVersion
from slurm_factory.builder import build as builder_build
from slurm_factory.config import Settings
from slurm_factory.constants import COMPILER_TOOLCHAINS

# Configure logging following craft-providers pattern
app = typer.Typer(name="Slurm Factory", add_completion=True)


def setup_logging(verbose: bool = False):
    """Configure logging based on verbosity level."""
    if verbose:
        level = logging.DEBUG
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    else:
        level = logging.INFO
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logging.basicConfig(
        level=level,
        format=format_string,
        stream=sys.stderr,
        force=True,  # Override any existing logging config
    )

    # Set specific loggers to appropriate levels
    if verbose:
        logging.getLogger("slurm_factory").setLevel(logging.DEBUG)
        logging.getLogger("craft_providers").setLevel(logging.DEBUG)
    else:
        logging.getLogger("slurm_factory").setLevel(logging.INFO)
        logging.getLogger("craft_providers").setLevel(logging.WARNING)


@app.callback()
def main(
    ctx: typer.Context,
    project_name: Annotated[
        str,
        typer.Option(
            "--project-name",
            envvar="IF_PROJECT_NAME",
            help="The LXD project in which resources are going to be created",
        ),
    ] = "slurm-factory",
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose output")] = False,
):
    """Handle global options for the application."""
    setup_logging(verbose=verbose)

    settings = Settings(project_name=project_name)

    ctx.ensure_object(dict)
    ctx.obj["project_name"] = project_name
    ctx.obj["verbose"] = verbose
    ctx.obj["settings"] = settings


@app.command("clean")
def clean(
    ctx: typer.Context,
    full_cleanup: Annotated[
        bool, typer.Option("--full", help="Remove Docker images in addition to containers")
    ] = False,
):
    """
    Clean up Docker containers and images from slurm-factory builds.

    By default, removes stopped containers but keeps images for faster rebuilds.
    Use --full to remove both containers and images.

    Examples:
        slurm-factory clean        # Remove stopped containers
        slurm-factory clean --full  # Remove containers and images

    """
    console = Console()
    logger = logging.getLogger(__name__)
    logger.info("Cleaning up Docker containers and images")

    try:
        # List all containers with slurm-factory prefix
        result = subprocess.run(
            ["docker", "ps", "-a", "--filter", "name=slurm-factory", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            console.print("[bold red]Failed to list Docker containers[/bold red]")
            return

        containers = [line.strip() for line in result.stdout.split("\n") if line.strip()]

        if not containers:
            console.print("[green]No slurm-factory containers found[/green]")
        else:
            console.print(f"[bold red]Removing {len(containers)} slurm-factory container(s):[/bold red]")
            for container_name in containers:
                console.print(f"  [red]🗑️  {container_name}[/red]")

            # Remove containers
            for container_name in containers:
                try:
                    logger.debug(f"Removing container: {container_name}")
                    subprocess.run(
                        ["docker", "rm", "-f", container_name],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    console.print(f"  [green]✓[/green] Removed {container_name}")
                except Exception as e:
                    logger.error(f"Failed to remove container {container_name}: {e}")
                    console.print(f"  [red]✗[/red] Failed to remove {container_name}")

        # Clean up images if full cleanup requested
        if full_cleanup:
            console.print("\n[bold blue]Cleaning up Docker images...[/bold blue]")
            result = subprocess.run(
                [
                    "docker",
                    "images",
                    "--filter",
                    "reference=slurm-factory:*",
                    "--format",
                    "{{.Repository}}:{{.Tag}}",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                images = [line.strip() for line in result.stdout.split("\n") if line.strip()]

                if not images:
                    console.print("[green]No slurm-factory images found[/green]")
                else:
                    console.print(f"[bold red]Removing {len(images)} slurm-factory image(s):[/bold red]")
                    for image_name in images:
                        console.print(f"  [red]�️  {image_name}[/red]")

                    # Remove images
                    for image_name in images:
                        try:
                            logger.debug(f"Removing image: {image_name}")
                            subprocess.run(
                                ["docker", "rmi", "-f", image_name],
                                capture_output=True,
                                text=True,
                                timeout=60,
                            )
                            console.print(f"  [green]✓[/green] Removed {image_name}")
                        except Exception as e:
                            logger.error(f"Failed to remove image {image_name}: {e}")
                            console.print(f"  [red]✗[/red] Failed to remove {image_name}")

        console.print("\n[bold green]✓ Cleanup completed[/bold green]")

        if not full_cleanup and len(containers) > 0:
            console.print("[dim]Tip: Use [bold]--full[/bold] to also remove Docker images[/dim]")

    except FileNotFoundError:
        console.print("[bold red]Docker is not installed or not in PATH[/bold red]")
        logger.error("Docker command not found")
        raise typer.Exit(1)
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        console.print(f"[bold red]Error during cleanup: {escape(str(e))}[/bold red]")
        raise typer.Exit(1)


@app.command("build-compiler")
def build_compiler(
    ctx: typer.Context,
    compiler_version: Annotated[
        str,
        typer.Option(
            "--compiler-version",
            help=f"GCC compiler version to build ({', '.join(COMPILER_TOOLCHAINS.keys())})",
        ),
    ] = "13.4.0",
    no_cache: Annotated[
        bool, typer.Option("--no-cache", help="Force a fresh build without using Docker cache")
    ] = False,
    publish: Annotated[
        bool, typer.Option("--publish", help="Publish compiler binaries to S3 buildcache after build")
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
):
    """
    Build a GCC compiler toolchain for use in Slurm builds.

    This command builds a relocatable GCC compiler toolchain using Spack and
    optionally publishes it to S3 buildcache for reuse across builds.

    Compiler toolchains - all built with Spack for relocatability:
    - 14.2.0: GCC 14.2, glibc 2.39, latest stable
    - 13.4.0 (default): GCC 13.4, glibc 2.39, Ubuntu 24.04 compatible
    - 12.5.0: GCC 12.5, glibc 2.35, Ubuntu 22.04 compatible
    - 11.5.0: GCC 11.5, glibc 2.35, good compatibility
    - 10.5.0: GCC 10.5, glibc 2.31, RHEL 8/Ubuntu 20.04 compatible
    - 9.5.0: GCC 9.5, glibc 2.28, wide compatibility
    - 8.5.0: GCC 8.5, glibc 2.28, RHEL 8 minimum
    - 7.5.0: GCC 7.5, glibc 2.17, RHEL 7 compatible (maximum compatibility)

    Examples:
        slurm-factory build-compiler                              # Build default compiler (gcc 13.4.0)
        slurm-factory build-compiler --compiler-version 14.2.0    # Build gcc 14.2
        slurm-factory build-compiler --compiler-version 10.5.0    # Build gcc 10.5 for RHEL 8
        slurm-factory build-compiler --publish                    # Build and publish to S3 buildcache
        slurm-factory build-compiler --publish --signing-key 0xKEYID  # Build and publish with signing
        slurm-factory build-compiler --no-cache                   # Build without Docker cache

    """
    from slurm_factory.builder import build_compiler as builder_build_compiler

    console = Console()

    if compiler_version not in COMPILER_TOOLCHAINS:
        console.print(f"[bold red]Error: Invalid compiler version '{compiler_version}'[/bold red]")
        console.print(
            f"[bold yellow]Available versions: {', '.join(sorted(COMPILER_TOOLCHAINS.keys()))}[/bold yellow]"
        )
        raise typer.Exit(1)

    # Show compiler info
    gcc_ver, glibc_ver, description = COMPILER_TOOLCHAINS[compiler_version]
    console.print(
        f"[bold blue]Building compiler toolchain:[/bold blue] "
        f"GCC {gcc_ver}, glibc {glibc_ver} ({description})"
    )

    if no_cache:
        console.print("[bold yellow]Building with --no-cache (fresh build)[/bold yellow]")

    if publish:
        console.print("[bold blue]Will publish compiler to S3 buildcache after build[/bold blue]")
        if signing_key:
            console.print(f"[bold blue]Using GPG signing key: {signing_key}[/bold blue]")

    builder_build_compiler(ctx, compiler_version, no_cache, publish, signing_key, gpg_private_key)


@app.command("build")
def build(
    ctx: typer.Context,
    slurm_version: Annotated[
        SlurmVersion, typer.Option("--slurm-version", help="Slurm version to build")
    ] = SlurmVersion.v25_05,
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
):
    """
    Build a specific Slurm version.

    Available versions: 25.05 (default), 24.11, 23.11, 23.02

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
    - Global patches (shared across versions)
    - Professional Lmod modules with hierarchy support

    Examples:
        slurm-factory build                                    # Build default CPU version (25.05, gcc 13.4.0)
        slurm-factory build --slurm-version 24.11             # Build specific version
        slurm-factory build --compiler-version 14.2.0         # Build with gcc 14.2
        slurm-factory build --compiler-version 12.5.0         # Build with gcc 12 - Ubuntu 22.04 compatibility
        slurm-factory build --compiler-version 10.5.0         # Build with gcc 10.5 - RHEL 8 compatibility
        slurm-factory build --compiler-version 7.5.0          # Build with gcc 7.5 - RHEL 7 compatibility
        slurm-factory build --gpu                             # Build with GPU support
        slurm-factory build --verify                          # Build with verification (CI)
        slurm-factory build --no-cache                        # Build without Docker cache
        slurm-factory build --enable-hierarchy                # Build with module hierarchy
        slurm-factory build --publish=all                     # Build and publish all to buildcache
        slurm-factory build --publish=slurm                   # Build and publish only Slurm
        slurm-factory build --publish=deps                    # Build and publish only dependencies
        slurm-factory build --use-local-buildcache            # Use local compiler tarball (advanced)

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

    console.print(
        f"[bold green]Starting build for Slurm {slurm_version}[/bold green]"
    )
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

    builder_build(
        ctx,
        slurm_version,
        compiler_version,
        gpu,
        verify,
        no_cache,
        use_local_buildcache,
        publish_s3,
        publish,
        enable_hierarchy,
        signing_key,
    )


if __name__ == "__main__":
    app()
