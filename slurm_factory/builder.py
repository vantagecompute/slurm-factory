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
    additional_variants: str = "",
    base_only: bool = False,
    minimal: bool = False,
    verify: bool = False,
):
    """Build a specific Slurm version."""
    console = Console()

    # Initialize settings and ensure cache directories exist
    settings = ctx.obj["settings"]
    project_name = ctx.obj["project_name"]
    verbose = ctx.obj["verbose"]

    logger.debug(
        f"Starting build with parameters: slurm_version={slurm_version.value}, "
        f"gpu={gpu}, base_only={base_only}, minimal={minimal}, verify={verify}"
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

    base_instance_name = get_base_instance_name()
    logger.debug(f"Generated base instance name: {base_instance_name}")

    base_instance = get_base_instance(base_instance_name, project_name)

    if base_instance is None:
        console.print("[bold blue]Creating base instance....[/bold blue]")
        logger.debug(f"Base instance {base_instance_name} not found, creating new one")
        try:
            base_instance = create_base_instance(base_instance_name, project_name)
            logger.debug(f"Successfully created base instance: {base_instance.instance_name}")
        except SlurmFactoryInstanceCreationError as e:
            logger.error(f"Failed to create base instance: {e}")
            logger.debug(f"Instance creation failed with error: {type(e).__name__}: {e}")
            return typer.Exit(1)

        ctxt = {
            "base_instance": base_instance,
            "project_name": project_name,
            "version": version,
            "gpu_support": gpu,
            "minimal": minimal,
            "verify": verify,
        }
        if additional_variants is not None:
            ctxt["additional_variants"] = additional_variants
        try:
            logger.debug("Initializing base instance buildcache")
            initialize_base_instance_buildcache(**ctxt)
            logger.debug("Base instance buildcache initialization completed")
        except SlurmFactoryError as e:
            logger.error(f"Failed to initialize buildcache: {e}")
            logger.debug(f"Buildcache initialization failed with error: {type(e).__name__}: {e}")
            return typer.Exit(1)

        # Stop the base instance
        logger.debug(f"Stopping base instance: {base_instance.instance_name}")
        lxc.stop(instance_name=base_instance.instance_name, project=project_name, force=True)
        logger.debug("Base instance stopped successfully")
    else:
        logger.debug(f"Using existing base instance: {base_instance.instance_name}")

    logger.info(f"Base instance {base_instance.instance_name} created successfully")
    if base_only:
        console.print(
            f"[bold green]Base instance {base_instance.instance_name} is ready for use![/bold green]"
        )
        logger.debug("Base-only build completed successfully")
        return typer.Exit(0)

    short_uuid = f"{uuid.uuid4()}"[:8]
    # Replace dots with hyphens for LXD instance name (dots not allowed)
    safe_version = version.replace(".", "-")
    instance_name = f"{INSTANCE_NAME_PREFIX}-{safe_version}-{short_uuid}"
    logger.debug(f"Generated package build instance name: {instance_name}")

    console.print(
        f"Starting slurm build instance {instance_name} from base instance {base_instance.instance_name}..."
    )
    logger.debug(f"Copying base instance {base_instance.instance_name} to {instance_name}")

    lxc.copy(
        source_remote="local",
        source_instance_name=base_instance.instance_name,
        destination_remote="local",
        destination_instance_name=instance_name,
        project=project_name,
    )
    logger.debug("Instance copy completed")

    # Start the copied instance
    logger.debug(f"Starting instance: {instance_name}")
    lxc.start(instance_name=instance_name, project=project_name)
    logger.debug("Instance started successfully")

    # Create the instance object for the started instance
    lxd_instance = lxd.LXDInstance(name=instance_name, project=project_name, remote="local")
    logger.debug(f"Created LXD instance object for {instance_name}")

    logger.debug("Starting Slurm package creation")
    create_slurm_package(lxd_instance, version, gpu, minimal, verify)
    logger.debug("Slurm package creation completed")

    logger.debug(f"Stopping package build instance: {instance_name}")
    lxc.stop(instance_name=instance_name, project=project_name, force=True)
    logger.debug("Package build instance stopped successfully")

    logger.info(f"Build process completed successfully for Slurm {version}")
