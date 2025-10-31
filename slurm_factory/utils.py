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
            cmd.extend([
                "--build-arg", f"BUILDCACHE_DIR={cache_path}/buildcache",
                "--build-arg", f"SOURCECACHE_DIR={cache_path}/source",
            ])

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
    publish: bool = False,
) -> None:
    """Create compiler package in a Docker container."""
    console.print("[bold blue]Creating compiler package in Docker container...[/bold blue]")

    logger.debug(
        f"Building compiler package: compiler_version={compiler_version}, "
        f"no_cache={no_cache}, publish={publish}"
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
            no_cache=no_cache,
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

        # If publish is enabled, also publish to buildcache
        if publish:
            console.print("[bold cyan]Publishing compiler binaries to buildcache...[/bold cyan]")
            publish_compiler_to_buildcache(
                image_tag=image_tag,
                cache_dir=cache_dir,
                compiler_version=compiler_version,
                verbose=verbose,
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
    version: str = "25.05",
    compiler_version: str = "13.4.0",
    gpu_support: bool = False,
    additional_variants: str = "",
    minimal: bool = False,
    verify: bool = False,
    cache_dir: str = "",
    verbose: bool = False,
    no_cache: bool = False,
    use_buildcache: bool = True,
) -> None:
    """Create slurm package in a Docker container using a multi-stage build."""
    console.print("[bold blue]Creating slurm package in Docker container...[/bold blue]")

    logger.debug(
        f"Building Slurm package: version={version}, compiler_version={compiler_version}, "
        f"gpu={gpu_support}, minimal={minimal}, verify={verify}, no_cache={no_cache}, "
        f"use_buildcache={use_buildcache}"
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
            minimal=minimal,
            additional_variants=additional_variants,
            enable_verification=verify,
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
            use_buildcache=use_buildcache,
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
) -> None:
    """
    Publish compiler binaries to buildcache from a Docker image.

    This extracts the Spack buildcache directory which contains binary packages
    that can be reused in future builds.

    Args:
        image_tag: Tag of the compiler Docker image
        cache_dir: Base cache directory
        compiler_version: GCC compiler version
        verbose: Whether to show detailed output

    """
    console.print(f"[bold blue]Publishing compiler binaries to buildcache...[/bold blue]")

    # Create buildcache directory structure
    base_path = Path(cache_dir)
    buildcache_path = base_path / "buildcache"
    buildcache_path.mkdir(parents=True, exist_ok=True)

    logger.debug(f"Publishing compiler {compiler_version} to buildcache at {buildcache_path}")

    container_name = f"slurm-factory-publish-compiler-{compiler_version.replace('.', '-')}"

    # The Spack buildcache is stored in the misc_cache directory configured in spack.yaml
    # which is {CONTAINER_CACHE_DIR}/buildcache
    from .constants import CONTAINER_CACHE_DIR

    container_buildcache_path = f"{CONTAINER_CACHE_DIR}/buildcache"

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
            msg = f"Failed to create container for publishing: {result.stderr}"
            logger.error(msg)
            console.print(f"[bold red]{escape(msg)}[/bold red]")
            raise SlurmFactoryError(msg)

        # Check if buildcache exists in container
        logger.debug(f"Checking if buildcache exists at {container_buildcache_path}")
        check_result = subprocess.run(
            ["docker", "run", "--rm", image_tag, "ls", "-la", container_buildcache_path],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if check_result.returncode != 0:
            logger.warning(f"Buildcache directory not found or empty at {container_buildcache_path}")
            console.print(
                f"[yellow]Warning: No buildcache found at {container_buildcache_path}. "
                "Spack may not have created binary packages.[/yellow]"
            )
            # Don't fail - this might be expected in some cases
            return

        # Copy the buildcache directory from the container
        logger.debug(f"Copying buildcache from {container_buildcache_path} to {buildcache_path}")
        console.print(f"[dim]Copying compiler binaries to buildcache...[/dim]")

        result = subprocess.run(
            [
                "docker",
                "cp",
                f"{container_name}:{container_buildcache_path}/.",
                str(buildcache_path),
            ],
            capture_output=True,
            text=True,
            timeout=180,
        )

        if result.returncode != 0:
            msg = f"Failed to copy buildcache from container: {result.stderr}"
            logger.error(msg)
            console.print(f"[bold red]{escape(msg)}[/bold red]")
            raise SlurmFactoryError(msg)

        console.print(f"[bold green]✓ Published compiler binaries to {buildcache_path}[/bold green]")
        logger.debug(f"Successfully published compiler to buildcache at {buildcache_path}")

    except subprocess.TimeoutExpired:
        msg = "Publishing timed out"
        logger.error(msg)
        console.print(f"[bold red]{msg}[/bold red]")
        raise SlurmFactoryError(msg)
    except Exception as e:
        msg = f"Failed to publish compiler to buildcache: {e}"
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
