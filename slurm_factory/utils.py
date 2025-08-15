"""Constants used throughout the slurm-factory package."""

import io
import logging
from datetime import datetime
from pathlib import Path, PurePath

import yaml
from craft_providers import lxd
from rich.console import Console

from .config import Settings
from .exceptions import SlurmFactoryError, SlurmFactoryInstanceCreationError, SlurmFactoryStreamExecError
from .spack_yaml import generate_yaml_string
from .constants import (
    BASE_INSTANCE_PREFIX,
    BASH_HEADER,
    CLOUD_INIT_TIMEOUT,
    CONTAINER_PATCHES_DIR,
    CONTAINER_ROOT_DIR,
    CONTAINER_SPACK_PROJECT_DIR,
    CONTAINER_SPACK_TEMPLATES_DIR,
    SPACK_BASE_INSTANCE_CONCRETIZE_SCRIPT,
    LXD_IMAGE,
    LXD_IMAGE_REMOTE,
)

# Set up logging following craft-providers pattern
logger = logging.getLogger(__name__)
console = Console()


def _stream_exec_output(
    instance: lxd.LXDInstance, command: list[str], description: str, verbose: bool = False, **kwargs
):
    """Execute a command in the instance and stream its output in real-time."""
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
                msg = f"Command failed with exit code {result.returncode}"
                logger.error(msg)
                console.print(f"[bold red]{msg}[/bold red]")
                raise SlurmFactoryStreamExecError(msg)

            return (
                result.returncode,
                result.stdout.split("\n") if result.stdout else [],
                result.stderr.split("\n") if result.stderr else [],
            )

        except Exception as e:
            msg = f"Command execution failed: {e}"
            logger.error(msg)
            console.print(f"[bold red]{msg}[/bold red]")
            raise SlurmFactoryStreamExecError(msg)
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
                    msg = f"Command failed with exit code {result.returncode}"
                    logger.error(msg)
                    console.print(f"[bold red]{msg}[/bold red]")
                    raise SlurmFactoryStreamExecError(msg)

                return (
                    result.returncode,
                    result.stdout.split("\n") if result.stdout else [],
                    result.stderr.split("\n") if result.stderr else [],
                )

            except Exception as e:
                msg = f"Command execution failed: {e}"
                logger.error(msg)
                console.print(f"[bold red]{msg}[/bold red]")
                raise SlurmFactoryStreamExecError(msg)


def _get_base_instance_name() -> str:
    """Get the base instance name for the project with timestamp and build configuration."""
    # Use current YEAR/MO for base instance name
    timestamp_str = datetime.now().strftime("%Y%m")
    return f"{BASE_INSTANCE_PREFIX}-{timestamp_str}"


def _pre_build_base_instance_setup(lxd_instance: lxd.LXDInstance):
    """Set up permissions and basic configuration before build cache setup."""
    logger.debug("Setting up base instance permissions and configuration")

    # Clear any previous Spack state that might have leftover failure marks
    logger.debug("Clearing any previous Spack state")
    clean_commands = BASH_HEADER + [
        "spack env activate .spack clean -a >/dev/null 2>&1 || true",
        "rm -rf ~/.spack/cache >/dev/null 2>&1 || true",
        "echo 'Spack environment cleaned'",
    ]

    try:
        _stream_exec_output(
            lxd_instance,
            clean_commands,
            "Cleaning previous Spack state",
            verbose=True,
            cwd=Path(CONTAINER_ROOT_DIR),
        )
    except SlurmFactoryStreamExecError as e:
        msg = f"Command execution failed: {e}"
        logger.error(msg)
        console.print(f"[bold red]{msg}[/bold red]")
        raise SlurmFactoryError(msg)


