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

"""Utils used throughout the slurm-factory package."""

import logging
import subprocess
from pathlib import Path

from rich.console import Console
from rich.markup import escape

from .constants import (
    get_dockerfile,
)
from .exceptions import SlurmFactoryError, SlurmFactoryStreamExecError
from .spack_yaml import generate_yaml_string

# Set up logging following craft-providers pattern
logger = logging.getLogger(__name__)
console = Console()


def _build_docker_image(
    image_tag: str,
    dockerfile_content: str,
    cache_dir: str,
    verbose: bool = False,
    no_cache: bool = False,
    target: str = "",
    build_args: dict | None = None,
) -> None:
    """
    Build a Docker image from a Dockerfile string.

    Args:
        image_tag: Tag for the Docker image
        dockerfile_content: Complete Dockerfile as a string
        cache_dir: Host directory for cache mounts
        verbose: Whether to show detailed output
        no_cache: Force a fresh build without using Docker cache
        target: Build target stage in multi-stage builds (e.g., "builder")
        build_args: Dictionary of build arguments to pass to Docker

    """
    console.print(f"[bold blue]Building Docker image {image_tag}...[/bold blue]")
    logger.debug(f"Building Docker image: {image_tag}")
    logger.debug(f"Dockerfile size: {len(dockerfile_content)} characters")

    if no_cache:
        logger.debug("Building with --no-cache flag")
        console.print("[bold yellow]Building without cache (this may take longer)[/bold yellow]")

    if target:
        logger.debug(f"Building target stage: {target}")
        console.print(f"[dim]Building target stage: {target}[/dim]")

    if build_args is not None:
        logger.debug(f"Build arguments: {build_args}")

    process = None
    try:
        # Find the repository root (where pyproject.toml is located)
        from pathlib import Path

        # Start from current directory and search upwards for pyproject.toml
        current_dir = Path.cwd()
        repo_root = current_dir
        while repo_root != repo_root.parent:
            if (repo_root / "pyproject.toml").exists():
                break
            repo_root = repo_root.parent

        # If pyproject.toml not found, fallback to current directory
        if not (repo_root / "pyproject.toml").exists():
            repo_root = current_dir
            logger.warning(f"Could not find repository root, using current directory: {repo_root}")
        else:
            logger.debug(f"Using repository root as build context: {repo_root}")

        # Ensure cache directory exists and is absolute
        if cache_dir:
            cache_path = Path(cache_dir).resolve()
            cache_path.mkdir(parents=True, exist_ok=True)

            # Create subdirectories for buildcache and source cache
            (cache_path / "buildcache").mkdir(parents=True, exist_ok=True)
            (cache_path / "source").mkdir(parents=True, exist_ok=True)
            logger.debug(f"Using cache directory: {cache_path}")

        # Use docker build with stdin for the Dockerfile
        # Enable BuildKit for better caching and features
        cmd = [
            "docker",
            "build",
            "-t",
            image_tag,
            "-f",
            "-",  # Read Dockerfile from stdin
            str(repo_root),  # Build context - use repository root so COPY paths work
        ]

        # Add build arguments
        if build_args is not None:
            for key, value in build_args.items():
                # Ensure value is converted to string for Docker build arg
                cmd.extend(["--build-arg", f"{key}={str(value)}"])

        # Add cache directory as build context if specified
        if cache_dir:
            cache_path = Path(cache_dir).resolve()
            # Pass cache directory paths as build args for use in RUN --mount
            cmd.extend(
                [
                    "--build-arg",
                    f"BUILDCACHE_DIR={cache_path}/buildcache",
                    "--build-arg",
                    f"SOURCECACHE_DIR={cache_path}/source",
                ]
            )

        # Add --no-cache flag if requested
        if no_cache:
            cmd.insert(2, "--no-cache")

        # Add --target flag if specified
        if target:
            cmd.extend(["--target", target])

        if verbose:
            logger.debug(f"Docker build command: {' '.join(cmd)}")
            console.print(f"[dim]$ {' '.join(cmd)}[/dim]")

        # Stream output to terminal in real-time
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Merge stderr into stdout
            text=True,
            bufsize=1,  # Line buffered
        )

        # Write Dockerfile to stdin
        if process.stdin:
            process.stdin.write(dockerfile_content)
            process.stdin.close()

        # Stream output line by line
        # Use sys.stdout.write() instead of console.print() to avoid any buffering/limits
        if process.stdout:
            import sys

            for line in process.stdout:
                line = line.rstrip()
                if line:
                    # Direct write to stdout to avoid any buffering or size limits
                    sys.stdout.write(f"  {line}\n")
                    sys.stdout.flush()
                    logger.debug(f"Docker build: {line}")

        # Wait for process to complete
        # Increased timeout to 4 hours (14400s) for large Spack builds with GPU support
        returncode = process.wait(timeout=14400)

        if returncode != 0:
            msg = f"Docker image build failed with exit code {returncode}"
            logger.error(msg)
            console.print(f"[bold red]{msg}[/bold red]")
            raise SlurmFactoryError(msg)

        console.print(f"[bold green]✓ Docker image {image_tag} built successfully[/bold green]")
        logger.debug("Docker image built successfully")

    except subprocess.TimeoutExpired:
        msg = "Docker image build timed out"
        logger.error(msg)
        console.print(f"[bold red]{msg}[/bold red]")
        if process:
            process.kill()
        raise SlurmFactoryError(msg)
    except Exception as e:
        msg = f"Failed to build Docker image: {e}"
        logger.error(msg)
        console.print(f"[bold red]{escape(msg)}[/bold red]")
        raise SlurmFactoryError(msg)


