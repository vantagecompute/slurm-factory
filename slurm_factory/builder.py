"""Slurm build process management."""

import logging
import uuid

import typer
from craft_providers import lxd
from rich.console import Console
from typing_extensions import Annotated

from .constants import INSTANCE_NAME_PREFIX, SlurmVersion
from .exceptions import SlurmFactoryError, SlurmFactoryInstanceCreationError
from .utils import (
    create_base_instance,
    create_slurm_package,
    get_base_instance,
    get_base_instance_name,
    initialize_base_instance_buildcache,
    set_profile,
)

logger = logging.getLogger(__name__)


def build(
    ctx: typer.Context,
    slurm_version: Annotated[
        SlurmVersion, typer.Option("--slurm-version", help="Slurm version to build")
    ] = SlurmVersion.v25_05,
    gpu: bool = False,
    base_only: bool = False,
    minimal: bool = False,
    verify: bool = False,
):
    """Build a specific Slurm version."""
    console = Console()

    # Initialize settings and ensure cache directories exist
    settings = ctx.obj["settings"]
    project_name = ctx.obj["project_name"]

    settings.ensure_cache_dirs()
    logger.debug(f"Ensured cache directories exist at {settings.home_cache_dir}")

    lxc = lxd.LXC()
    if project_name not in lxc.project_list():
        console.print(f"Project [bold]{project_name}[/bold] doesn't exist. [green]Creating it![/green]")
        lxc.project_create(project=project_name)
        console.print(f"Customizing profile [bold]default[/bold] for project [bold]{project_name}[/bold]")
        set_profile(
            profile_name="default", project_name=project_name, home_cache_dir=f"{settings.home_cache_dir}"
        )
    else:
        console.print(f"Project [bold]{project_name}[/bold] already exists. Using it for the build.")

    # verbose = ctx.obj["verbose"]
    version = slurm_version.value
    console.print(f"Starting Slurm build process for version {version}")

    base_instance_name = get_base_instance_name()
    base_instance = get_base_instance(base_instance_name, project_name)

    if base_instance is None:
        console.print("[bold blue]Creating base instance....[/bold blue]")
        try:
            base_instance = create_base_instance(base_instance_name, project_name)
        except SlurmFactoryInstanceCreationError as e:
            logger.error(f"Failed to create base instance: {e}")
            return typer.Exit(1)

        try:
            initialize_base_instance_buildcache(base_instance, project_name, version, gpu, minimal, verify)
        except SlurmFactoryError as e:
            logger.error(f"Failed to initialize buildcache: {e}")
            return typer.Exit(1)

        # Stop the base instance
        lxc.stop(instance_name=base_instance.instance_name, project=project_name, force=True)

    logger.info(f"Base instance {base_instance.instance_name} created successfully")
    if base_only:
        console.print(
            f"[bold green]Base instance {base_instance.instance_name} is ready for use![/bold green]"
        )
        return typer.Exit(0)

    short_uuid = f"{uuid.uuid4()}"[:8]
    # Replace dots with hyphens for LXD instance name (dots not allowed)
    safe_version = version.replace(".", "-")
    instance_name = f"{INSTANCE_NAME_PREFIX}-{safe_version}-{short_uuid}"

    console.print(
        f"Starting slurm build instance {instance_name} from base instance {base_instance.instance_name}..."
    )

    lxc.copy(
        source_remote="local",
        source_instance_name=base_instance.instance_name,
        destination_remote="local",
        destination_instance_name=instance_name,
        project=project_name,
    )

    # Start the copied instance
    lxc.start(instance_name=instance_name, project=project_name)

    # Create the instance object for the started instance
    lxd_instance = lxd.LXDInstance(name=instance_name, project=project_name, remote="local")

    create_slurm_package(lxd_instance, version, gpu, minimal, verify)
    lxc.stop(instance_name=instance_name, project=project_name, force=True)