def _setup_base_instance_spack_project(
    lxd_instance: lxd.LXDInstance,
    version: str,
    gpu_support: bool = False,
    minimal: bool = False,
    verify: bool = False,
    verbose: bool = False
) -> lxd.LXDInstance:
    """Set up the base instance with ALL components of the spack project."""
    # Generate dynamic Spack configuration and copy to container
    spack_yaml = generate_yaml_string(
        slurm_version=version, gpu_support=gpu_support, minimal=minimal, enable_verification=verify
    )
    _copy_spack_yaml_to_container(lxd_instance, spack_yaml, verbose=False, target_description="base instance")
    # Copy patches to container
    _copy_patches_to_container(lxd_instance, verbose=False, target_description="base instance")
    # Copy templates to container
    _copy_templates_to_container(lxd_instance, verbose=False, target_description="base instance")

    try:
        _stream_exec_output(
            lxd_instance,
             BASH_HEADER + [SPACK_BASE_INSTANCE_CONCRETIZE_SCRIPT],
            f"Concretizing base environment for Slurm {version}",
            verbose=verbose,
        )
    except SlurmFactoryStreamExecError as e:
        msg = f"Command execution failed: {e}"
        logger.error(msg)
        console.print(f"[bold red]{msg}[/bold red]")
        raise SlurmFactoryError(msg)


