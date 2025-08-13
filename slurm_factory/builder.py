"""Slurm build process management."""

import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import typer
import yaml
from craft_providers import lxd
from rich.console import Console
from typing_extensions import Annotated

from .config import Settings
from .constants import (
    BASE_INSTANCE_EXPIRY_DAYS,
    BASE_INSTANCE_PREFIX,
    BASH_HEADER,
    CACHE_SETUP_SCRIPT,
    CACHE_SUBDIRS,
    CLOUD_INIT_TIMEOUT,
    CONTAINER_BUILD_OUTPUT_DIR,
    CONTAINER_CACHE_DIR,
    CONTAINER_PATCHES_DIR,
    CONTAINER_ROOT_DIR,
    CONTAINER_SLURM_DIR,
    CONTAINER_SPACK_CACHE_DIR,
    CONTAINER_SPACK_PROJECT_DIR,
    COPY_OUTPUT_SCRIPT,
    INSTANCE_NAME_PREFIX,
    LXD_IMAGE,
    LXD_IMAGE_REMOTE,
    PACKAGE_CREATION_SCRIPT,
    PATCH_COPY_SCRIPT,
    SLURM_VERSIONS,
    SPACK_BUILD_CACHE_SCRIPT,
    SPACK_INSTALL_SCRIPT,
    SPACK_PROJECT_SETUP_SCRIPT,
    SPACK_REPO_PATH,
    SPACK_SETUP_SCRIPT,
    SlurmVersion,
    get_mkdir_commands,
)
from .spack_yaml import generate_yaml_string

# Set up logging following craft-providers pattern
logger = logging.getLogger(__name__)


def _get_data_file(filename: str) -> Path:
    """Get path to a data file, prioritizing installed package locations over development."""
    import sys
    
    # First priority: Virtual environment (for pip installed packages)
    if hasattr(sys, 'prefix') and sys.prefix != sys.base_prefix:
        # We're in a virtual environment
        venv_path = Path(sys.prefix) / "share" / "slurm-factory" / filename
        if venv_path.exists():
            return venv_path.resolve()
    
    # Second priority: System-wide installation locations
    try:
        import site
        
        # Check each site-packages directory for shared data
        for site_dir in site.getsitepackages() + [site.getusersitepackages()]:
            if site_dir:
                installed_path = Path(site_dir) / "share" / "slurm-factory" / filename
                if installed_path.exists():
                    return installed_path.resolve()
                    
                # Also check the parent directory of site-packages for share
                parent_share = Path(site_dir).parent / "share" / "slurm-factory" / filename
                if parent_share.exists():
                    return parent_share.resolve()
    except Exception:
        pass

    # Last fallback: Development mode (files in current directory)
    dev_path = Path("data") / filename
    if dev_path.exists():
        return dev_path.resolve()

    # If nothing found, return the development path anyway (will cause an error if file doesn't exist)
    return dev_path.resolve()


def _set_profile(profile_name: str, project_name: str, settings: Settings):
    """Customize the default profile to include the profile at `lxd-profile.yaml`."""
    logger.debug(f"Setting up LXD profile '{profile_name}' for project '{project_name}'")
    lxc = lxd.LXC()
    profile_file = _get_data_file("lxd-profile.yaml")
    profile_content = profile_file.read_text()

    # Replace the placeholder with the actual cache directory path
    profile_content = profile_content.replace("CACHE_SOURCE_PLACEHOLDER", str(settings.home_cache_dir))
    profile_as_dict = yaml.safe_load(profile_content)

    # Verify the cache mount device is properly configured
    cache_mount_device = profile_as_dict.get("devices", {}).get("slurm-factory-cache", {})
    if cache_mount_device:
        logger.debug(
            f"Cache mount configured: {cache_mount_device['source']} -> {cache_mount_device['path']}"
        )
    else:
        logger.warning("Cache mount device not found in profile configuration")

    lxc.profile_edit(profile=profile_name, config=profile_as_dict, project=project_name)
    logger.debug(f"Successfully configured LXD profile '{profile_name}'")


