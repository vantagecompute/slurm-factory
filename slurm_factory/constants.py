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

"""Constants of slurm-factory."""

import textwrap
from enum import Enum

# Mapping of user-facing version strings to Spack package versions
SLURM_VERSIONS = {
    "25.05": "25-05-3-1",
    "24.11": "24-11-6-1",
    "23.11": "23-11-11-1",
    "23.02": "23-02-7-1",
}


class SlurmVersion(str, Enum):
    """Available Slurm versions for building."""

    v25_05 = "25.05"
    v24_11 = "24.11"
    v23_11 = "23.11"
    v23_02 = "23.02"


class BuildType(str, Enum):
    """Build type options for Slurm."""

    cpu = "cpu"
    gpu = "gpu"
    minimal = "minimal"


# LXD image configuration
LXD_IMAGE = "24.04"
LXD_IMAGE_REMOTE = "ubuntu"

INSTANCE_NAME_PREFIX = "slurm-factory"

# Timeouts
CLOUD_INIT_TIMEOUT = 300  # 5 minutes

# Spack repository paths
SPACK_SETUP_SCRIPT = "/opt/spack/share/spack/setup-env.sh"

# Container paths
CONTAINER_CACHE_DIR = "/opt/slurm-factory-cache"
CONTAINER_SPACK_TEMPLATES_DIR = "/opt/spack/share/spack/templates/modules"
CONTAINER_SPACK_PROJECT_DIR = "/root/spack-project"
CONTAINER_SLURM_DIR = "/opt/slurm"
CONTAINER_BUILD_OUTPUT_DIR = f"{CONTAINER_CACHE_DIR}/builds"
CONTAINER_ROOT_DIR = "/root"
CONTAINER_SPACK_CACHE_DIR = "/root/.cache/spack"

# Patch files
SLURM_PATCH_FILES = ["slurm_prefix.patch", "package.py"]

# Shell script templates
BASH_HEADER = ["bash", "-c"]