def _remove_old_docker_image(image_tag: str, verbose: bool = False) -> None:
    """
    Remove an old Docker image if it exists.

    Args:
        image_tag: Tag of the image to remove
        verbose: Whether to show detailed output

    """
    logger.debug(f"Checking for existing Docker image: {image_tag}")

    try:
        # Check if image exists
        result = subprocess.run(
            ["docker", "images", "-q", image_tag],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.stdout.strip():
            # Image exists, remove it
            console.print(f"[bold yellow]Removing old Docker image: {image_tag}[/bold yellow]")
            remove_result = subprocess.run(
                ["docker", "rmi", "-f", image_tag],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if remove_result.returncode == 0:
                console.print("[bold green]✓ Removed old Docker image[/bold green]")
                logger.debug(f"Removed Docker image: {image_tag}")
            else:
                logger.warning(f"Failed to remove Docker image: {remove_result.stderr}")
        else:
            logger.debug(f"No existing Docker image found for: {image_tag}")

    except Exception as e:
        # Don't fail the build if we can't remove the old image
        logger.warning(f"Could not remove old Docker image: {e}")
        if verbose:
            console.print(f"[dim]Warning: Could not remove old image: {escape(str(e))}[/dim]")


def _clear_cache_directory(cache_dir: str, verbose: bool = False) -> None:
    """
    Clear the cache directory to force a completely fresh build.

    Args:
        cache_dir: Path to the cache directory to clear
        verbose: Whether to show detailed output

    """
    console.print("[bold yellow]Clearing cache directory for fresh build...[/bold yellow]")
    logger.debug(f"Clearing cache directory: {cache_dir}")

    import shutil

    cache_path = Path(cache_dir)

    if not cache_path.exists():
        logger.debug(f"Cache directory does not exist: {cache_dir}")
        return

    try:
        # Remove all contents but keep the directory
        for item in cache_path.iterdir():
            if item.is_file():
                item.unlink()
                if verbose:
                    console.print(f"[dim]Removed file: {item.name}[/dim]")
            elif item.is_dir():
                shutil.rmtree(item)
                if verbose:
                    console.print(f"[dim]Removed directory: {item.name}[/dim]")

        console.print(f"[bold green]✓ Cleared cache directory: {cache_dir}[/bold green]")
        logger.debug("Cache directory cleared successfully")

    except Exception as e:
        msg = f"Failed to clear cache directory: {e}"
        logger.error(msg)
        console.print(f"[bold red]{escape(msg)}[/bold red]")
        raise SlurmFactoryError(msg)


def create_compiler_package(
    container_name: str,
    image_tag: str,
    compiler_version: str = "13.4.0",
    cache_dir: str = "",
    verbose: bool = False,
    no_cache: bool = False,
    publish: str = "none",
    signing_key: str | None = None,
    gpg_private_key: str | None = None,
    gpg_passphrase: str | None = None,
) -> None:
    """Create compiler package in a Docker container."""
    console.print("[bold blue]Creating compiler package in Docker container...[/bold blue]")

    logger.debug(
        f"Building compiler package: compiler_version={compiler_version}, "
        f"no_cache={no_cache}, publish={publish}, has_gpg_key={gpg_private_key is not None}"
    )

    try:
        # Always prune Docker buildx cache for compiler builds to avoid stale cache issues
        console.print("[dim]Pruning Docker buildx cache...[/dim]")
        try:
            subprocess.run(
                ["docker", "buildx", "prune", "-f"],
                check=True,
                capture_output=True,
                text=True,
            )
            logger.debug("Docker buildx cache cleared")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Could not clear Docker buildx cache: {e}")
            if verbose:
                console.print(f"[dim]Warning: Could not clear buildx cache: {escape(str(e))}[/dim]")

        # Always use no-cache for compiler builds to ensure clean state
        # Compiler builds are infrequent but need to be reliable
        force_no_cache = True
        logger.debug("Forcing --no-cache for compiler build to ensure clean state")

        # If no_cache is enabled, clean up old images too
        if no_cache or force_no_cache:
            console.print("[bold yellow]🗑️  Performing fresh build - cleaning all caches...[/bold yellow]")

            # Remove old Docker images
            _remove_old_docker_image(image_tag, verbose=verbose)

        # Generate Dockerfile for compiler-only build
        logger.debug("Generating compiler Dockerfile")
        from .constants import get_compiler_dockerfile

        dockerfile_content = get_compiler_dockerfile(
            compiler_version=compiler_version,
            cache_dir=cache_dir,
        )
        logger.debug(f"Generated Dockerfile ({len(dockerfile_content)} chars)")

        # Build the compiler image
        console.print("[bold cyan]Building compiler Docker image...[/bold cyan]")
        _build_docker_image(
            image_tag,
            dockerfile_content,
            cache_dir,
            verbose=verbose,
            no_cache=force_no_cache,  # Always use no-cache for reliable compiler builds
            target="compiler-packager",  # Build up to the packager stage
        )

        console.print("[bold green]✓ Compiler build complete[/bold green]")

        # Extract the tarball from the image
        if cache_dir:
            console.print("[bold cyan]Extracting compiler tarball from image...[/bold cyan]")
            extract_compiler_package_from_image(
                image_tag=image_tag,
                output_dir=cache_dir,
                compiler_version=compiler_version,
                verbose=verbose,
            )

        # If publish is enabled, push to S3 buildcache using spack
        if publish != "none":
            console.print(f"[bold cyan]Publishing compiler to S3 buildcache ({publish})...[/bold cyan]")
            publish_compiler_to_buildcache(
                image_tag=image_tag,
                cache_dir=cache_dir,
                compiler_version=compiler_version,
                verbose=verbose,
                signing_key=signing_key,
                gpg_private_key=gpg_private_key,
                gpg_passphrase=gpg_passphrase,
            )

        console.print("[bold green]✓ Compiler package built successfully[/bold green]")

    except SlurmFactoryStreamExecError as e:
        msg = f"Compiler build failed: {e}"
        logger.error(msg)
        console.print(f"[bold red]{escape(msg)}[/bold red]")
        raise SlurmFactoryError(msg)
    except Exception as e:
        msg = f"Failed to create compiler package: {e}"
        logger.error(msg)
        console.print(f"[bold red]{escape(msg)}[/bold red]")
        raise SlurmFactoryError(msg)


def create_slurm_package(
    container_name: str,
    image_tag: str,
    version: str = "25.11",
    compiler_version: str = "13.4.0",
    gpu_support: bool = False,
    verify: bool = False,
    cache_dir: str = "",
    verbose: bool = False,
    no_cache: bool = False,
    use_local_buildcache: bool = False,
    publish_s3: bool = False,
    publish: str = "none",
    enable_hierarchy: bool = False,
    signing_key: str | None = None,
    gpg_private_key: str | None = None,
    gpg_passphrase: str | None = None,
) -> None:
    """Create slurm package in a Docker container using a multi-stage build."""
    console.print("[bold blue]Creating slurm package in Docker container...[/bold blue]")

    logger.debug(
        f"Building Slurm package: version={version}, compiler_version={compiler_version}, "
        f"gpu={gpu_support}, verify={verify}, no_cache={no_cache}, "
        f"use_local_buildcache={use_local_buildcache}, publish_s3={publish_s3}, "
        f"publish={publish}, enable_hierarchy={enable_hierarchy}"
    )

    try:
        # If no_cache is enabled, clean up everything first
        if no_cache:
            console.print("[bold yellow]🗑️  Performing fresh build - cleaning all caches...[/bold yellow]")

            # Remove old Docker images
            _remove_old_docker_image(image_tag, verbose=verbose)

            # Clear Docker build cache
            console.print("[dim]Pruning Docker build cache...[/dim]")
            try:
                subprocess.run(
                    ["docker", "builder", "prune", "-f"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                logger.debug("Docker build cache cleared")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Could not clear Docker build cache: {e}")
                if verbose:
                    console.print(f"[dim]Warning: Could not clear build cache: {escape(str(e))}[/dim]")

            # Clear the cache directory
            if cache_dir:
                _clear_cache_directory(cache_dir, verbose=verbose)

        # Generate dynamic Spack configuration
        logger.debug("Generating dynamic Spack YAML configuration")

        # Always use Spack-built compiler for consistency and relocatability
        spack_yaml = generate_yaml_string(
            slurm_version=version,
            compiler_version=compiler_version,
            gpu_support=gpu_support,
            enable_verification=verify,
            enable_hierarchy=enable_hierarchy,
        )
        logger.debug(f"Generated Spack YAML configuration ({len(spack_yaml)} chars)")

        # Generate multi-stage Dockerfile with embedded spack.yaml
        # This creates 3 stages:
        # 0. compiler-bootstrap: Build custom GCC toolchain (or reuse from buildcache)
        # 1. init: Ubuntu + deps + Spack (heavily cached)
        # 2. builder: Spack install + view + modules (cached on spack.yaml changes)
        # 3. packager: Copy assets + create tarball (invalidates on asset changes)
        logger.debug("Generating multi-stage Dockerfile")
        dockerfile_content = get_dockerfile(
            spack_yaml,
            version,
            compiler_version=compiler_version,
            gpu_support=gpu_support,
            cache_dir=cache_dir,
            use_local_buildcache=use_local_buildcache,
        )
        logger.debug(f"Generated Dockerfile ({len(dockerfile_content)} chars)")

        # Build all stages up to packager (the final stage)
        console.print(
            "[bold cyan]Building multi-stage Docker image (init → builder → packager)...[/bold cyan]"
        )
        _build_docker_image(
            image_tag,
            dockerfile_content,
            cache_dir,
            verbose=verbose,
            no_cache=no_cache,
            target="packager",  # Build all stages up to packager
        )

        console.print("[bold green]✓ Multi-stage build complete[/bold green]")

        # Extract the tarball from the packager image
        if cache_dir:
            console.print("[bold cyan]Extracting tarball from image...[/bold cyan]")
            extract_slurm_package_from_image(
                image_tag=image_tag,
                output_dir=cache_dir,
                version=version,
                compiler_version=compiler_version,
                verbose=verbose,
            )

        # If publish_s3 is enabled, upload to S3
        if publish_s3:
            console.print("[bold cyan]Uploading Slurm binaries to S3...[/bold cyan]")
            upload_to_s3_buildcache(
                cache_dir=cache_dir,
                compiler_version=compiler_version,
                slurm_version=version,
                package_type="slurm",
                verbose=verbose,
            )

        # If publish is enabled, push to buildcache
        if publish != "none":
            console.print(f"[bold cyan]Publishing to buildcache ({publish})...[/bold cyan]")
            push_to_buildcache(
                image_tag=image_tag,
                version=version,
                compiler_version=compiler_version,
                publish_mode=publish,
                verbose=verbose,
                signing_key=signing_key,
                gpg_private_key=gpg_private_key,
                gpg_passphrase=gpg_passphrase,
            )

        console.print("[bold green]✓ Slurm package built successfully[/bold green]")

    except SlurmFactoryStreamExecError as e:
        msg = f"Build failed: {e}"
        logger.error(msg)
        console.print(f"[bold red]{escape(msg)}[/bold red]")
        raise SlurmFactoryError(msg)
    except Exception as e:
        msg = f"Failed to create slurm package: {e}"
        logger.error(msg)
        console.print(f"[bold red]{escape(msg)}[/bold red]")
        raise SlurmFactoryError(msg)


def extract_slurm_package_from_image(
    image_tag: str,
    output_dir: str,
    version: str,
    compiler_version: str = "13.4.0",
    verbose: bool = False,
) -> None:
    """
    Extract the Slurm package tarball from a packager Docker image.

    Args:
        image_tag: Tag of the packager Docker image
        output_dir: Directory to extract the tarball to (will be appended with version/compiler_version)
        version: Slurm version (for finding the correct tarball)
        compiler_version: GCC compiler version used for the build
        verbose: Whether to show detailed output

    """
    console.print(f"[bold blue]Extracting Slurm package from image {image_tag}...[/bold blue]")

    # Create version-specific output directory: ~/.slurm-factory/version/compiler_version/
    base_path = Path(output_dir)
    output_path = base_path / version / compiler_version
    output_path.mkdir(parents=True, exist_ok=True)

    logger.debug(f"Extracting package from image {image_tag} to {output_path}")

    container_name = f"slurm-factory-extract-{version.replace('.', '-')}"

    # Tarball name always includes compiler version for consistency
    tarball_name = f"slurm-{version}-gcc{compiler_version}-software.tar.gz"

    container_tarball_path = f"/opt/slurm/build_output/{tarball_name}"

    try:
        # Create a temporary container from the image
        logger.debug(f"Creating temporary container {container_name}")
        result = subprocess.run(
            ["docker", "create", "--name", container_name, image_tag],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            msg = f"Failed to create container for extraction: {result.stderr}"
            logger.error(msg)
            console.print(f"[bold red]{escape(msg)}[/bold red]")
            raise SlurmFactoryError(msg)

        # Copy the tarball from the container
        logger.debug(f"Copying {container_tarball_path} from container to {output_path}")
        console.print(f"[dim]Copying tarball to {output_path}...[/dim]")

        result = subprocess.run(
            ["docker", "cp", f"{container_name}:{container_tarball_path}", str(output_path)],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            msg = f"Failed to copy tarball from container: {result.stderr}"
            logger.error(msg)
            console.print(f"[bold red]{escape(msg)}[/bold red]")
            raise SlurmFactoryError(msg)

        console.print(f"[bold green]✓ Extracted {tarball_name} to {output_path}[/bold green]")
        logger.debug(f"Successfully extracted package to {output_path}/{tarball_name}")

    except subprocess.TimeoutExpired:
        msg = "Extraction timed out"
        logger.error(msg)
        console.print(f"[bold red]{msg}[/bold red]")
        raise SlurmFactoryError(msg)
    except Exception as e:
        msg = f"Failed to extract package: {e}"
        logger.error(msg)
        console.print(f"[bold red]{escape(msg)}[/bold red]")
        raise SlurmFactoryError(msg)
    finally:
        # Clean up the temporary container
        try:
            subprocess.run(
                ["docker", "rm", container_name],
                capture_output=True,
                text=True,
                timeout=30,
            )
            logger.debug(f"Removed temporary container {container_name}")
        except Exception as e:
            logger.warning(f"Failed to remove temporary container: {e}")


def extract_compiler_package_from_image(
    image_tag: str,
    output_dir: str,
    compiler_version: str = "13.4.0",
    verbose: bool = False,
) -> None:
    """
    Extract the compiler package tarball from a Docker image.

    Args:
        image_tag: Tag of the compiler Docker image
        output_dir: Directory to extract the tarball to
        compiler_version: GCC compiler version
        verbose: Whether to show detailed output

    """
    console.print(f"[bold blue]Extracting compiler package from image {image_tag}...[/bold blue]")

    # Create compiler-specific output directory: ~/.slurm-factory/compilers/compiler_version/
    base_path = Path(output_dir)
    output_path = base_path / "compilers" / compiler_version
    output_path.mkdir(parents=True, exist_ok=True)

    logger.debug(f"Extracting compiler package from image {image_tag} to {output_path}")

    container_name = f"slurm-factory-extract-compiler-{compiler_version.replace('.', '-')}"

    # Tarball name for the compiler
    from .constants import get_compiler_tarball_name

    tarball_name = get_compiler_tarball_name(compiler_version)

    container_tarball_path = f"/opt/compiler-output/{tarball_name}"

    try:
        # Create a temporary container from the image
        logger.debug(f"Creating temporary container {container_name}")
        result = subprocess.run(
            ["docker", "create", "--name", container_name, image_tag],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            msg = f"Failed to create container for extraction: {result.stderr}"
            logger.error(msg)
            console.print(f"[bold red]{escape(msg)}[/bold red]")
            raise SlurmFactoryError(msg)

        # Copy the tarball from the container
        logger.debug(f"Copying {container_tarball_path} from container to {output_path}")
        console.print(f"[dim]Copying compiler tarball to {output_path}...[/dim]")

        result = subprocess.run(
            ["docker", "cp", f"{container_name}:{container_tarball_path}", str(output_path)],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            msg = f"Failed to copy tarball from container: {result.stderr}"
            logger.error(msg)
            console.print(f"[bold red]{escape(msg)}[/bold red]")
            raise SlurmFactoryError(msg)

        console.print(f"[bold green]✓ Extracted {tarball_name} to {output_path}[/bold green]")
        logger.debug(f"Successfully extracted compiler package to {output_path}/{tarball_name}")

    except subprocess.TimeoutExpired:
        msg = "Extraction timed out"
        logger.error(msg)
        console.print(f"[bold red]{msg}[/bold red]")
        raise SlurmFactoryError(msg)
    except Exception as e:
        msg = f"Failed to extract compiler package: {e}"
        logger.error(msg)
        console.print(f"[bold red]{escape(msg)}[/bold red]")
        raise SlurmFactoryError(msg)
    finally:
        # Clean up the temporary container
        try:
            subprocess.run(
                ["docker", "rm", container_name],
                capture_output=True,
                text=True,
                timeout=30,
            )
            logger.debug(f"Removed temporary container {container_name}")
        except Exception as e:
            logger.warning(f"Failed to remove temporary container: {e}")


def publish_compiler_to_buildcache(
    image_tag: str,
    cache_dir: str,
    compiler_version: str = "13.4.0",
    verbose: bool = False,
    signing_key: str | None = None,
    gpg_private_key: str | None = None,
    gpg_passphrase: str | None = None,
) -> None:
    """
    Publish compiler binaries to S3 buildcache using spack buildcache push.

    This runs `spack buildcache push` inside the Docker container with AWS
    credentials/role passed as environment variables.

    Args:
        image_tag: Tag of the compiler Docker image
        cache_dir: Base cache directory (not used, kept for compatibility)
        compiler_version: GCC compiler version
        verbose: Whether to show detailed output
        signing_key: Optional GPG key ID for signing packages (e.g., "0xKEYID")
        gpg_private_key: Optional GPG private key (base64 encoded) to import into container
        gpg_passphrase: Optional GPG key passphrase for signing packages

    """
    console.print("[bold blue]Publishing compiler to S3 buildcache...[/bold blue]")

    s3_bucket = "s3://slurm-factory-spack-buildcache-4b670"
    # NOTE: Spack adds build_cache/ subdirectory automatically - do NOT append /buildcache here
    s3_mirror_url = f"{s3_bucket}/compilers/{compiler_version}"

    logger.debug(f"Publishing compiler {compiler_version} to {s3_mirror_url}")

    # Check for AWS credentials - support both direct credentials and OIDC role
    import os

    aws_env = {}

    # Check for AWS credentials (GitHub Actions OIDC or static credentials)
    # The configure-aws-credentials action sets these environment variables
    if "AWS_ACCESS_KEY_ID" in os.environ:
        # Use temporary credentials from configure-aws-credentials action
        aws_env["AWS_ACCESS_KEY_ID"] = os.environ["AWS_ACCESS_KEY_ID"]
        aws_env["AWS_SECRET_ACCESS_KEY"] = os.environ["AWS_SECRET_ACCESS_KEY"]
        if "AWS_SESSION_TOKEN" in os.environ:
            aws_env["AWS_SESSION_TOKEN"] = os.environ["AWS_SESSION_TOKEN"]
        if "AWS_DEFAULT_REGION" in os.environ:
            aws_env["AWS_DEFAULT_REGION"] = os.environ["AWS_DEFAULT_REGION"]
        if "AWS_REGION" in os.environ:
            aws_env["AWS_REGION"] = os.environ["AWS_REGION"]
        logger.debug("Using AWS credentials from environment (GitHub Actions OIDC or configured credentials)")
    else:
        # Fall back to checking for credentials file
        aws_dir = Path.home() / ".aws"
        if not aws_dir.exists():
            msg = "AWS credentials not found. Set AWS_ACCESS_KEY_ID or configure ~/.aws/ credentials."
            logger.error(msg)
            console.print(f"[bold red]{escape(msg)}[/bold red]")
            raise SlurmFactoryError(msg)
        logger.debug("Using AWS credentials from ~/.aws/")

    try:
        console.print(f"[dim]Pushing packages to {s3_mirror_url} using spack buildcache push...[/dim]")

        # Determine signing flags
        if signing_key:
            signing_flags = f"--key {signing_key}"
            logger.debug(f"Using GPG signing key: {signing_key}")
        else:
            signing_flags = "--unsigned"
            logger.debug("Publishing unsigned packages")

        # Build docker run command with AWS environment variables
        cmd = ["docker", "run", "--rm"]

        # Add AWS environment variables
        for key, value in aws_env.items():
            cmd.extend(["-e", f"{key}={value}"])

        # If GPG private key is provided, pass it as an environment variable
        if gpg_private_key:
            cmd.extend(["-e", f"GPG_PRIVATE_KEY={gpg_private_key}"])
            logger.debug("GPG private key will be imported into container")

        # If GPG passphrase is provided, pass it as an environment variable
        if gpg_passphrase:
            cmd.extend(["-e", f"GPG_PASSPHRASE={gpg_passphrase}"])
            logger.debug("GPG passphrase will be available in container")

        # Mount AWS credentials directory if not using environment credentials
        if "AWS_ACCESS_KEY_ID" not in aws_env:
            cmd.extend(["-v", f"{Path.home() / '.aws'}:/root/.aws:ro"])

        # Build the bash script to run in the container
        bash_script_parts = ["source /opt/spack/share/spack/setup-env.sh"]

        # If GPG private key is provided, import it before running buildcache commands
        if gpg_private_key:
            bash_script_parts.extend(
                [
                    # Import GPG key using Spack's gpg trust command (imports to /opt/spack/opt/spack/gpg)
                    'echo "$GPG_PRIVATE_KEY" | base64 -d > /tmp/gpg-key.asc',
                    'spack gpg trust /tmp/gpg-key.asc',
                    # Store passphrase for GPG wrapper to use
                    'echo "${GPG_PASSPHRASE}" > /tmp/gpg-passphrase.txt',
                    # Configure GPG with loopback pinentry
                    'mkdir -p /opt/spack/opt/spack/gpg',
                    'echo "pinentry-mode loopback" > /opt/spack/opt/spack/gpg/gpg.conf',
                    'echo -e "allow-loopback-pinentry\\ndefault-cache-ttl 34560000\\nmax-cache-ttl 34560000" > /opt/spack/opt/spack/gpg/gpg-agent.conf',
                    # Kill and restart agent
                    'gpgconf --homedir /opt/spack/opt/spack/gpg --kill gpg-agent 2>/dev/null || true',
                    'gpg-connect-agent --homedir /opt/spack/opt/spack/gpg /bye',
                    # Create GPG wrapper to inject passphrase when Spack calls gpg for signing
                    'mv /usr/bin/gpg /usr/bin/gpg-real',
                    r'''printf '#!/bin/bash\n# Wrapper to add passphrase for non-interactive signing\nif [[ "$*" == *"--clearsign"* ]]; then\n  exec /usr/bin/gpg-real --pinentry-mode loopback --passphrase-file /tmp/gpg-passphrase.txt "$@"\nelse\n  exec /usr/bin/gpg-real "$@"\nfi\n' > /usr/bin/gpg''',
                    'chmod +x /usr/bin/gpg',
                ]
            )

        # Add the buildcache push commands
        # Note: We only push packages that are installed in the environment.
        # 
        # This is changing:
        # gcc-runtime and compiler-wrapper are NOT built during compiler phase,
        # they are built later as dependencies during the Slurm build phase.
        bash_script_parts.extend(
            [
                "cd /root/compiler-bootstrap",
                # Activate the environment
                "source /opt/spack/share/spack/setup-env.sh",
                "spack env activate .",
                # List what we're about to push for debugging
                "echo '==> Packages in environment:'",
                "spack find",
                # Add the mirror
                f"spack mirror add --scope site s3-buildcache {s3_mirror_url}",
                # Push ALL installed packages from the environment, including dependencies
                # This ensures gcc-runtime and other dependencies are available in buildcache
                # Use --force to overwrite existing packages
                # Use --update-index to regenerate index after pushing
                # Note: --verbose doesn't exist in Spack v1.0.0
                # Use --fail-fast to stop on first failure
                f"spack buildcache push {signing_flags} --force --update-index --fail-fast s3-buildcache",
                # Verify upload succeeded
                "echo '==> Buildcache contents:'",
                "spack buildcache list --allarch",
            ]
        )

        # Join the script parts with && 
        # Use && to ensure each step succeeds before continuing
        bash_script = " && ".join(bash_script_parts)

        # Add image and command
        cmd.extend([image_tag, "bash", "-c", bash_script])

        if verbose:
            console.print("[dim]Running spack buildcache push in container with AWS credentials[/dim]")

        logger.debug(f"Running: {' '.join(cmd[:10])}...")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1800,  # 30 minutes for large uploads
        )

        if result.returncode != 0:
            msg = f"Failed to push to buildcache: {result.stderr}"
            logger.error(msg)
            console.print(f"[dim]stdout: {result.stdout}[/dim]")
            console.print(f"[bold red]{escape(msg)}[/bold red]")
            raise SlurmFactoryError(msg)

        # Always show buildcache push output for transparency
        if result.stdout:
            console.print(f"[dim]Buildcache push output:\n{result.stdout}[/dim]")
        else:
            console.print("[dim]No buildcache push output (command may have failed silently)[/dim]")
        
        if result.stderr:
            console.print(f"[yellow]Buildcache push stderr:\n{result.stderr}[/yellow]")

        console.print(f"[bold green]✓ Published compiler to {s3_mirror_url}[/bold green]")
        logger.debug(f"Successfully published compiler to {s3_mirror_url}")

    except subprocess.TimeoutExpired:
        msg = "Publishing timed out (>30 minutes)"
        logger.error(msg)
        console.print(f"[bold red]{msg}[/bold red]")
        raise SlurmFactoryError(msg)
    except Exception as e:
        msg = f"Failed to publish compiler to buildcache: {e}"
        logger.error(msg)
        console.print(f"[bold red]{escape(msg)}[/bold red]")
        raise SlurmFactoryError(msg)


def push_to_buildcache(
    image_tag: str,
    version: str,
    compiler_version: str,
    publish_mode: str = "all",
    verbose: bool = False,
    signing_key: str | None = None,
    gpg_private_key: str | None = None,
    gpg_passphrase: str | None = None,
) -> None:
    """
    Push Slurm specs to buildcache using spack buildcache push.

    This runs `spack buildcache push` inside the Docker container with AWS
    credentials/role passed as environment variables.

    Args:
        image_tag: Tag of the build Docker image
        version: Slurm version
        compiler_version: GCC compiler version
        publish_mode: What to publish - "slurm", "deps", or "all"
        verbose: Whether to show detailed output
        signing_key: Optional GPG key ID for signing packages (e.g., "0xKEYID")
        gpg_private_key: Optional GPG private key (base64 encoded) to import into container

    """
    console.print(f"[bold blue]Publishing to buildcache (mode: {publish_mode})...[/bold blue]")

    s3_bucket = "s3://slurm-factory-spack-buildcache-4b670"
    # NOTE: Spack adds build_cache/ subdirectory automatically - do NOT append /buildcache here
    s3_mirror_url = f"{s3_bucket}/slurm/{version}/{compiler_version}"

    logger.debug(f"Publishing Slurm {version} to {s3_mirror_url} (mode: {publish_mode})")

    # Check for AWS credentials - support both direct credentials and OIDC role
    import os

    aws_env = {}

    # Check for AWS credentials (GitHub Actions OIDC or static credentials)
    # The configure-aws-credentials action sets these environment variables
    if "AWS_ACCESS_KEY_ID" in os.environ:
        # Use temporary credentials from configure-aws-credentials action
        aws_env["AWS_ACCESS_KEY_ID"] = os.environ["AWS_ACCESS_KEY_ID"]
        aws_env["AWS_SECRET_ACCESS_KEY"] = os.environ["AWS_SECRET_ACCESS_KEY"]
        if "AWS_SESSION_TOKEN" in os.environ:
            aws_env["AWS_SESSION_TOKEN"] = os.environ["AWS_SESSION_TOKEN"]
        if "AWS_DEFAULT_REGION" in os.environ:
            aws_env["AWS_DEFAULT_REGION"] = os.environ["AWS_DEFAULT_REGION"]
        if "AWS_REGION" in os.environ:
            aws_env["AWS_REGION"] = os.environ["AWS_REGION"]
        logger.debug("Using AWS credentials from environment (GitHub Actions OIDC or configured credentials)")
    else:
        # Fall back to checking for credentials file
        aws_dir = Path.home() / ".aws"
        if not aws_dir.exists():
            msg = "AWS credentials not found. Set AWS_ACCESS_KEY_ID or configure ~/.aws/ credentials."
            logger.error(msg)
            console.print(f"[bold red]{escape(msg)}[/bold red]")
            raise SlurmFactoryError(msg)
        logger.debug("Using AWS credentials from ~/.aws/")

    try:
        console.print(f"[dim]Pushing packages to {s3_mirror_url}...[/dim]")

        # Determine signing flags
        if signing_key:
            signing_flags = f"--key {signing_key}"
            logger.debug(f"Using GPG signing key: {signing_key}")
        else:
            signing_flags = "--unsigned"
            logger.debug("Publishing unsigned packages")

        # Determine what to push based on publish_mode
        if publish_mode == "slurm":
            # Push only slurm package
            push_cmd = f"spack buildcache push {signing_flags} s3-buildcache slurm"
            update_index_cmd = "spack buildcache update-index s3-buildcache || echo 'Warning: Could not update buildcache index'"
        elif publish_mode == "deps":
            # Push only dependencies (everything except slurm)
            push_cmd = (
                f"spack -e . buildcache push {signing_flags} --only dependencies s3-buildcache"
            )
            update_index_cmd = "spack buildcache update-index s3-buildcache || echo 'Warning: Could not update buildcache index'"
        else:  # all
            # Push everything
            push_cmd = f"spack -e . buildcache push {signing_flags} s3-buildcache"
            update_index_cmd = "spack buildcache update-index s3-buildcache || echo 'Warning: Could not update buildcache index'"

        # Build docker run command with AWS environment variables
        cmd = ["docker", "run", "--rm"]

        # Add AWS environment variables
        for key, value in aws_env.items():
            cmd.extend(["-e", f"{key}={value}"])

        # If GPG private key is provided, pass it as an environment variable
        if gpg_private_key:
            cmd.extend(["-e", f"GPG_PRIVATE_KEY={gpg_private_key}"])
            logger.debug("GPG private key will be imported into container")

        # If GPG passphrase is provided, pass it as an environment variable
        if gpg_passphrase:
            cmd.extend(["-e", f"GPG_PASSPHRASE={gpg_passphrase}"])
            logger.debug("GPG passphrase will be available in container")

        # Mount AWS credentials directory if not using environment credentials
        if "AWS_ACCESS_KEY_ID" not in aws_env:
            cmd.extend(["-v", f"{Path.home() / '.aws'}:/root/.aws:ro"])

        # Build the bash script to run in the container
        bash_script_parts = ["source /opt/spack/share/spack/setup-env.sh"]

        # If GPG private key is provided, import it before running buildcache commands
        if gpg_private_key:
            bash_script_parts.extend(
                [
                    # Import GPG key using Spack's gpg trust command (imports to /opt/spack/opt/spack/gpg)
                    'echo "$GPG_PRIVATE_KEY" | base64 -d > /tmp/gpg-key.asc',
                    'spack gpg trust /tmp/gpg-key.asc',
                    # Store passphrase for GPG wrapper to use
                    'echo "${GPG_PASSPHRASE}" > /tmp/gpg-passphrase.txt',
                    # Configure GPG with loopback pinentry
                    'mkdir -p /opt/spack/opt/spack/gpg',
                    'echo "pinentry-mode loopback" > /opt/spack/opt/spack/gpg/gpg.conf',
                    'echo -e "allow-loopback-pinentry\\ndefault-cache-ttl 34560000\\nmax-cache-ttl 34560000" > /opt/spack/opt/spack/gpg/gpg-agent.conf',
                    # Kill and restart agent
                    'gpgconf --homedir /opt/spack/opt/spack/gpg --kill gpg-agent 2>/dev/null || true',
                    'gpg-connect-agent --homedir /opt/spack/opt/spack/gpg /bye',
                    # Create GPG wrapper to inject passphrase when Spack calls gpg for signing
                    'mv /usr/bin/gpg /usr/bin/gpg-real',
                    r'''printf '#!/bin/bash\n# Wrapper to add passphrase for non-interactive signing\nif [[ "$*" == *"--clearsign"* ]]; then\n  exec /usr/bin/gpg-real --pinentry-mode loopback --passphrase-file /tmp/gpg-passphrase.txt "$@"\nelse\n  exec /usr/bin/gpg-real "$@"\nfi\n' > /usr/bin/gpg''',
                    'chmod +x /usr/bin/gpg',
                ]
            )

        # Add spack environment and buildcache commands
        bash_script_parts.extend(
            [
                "cd /root/spack-project",
                "spack env activate .",
                f"spack mirror add --scope site s3-buildcache {s3_mirror_url}",
                push_cmd,
                # Update buildcache index after pushing (Spack 1.0+ requirement)
                update_index_cmd,
            ]
        )

        # Join the script parts with &&
        bash_script = " && ".join(bash_script_parts)

        # Add image and command
        cmd.extend([image_tag, "bash", "-c", bash_script])

        if verbose:
            console.print("[dim]Running spack buildcache push in container with AWS credentials[/dim]")

        logger.debug(f"Running: {' '.join(cmd[:10])}...")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600,  # 60 minutes for large uploads
        )

        if result.returncode != 0:
            msg = f"Failed to push to buildcache: {result.stderr}"
            logger.error(msg)
            console.print(f"[dim]stdout: {result.stdout}[/dim]")
            console.print(f"[bold red]{escape(msg)}[/bold red]")
            raise SlurmFactoryError(msg)

        # Always show buildcache push output for transparency
        if result.stdout:
            console.print(f"[dim]Buildcache push output:\n{result.stdout}[/dim]")
        else:
            console.print("[dim]No buildcache push output (command may have failed silently)[/dim]")
        
        if result.stderr:
            console.print(f"[yellow]Buildcache push stderr:\n{result.stderr}[/yellow]")

        console.print(f"[bold green]✓ Published to buildcache ({publish_mode})[/bold green]")
        logger.debug(f"Successfully published to {s3_mirror_url}")

    except subprocess.TimeoutExpired:
        msg = "Publishing timed out (>60 minutes)"
        logger.error(msg)
        console.print(f"[bold red]{msg}[/bold red]")
        raise SlurmFactoryError(msg)
    except Exception as e:
        msg = f"Failed to push to buildcache: {e}"
        logger.error(msg)
        console.print(f"[bold red]{escape(msg)}[/bold red]")
        raise SlurmFactoryError(msg)


def upload_to_s3_buildcache(
    cache_dir: str,
    compiler_version: str | None = None,
    slurm_version: str | None = None,
    package_type: str = "compiler",
    verbose: bool = False,
) -> None:
    """
    Upload Spack buildcache binaries to S3.

    Args:
        cache_dir: Base cache directory containing buildcache
        compiler_version: GCC compiler version (for compiler packages)
        slurm_version: Slurm version (for slurm packages)
        package_type: Type of package ("compiler" or "slurm")
        verbose: Whether to show detailed output

    """
    console.print(f"[bold blue]Uploading {package_type} binaries to S3...[/bold blue]")

    s3_bucket = "s3://slurm-factory-spack-buildcache-4b670"

    # Determine the source path based on package type
    base_path = Path(cache_dir)

    if package_type == "compiler":
        if not compiler_version:
            raise SlurmFactoryError("compiler_version required for compiler package type")
        source_path = base_path / "buildcache"
        s3_prefix = f"{s3_bucket}/compilers/{compiler_version}/"
        # Also upload the tarball
        tarball_path = base_path / "compilers" / compiler_version
        from .constants import get_compiler_tarball_name

        tarball_file = tarball_path / get_compiler_tarball_name(compiler_version)
    elif package_type == "slurm":
        if not slurm_version or not compiler_version:
            raise SlurmFactoryError("Both slurm_version and compiler_version required for slurm package type")
        source_path = base_path / "buildcache"
        s3_prefix = f"{s3_bucket}/slurm/{slurm_version}/{compiler_version}/"
        tarball_path = base_path / slurm_version / compiler_version
        tarball_file = None  # Will be determined based on files in directory
    else:
        raise SlurmFactoryError(f"Invalid package_type: {package_type}")

    if not source_path.exists():
        logger.warning(f"Buildcache directory not found: {source_path}")
        console.print(f"[yellow]Warning: No buildcache found at {source_path}[/yellow]")
        return

    try:
        # Check if AWS CLI is available
        result = subprocess.run(
            ["aws", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            raise SlurmFactoryError("AWS CLI is not available. Please install aws-cli.")

        logger.debug(f"AWS CLI version: {result.stdout.strip()}")

        # Upload buildcache directory
        console.print(f"[dim]Uploading buildcache from {source_path} to {s3_prefix}...[/dim]")
        logger.debug(f"Syncing {source_path} to {s3_prefix}")

        cmd = [
            "aws",
            "s3",
            "sync",
            str(source_path),
            f"{s3_prefix}buildcache/",
        ]

        if verbose:
            console.print(f"[dim]$ {' '.join(cmd)}[/dim]")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minutes for large uploads
        )

        if result.returncode != 0:
            msg = f"Failed to upload buildcache to S3: {result.stderr}"
            logger.error(msg)
            console.print(f"[bold red]{escape(msg)}[/bold red]")
            raise SlurmFactoryError(msg)

        if verbose and result.stdout:
            console.print(f"[dim]{result.stdout}[/dim]")

        console.print(f"[bold green]✓ Uploaded buildcache to {s3_prefix}buildcache/[/bold green]")

        # Upload tarball if it exists
        if package_type == "compiler" and tarball_file and tarball_file.exists():
            console.print(f"[dim]Uploading tarball {tarball_file.name} to S3...[/dim]")
            logger.debug(f"Uploading {tarball_file} to {s3_prefix}")

            cmd = [
                "aws",
                "s3",
                "cp",
                str(tarball_file),
                f"{s3_prefix}{tarball_file.name}",
            ]

            if verbose:
                console.print(f"[dim]$ {' '.join(cmd)}[/dim]")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes for tarball upload
            )

            if result.returncode != 0:
                msg = f"Failed to upload tarball to S3: {result.stderr}"
                logger.error(msg)
                console.print(f"[bold red]{escape(msg)}[/bold red]")
                raise SlurmFactoryError(msg)

            console.print(f"[bold green]✓ Uploaded {tarball_file.name} to {s3_prefix}[/bold green]")

        console.print(f"[bold green]✓ Successfully uploaded {package_type} binaries to S3[/bold green]")
        logger.debug(f"Successfully uploaded to {s3_prefix}")

    except FileNotFoundError:
        msg = "AWS CLI not found. Please install aws-cli to upload to S3."
        logger.error(msg)
        console.print(f"[bold red]{escape(msg)}[/bold red]")
        raise SlurmFactoryError(msg)
    except subprocess.TimeoutExpired:
        msg = "S3 upload timed out"
        logger.error(msg)
        console.print(f"[bold red]{msg}[/bold red]")
        raise SlurmFactoryError(msg)
    except Exception as e:
        msg = f"Failed to upload to S3: {e}"
        logger.error(msg)
        console.print(f"[bold red]{escape(msg)}[/bold red]")
        raise SlurmFactoryError(msg)