def _stream_exec_output(
    instance: lxd.LXDInstance, command: list[str], description: str, verbose: bool = False, **kwargs
):
    """Execute a command in the instance and stream its output in real-time."""
    console = Console()

    if verbose:
        # In verbose mode, show output in real-time without status spinner
        console.print(f"[bold blue]{description}[/bold blue]")

        # Use execute_run for simpler real-time output
        try:
            result = instance.execute_run(command=command, **kwargs)

            # Print output
            if result.stdout:
                for line in result.stdout.split("\n"):
                    if line.strip():
                        console.print(f"  {line}")

            if result.stderr:
                for line in result.stderr.split("\n"):
                    if line.strip():
                        console.print(f"[yellow]  {line}[/yellow]")

            if result.returncode != 0:
                logger.error(f"Command failed with exit code {result.returncode}")
                console.print(f"[bold red]Command failed with exit code {result.returncode}[/bold red]")
                raise typer.Exit(result.returncode)

            return (
                result.returncode,
                result.stdout.split("\n") if result.stdout else [],
                result.stderr.split("\n") if result.stderr else [],
            )

        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            console.print(f"[bold red]Command execution failed: {e}[/bold red]")
            raise typer.Exit(1)
    else:
        # In non-verbose mode, use status spinner and show minimal output
        with console.status(f"[bold blue]{description}[/bold blue]"):
            try:
                result = instance.execute_run(command=command, **kwargs)

                # Show only important lines in non-verbose mode
                if result.stdout:
                    important_lines = [
                        line
                        for line in result.stdout.split("\n")
                        if line.strip() and ("error" in line.lower() or "warning" in line.lower())
                    ]
                    for line in important_lines:
                        console.print(f"[dim]  {line}[/dim]")

                if result.stderr:
                    for line in result.stderr.split("\n"):
                        if line.strip():
                            console.print(f"[red]  {line}[/red]")

                if result.returncode != 0:
                    logger.error(f"Command failed with exit code {result.returncode}")
                    console.print(f"[bold red]Command failed with exit code {result.returncode}[/bold red]")
                    raise typer.Exit(result.returncode)

                return (
                    result.returncode,
                    result.stdout.split("\n") if result.stdout else [],
                    result.stderr.split("\n") if result.stderr else [],
                )

            except Exception as e:
                logger.error(f"Command execution failed: {e}")
                console.print(f"[bold red]Command execution failed: {e}[/bold red]")
                raise typer.Exit(1)


def _wait_for_cloud_init_with_output(instance: lxd.LXDInstance):
    """Wait for cloud-init to finish, showing real-time log output."""
    console = Console()

    try:
        # This command will block until cloud-init is done
        console.print("[dim cyan]Running cloud-init status --wait...[/dim cyan]")
        result = instance.execute_run(
            command=["cloud-init", "status", "--wait"],
            timeout=CLOUD_INIT_TIMEOUT,  # 5 minute timeout
        )

        if result.returncode != 0:
            logger.error(f"Cloud-init failed with return code {result.returncode}")
            console.print(f"[bold red]✗ Cloud-init failed with return code {result.returncode}[/bold red]")
            # Show the error details
            try:
                error_result = instance.execute_run(command=["cat", "/var/log/cloud-init.log"], timeout=30)
                console.print("[bold red]Cloud-init error log:[/bold red]")
                if error_result.stdout:
                    for line in error_result.stdout.split("\n")[-20:]:  # Last 20 lines
                        if line.strip():
                            console.print(f"[red]  {line}[/red]")
                            logger.error(f"Cloud-init error: {line.strip()}")
            except Exception as log_error:
                logger.warning(f"Could not retrieve cloud-init error log: {log_error}")
            raise typer.Exit(1)

    except Exception as e:
        logger.error(f"Error waiting for cloud-init: {e}")
        console.print(f"[bold red]✗ Error waiting for cloud-init: {e}[/bold red]")
        raise typer.Exit(1)


def _get_base_instance_name(project_name: str, gpu_support: bool = False, minimal: bool = False) -> str:
    """Get the base instance name for the project with timestamp and build configuration."""
    # Use current date as timestamp for base instance naming
    timestamp_str = datetime.now().strftime("%Y%m%d")
    
    # Add configuration suffix to differentiate base instances
    config_suffix = ""
    if minimal:
        config_suffix = "-minimal"
    elif gpu_support:
        config_suffix = "-gpu"
    else:
        config_suffix = "-full"
    
    return f"{BASE_INSTANCE_PREFIX}-{timestamp_str}{config_suffix}"