def _create_base_instance(
    lxc: lxd.LXC,
    project_name: str,
    version: str = "25.05",
    gpu_support: bool = False,
    minimal: bool = False,
    verify: bool = False,
) -> str:
    """Create a base instance with cloud-init completed and build cache set up."""
    console = Console()
    base_instance_name = _get_base_instance_name()

    logger.debug(
        f"Creating base instance '{base_instance_name}' from  Ubuntu {LXD_IMAGE} "
        f"with build cache (gpu={gpu_support}, minimal={minimal})"
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
        lxd_base_instance = lxd.LXDInstance(name=base_instance_name, project=project_name, remote="local")

        console.print("[bold blue]Waiting for cloud-init to complete...[/bold blue]")
        _wait_for_cloud_init_with_output(lxd_base_instance)

        console.print("[bold green]✓ Cloud-init completed successfully[/bold green]")

        # Run pre-setup to configure permissions before build cache setup
        console.print("[bold blue]Setting up base instance permissions...[/bold blue]")
        # _pre_build_base_instance_setup(lxd_instance)
        _setup_base_instance_spack_project(
            lxd_base_instance, version, gpu_support=gpu_support, minimal=minimal, verify=verify
        )
        # Set up build cache in the base instance
        # console.print("[bold blue]Setting up build cache in base instance...[/bold blue]")
        # _setup_base_instance_buildcache(
        #    lxd_instance, version, gpu_support=gpu_support, minimal=minimal, verify=verify
        # )  # Use the actual configuration requested

        # Stop the instance to save it as a base
        console.print("[bold blue]Stopping base instance...[/bold blue]")
        lxc.stop(instance_name=base_instance_name, project=project_name, force=True)

        logger.debug(f"Base instance '{base_instance_name}' created successfully with build cache")
        console.print(
            f"[bold green]✓ Base instance '{base_instance_name}' created with build cache[/bold green]"
        )
    except Exception as e:
        logger.error(f"Failed to create base instance: {e}")
        raise SlurmFactoryInstanceCreationError("Failed to create base instance")
    return lxd_base_instance


def get_base_instance(
    lxc: lxd.LXC,
    project_name: str,
    version: str = "25.05",
    gpu_support: bool = False,
    minimal: bool = False,
    verify: bool = False,
) -> lxd.LXDInstance:
    """Initialize and return the base instance, otherwise return pre-existing base_instance."""
    console = Console()
    base_instance: lxd.LXDInstance = None

    base_instance_name = _get_base_instance_name()

    # Check if the instance exists, return it if so
    instances = lxc.list(project=project_name)
    for instance in instances:
        if instance["name"] == base_instance_name:
            console.print(
                f"[bold green]Using cached base instance with build cache:[/bold green] {base_instance_name}"
            )
            return instance

    # If not found, create a new base instance
    try:
        base_instance = _create_base_instance(lxc, project_name, version, gpu_support, minimal, verify)
    except SlurmFactoryInstanceCreationError as e:
        logger.error(f"Failed to create base instance: {e}")
        raise SlurmFactoryError("Failed to create base instance")

    return base_instance


def set_profile(profile_name: str, project_name: str, settings: Settings) -> None:
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


def _push_script_to_container(
    lxd_instance: lxd.LXDInstance,
    script_content: str,
    script_name: str,
    container_path: str = "/tmp",
    verbose: bool = False,
) -> str:
    """Push a script to the container and return the path for execution."""
    script_path = f"{container_path}/{script_name}"
    content_io = io.BytesIO(script_content.encode("utf-8"))

    lxd_instance.push_file_io(
        destination=Path(script_path),
        content=content_io,
        file_mode="0755",  # Make it executable
    )

    if verbose:
        logger.info(f"Pushed script {script_name} to container at {script_path}")

    return script_path


def _get_data_file(filename: str) -> Path:
    """Get path to a data file, prioritizing installed package locations over development."""
    import sys

    # First priority: Virtual environment (for pip installed packages)
    if hasattr(sys, "prefix") and sys.prefix != sys.base_prefix:
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
    dev_path = Path.cwd() / "data" / filename
    if dev_path.exists():
        return dev_path.resolve()

    # If nothing found, return the development path anyway (will cause an error if file doesn't exist)
    raise FileNotFoundError(f"Data file '{filename}' not found in any expected location")


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
            raise SlurmFactoryError("Cloud-init failed, see logs for details")

    except Exception as e:
        logger.error(f"Error waiting for cloud-init: {e}")
        console.print(f"[bold red]✗ Error waiting for cloud-init: {e}[/bold red]")
        raise SlurmFactoryError("Error waiting for cloud-init, see logs for details")


def _copy_patches_to_container(
    lxd_instance: lxd.LXDInstance, verbose: bool = False, target_description: str = "container"
):
    """Copy global patches into the container."""
    patches_source = _get_data_file("patches")

    if patches_source.exists():
        logger.debug(f"Copying global patches from {patches_source} into {target_description}")

        # Copy each patch file directly using LXD file operations
        for patch_file in patches_source.glob("*"):
            if patch_file.is_file():
                with open(patch_file, "rb") as f:
                    patch_content = f.read()

                # Use LXD's push_file_io to copy the file directly
                content_io = io.BytesIO(patch_content)
                target_path = Path(f"{CONTAINER_PATCHES_DIR}/{patch_file.name}")

                lxd_instance.push_file_io(destination=target_path, content=content_io, file_mode="0644")

                if verbose:
                    logger.info(f"Copied {patch_file.name} to container")

        logger.debug(f"Copied patch files to {target_description}")
    else:
        logger.warning(f"Patches directory not found at {patches_source}")


def _copy_templates_to_container(
    lxd_instance: lxd.LXDInstance, verbose: bool = False, target_description: str = "container"
):
    """Copy template files into the container."""
    templates_source = _get_data_file("templates")

    if templates_source.exists():
        logger.debug(f"Copying template files from {templates_source} into {target_description}")

        # Read the template files and copy them into the container
        # Create the templates directory in the container first
        create_dir_commands = BASH_HEADER + [f"mkdir -p {CONTAINER_SPACK_TEMPLATES_DIR}"]
        _stream_exec_output(
            lxd_instance,
            create_dir_commands,
            f"Creating templates directory in {target_description}",
            verbose=verbose,
        )

        for template_file in templates_source.glob("*"):
            if template_file.is_file():
                # Use LXD's file copying to avoid shell escaping issues
                destination_path = f"{CONTAINER_SPACK_TEMPLATES_DIR}/{template_file.name}"

                try:
                    lxd_instance.push_file_io(
                        content=io.BytesIO(template_file.read_bytes()),
                        destination=PurePath(destination_path),
                        file_mode="644",
                    )
                    logger.info(
                        f"Copied {template_file.name} to container at {CONTAINER_SPACK_TEMPLATES_DIR}"
                    )
                except Exception as e:
                    logger.error(f"Failed to copy template file {template_file.name}: {e}")
                    raise

        logger.debug(f"Copied template files to {target_description}")
    else:
        logger.warning(f"Templates directory not found at {templates_source}")


def _copy_spack_yaml_to_container(
    lxd_instance: lxd.LXDInstance,
    spack_yaml: str,
    verbose: bool = False,
    target_description: str = "container",
):
    """Copy Spack YAML configuration into the container."""
    destination_path = f"{CONTAINER_SPACK_PROJECT_DIR}/spack.yaml"

    logger.debug(f"Copying Spack YAML configuration to {target_description} at {destination_path}")
    try:
        lxd_instance.push_file_io(
            content=io.BytesIO(spack_yaml.encode("utf-8")),
            destination=PurePath(destination_path),
            file_mode="644",
        )
    except Exception as e:
        logger.error(f"Failed to copy spack.yaml to container: {e}")
        raise

    logger.debug(f"Copied spack.yaml to {destination_path}")
