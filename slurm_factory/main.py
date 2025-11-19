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

"""Main typer app for slurm-factory."""

import logging
import subprocess
import sys

import typer
from rich.console import Console
from rich.markup import escape
from typing_extensions import Annotated

from slurm_factory.commands.build_slurm import build_slurm_app
from slurm_factory.commands.build_toolchain import build_toolchain_app
from slurm_factory.config import Settings

# Configure logging following craft-providers pattern
app = typer.Typer(name="Slurm Factory", add_completion=True)


def setup_logging(verbose: bool = False):
    """Configure logging based on verbosity level."""
    if verbose:
        level = logging.DEBUG
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    else:
        level = logging.INFO
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logging.basicConfig(
        level=level,
        format=format_string,
        stream=sys.stderr,
        force=True,  # Override any existing logging config
    )

    # Set specific loggers to appropriate levels
    if verbose:
        logging.getLogger("slurm_factory").setLevel(logging.DEBUG)
        logging.getLogger("craft_providers").setLevel(logging.DEBUG)
    else:
        logging.getLogger("slurm_factory").setLevel(logging.INFO)
        logging.getLogger("craft_providers").setLevel(logging.WARNING)


@app.callback()
def main(
    ctx: typer.Context,
    project_name: Annotated[
        str,
        typer.Option(
            "--project-name",
            envvar="IF_PROJECT_NAME",
            help="The LXD project in which resources are going to be created",
        ),
    ] = "slurm-factory",
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose output")] = False,
):
    """Handle global options for the application."""
    setup_logging(verbose=verbose)

    settings = Settings(project_name=project_name)

    ctx.ensure_object(dict)
    ctx.obj["project_name"] = project_name
    ctx.obj["verbose"] = verbose
    ctx.obj["settings"] = settings


@app.command("clean")
def clean(
    ctx: typer.Context,
    full_cleanup: Annotated[
        bool, typer.Option("--full", help="Remove Docker images in addition to containers")
    ] = False,
):
    """
    Clean up Docker containers and images from slurm-factory builds.

    By default, removes stopped containers but keeps images for faster rebuilds.
    Use --full to remove both containers and images.

    Examples:
        slurm-factory clean        # Remove stopped containers
        slurm-factory clean --full  # Remove containers and images

    """
    console = Console()
    logger = logging.getLogger(__name__)
    logger.info("Cleaning up Docker containers and images")

    try:
        # List all containers with slurm-factory prefix
        result = subprocess.run(
            ["docker", "ps", "-a", "--filter", "name=slurm-factory", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            console.print("[bold red]Failed to list Docker containers[/bold red]")
            return

        containers = [line.strip() for line in result.stdout.split("\n") if line.strip()]

        if not containers:
            console.print("[green]No slurm-factory containers found[/green]")
        else:
            console.print(f"[bold red]Removing {len(containers)} slurm-factory container(s):[/bold red]")
            for container_name in containers:
                console.print(f"  [red]🗑️  {container_name}[/red]")

            # Remove containers
            for container_name in containers:
                try:
                    logger.debug(f"Removing container: {container_name}")
                    subprocess.run(
                        ["docker", "rm", "-f", container_name],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    console.print(f"  [green]✓[/green] Removed {container_name}")
                except Exception as e:
                    logger.error(f"Failed to remove container {container_name}: {e}")
                    console.print(f"  [red]✗[/red] Failed to remove {container_name}")

        # Clean up images if full cleanup requested
        if full_cleanup:
            console.print("\n[bold blue]Cleaning up Docker images...[/bold blue]")
            result = subprocess.run(
                [
                    "docker",
                    "images",
                    "--filter",
                    "reference=slurm-factory:*",
                    "--format",
                    "{{.Repository}}:{{.Tag}}",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                images = [line.strip() for line in result.stdout.split("\n") if line.strip()]

                if not images:
                    console.print("[green]No slurm-factory images found[/green]")
                else:
                    console.print(f"[bold red]Removing {len(images)} slurm-factory image(s):[/bold red]")
                    for image_name in images:
                        console.print(f"  [red]�️  {image_name}[/red]")

                    # Remove images
                    for image_name in images:
                        try:
                            logger.debug(f"Removing image: {image_name}")
                            subprocess.run(
                                ["docker", "rmi", "-f", image_name],
                                capture_output=True,
                                text=True,
                                timeout=60,
                            )
                            console.print(f"  [green]✓[/green] Removed {image_name}")
                        except Exception as e:
                            logger.error(f"Failed to remove image {image_name}: {e}")
                            console.print(f"  [red]✗[/red] Failed to remove {image_name}")

        console.print("\n[bold green]✓ Cleanup completed[/bold green]")

        if not full_cleanup and len(containers) > 0:
            console.print("[dim]Tip: Use [bold]--full[/bold] to also remove Docker images[/dim]")

    except FileNotFoundError:
        console.print("[bold red]Docker is not installed or not in PATH[/bold red]")
        logger.error("Docker command not found")
        raise typer.Exit(1)
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        console.print(f"[bold red]Error during cleanup: {escape(str(e))}[/bold red]")
        raise typer.Exit(1)


# Register command groups
app.add_typer(build_toolchain_app, name="build-toolchain")
app.add_typer(build_slurm_app, name="build-slurm")


if __name__ == "__main__":
    app()
