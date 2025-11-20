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
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

from rich.console import Console
from rich.markup import escape

from .exceptions import SlurmFactoryError

# Set up logging following craft-providers pattern
logger = logging.getLogger(__name__)
console = Console()


def get_data_dir() -> Path:
    """
    Get the path to the data directory.

    When installed as a wheel, data files are in share/slurm-factory/
    When running from source, data files are in data/ at the repository root.

    Returns
    -------
        Path to the data directory

    """
    # Try installed location first (sys.prefix/share/slurm-factory/)
    installed_data = Path(sys.prefix) / "share" / "slurm-factory"
    if installed_data.exists():
        logger.debug(f"Using installed data directory: {installed_data}")
        return installed_data

    # Fall back to development/source location (repo_root/data/)
    package_dir = Path(__file__).parent.parent
    source_data = package_dir / "data"
    if source_data.exists():
        logger.debug(f"Using source data directory: {source_data}")
        return source_data

    raise FileNotFoundError(
        f"Could not find data directory. Tried:\n  - {installed_data}\n  - {source_data}"
    )


def build_docker_image(
    image_tag: str,
    dockerfile_content: str,
    target: str,
) -> None:
    """
    Build a Docker image from a Dockerfile string.

    Args:
        image_tag: Tag for the Docker image
        dockerfile_content: Complete Dockerfile as a string
        no_cache: Force a fresh build without using Docker cache
        target: Build target stage in multi-stage builds (e.g., "builder")

    """
    console.print(f"[bold blue]Building Docker image {image_tag}...[/bold blue]")
    logger.debug(f"Building Docker image: {image_tag}")
    logger.debug(f"Dockerfile size: {len(dockerfile_content)} characters")

    logger.debug("Building with --no-cache flag")
    console.print("[bold yellow]Building without cache (this may take longer)[/bold yellow]")

    logger.debug(f"Building target stage: {target}")
    console.print(f"[dim]Building target stage: {target}[/dim]")

    process = None
    try:
        # Find the repository root (where pyproject.toml is located)

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

        # Ensure data files are available in the build context
        # If running from installed wheel, copy data files to build context
        data_source = get_data_dir()
        data_target = repo_root / "data"

        if data_source != data_target:
            logger.debug(f"Staging data files from {data_source} to {data_target}")

            if data_target.exists():
                shutil.rmtree(data_target)
            shutil.copytree(data_source, data_target)

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

        # Add --no-cache flag for fresh builds and to reduce issues caused by caching in build environments
        cmd.insert(2, "--no-cache")

        # Add --target flag if specified
        if target:
            cmd.extend(["--target", target])

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


def remove_old_docker_image(image_tag: str) -> None:
    """
    Remove an old Docker image if it exists.

    Args:
        image_tag: Tag of the image to remove

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
        console.print(f"[dim]Warning: Could not remove old image: {escape(str(e))}[/dim]")



def get_install_spack_script() -> str:
    """Generate script to install Spack."""
    return textwrap.dedent(
        """\
        git clone --depth 1 --branch v1.0.0 https://github.com/spack/spack.git /opt/spack && \\
        chown -R root:root /opt/spack && chmod -R a+rX /opt/spack
    """
    ).strip()


def get_create_spack_profile_script() -> str:
    """Generate script to set up Spack profile."""
    return textwrap.dedent("""\
        echo 'source /opt/spack/share/spack/setup-env.sh' >> /etc/profile.d/spack.sh && \\
        chmod 644 /etc/profile.d/spack.sh
    """).strip()
