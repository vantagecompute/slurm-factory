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

"""Toolchain build commands for slurm-factory."""

import typer

from .build import build_toolchain_command

# Create the build-toolchain command group
build_toolchain_app = typer.Typer(
    name="build-toolchain",
    help="Build GCC compiler toolchains for Slurm builds.",
    invoke_without_command=True,
    callback=build_toolchain_command,
)

__all__ = ["build_toolchain_app"]
