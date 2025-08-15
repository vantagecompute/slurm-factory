"""Slurm build process management."""

import logging

import typer
from craft_providers import lxd
from rich.console import Console
from typing_extensions import Annotated

from .config import Settings
from .constants import SlurmFactoryError
from .utils import (
    set_profile,
    get_base_instance,
    SlurmVersion,
)
from .spack_yaml import generate_yaml_string

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
    #verbose = ctx.obj["verbose"]

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
    
    logger.info(f"Base instance {base_instance['name']} created successfully")


"""     short_uuid = f"{uuid.uuid4()}"[:8]
    # Replace dots with hyphens for LXD instance name (dots not allowed)
    safe_version = version.replace(".", "-")
    instance_name = f"{INSTANCE_NAME_PREFIX}-{safe_version}-{short_uuid}"
    logger.debug(f"Generated instance name: {instance_name}")
   # Mount needed directories into the instance
    lxd_instance = lxd.LXDInstance(name=instance_name, project=project_name)


    # Determine build type description for logging
    if minimal:
        build_desc = "minimal"
    elif gpu:
        build_desc = "GPU-enabled"
    else:
        build_desc = "CPU-only"

    # Create dynamic spack.yaml configuration for this Slurm version
    logger.debug(
        f"Generating dynamic Spack configuration for Slurm {slurm_version} with build type: {build_desc}"
    )

    # Generate the dynamic configuration YAML string
    spack_yaml_content = generate_yaml_string(slurm_version, gpu, minimal, verify)

    console.print(f"[bold cyan]Generated dynamic Spack configuration for Slurm {slurm_version} ({build_desc})[/bold cyan]")

    # Create the spack project directory and push spack.yaml directly using LXD API
    logger.debug("Creating spack project directory and configuration in container")

   
    spack_yaml_path = f"{CONTAINER_SPACK_PROJECT_DIR}/spack.yaml"
    
    try:
        lxd_instance.push_file_io(
            content=io.BytesIO(spack_yaml_content.encode('utf-8')),
            destination=PurePath(spack_yaml_path),
            file_mode="644",
        )
        logger.info(f"Pushed spack.yaml directly to container at {spack_yaml_path}")
        if verbose:
            console.print(f"[green]✓[/green] Created dynamic spack.yaml configuration in container")
    except Exception as e:
        logger.error(f"Failed to push spack.yaml to container: {e}")
        raise
 """
    # Copy the global patches into the container
    #_copy_patches_to_container(lxd_instance, verbose=verbose)
    #console.print("[bold green]Copied patch files to container[/bold green]")

    # Copy template files into the container
    #_copy_templates_to_container(lxd_instance, verbose=verbose)
    #console.print("[bold green]Copied template files to container[/bold green]")

    # Mount a build output directory to persist results
    #logger.debug(f"Mounting build output directory: {settings.builds_dir}")
    #lxd_instance.mount(host_source=settings.builds_dir, target=Path(CONTAINER_BUILD_OUTPUT_DIR))

    # If you already have a spack cache in your home, mount it to speed things up
    #spack_cache = Path.home() / ".spack" / "cache"
    #if spack_cache.exists():
    #    logger.debug("Mounting existing Spack cache to accelerate builds")
    #    lxd_instance.mount(host_source=spack_cache, target=Path(CONTAINER_SPACK_CACHE_DIR))

    # Check if we're using the base instance (cloud-init already completed) or need to wait
    #if used_instance and used_instance.startswith(BASE_INSTANCE_PREFIX):
    #    logger.debug("Using base instance with cloud-init already completed, skipping wait")
    #    console.print(
    #        "[bold green]Using base instance - cloud-init already completed, "
    #        "proceeding directly to build[/bold green]"
    #    )
    #else:
    #    # Wait for cloud-init to finish, then execute the build command in the container
    #    logger.debug("Starting cloud-init wait process")
    #    console.print("[bold yellow]Waiting for cloud-init to finish and showing progress...[/bold yellow]")
    #_wait_for_cloud_init_with_output(lxd_instance)
    #import sys
    #sys.exit()

    #logger.debug(f"Initializing Spack build environment for Slurm {slurm_version}")
    #console.print(
    #    f"[bold cyan]Building Slurm {slurm_version} using cached base instance with build cache[/bold cyan]"
    #)

    # Execute the Spack build using the cached base instance (Spack already configured via LXD profile)
    #logger.debug(f"Starting Slurm build process using cached dependencies for Slurm {slurm_version}")
    #console.print(f"[bold green]Building Slurm {slurm_version} with bootstrapped compiler workflow[/bold green]")

    # Step 1: Multi-stage bootstrapped compiler build for true relocatability
    #logger.debug("Step 1: Installing Slurm with bootstrapped compiler workflow")

    #script_content = SPACK_BOOTSTRAPPED_INSTALL_SCRIPT.substitute(
    #    project_dir=CONTAINER_SPACK_PROJECT_DIR, 
    #    spack_setup=SPACK_SETUP_SCRIPT,
    #    verify=str(verify)  # Pass verification flag to script
    #)

    #build_commands = BASH_HEADER + [script_content]

    #_stream_exec_output(
    #    lxd_instance,
    #    build_commands,
    #    f"Installing Slurm {version} with bootstrapped compiler (truly relocatable)",
    #    verbose=verbose,
    #    cwd=Path(CONTAINER_SPACK_PROJECT_DIR),
    #)

    # Create redistributable packages from the Spack view and auto-generated modules
    #logger.debug("Creating redistributable packages from Spack installation")
    #console.print(f"[bold magenta]Creating redistributable packages for Slurm {version}[/bold magenta]")

    #script_content = PACKAGE_CREATION_SCRIPT.substitute(
    #    project_dir=CONTAINER_SPACK_PROJECT_DIR,
    #    spack_setup=SPACK_SETUP_SCRIPT,
    #    slurm_dir=CONTAINER_SLURM_DIR,
    #    version=version,
    #    slurm_spec_version=SLURM_VERSIONS[version],
    #)

    # Push the package creation script to container and execute it
    #script_path = _push_script_to_container(
    #    lxd_instance, script_content, "package_creation.sh", verbose=verbose
    #)
    
    #package_commands = BASH_HEADER + [script_path]

    #_stream_exec_output(
    #    lxd_instance,
    #    package_commands,
    #    f"Creating redistributable packages for Slurm {version}",
    #    verbose=verbose,
    #    cwd=Path(CONTAINER_ROOT_DIR),
    #)

    # Copy redistributable files out of the container before destroying it
    #logger.debug("Extracting redistributable packages from container")
    #console.print(f"[bold cyan]Extracting redistributable packages for Slurm {version}[/bold cyan]")

    # Copy the module and software packages directly to the mounted build output directory
    #script_content = COPY_OUTPUT_SCRIPT.substitute(
    #    slurm_dir=CONTAINER_SLURM_DIR, version=version, output_dir=CONTAINER_BUILD_OUTPUT_DIR
    #)

    #copy_commands = BASH_HEADER + [script_content]

    #_stream_exec_output(
    #    lxd_instance,
    #    copy_commands,
    #    "Copying redistributable packages",
    #    verbose=verbose,
    #    cwd=Path(CONTAINER_ROOT_DIR),
    #)

    #logger.info(f"Build process completed successfully for Slurm {version}")
    #console.print(
    #    f"[bold green]✓ Redistributable packages created in ~/.slurm-factory/builds/[/bold green]"
    #)
    #console.print(f"  • [green]slurm-{version}-module.tar.gz[/green] (Lmod module)")
    #console.print(f"  • [green]slurm-{version}-software.tar.gz[/green] (Compiled software)")

    #logger.debug("Keeping LXD container for debugging")
    #console.print(f"[bold yellow]Build complete, keeping container [cyan]{instance_name}[/cyan] for debugging.[/bold yellow]")
    # lxc.delete(instance_name=instance_name, project=project_name, force=True)

    #console.print(
    #    f"[bold green]🎉 Build artifacts available in: ~/.slurm-factory/builds/[/bold green]"
    #)