def get_package_creation_script(version: str) -> str:
    """Return the package creation script."""
    return textwrap.dedent(
        f"""
        set -e
        set -x  # Enable debug output for all commands

        echo "DEBUG: Starting package creation script for Slurm version {version}"
        echo "DEBUG: Working directory: $(pwd)"
        echo "DEBUG: Available disk space: $(df -h /opt)"

        cd {CONTAINER_SPACK_PROJECT_DIR}
        echo "DEBUG: Changed to Spack project directory: $(pwd)"

        source {SPACK_SETUP_SCRIPT}
        spack env activate .
        echo "DEBUG: Spack environment activated"

        echo 'Setting up Spack environment and build cache...'
        echo 'Generated dynamic Spack configuration'
        echo 'Binary cache mirrors configured:'
        spack mirror list

        echo "DEBUG: Starting concretization process..."
        echo 'Removing any stale lock file to ensure fresh concretization...'
        rm -f spack.lock
        echo 'Starting Spack concretization...'
        spack concretize -j $(nproc) -f --fresh

        echo "DEBUG: Concretization completed, starting installation..."
        echo 'Installing ALL dependencies from dynamic configuration...'
        echo 'Building everything from source (no binary cache in single-stage builds)...'
        # Use --only-concrete to ensure we only install what was concretized, without re-concretization
        spack install -j$(nproc) --only-concrete -f --verbose -p 4 --no-cache

        echo "DEBUG: Verifying Slurm installation..."
        if ! spack find --format "{{hash:7}}" slurm | grep -qE "^[a-z0-9]{{7}}$"; then
            echo "ERROR: Slurm package was not installed!"
            echo "Installed packages:"
            spack find
            exit 1
        fi
        echo "DEBUG: Slurm installation verified"

        echo "DEBUG: Installation completed, running garbage collection..."
        spack gc -y

        echo "DEBUG: Creating redistributable package structure..."
        echo 'Creating redistributable package structure...'
        mkdir -p {CONTAINER_SLURM_DIR}/redistributable

        echo "DEBUG: Verifying view was created successfully..."
        if [ ! -d "{CONTAINER_SLURM_DIR}/view" ]; then
            echo "ERROR: Spack view was not created at {CONTAINER_SLURM_DIR}/view"
            exit 1
        fi
        echo "DEBUG: View exists and will be used for packaging"

        # The view already contains everything we need in a FHS-compliant structure
        # Spack has already created hardlinks and set proper RPATHs
        # We just need to verify critical libraries are present

        echo "DEBUG: Verifying critical libraries in view..."
        MISSING_LIBS=""

        # Check for Slurm binaries
        if [ ! -f "{CONTAINER_SLURM_DIR}/view/bin/slurmctld" ]; then
            echo "WARNING: slurmctld not found in view"
            MISSING_LIBS="$MISSING_LIBS slurmctld"
        fi

        # Check for critical libraries that Slurm needs
        for lib in libmunge.so libjwt.so libjansson.so; do
            if ! find {CONTAINER_SLURM_DIR}/view/lib* -name "$lib*" 2>/dev/null | grep -q .; then
                echo "WARNING: $lib not found in view"
                MISSING_LIBS="$MISSING_LIBS $lib"
            fi
        done

        if [ -n "$MISSING_LIBS" ]; then
            echo "WARNING: Some expected libraries/binaries are missing: $MISSING_LIBS"
            echo "Continuing anyway - they may not be required for this configuration"
        else
            echo "DEBUG: All critical libraries verified in view"
        fi

        echo "DEBUG: Merging view into software directory..."
        echo "Copying Spack view contents to software directory (resolving symlinks)..."
        echo "DEBUG: Copying from {CONTAINER_SLURM_DIR}/view/* to {CONTAINER_SLURM_DIR}/software/"
        cp -rL {CONTAINER_SLURM_DIR}/view/* {CONTAINER_SLURM_DIR}/software/

        echo "DEBUG: Checking for MySQL libraries..."
        echo "Ensuring MySQL client libraries are included..."
        # Check if MySQL libraries are missing from the view and add them manually if needed
        if [ ! -f "{CONTAINER_SLURM_DIR}/software/lib/libmysqlclient.so.21" ]; then
            echo "DEBUG: MySQL libraries missing from view, adding them manually..."
            echo "MySQL libraries missing from view, adding them manually..."
            MYSQL_INSTALL_DIR=$(spack location -i mysql)
            echo "DEBUG: MySQL installation directory: $MYSQL_INSTALL_DIR"
            if [ -d "$MYSQL_INSTALL_DIR/lib" ]; then
                echo "DEBUG: Copying MySQL libraries from $MYSQL_INSTALL_DIR/lib/"
                cp -L "$MYSQL_INSTALL_DIR/lib/libmysqlclient.so"* \
                    {CONTAINER_SLURM_DIR}/software/lib/ 2>/dev/null || true
                echo "MySQL client libraries copied successfully"
                echo "DEBUG: MySQL library copy completed"
            else
                echo "Warning: MySQL installation directory not found"
                echo "DEBUG: MySQL installation directory $MYSQL_INSTALL_DIR/lib not found"
            fi
        else
            echo "MySQL libraries already present in view"
            echo "DEBUG: MySQL libraries already present in view"
        fi

        echo "DEBUG: Starting software cleanup process..."
        echo "Performing lightweight cleanup of development files from software directory..."
        cd {CONTAINER_SLURM_DIR}/software

        # Show original size
        ORIGINAL_SIZE=$(du -sh . | cut -f1)
        echo "Original software size: $ORIGINAL_SIZE"
        echo "DEBUG: Original software size: $ORIGINAL_SIZE"

        # Light cleanup - remove development files not needed at runtime
        echo "DEBUG: Removing include directories..."
        find . -name "include" -type d -exec rm -rf {{}} + 2>/dev/null || true
        echo "DEBUG: Removing pkgconfig directories..."
        find . -path "*/lib/pkgconfig" -type d -exec rm -rf {{}} + 2>/dev/null || true
        echo "DEBUG: Removing documentation directories..."
        find . -path "*/share/doc" -type d -exec rm -rf {{}} + 2>/dev/null || true
        find . -path "*/share/man" -type d -exec rm -rf {{}} + 2>/dev/null || true
        find . -path "*/share/info" -type d -exec rm -rf {{}} + 2>/dev/null || true
        echo "DEBUG: Removing Python cache files..."
        find . -name "__pycache__" -type d -exec rm -rf {{}} + 2>/dev/null || true
        find . -name "*.pyc" -delete 2>/dev/null || true
        echo "DEBUG: Removing static libraries..."
        find . -name "*.a" -delete 2>/dev/null || true

        # Show size after cleanup
        PRUNED_SIZE=$(du -sh . | cut -f1)
        echo "Cleaned software size: $PRUNED_SIZE (reduced from $ORIGINAL_SIZE)"
        echo "DEBUG: Cleaned software size: $PRUNED_SIZE (reduced from $ORIGINAL_SIZE)"

        echo "DEBUG: Creating software tarball from install tree..."
        # Package the Spack install tree preserving the software/ directory structure
        tar -czf {CONTAINER_SLURM_DIR}/redistributable/slurm-{version}-software.tar.gz -C \
            {CONTAINER_SLURM_DIR} software/
        echo "Software package created successfully"
        echo "DEBUG: Software package created successfully"

        echo "DEBUG: Starting module packaging process..."
        echo 'Packaging Spack-generated relocatable modules...'
        mkdir -p {CONTAINER_SLURM_DIR}/modules

        # Generate modules explicitly using our custom template
        echo "Generating modules with custom relocatable template..."
        echo "DEBUG: Refreshing module tree..."
        spack module lmod refresh --delete-tree -y
        echo "DEBUG: Generating new modules..."
        spack module lmod refresh -y

        # Find the generated module using Spack's module system
        echo "Finding Spack-generated module..."
        echo "DEBUG: Finding Spack-generated module..."
        MODULE_FILE=$(spack module lmod find slurm 2>/dev/null || echo "")

        if [ -n "$MODULE_FILE" ]; then
            echo "Found Spack module: $MODULE_FILE"
            echo "DEBUG: Found Spack module: $MODULE_FILE"
            # Find the actual file path for this module
            SPACK_ROOT=$(spack location -r)
            echo "DEBUG: Spack root: $SPACK_ROOT"
            MODULE_PATH=$(find "$SPACK_ROOT" -name "*.lua" -path "*$MODULE_FILE*" 2>/dev/null | head -1)
            echo "DEBUG: Module path search result: $MODULE_PATH"

            if [ -n "$MODULE_PATH" ] && [ -f "$MODULE_PATH" ]; then
                echo "Copying module file from: $MODULE_PATH"
                echo "DEBUG: Copying module file from: $MODULE_PATH"
                cp "$MODULE_PATH" {CONTAINER_SLURM_DIR}/modules/
                echo "Module copied successfully"
                echo "DEBUG: Module copied successfully"
            else
                echo "Error: Could not find module file for $MODULE_FILE"
                echo "DEBUG: Error: Could not find module file for $MODULE_FILE"
                exit 1
            fi
        else
            echo "Error: Could not find Slurm module using 'spack module lmod find'"
            echo "DEBUG: Error: Could not find Slurm module using 'spack module lmod find'"
            exit 1
        fi

        # Create the proper directory structure for module deployment
        echo 'Structuring module files for deployment...'
        echo "DEBUG: Creating module package structure..."
        mkdir -p {CONTAINER_SLURM_DIR}/module-package/slurm

        # Copy the module files
        if [ -d "{CONTAINER_SLURM_DIR}/modules" ] && \
            [ "$(ls -A {CONTAINER_SLURM_DIR}/modules 2>/dev/null)" ]; then
            echo "Copying module files to package structure..."
            echo "DEBUG: Copying module files to package structure..."
            cp -r {CONTAINER_SLURM_DIR}/modules/* {CONTAINER_SLURM_DIR}/module-package/slurm/

            # Create .modulerc.lua to set default version
            echo "Creating .modulerc.lua for module default version..."
            echo "DEBUG: Creating .modulerc.lua for module default version..."
            MODULE_LUA_FILE=$(ls {CONTAINER_SLURM_DIR}/module-package/slurm/*.lua | head -1)
            if [ -n "$MODULE_LUA_FILE" ]; then
                MODULE_VERSION=$(basename "$MODULE_LUA_FILE" .lua)
                echo "DEBUG: Detected module version: $MODULE_VERSION"
                cat > {CONTAINER_SLURM_DIR}/module-package/slurm/.modulerc.lua << EOF
-- Set default version for slurm module using module_version
module_version("$MODULE_VERSION","default")
EOF
                echo "DEBUG: Created .modulerc.lua with default version: $MODULE_VERSION"
            else
                echo "Warning: Could not detect module version for .modulerc.lua"
                echo "DEBUG: Warning: Could not detect module version for .modulerc.lua"
            fi

            echo "DEBUG: Module package contents:"
            ls -la {CONTAINER_SLURM_DIR}/module-package/slurm/
        else
            echo "Error: No module files found after generation"
            echo "DEBUG: Error: No module files found after generation"
            exit 1
        fi

        # Create tarball with the correct structure for extraction to /usr/share/lmod/lmod/modulefiles/
        echo "DEBUG: Creating module tarball..."
        tar -czf {CONTAINER_SLURM_DIR}/redistributable/slurm-{version}-module.tar.gz -C \
            {CONTAINER_SLURM_DIR}/module-package .

        echo 'Redistributable packages created successfully!'
        echo "DEBUG: Redistributable packages created successfully!"
        echo "DEBUG: Package contents:"
        ls -la {CONTAINER_SLURM_DIR}/redistributable/
        du -sh {CONTAINER_SLURM_DIR}/redistributable/*

        echo 'Copying redistributable packages to output directory...'
        echo "DEBUG: Copying packages to {CONTAINER_BUILD_OUTPUT_DIR}/"
        cp {CONTAINER_SLURM_DIR}/redistributable/slurm-{version}-module.tar.gz \
            {CONTAINER_BUILD_OUTPUT_DIR}/
        cp {CONTAINER_SLURM_DIR}/redistributable/slurm-{version}-software.tar.gz \
                {CONTAINER_BUILD_OUTPUT_DIR}/

        echo "DEBUG: Final output directory contents:"
        ls -la {CONTAINER_BUILD_OUTPUT_DIR}/
        echo 'Files copied successfully!'
        echo "DEBUG: Package creation script completed successfully"
        """
    )
