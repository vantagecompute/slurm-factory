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

"""Slurm build process management."""

import logging
import uuid

import typer
from craft_providers import lxd
from rich.console import Console
from typing_extensions import Annotated

from .constants import INSTANCE_NAME_PREFIX, LXD_IMAGE, LXD_IMAGE_REMOTE, SlurmVersion
from .exceptions import SlurmFactoryError, SlurmFactoryInstanceCreationError
from .utils import (
    create_slurm_package,
    set_profile,
)

logger = logging.getLogger(__name__)


def build(
    ctx: typer.Context,
    slurm_version: Annotated[
        SlurmVersion, typer.Option("--slurm-version", help="Slurm version to build")
    ] = SlurmVersion.v25_05,
    gpu: bool = False,
    additional_variants: str = "",
    minimal: bool = False,
    verify: bool = False,
):
    """Build a specific Slurm version in a single build instance."""
    console = Console()

    # Initialize settings and ensure cache directories exist
    settings = ctx.obj["settings"]
    project_name = ctx.obj["project_name"]
    verbose = ctx.obj["verbose"]

    logger.debug(
        f"Starting build with parameters: slurm_version={slurm_version.value}, "
        f"gpu={gpu}, minimal={minimal}, verify={verify}"
    )
    logger.debug(f"Project name: {project_name}, verbose: {verbose}")

    settings.ensure_cache_dirs()
    logger.debug(f"Ensured cache directories exist at {settings.home_cache_dir}")

    lxc = lxd.LXC()
    if project_name not in lxc.project_list():
        console.print(f"Project [bold]{project_name}[/bold] doesn't exist. [green]Creating it![/green]")
        logger.debug(f"Creating new LXD project: {project_name}")
        lxc.project_create(project=project_name)
        console.print(f"Customizing profile [bold]default[/bold] for project [bold]{project_name}[/bold]")
        logger.debug(f"Setting up default profile for project {project_name}")
        set_profile(
            profile_name="default", project_name=project_name, home_cache_dir=f"{settings.home_cache_dir}"
        )
        logger.debug("Profile configuration completed")
    else:
        console.print(f"Project [bold]{project_name}[/bold] already exists. Using it for the build.")
        logger.debug(f"Using existing LXD project: {project_name}")

    version = slurm_version.value
    console.print(f"Starting Slurm build process for version {version}")
    logger.debug(f"Mapped Slurm version {slurm_version.value} to package version")

    # Generate unique instance name for this build
    short_uuid = f"{uuid.uuid4()}"[:8]
    safe_version = version.replace(".", "-")
    instance_name = f"{INSTANCE_NAME_PREFIX}-{safe_version}-{short_uuid}"
    logger.debug(f"Generated build instance name: {instance_name}")

    console.print(f"[bold blue]Creating build instance {instance_name}...[/bold blue]")

    try:
        # Create instance directly from Ubuntu image
        logger.debug(f"Launching instance {instance_name} from Ubuntu {LXD_IMAGE}")
        lxc.launch(
            instance_name=instance_name,
            image=LXD_IMAGE,
            image_remote=LXD_IMAGE_REMOTE,
            project=project_name,
            ephemeral=False,
        )
        logger.debug(f"Successfully launched instance: {instance_name}")
    except Exception as e:
        logger.error(f"Failed to create build instance: {e}")
        console.print(f"[bold red]Failed to create build instance:[/bold red] {e}")
        raise SlurmFactoryInstanceCreationError("Failed to create build instance")

    # Create the instance object
    lxd_instance = lxd.LXDInstance(name=instance_name, project=project_name, remote="local")
    logger.debug(f"Created LXD instance object for {instance_name}")

    # Wait for cloud-init to complete
    console.print("[bold blue]Waiting for cloud-init to complete...[/bold blue]")
    try:
        from .utils import _wait_for_cloud_init_with_output

        _wait_for_cloud_init_with_output(lxd_instance)
        console.print("[bold green]✓ Cloud-init completed successfully[/bold green]")
    except SlurmFactoryError as e:
        logger.error(f"Cloud-init failed: {e}")
        console.print(f"[bold red]Cloud-init failed:[/bold red] {e}")
        raise

    # Build the Slurm package
    logger.debug("Starting Slurm package creation")
    console.print(f"[bold blue]Building Slurm {version} package...[/bold blue]")

    try:
        create_slurm_package(lxd_instance, version, gpu, additional_variants, minimal, verify)
        logger.debug("Slurm package creation completed")
        console.print("[bold green]✓ Slurm package created successfully[/bold green]")
    except SlurmFactoryError as e:
        logger.error(f"Failed to create Slurm package: {e}")
        console.print(f"[bold red]Failed to create Slurm package:[/bold red] {e}")
        # Keep instance running for debugging
        console.print(f"[yellow]Build instance {instance_name} left running for debugging[/yellow]")
        raise

    # Stop the build instance
    logger.debug(f"Stopping build instance: {instance_name}")
    lxc.stop(instance_name=instance_name, project=project_name, force=True)
    logger.debug("Build instance stopped successfully")

    logger.info(f"Build process completed successfully for Slurm {version}")
    console.print("[bold green]Build completed successfully![/bold green]")
