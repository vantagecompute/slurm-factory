"""Main typer app for slurm-build-factory."""

import logging

import typer
from craft_providers import lxd
from rich.console import Console
from typing_extensions import Annotated

from slurm_factory.builder import SlurmVersion
from slurm_factory.builder import build as builder_build

# Configure logging following craft-providers pattern
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

app = typer.Typer(name="Slurm Build Factory", add_completion=False)


@app.callback()
def main(
    ctx: typer.Context,
    project_name: str = typer.Option(
        "slurm-factory",
        envvar="IF_PROJECT_NAME",
        help="The LXD project in which resources are going to be created",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
):
    """Handle global options for the application."""
    # Configure logging level based on verbose flag
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger("slurm_factory").setLevel(logging.DEBUG)

    # Store settings in context dictionary
    ctx.ensure_object(dict)
    ctx.obj["project_name"] = project_name
    ctx.obj["verbose"] = verbose

    # Set up logger for this application
    logger = logging.getLogger(__name__)

    # Create the LXD project in case it doesn't exist yet

    console = Console()
    logger.debug(f"Checking if LXD project '{project_name}' exists")

    lxc = lxd.LXC()
    if project_name not in lxc.project_list():
        logger.info(f"Creating new LXD project: {project_name}")
        console.print(f"Project [bold]{project_name}[/bold] doesn't exist. [green]Creating it![/green]")
        lxc.project_create(project=project_name)
    else:
        logger.debug(f"LXD project '{project_name}' already exists")


@app.command("clean")
def clean(
    ctx: typer.Context, all_instances: bool = typer.Option(False, "--all", help="Delete base instances too")
):
    """
    Clean up LXD instances from the project.

    By default, keeps base instances for faster subsequent builds.
    Use --all to remove everything including base instances.

    Examples:
        slurm-factory clean        # Clean build instances, keep base instances
        slurm-factory clean --all  # Clean everything including base instances

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
                if all_instances:
                    instances_to_delete.append(instance_name)
            else:
                instances_to_delete.append(instance_name)

        if not instances_to_delete:
            if base_instances and not all_instances:
                console.print(
                    "[green]Only base instances found. Use [bold]--all[/bold] to remove them too[/green]"
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

        if base_instances and not all_instances:
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

        console.print(
            f"\n[bold green]✓ Cleanup completed for project [bold]{project_name}[/bold][/bold green]"
        )

        if base_instances and all_instances:
            console.print(
                "[yellow]⚠️  Base instances deleted - next build will take longer "
                "due to cloud-init setup[/yellow]"
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
    minimal: Annotated[
        bool, typer.Option("--minimal", help="Build minimal Slurm only (no OpenMPI, smaller size)")
    ] = False,
):
    """
    Build a specific Slurm version.

    Available versions: 25.05 (default), 24.11, 23.11, 23.02

    Build types:
    - Default: ~2-5GB, CPU-only with OpenMPI and standard features
    - --gpu: ~15-25GB, includes CUDA/ROCm support for GPU workloads  
    - --minimal: ~1-2GB, basic Slurm only without OpenMPI or extra features

    Each version includes:
    - Dynamic Spack configuration
    - Global patches (shared across versions)
    - Redistributable Lmod modules

    Examples:
        slurm-factory build                                    # Build default CPU version (25.05)
        slurm-factory build --slurm-version 24.11             # Build specific version
        slurm-factory build --gpu                             # Build with GPU support
        slurm-factory build --minimal                         # Build minimal version

    """
    # Validate that gpu and minimal are not both specified
    if gpu and minimal:
        console = Console()
        console.print("[bold red]Error: --gpu and --minimal cannot be used together[/bold red]")
        raise typer.Exit(1)
    
    builder_build(ctx, slurm_version, gpu, minimal)


if __name__ == "__main__":
    app()