def _base_instance_exists(lxc: lxd.LXC, project_name: str, gpu_support: bool = False, minimal: bool = False) -> bool:
    """Check if the base instance exists and is not expired."""
    base_instance_name = _get_base_instance_name(project_name, gpu_support, minimal)

    try:
        # Check if the instance exists
        instances = lxc.list(project=project_name)
        for instance in instances:
            if instance["name"] == base_instance_name:
                # Check if instance is not expired (90 days)
                created_at_str = instance.get("created_at", "")
                if created_at_str:
                    # Handle different datetime formats from LXD
                    created_at_str = created_at_str.replace("Z", "+00:00")
                    try:
                        created_at = datetime.fromisoformat(created_at_str)
                    except ValueError:
                        # If we can't parse the date, assume it's expired
                        logger.warning(f"Could not parse creation date for base instance: {created_at_str}")
                        return False

                    expiry_date = created_at + timedelta(days=BASE_INSTANCE_EXPIRY_DAYS)

                    if datetime.now(created_at.tzinfo) < expiry_date:
                        logger.debug(f"Base instance '{base_instance_name}' exists and is valid")
                        return True
                    else:
                        logger.debug(
                            f"Base instance '{base_instance_name}' exists but is expired, will recreate"
                        )
                        # Delete expired instance
                        lxc.delete(instance_name=base_instance_name, project=project_name, force=True)
                        return False

        logger.debug(f"Base instance '{base_instance_name}' does not exist")
        return False

    except Exception as e:
        logger.warning(f"Error checking base instance: {e}")
        return False


def _pre_build_base_instance_setup(lxd_instance: lxd.LXDInstance):
    """Set up permissions and basic configuration before build cache setup."""
    logger.debug("Setting up base instance permissions and configuration")

    # Create cache directory commands
    cache_dirs = get_mkdir_commands(CONTAINER_CACHE_DIR, CACHE_SUBDIRS)

    script_content = CACHE_SETUP_SCRIPT.substitute(
        cache_dir=CONTAINER_CACHE_DIR, create_cache_dirs=cache_dirs
    )

    setup_commands = BASH_HEADER + [script_content]

    _stream_exec_output(
        lxd_instance,
        setup_commands,
        "Setting up base instance permissions and cache directories",
        verbose=True,  # Always verbose for setup
        cwd=Path(CONTAINER_ROOT_DIR),
    )


def _copy_patches_to_container(
    lxd_instance: lxd.LXDInstance, verbose: bool = False, target_description: str = "container"
):
    """Copy global patches into the container."""
    patches_source = _get_data_file("patches")

    if patches_source.exists():
        logger.debug(f"Copying global patches from {patches_source} into {target_description}")

        # Read the patch files and copy them into the container
        for patch_file in patches_source.glob("*"):
            if patch_file.is_file():
                with open(patch_file, "r") as f:
                    patch_content = f.read()

                script_content = PATCH_COPY_SCRIPT.substitute(
                    patches_dir=CONTAINER_PATCHES_DIR, patch_name=patch_file.name, patch_content=patch_content
                )

                copy_patch_commands = BASH_HEADER + [script_content]

                _stream_exec_output(
                    lxd_instance,
                    copy_patch_commands,
                    f"Copying patch file {patch_file.name} to {target_description}",
                    verbose=verbose,
                )

        logger.debug(f"Copied patch files to {target_description}")
    else:
        logger.warning(f"Patches directory not found at {patches_source}")


