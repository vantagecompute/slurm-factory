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

"""Build GCC compiler toolchain command."""

import typer
from rich.console import Console
from typing_extensions import Annotated

from slurm_factory.builders.toolchain_builder import build_compiler as builder_build_compiler
from slurm_factory.constants import COMPILER_TOOLCHAINS


def build_toolchain_command(
    ctx: typer.Context,
    compiler_version: Annotated[
        str,
        typer.Option(
            "--compiler-version",
            help=f"GCC compiler version to build ({', '.join(COMPILER_TOOLCHAINS.keys())})",
        ),
    ] = "13.4.0",
    no_cache: Annotated[
        bool, typer.Option("--no-cache", help="Force a fresh build without using Docker cache")
    ] = False,
    publish: Annotated[
        str,
        typer.Option(
            "--publish",
            help=(
                "Publish to buildcache: none (default), compiler (publish compiler), all (same as compiler)"
            ),
        ),
    ] = "none",
    signing_key: Annotated[
        str | None,
        typer.Option("--signing-key", help="GPG key ID for signing buildcache packages (e.g., '0xKEYID')"),
    ] = None,
    gpg_private_key: Annotated[
        str | None,
        typer.Option(
            "--gpg-private-key",
            help="Base64-encoded GPG private key to import into Docker container for signing",
        ),
    ] = None,
    gpg_passphrase: Annotated[
        str | None,
        typer.Option(
            "--gpg-passphrase",
            help="GPG private key passphrase for signing packages",
        ),
    ] = None,
):
    """
    Build a GCC compiler toolchain for use in Slurm builds.

    This command builds a relocatable GCC compiler toolchain using Spack and
    optionally publishes it to S3 buildcache for reuse across builds.

    Compiler toolchains - all built with Spack for relocatability:
    - 14.2.0: GCC 14.2, glibc 2.39, latest stable
    - 13.4.0 (default): GCC 13.4, glibc 2.39, Ubuntu 24.04 compatible
    - 12.5.0: GCC 12.5, glibc 2.35, Ubuntu 22.04 compatible
    - 11.5.0: GCC 11.5, glibc 2.35, good compatibility
    - 10.5.0: GCC 10.5, glibc 2.31, RHEL 8/Ubuntu 20.04 compatible
    - 9.5.0: GCC 9.5, glibc 2.28, wide compatibility
    - 8.5.0: GCC 8.5, glibc 2.28, RHEL 8 minimum
    - 7.5.0: GCC 7.5, glibc 2.17, RHEL 7 compatible (maximum compatibility)

    Buildcache publishing (--publish):
    - none (default): Don't publish to buildcache
    - compiler: Publish the compiler to buildcache
    - all: Publish all packages (same as compiler for this command)

    Examples:
        slurm-factory build-toolchain                              # Build default compiler (gcc 13.4.0)
        slurm-factory build-toolchain --compiler-version 14.2.0    # Build gcc 14.2
        slurm-factory build-toolchain --compiler-version 10.5.0    # Build gcc 10.5 for RHEL 8
        slurm-factory build-toolchain --publish=compiler           # Build and publish to S3 buildcache
        slurm-factory build-toolchain --publish=all --signing-key 0xKEYID  # Build and publish with signing
        slurm-factory build-toolchain --no-cache                   # Build without Docker cache

    """
    console = Console()

    # Validate publish parameter
    valid_publish_options = ["none", "compiler", "all"]
    if publish not in valid_publish_options:
        console.print(f"[bold red]Error: Invalid --publish value '{publish}'[/bold red]")
        console.print(f"[bold yellow]Valid options: {', '.join(valid_publish_options)}[/bold yellow]")
        raise typer.Exit(1)

    if compiler_version not in COMPILER_TOOLCHAINS:
        console.print(f"[bold red]Error: Invalid compiler version '{compiler_version}'[/bold red]")
        console.print(
            f"[bold yellow]Available versions: {', '.join(sorted(COMPILER_TOOLCHAINS.keys()))}[/bold yellow]"
        )
        raise typer.Exit(1)

    # Show compiler info
    gcc_ver, glibc_ver, description = COMPILER_TOOLCHAINS[compiler_version]
    console.print(
        f"[bold blue]Building compiler toolchain:[/bold blue] "
        f"GCC {gcc_ver}, glibc {glibc_ver} ({description})"
    )

    if no_cache:
        console.print("[bold yellow]Building with --no-cache (fresh build)[/bold yellow]")

    if publish != "none":
        console.print(f"[bold cyan]Will publish to buildcache: {publish}[/bold cyan]")
        if signing_key:
            console.print(f"[bold blue]Using GPG signing key: {signing_key}[/bold blue]")

    builder_build_compiler(
        ctx, compiler_version, no_cache, publish, signing_key, gpg_private_key, gpg_passphrase
    )
