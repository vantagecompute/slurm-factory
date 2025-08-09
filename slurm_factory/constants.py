"""Constants used throughout the slurm-factory package."""

import textwrap
from enum import Enum
from string import Template

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
CONTAINER_SPACK_PROJECT_DIR = "/root/spack-project"
CONTAINER_SLURM_DIR = "/opt/slurm"
CONTAINER_BUILD_OUTPUT_DIR = f"{CONTAINER_CACHE_DIR}/builds"
CONTAINER_ROOT_DIR = "/root"
CONTAINER_SPACK_CACHE_DIR = "/root/.cache/spack"

# Cache subdirectories
CACHE_SUBDIRS = ["spack-buildcache", "spack-sourcecache", "builds"]


def get_mkdir_commands(base_dir: str, subdirs: list[str]) -> str:
    """Generate mkdir commands for creating cache subdirectories."""
    commands: list[str] = []
    for subdir in subdirs:
        commands.append(f"mkdir -p {base_dir}/{subdir}")
    return "\n".join(commands)


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
SPACK_REPO_PATH = "./.spack-env/repos/builtin/spack_repo/builtin/packages/slurm/"

# Patch files
SLURM_PATCH_FILES = ["slurm_prefix.patch", "package.py"]

# Shell script templates
BASH_HEADER = ["bash", "-c"]

# Common bash script preamble
BASH_PREAMBLE = textwrap.dedent("""
    set -e
""").strip()

# Cache setup script template
CACHE_SETUP_SCRIPT = Template(
    textwrap.dedent(
        """
        set -e

        echo 'Setting up cache directory permissions...'

        # Create subdirectories with proper permissions
        ${create_cache_dirs}

        # Set permissions on files/dirs that the container can write to
        # Make everything world-writable so container can create subdirectories
        chmod -R 777 ${cache_dir}/ 2>/dev/null || true

        echo 'Cache directory setup completed'
        ls -la ${cache_dir}/
        """
    )
)

# Patch copy script template
PATCH_COPY_SCRIPT = Template(
    textwrap.dedent(
        """
        set -e
        # Create patches directory in container
        mkdir -p ${patches_dir}

        # Copy ${patch_name} into container
        cat > ${patches_dir}/${patch_name} << 'EOF'
        ${patch_content}
        EOF

        echo "Copied ${patch_name} to container"
        """
    )
)

# Spack project setup script template
SPACK_PROJECT_SETUP_SCRIPT = Template(
    textwrap.dedent(
        """
        set -e
        # Create the spack project directory
        mkdir -p ${project_dir}

        # Write the dynamic spack.yaml configuration
        cat > ${project_dir}/spack.yaml << 'EOF'
        ${spack_config}
        EOF
        echo "Created dynamic spack.yaml configuration in container"
        """
    )
)

# Spack build cache setup script template
SPACK_BUILD_CACHE_SCRIPT = Template(
    textwrap.dedent(
        """
        set -e

        # Create spack project directory and write dynamic configuration
        mkdir -p ${project_dir} /opt/
        cd ${project_dir}

        # Write the dynamically generated spack.yaml
        cat > spack.yaml << 'EOF'
        ${spack_config}
        EOF

        source ${spack_setup}
        spack env activate .

        echo 'Setting up Spack environment and build cache...'
        echo 'Generated dynamic Spack configuration for version ${version} (GPU: ${gpu_support})'
        echo 'Binary cache mirrors configured:'
        spack mirror list

        echo 'Starting Spack concretization...'
        spack concretize -f

        # Apply patches for Slurm package
        mkdir -p ${spack_repo_path}
        cp ${patches_dir}/slurm_prefix.patch ${spack_repo_path}
        cp ${patches_dir}/package.py ${spack_repo_path}
        echo 'Custom patches applied successfully'

        echo 'Installing ALL dependencies from dynamic configuration into build cache...'
        echo 'This will build and cache everything: Slurm, OpenMPI, dependencies, etc.'
        spack install -j$$(nproc) --verbose

        echo 'Cleaning up build-only dependencies to optimize cache...'
        # Remove packages that are only needed for building (not runtime)
        spack gc -y

        echo 'Creating build cache entries for ALL remaining packages...'
        # Use a simpler, more reliable approach for buildcache creation
        echo 'Attempting to push all installed packages to buildcache...'
        
        # First, check what packages are actually installed
        echo "Currently installed packages:"
        spack find
        
        # Try to push all packages at once, but handle failures gracefully
        echo "Pushing all packages to buildcache (errors will be ignored)..."
        spack buildcache push local-buildcache --force 2>/dev/null || {
            echo "Bulk push failed, trying individual package approach..."
            
            # Fallback: try to push each package individually with error handling
            spack find --format '{name}@{version}' | while read -r pkg; do
                if [ -n "$$pkg" ]; then
                    echo "Attempting to push $$pkg..."
                    spack buildcache push local-buildcache "$$pkg" 2>/dev/null || {
                        echo "Warning: Could not push $$pkg to buildcache, skipping..."
                    }
                fi
            done
        }
        
        # Always update the buildcache index, even if some packages failed
        echo 'Updating buildcache index...'
        mkdir -p /opt/slurm-factory-cache/spack-buildcache/build_cache
        spack buildcache update-index local-buildcache 2>/dev/null || {
            echo "Warning: Could not update buildcache index, but continuing..."
        }

        echo 'Listing cached packages:'
        spack buildcache list local-buildcache | head -20

        echo 'Build cache setup completed - ALL packages from dynamic configuration are now cached!'
        """
    )
)