def _setup_base_instance_buildcache(lxd_instance: lxd.LXDInstance, version: str, gpu_support: bool = False, minimal: bool = False):
    """Set up build cache in the base instance with ALL dependencies from dynamic spack configuration."""
    # Generate dynamic Spack configuration
    spack_config_yaml = generate_yaml_string(slurm_version=version, gpu_support=gpu_support, minimal=minimal)

    # Copy patches to container
    _copy_patches_to_container(lxd_instance, verbose=False, target_description="base instance")

    script_content = SPACK_BUILD_CACHE_SCRIPT.substitute(
        project_dir=CONTAINER_SPACK_PROJECT_DIR,
        spack_config=spack_config_yaml,
        spack_setup=SPACK_SETUP_SCRIPT,
        version=version,
        gpu_support=gpu_support,
        minimal=minimal,
        patches_dir=CONTAINER_PATCHES_DIR,
        spack_repo_path=SPACK_REPO_PATH,
    )

    build_cache_commands = BASH_HEADER + [script_content]

    _stream_exec_output(
        lxd_instance,
        build_cache_commands,
        f"Setting up build cache with dynamic Spack configuration (version={version}, gpu={gpu_support}, minimal={minimal})",
    )


def _create_base_instance(lxc: lxd.LXC, project_name: str, version: str = "25.05", gpu_support: bool = False, minimal: bool = False) -> str:
    """Create a base instance with cloud-init completed and build cache set up."""
    console = Console()
    base_instance_name = _get_base_instance_name(project_name, gpu_support, minimal)

    logger.debug(
        f"Creating base instance '{base_instance_name}' from fresh Ubuntu {LXD_IMAGE} with build cache (gpu={gpu_support}, minimal={minimal})"
    )
    console.print(f"[bold blue]Creating base instance with build cache:[/bold blue] {base_instance_name}")

    try:
        # Launch base instance
        console.print(f"[bold blue]Launching base instance:[/bold blue] {base_instance_name}")
        lxc.launch(
            instance_name=base_instance_name,
            image=LXD_IMAGE,
            image_remote=LXD_IMAGE_REMOTE,
            project=project_name,
        )

        # Wait for cloud-init to complete
        lxd_instance = lxd.LXDInstance(name=base_instance_name, project=project_name, remote="local")

        console.print("[bold blue]Waiting for cloud-init to complete...[/bold blue]")
        _wait_for_cloud_init_with_output(lxd_instance)

        console.print("[bold green]✓ Cloud-init completed successfully[/bold green]")

        # Run pre-setup to configure permissions before build cache setup
        console.print("[bold blue]Setting up base instance permissions...[/bold blue]")
        _pre_build_base_instance_setup(lxd_instance)

        # Set up build cache in the base instance
        console.print("[bold blue]Setting up build cache in base instance...[/bold blue]")
        _setup_base_instance_buildcache(
            lxd_instance, version, gpu_support=gpu_support, minimal=minimal
        )  # Use the actual configuration requested

        # Stop the instance to save it as a base
        console.print("[bold blue]Stopping base instance...[/bold blue]")
        lxc.stop(instance_name=base_instance_name, project=project_name, force=True)

        logger.debug(f"Base instance '{base_instance_name}' created successfully with build cache")
        console.print(
            f"[bold green]✓ Base instance '{base_instance_name}' created with build cache[/bold green]"
        )

        return base_instance_name

    except Exception as e:
        logger.error(f"Failed to create base instance: {e}")
        # Clean up on failure
        try:
            lxc.delete(instance_name=base_instance_name, project=project_name, force=True)
        except Exception:
            pass
        raise typer.Exit(1)


def _launch_from_base_instance(
    lxc: lxd.LXC, instance_name: str, project_name: str, version: str = "25.05", gpu_support: bool = False, minimal: bool = False
) -> str:
    """Launch an instance from the base instance if available, otherwise create it."""
    console = Console()
    base_instance_name = _get_base_instance_name(project_name, gpu_support, minimal)

    if _base_instance_exists(lxc, project_name, gpu_support, minimal):
        logger.debug(f"Using cached base instance '{base_instance_name}' for faster startup")
        console.print(
            f"[bold green]Using cached base instance with build cache:[/bold green] {base_instance_name}"
        )

        # Copy from base instance
        lxc.copy(
            source_remote="local",
            source_instance_name=base_instance_name,
            destination_remote="local",
            destination_instance_name=instance_name,
            project=project_name,
        )

        # Start the copied instance
        lxc.start(instance_name=instance_name, project=project_name)

        return base_instance_name
    else:
        # Create base instance first with build cache
        _create_base_instance(lxc, project_name, version, gpu_support, minimal)

        # Now copy from the newly created base instance
        logger.debug(f"Copying from newly created base instance '{base_instance_name}'")
        console.print(
            f"[bold blue]Copying from base instance with build cache:[/bold blue] {base_instance_name}"
        )

        lxc.copy(
            source_remote="local",
            source_instance_name=base_instance_name,
            destination_remote="local",
            destination_instance_name=instance_name,
            project=project_name,
        )

        # Start the copied instance
        lxc.start(instance_name=instance_name, project=project_name)

        return base_instance_name


