"""Main typer app for slurm-build-factory."""

import logging
import sys

import typer
from craft_providers import lxd
from rich.console import Console
from typing_extensions import Annotated

from slurm_factory.builder import SlurmVersion
from slurm_factory.builder import build as builder_build
from slurm_factory.config import Settings

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
    full_cleanup: Annotated[bool, typer.Option("--full", help="Completely delete the LXD project")] = False,
):
    """
    Clean up LXD instances from the project.

    By default, keeps base instances for faster subsequent builds.
    Use --full to remove everything including base instances.

    Examples:
        slurm-factory clean        # Clean build instances, keep base instances
        slurm-factory clean --full  # Completely delete the lxd 'slurm-factory' project

    """
    console = Console()
    project_name = ctx.obj["project_name"]

    logger = logging.getLogger(__name__)
    logger.info(f"Cleaning LXD instances from project: {project_name}")

    lxc = lxd.LXC()

    # Check if project exists
    if project_name not in lxc.project_list():
        console.print(
            f"[yellow]Project [bold]{project_name}[/bold] doesn't exist - nothing to clean[/yellow]"
        )
        return

    try:
        # Get list of instances
        instances = lxc.list(project=project_name)

        if not instances:
            console.print(f"[green]No instances found in project [bold]{project_name}[/bold][/green]")
            return

        # Filter instances to clean
        instances_to_delete = []
        base_instances = []

        for instance in instances:
            instance_name = instance["name"]
            if instance_name.startswith("slurm-factory-base-"):
                base_instances.append(instance_name)
                if full_cleanup:
                    instances_to_delete.append(instance_name)
            else:
                instances_to_delete.append(instance_name)

        if not instances_to_delete:
            if base_instances and not full_cleanup:
                console.print(
                    "[green]Only base instances found. Use [bold]--full[/bold] to remove them too[/green]"
                )
            else:
                console.print(f"[green]No instances to clean in project [bold]{project_name}[/bold][/green]")
            return

        # Show what will be deleted
        console.print(
            f"[bold red]Deleting {len(instances_to_delete)} instance(s) from project "
            f"[bold]{project_name}[/bold]:[/bold red]"
        )
        for instance_name in instances_to_delete:
            if instance_name.startswith("slurm-factory-base-"):
                console.print(f"  [red]🗑️  {instance_name}[/red] [dim](base instance)[/dim]")
            else:
                console.print(f"  [red]🗑️  {instance_name}[/red] [dim](build instance)[/dim]")

        if base_instances and not full_cleanup:
            console.print(
                f"\n[green]Keeping {len(base_instances)} base instance(s) for faster future builds:[/green]"
            )
            for instance_name in base_instances:
                console.print(f"  [green]💾  {instance_name}[/green] [dim](base instance)[/dim]")

        # Delete instances
        for instance_name in instances_to_delete:
            try:
                logger.debug(f"Deleting instance: {instance_name}")
                lxc.delete(instance_name=instance_name, project=project_name, force=True)
                console.print(f"  [green]✓[/green] Deleted {instance_name}")
            except Exception as e:
                logger.error(f"Failed to delete instance {instance_name}: {e}")
                console.print(f"  [red]✗[/red] Failed to delete {instance_name}: {e}")

        if full_cleanup:
            for image in lxc.image_list(project=project_name):
                lxc.image_delete(image=image["fingerprint"], project=project_name)
            lxc.project_delete(project=project_name)

        console.print(
            f"\n[bold green]✓ Cleanup completed for project [bold]{project_name}[/bold][/bold green]"
        )

        if base_instances and full_cleanup:
            console.print(
                "[yellow]⚠️  Base instances deleted - next build will take longer "
                "due to cloud-init setup and spack buildcache creation[/yellow]"
            )

    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        console.print(f"[bold red]Error during cleanup: {e}[/bold red]")
        raise typer.Exit(1)


@app.command("build")
def build(
    ctx: typer.Context,
    slurm_version: Annotated[
        SlurmVersion, typer.Option("--slurm-version", help="Slurm version to build")
    ] = SlurmVersion.v25_05,
    gpu: Annotated[
        bool, typer.Option("--gpu", help="Enable GPU support (CUDA/ROCm) - creates larger packages")
    ] = False,
    additional_variants: Annotated[
        str, typer.Option("--additional-variants", help="Additional Spack variants to include")
    ] = "",
    minimal: Annotated[
        bool, typer.Option("--minimal", help="Build minimal Slurm only (no OpenMPI, smaller size)")
    ] = False,
    verify: Annotated[
        bool, typer.Option("--verify", help="Enable relocatability verification (for CI/testing)")
    ] = False,
    base_only: Annotated[
        bool, typer.Option("--base-only", help="Only build base images (no extra features)")
    ] = False,
):
    """
    Build a specific Slurm version.

    Available versions: 25.05 (default), 24.11, 23.11, 23.02

    Build types:
    - Default: ~2-5GB, CPU-only with OpenMPI and standard features
    - --gpu: ~15-25GB, includes CUDA/ROCm support for GPU workloads
    - --minimal: ~1-2GB, basic Slurm only without OpenMPI or extra features
    - --verify: Enable relocatability verification for CI/testing

    Each version includes:
    - Dynamic Spack configuration with relocatability features
    - Explicit compiler toolchains (toolchains)
    - Short install paths (install_tree.padded_length: 0)
    - System linkage validation (shared_linking.missing_library_policy: error)
    - Optional verification checks (--verify for CI)
    - Global patches (shared across versions)
    - Redistributable Lmod modules

    Examples:
        slurm-factory build                                    # Build default CPU version (25.05)
        slurm-factory build --slurm-version 24.11             # Build specific version
        slurm-factory build --gpu                             # Build with GPU support
        slurm-factory build --minimal                         # Build minimal version
        slurm-factory build --verify                          # Build with verification (CI)

    """
    console = Console()

    if additional_variants is not None:
        console.print(
            f"[bold yellow]Including additional Spack variants: {additional_variants}[/bold yellow]"
        )
        console.print("[bold yellow]⚠️  Note: This may increase build time and image size.[/bold yellow]")
        if "+mcs" in additional_variants and slurm_version != SlurmVersion.v25_05:
            console.print("[bold error] 'mcs' variant is only supported in slurm > 25.05.[/bold error]")

    if gpu and minimal:
        console.print("[bold red]Error: --gpu and --minimal cannot be used together[/bold red]")
        raise typer.Exit(1)

    console.print(
        f"[bold green]Starting build for Slurm {slurm_version} "
        f"with additional variants: {additional_variants}[/bold green]"
    )
    builder_build(ctx, slurm_version, gpu, additional_variants, minimal, verify, base_only)


if __name__ == "__main__":
    app()
