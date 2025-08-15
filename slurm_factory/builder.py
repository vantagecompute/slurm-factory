"""Slurm build process management."""

import logging

import typer
from craft_providers import lxd
from rich.console import Console
from typing_extensions import Annotated

from .config import Settings
from .constants import SlurmVersion
from .exceptions import SlurmFactoryError
from .utils import (
    get_base_instance,
    set_profile,
)

logger = logging.getLogger(__name__)


def build(
    ctx: typer.Context,
    slurm_version: Annotated[
        SlurmVersion, typer.Option("--slurm-version", help="Slurm version to build")
    ] = SlurmVersion.v25_05,
    gpu: bool = False,
    minimal: bool = False,
    verify: bool = False,
):
    """Build a specific Slurm version."""
    console = Console()

    # Initialize settings and ensure cache directories exist
    settings = Settings(project_name=ctx.obj["project_name"])
    settings.ensure_cache_dirs()
    logger.debug(f"Ensured cache directories exist at {settings.home_cache_dir}")

    # Get verbose setting from context
    # verbose = ctx.obj["verbose"]

    # Use the enum value as a string
    version = slurm_version.value
    console.print(f"Starting Slurm build process for version {version}")

    # Set the default profile to include our custom profile
    project_name = ctx.obj["project_name"]
    console.print(f"Customizing profile [bold]default[/bold] for project [bold]{project_name}[/bold]")
    set_profile(profile_name="default", project_name=project_name, settings=settings)

    console.print("[bold blue]Creating base instance....[/bold blue]")
    lxc = lxd.LXC()
    try:
        base_instance = get_base_instance(lxc, project_name, version, gpu, minimal, verify)
    except SlurmFactoryError as e:
        logger.error(f"Failed to create base instance: {e}")
        return typer.Exit(1)

    logger.info(f"Base instance {base_instance.instance_name} created successfully")