def build(
    ctx: typer.Context,
    slurm_version: Annotated[
        SlurmVersion, typer.Option("--slurm-version", help="Slurm version to build")
    ] = SlurmVersion.v25_05,
    gpu: bool = False,
    minimal: bool = False,
):
    """
    Build a specific Slurm version.

    Available versions: 25.05 (default), 24.11, 23.11, 23.02

    Build types:
    - CPU-only (default): ~2-5GB, optimized for most deployments
    - GPU-enabled (--gpu): ~15-25GB, includes CUDA/ROCm support

    Each version includes:
    - Dynamic Spack configuration
    - Global patches (shared across versions)
    - OpenMPI integration
    - Redistributable Lmod modules

    Examples:
        slurm-factory build                           # Build CPU-only version (25.05)
        slurm-factory build --slurm-version 24.11    # Build specific version
        slurm-factory build --gpu                     # Build with GPU support

    """
    console = Console()

    # Initialize settings and ensure cache directories exist
    settings = Settings(project_name=ctx.obj["project_name"])
    settings.ensure_cache_dirs()
    logger.debug(f"Ensured cache directories exist at {settings.home_cache_dir}")

    # Get verbose setting from context
    verbose = ctx.obj["verbose"]

    # Use the enum value as a string
    version = slurm_version.value
    logger.info(f"Starting Slurm build process for version {version}")

    lxc = lxd.LXC()

    short_uuid = f"{uuid.uuid4()}"[:8]
    # Replace dots with hyphens for LXD instance name (dots not allowed)
    safe_version = version.replace(".", "-")
    instance_name = f"{INSTANCE_NAME_PREFIX}-{safe_version}-{short_uuid}"
    logger.debug(f"Generated instance name: {instance_name}")

    # Set the default profile to include our custom profile
    project_name = ctx.obj["project_name"]
    logger.debug(f"Customizing LXD profile for project {project_name}")
    console.print(f"Customizing profile [bold]default[/bold] for project [bold]{project_name}[/bold]")
    _set_profile(profile_name="default", project_name=project_name, settings=settings)

    logger.debug(f"Launching build instance: {instance_name}")
    console.print(f"[bold blue]Launching build instance:[/bold blue] {instance_name}")

    # Use base instance if available, otherwise create it with build cache
    used_instance = _launch_from_base_instance(lxc, instance_name, project_name, version, gpu, minimal)

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
    spack_yaml_content = generate_yaml_string(slurm_version, gpu, minimal)

    console.print(f"[bold cyan]Generated dynamic Spack configuration for Slurm {slurm_version} ({build_desc})[/bold cyan]")

    # Create the spack project directory in the container and write the configuration
    logger.debug("Creating spack project directory and configuration in container")

    script_content = SPACK_PROJECT_SETUP_SCRIPT.substitute(
        project_dir=CONTAINER_SPACK_PROJECT_DIR, spack_config=spack_yaml_content
    )

    setup_commands = BASH_HEADER + [script_content]

    _stream_exec_output(
        lxd_instance, setup_commands, "Setting up dynamic Spack configuration in container", verbose=verbose
    )

    # Copy the global patches into the container
    _copy_patches_to_container(lxd_instance, verbose=verbose)
    console.print("[bold green]Copied patch files to container[/bold green]")

    # Mount a build output directory to persist results
    #logger.debug(f"Mounting build output directory: {settings.builds_dir}")
    #lxd_instance.mount(host_source=settings.builds_dir, target=Path(CONTAINER_BUILD_OUTPUT_DIR))

    # If you already have a spack cache in your home, mount it to speed things up
    spack_cache = Path.home() / ".spack" / "cache"
    if spack_cache.exists():
        logger.debug("Mounting existing Spack cache to accelerate builds")
        lxd_instance.mount(host_source=spack_cache, target=Path(CONTAINER_SPACK_CACHE_DIR))

    # Check if we're using the base instance (cloud-init already completed) or need to wait
    if used_instance.startswith(BASE_INSTANCE_PREFIX):
        logger.debug("Using base instance with cloud-init already completed, skipping wait")
        console.print(
            "[bold green]Using base instance - cloud-init already completed, "
            "proceeding directly to build[/bold green]"
        )
    else:
        # Wait for cloud-init to finish, then execute the build command in the container
        logger.debug("Starting cloud-init wait process")
        console.print("[bold yellow]Waiting for cloud-init to finish and showing progress...[/bold yellow]")
        _wait_for_cloud_init_with_output(lxd_instance)

    logger.debug(f"Initializing Spack build environment for Slurm {slurm_version}")
    console.print(
        f"[bold cyan]Building Slurm {slurm_version} using cached base instance with build cache[/bold cyan]"
    )

    # Execute the Spack build using the cached base instance (Spack already configured via LXD profile)
    logger.debug(f"Starting Slurm build process using cached dependencies for Slurm {slurm_version}")
    console.print(f"[bold green]Building Slurm {slurm_version} with cached dependencies[/bold green]")

    # Step 1: Install from cache (everything should already be cached in base instance)
    logger.debug("Step 1: Installing Slurm from cached base instance")

    script_content = SPACK_INSTALL_SCRIPT.substitute(
        project_dir=CONTAINER_SPACK_PROJECT_DIR, spack_setup=SPACK_SETUP_SCRIPT
    )

    build_commands = BASH_HEADER + [script_content]

    _stream_exec_output(
        lxd_instance,
        build_commands,
        f"Installing Slurm {version} from build cache (ultra-fast)",
        verbose=verbose,
        cwd=Path(CONTAINER_SPACK_PROJECT_DIR),
    )

    # Create redistributable packages from the Spack view and auto-generated modules
    logger.debug("Creating redistributable packages from Spack installation")
    console.print(f"[bold magenta]Creating redistributable packages for Slurm {version}[/bold magenta]")

    script_content = PACKAGE_CREATION_SCRIPT.substitute(
        project_dir=CONTAINER_SPACK_PROJECT_DIR,
        spack_setup=SPACK_SETUP_SCRIPT,
        slurm_dir=CONTAINER_SLURM_DIR,
        version=version,
        slurm_spec_version=SLURM_VERSIONS[version],
    )

    package_commands = BASH_HEADER + [script_content]

    _stream_exec_output(
        lxd_instance,
        package_commands,
        f"Creating redistributable packages for Slurm {version}",
        verbose=verbose,
        cwd=Path(CONTAINER_ROOT_DIR),
    )

    # Copy redistributable files out of the container before destroying it
    logger.debug("Extracting redistributable packages from container")
    console.print(f"[bold cyan]Extracting redistributable packages for Slurm {version}[/bold cyan]")

    # Copy the module and software packages directly to the mounted build output directory
    script_content = COPY_OUTPUT_SCRIPT.substitute(
        slurm_dir=CONTAINER_SLURM_DIR, version=version, output_dir=CONTAINER_BUILD_OUTPUT_DIR
    )

    copy_commands = BASH_HEADER + [script_content]

    _stream_exec_output(
        lxd_instance,
        copy_commands,
        "Copying redistributable packages",
        verbose=verbose,
        cwd=Path(CONTAINER_ROOT_DIR),
    )

    logger.info(f"Build process completed successfully for Slurm {version}")
    console.print(
        f"[bold green]✓ Redistributable packages created in ~/.slurm-factory/builds/[/bold green]"
    )
    console.print(f"  • [green]slurm-{version}-module.tar.gz[/green] (Lmod module)")
    console.print(f"  • [green]slurm-{version}-software.tar.gz[/green] (Compiled software)")

    logger.debug("Cleaning up LXD container")
    console.print("[bold yellow]Build complete, destroying LXD container.[/bold yellow]")
    lxc.delete(instance_name=instance_name, project=project_name, force=True)

    console.print(
        f"[bold green]🎉 Build artifacts available in: ~/.slurm-factory/builds/[/bold green]"
    )
