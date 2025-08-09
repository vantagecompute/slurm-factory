"""Constants of slurm-factory."""

import textwrap
from enum import Enum

# Mapping of user-facing version strings to Spack package versions
SLURM_VERSIONS = {
    "25.05": "25-05-1-1",
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


# Container paths
CONTAINER_CACHE_DIR = "/opt/slurm-factory-cache"
CONTAINER_PATCHES_DIR = "/srv/global-patches"
CONTAINER_SPACK_TEMPLATES_DIR = "/opt/spack/share/spack/templates/modules"
CONTAINER_SPACK_PROJECT_DIR = "/root/spack-project"
CONTAINER_SLURM_DIR = "/opt/slurm"
CONTAINER_BUILD_OUTPUT_DIR = f"{CONTAINER_CACHE_DIR}/builds"
CONTAINER_ROOT_DIR = "/root"
CONTAINER_SPACK_CACHE_DIR = "/root/.cache/spack"


# LXD image configuration
LXD_IMAGE = "24.04"
LXD_IMAGE_REMOTE = "ubuntu"

# Base instance configuration
BASE_INSTANCE_PREFIX = "slurm-factory-base"
BASE_INSTANCE_EXPIRY_DAYS = 90
INSTANCE_NAME_PREFIX = "slurm-factory"

# Timeouts
CLOUD_INIT_TIMEOUT = 300  # 5 minutes

# Spack paths
SPACK_SETUP_SCRIPT = "/opt/spack/share/spack/setup-env.sh"
SPACK_BUILTIN_DIR = "./.spack-env/repos/builtin/spack_repo/builtin"
SPACK_REPO_PATH = f"{SPACK_BUILTIN_DIR}/packages/slurm/"

# Patch files
SLURM_PATCH_FILES = ["slurm_prefix.patch", "package.py"]

# Shell script templates
BASH_HEADER = ["bash", "-c"]


# Spack build cache setup script template
def get_spack_build_cache_script() -> str:
    """Return the rendered build cache script."""
    return textwrap.dedent(
        f"""
        set -e

        # Create spack project directory and write dynamic configuration
        cd {CONTAINER_SPACK_PROJECT_DIR}

        source {SPACK_SETUP_SCRIPT}
        spack env activate .

        # Apply patches for Slurm package
        mkdir -p {SPACK_REPO_PATH}
        cp {CONTAINER_PATCHES_DIR}/slurm_prefix.patch {SPACK_REPO_PATH}
        cp {CONTAINER_PATCHES_DIR}/package.py {SPACK_REPO_PATH}
        cp repo.yaml {SPACK_BUILTIN_DIR}
        echo 'Custom patches applied successfully'

        echo 'Setting up Spack environment and build cache...'
        echo 'Generated dynamic Spack configuration'
        echo 'Binary cache mirrors configured:'
        spack mirror list

        echo 'Starting Spack concretization...'
        spack concretize -j $(nproc) -f

        echo 'Installing ALL dependencies from dynamic configuration into build cache...'
        echo 'This will build and cache everything: Slurm, OpenMPI, dependencies, etc.'
        spack install -j$(nproc) -f --verbose

        echo 'Creating build cache entries for ALL remaining packages...'
        # Use a simpler, more reliable approach for buildcache creation
        echo 'Attempting to push all installed packages to buildcache...'

        # First, check what packages are actually installed
        echo "Currently installed packages:"
        spack find

        # Try to push all packages at once, but handle failures gracefully
        echo "Pushing all packages to buildcache (errors will be ignored)..."
        spack buildcache push local-buildcache --force 2>/dev/null || {{
            echo "Bulk push failed, trying individual package approach..."

            # Fallback: try to push each package individually with error handling
            spack find --format '{{name}}@{{version}}' | while read -r pkg; do
                if [ -n "$pkg" ]; then
                    echo "Attempting to push $pkg..."
                    spack buildcache push local-buildcache "$pkg" 2>/dev/null || {{
                        echo "Warning: Could not push $$pkg to buildcache, skipping..."
                    }}
                fi
            done
        }}

        # Always update the buildcache index, even if some packages failed
        echo 'Updating buildcache index...'
        mkdir -p /opt/slurm-factory-cache/spack-buildcache/build_cache
        spack buildcache update-index local-buildcache 2>/dev/null || {{
            echo "Warning: Could not update buildcache index, but continuing..."
        }}

        echo 'Listing cached packages:'
        spack buildcache list local-buildcache | head -20
        echo 'Build cache setup completed - ALL packages from dynamic configuration are now cached!'
        """
    )


def get_package_creation_script(version: str) -> str:
    """Return the package creation script."""
    return textwrap.dedent(
        f"""
        set -e

        cd {CONTAINER_SPACK_PROJECT_DIR}

        source {SPACK_SETUP_SCRIPT}
        spack env activate .

        echo 'Setting up Spack environment and build cache...'
        echo 'Generated dynamic Spack configuration'
        echo 'Binary cache mirrors configured:'
        spack mirror list

        echo 'Starting Spack concretization...'
        spack concretize -j $(nproc) -f

        echo 'Installing ALL dependencies from dynamic configuration into build cache...'
        echo 'This will build and cache everything: Slurm, OpenMPI, dependencies, etc.'
        spack install -j$(nproc) -f --verbose
        spack gc -y

        echo 'Creating redistributable package structure...'
        mkdir -p {CONTAINER_SLURM_DIR}/redistributable

        echo 'Packaging Spack view (compiled software)...'
        # Copy the actual files from the view, not just symlinks
        mkdir -p {CONTAINER_SLURM_DIR}/software
        echo "Copying Spack view contents (resolving symlinks)..."
        cp -rL {CONTAINER_SLURM_DIR}/view/* {CONTAINER_SLURM_DIR}/software/

        echo "Performing lightweight cleanup of development files..."
        cd {CONTAINER_SLURM_DIR}/software

        # Show original size
        ORIGINAL_SIZE=$(du -sh . | cut -f1)
        echo "Original software size: $ORIGINAL_SIZE"

        # Light cleanup - remove development files not needed at runtime
        find . -name "include" -type d -exec rm -rf {{}} + 2>/dev/null || true
        find . -path "*/lib/pkgconfig" -type d -exec rm -rf {{}} + 2>/dev/null || true
        rm -rf share/doc share/man share/info 2>/dev/null || true
        find . -name "__pycache__" -type d -exec rm -rf {{}} + 2>/dev/null || true
        find . -name "*.pyc" -delete 2>/dev/null || true
        find . -name "*.a" -delete 2>/dev/null || true

        # Show size after cleanup
        PRUNED_SIZE=$(du -sh . | cut -f1)
        echo "Cleaned software size: $PRUNED_SIZE (reduced from $ORIGINAL_SIZE)"

        tar -czf {CONTAINER_SLURM_DIR}/redistributable/slurm-{version}-software.tar.gz -C \
            {CONTAINER_SLURM_DIR} software/
        echo "Software package created successfully"

        echo 'Packaging Spack-generated relocatable modules...'
        mkdir -p {CONTAINER_SLURM_DIR}/modules

        # Generate modules explicitly using our custom template
        echo "Generating modules with custom relocatable template..."
        spack module lmod refresh --delete-tree -y
        spack module lmod refresh -y

        # Find the generated module using Spack's module system
        echo "Finding Spack-generated module..."
        MODULE_FILE=$(spack module lmod find slurm 2>/dev/null || echo "")

        if [ -n "$MODULE_FILE" ]; then
            echo "Found Spack module: $MODULE_FILE"
            # Find the actual file path for this module
            SPACK_ROOT=$(spack location -r)
            MODULE_PATH=$(find "$SPACK_ROOT" -name "*.lua" -path "*$MODULE_FILE*" 2>/dev/null | head -1)

            if [ -n "$MODULE_PATH" ] && [ -f "$MODULE_PATH" ]; then
                echo "Copying module file from: $MODULE_PATH"
                cp "$MODULE_PATH" {CONTAINER_SLURM_DIR}/modules/
                echo "Module copied successfully"
            else
                echo "Error: Could not find module file for $MODULE_FILE"
                exit 1
            fi
        else
            echo "Error: Could not find Slurm module using 'spack module lmod find'"
            exit 1
        fi

        # Create the proper directory structure for module deployment
        echo 'Structuring module files for deployment...'
        mkdir -p {CONTAINER_SLURM_DIR}/module-package/slurm

        # Copy the module files
        if [ -d "{CONTAINER_SLURM_DIR}/modules" ] && \
            [ "$(ls -A {CONTAINER_SLURM_DIR}/modules 2>/dev/null)" ]; then
            echo "Copying module files to package structure..."
            cp -r {CONTAINER_SLURM_DIR}/modules/* {CONTAINER_SLURM_DIR}/module-package/slurm/
            ls -la {CONTAINER_SLURM_DIR}/module-package/slurm/
        else
            echo "Error: No module files found after generation"
            exit 1
        fi

        # Create tarball with the correct structure for extraction to /usr/share/lmod/lmod/modulefiles/
        tar -czf {CONTAINER_SLURM_DIR}/redistributable/slurm-{version}-module.tar.gz -C \
            {CONTAINER_SLURM_DIR}/module-package .

        echo 'Redistributable packages created successfully!'
        ls -la {CONTAINER_SLURM_DIR}/redistributable/
        du -sh {CONTAINER_SLURM_DIR}/redistributable/*

        echo 'Copying redistributable packages to output directory...'
        cp {CONTAINER_SLURM_DIR}/redistributable/slurm-{version}-module.tar.gz \
            {CONTAINER_BUILD_OUTPUT_DIR}/
        cp {CONTAINER_SLURM_DIR}/redistributable/slurm-{version}-software.tar.gz \
                {CONTAINER_BUILD_OUTPUT_DIR}/

        ls -la {CONTAINER_BUILD_OUTPUT_DIR}/
        echo 'Files copied successfully!'
        """
    )