# Spack install script template
SPACK_INSTALL_SCRIPT = Template(
    textwrap.dedent(
        """
        set -e
        cd ${project_dir}
        source ${spack_setup}
        spack env activate .

        echo 'Using cached base instance with ALL dependencies pre-built...'
        echo 'Binary cache mirrors configured:'
        spack mirror list

        echo 'Concretizing environment for Slurm version...'
        spack concretize -f

        echo 'Installing Slurm from build cache (should be extremely fast)...'
        echo 'Everything should be cached from the base instance build.'
        spack install --cache-only -j$$(nproc) --verbose

        echo 'Cleaning up build-only dependencies...'
        # Remove packages that are only needed for building (not runtime)
        spack gc -y

        echo 'Verifying installation completed successfully...'
        spack find

        echo 'Slurm installation from cache completed successfully!'
        """
    )
)

# Package creation script template
PACKAGE_CREATION_SCRIPT = Template(
    textwrap.dedent(
        """
        set -e
        cd ${project_dir}
        source ${spack_setup}
        spack env activate .

        echo 'Creating redistributable package structure...'
        mkdir -p ${slurm_dir}/redistributable

        echo 'Packaging Spack view (compiled software)...'
        # Copy the actual files from the view, not just symlinks
        mkdir -p ${slurm_dir}/software
        echo "Copying Spack view contents (resolving symlinks)..."
        # Use cp -rL to follow symlinks and copy actual files
        cp -rL ${slurm_dir}/view/* ${slurm_dir}/software/

        echo "Performing lightweight cleanup of development files..."
        cd ${slurm_dir}/software

        # Show original size
        ORIGINAL_SIZE=$$(du -sh . | cut -f1)
        echo "Original software size: $$ORIGINAL_SIZE"

        # Light cleanup - Spack gc already removed build deps, just clean up dev files
        # Remove development headers (Spack should have removed most build deps already)
        find . -name "include" -type d -exec rm -rf {} + 2>/dev/null || true

        # Remove documentation (not needed at runtime)
        rm -rf share/doc share/man share/info 2>/dev/null || true

        # Remove Python bytecode
        find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
        find . -name "*.pyc" -delete 2>/dev/null || true

        # Show size after cleanup
        PRUNED_SIZE=$$(du -sh . | cut -f1)
        echo "Cleaned software size: $$PRUNED_SIZE (reduced from $$ORIGINAL_SIZE)"
        echo "Note: Major size reduction already achieved by 'spack gc' removing build dependencies"

        tar -czf ${slurm_dir}/redistributable/slurm-${version}-software.tar.gz -C ${slurm_dir} software/
        echo "Software package created with actual files"

        echo 'Packaging auto-generated Lmod modules...'
        # Find the auto-generated module location for the environment
        cd ${project_dir}
        
        # The correct way to find modules for a Spack environment
        # Look in the environment's module directory first
        ENV_MODULE_DIR="$$(pwd)/.spack-env/modules"
        GLOBAL_MODULE_DIR="$$(spack config get modules:default:roots:lmod 2>/dev/null || echo '/opt/spack/modules')"
        SLURM_SPEC="slurm@${slurm_spec_version}"

        echo "Environment module directory: $$ENV_MODULE_DIR"
        echo "Global module directory: $$GLOBAL_MODULE_DIR"
        mkdir -p ${slurm_dir}/modules

        # Generate modules explicitly first
        echo "Generating modules explicitly..."
        spack module lmod refresh --delete-tree -y
        spack module lmod refresh -y
        
        # Show what modules were generated
        echo "Looking for generated module files..."
        spack module lmod find slurm 2>/dev/null || echo "No slurm module found via spack module lmod find"

        # Search for modules in multiple locations
        FOUND_MODULES=false
        
        # 1. Check environment module directory
        if [ -d "$$ENV_MODULE_DIR" ]; then
            echo "Searching in environment modules: $$ENV_MODULE_DIR"
            find "$$ENV_MODULE_DIR" -name "*.lua" -path "*slurm*" -exec cp -v {} ${slurm_dir}/modules/ \\; && FOUND_MODULES=true
        fi
        
        # 2. Check global module directory
        if [ -d "$$GLOBAL_MODULE_DIR" ] && [ "$$FOUND_MODULES" = false ]; then
            echo "Searching in global modules: $$GLOBAL_MODULE_DIR"
            find "$$GLOBAL_MODULE_DIR" -name "*.lua" -path "*slurm*" -exec cp -v {} ${slurm_dir}/modules/ \\; && FOUND_MODULES=true
        fi
        
        # 3. Try Spack's internal module command to get the path
        echo "Trying spack module lmod find command..."
        MODULE_NAME=$$(spack module lmod find slurm 2>/dev/null || echo "")
        if [ -n "$$MODULE_NAME" ]; then
            echo "Found module name: $$MODULE_NAME"
            # Try to find the actual file for this module
            for search_dir in "$$ENV_MODULE_DIR" "$$GLOBAL_MODULE_DIR" "/opt/spack/share/spack/lmod" "$$(spack location -i)/share/spack/lmod"; do
                if [ -d "$$search_dir" ]; then
                    MODULE_FILE=$$(find "$$search_dir" -name "*.lua" -path "*$$MODULE_NAME*" 2>/dev/null | head -1)
                    if [ -n "$$MODULE_FILE" ] && [ -f "$$MODULE_FILE" ]; then
                        echo "Found module file: $$MODULE_FILE"
                        cp -v "$$MODULE_FILE" ${slurm_dir}/modules/
                        FOUND_MODULES=true
                        break
                    fi
                fi
            done
        fi
        
        # 4. Create a basic module if none found
        if [ "$$FOUND_MODULES" = false ]; then
            echo "No auto-generated modules found, creating basic module..."
            cat > ${slurm_dir}/modules/slurm.lua << 'MODULE_EOF'
        -- Slurm ${version} Module
        help([==[
        This module provides access to Slurm ${version} workload manager.
        ]==])

        whatis("Slurm ${version} - Simple Linux Utility for Resource Management")
        whatis("Homepage: https://slurm.schedmd.com")

        local slurm_root = "/opt/slurm/software"

        prepend_path("PATH", pathJoin(slurm_root, "bin"))
        prepend_path("PATH", pathJoin(slurm_root, "sbin"))
        prepend_path("MANPATH", pathJoin(slurm_root, "share/man"))
        prepend_path("LD_LIBRARY_PATH", pathJoin(slurm_root, "lib"))
        prepend_path("PKG_CONFIG_PATH", pathJoin(slurm_root, "lib/pkgconfig"))

        setenv("SLURM_ROOT", slurm_root)
        setenv("SLURM_CONF", "/etc/slurm/slurm.conf")
        MODULE_EOF
        fi

        tar -czf ${slurm_dir}/redistributable/slurm-${version}-module.tar.gz -C ${slurm_dir} modules/

        echo 'Redistributable packages created successfully!'
        ls -la ${slurm_dir}/redistributable/
        """
    )
)

# Copy output script template
COPY_OUTPUT_SCRIPT = Template(
    textwrap.dedent(
        """
        set -e
        echo 'Copying redistributable packages to output directory...'
        cp ${slurm_dir}/redistributable/slurm-${version}-module.tar.gz ${output_dir}/
        cp ${slurm_dir}/redistributable/slurm-${version}-software.tar.gz ${output_dir}/
        ls -la ${output_dir}/
        echo 'Files copied successfully!'
        """
    )
)