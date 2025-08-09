-- -*- lua -*-
-- Module file created by spack (https://github.com/spack/spack)
{% if spec -%}
-- {{ spec.short_spec }}
{% else -%}
-- Package information not available
{% endif -%}
--

{% if spec and spec.name -%}
whatis([[Name : {{ spec.name }}]])
{% else -%}
whatis([[Name : slurm]])
{% endif -%}
{% if spec and spec.version -%}
whatis([[Version : {{ spec.version }}]])
{% else -%}
whatis([[Version : unknown]])
{% endif -%}
whatis([[Short description : Slurm workload manager]])
{% if spec and spec.name -%}
help([[Name   : {{ spec.name }}]])
{% else -%}
help([[Name   : slurm]])
{% endif -%}
{% if spec and spec.version -%}
help([[Version: {{ spec.version }}]])
{% else -%}
help([[Version: unknown]])
{% endif -%}
help([[
Slurm is an open-source workload manager designed for Linux clusters of
all sizes. This is a relocatable module that allows installation at
any prefix by setting SLURM_INSTALL_PREFIX environment variable.

Relocatability Features:
- Binaries use RPATH for library discovery (no LD_LIBRARY_PATH needed)
- Can be relocated by setting SLURM_INSTALL_PREFIX before loading module
- Self-contained installation with all runtime dependencies included
- Compatible with containerized and distributed deployments

Usage:
  module load slurm                    # Use default installation path
  export SLURM_INSTALL_PREFIX=/new/path && module load slurm  # Use custom path
]])

-- Relocatable prefix logic with validation
local slurm_prefix = os.getenv("SLURM_INSTALL_PREFIX")
if not slurm_prefix then
{% if spec and spec.prefix -%}
    slurm_prefix = "{{ spec.prefix }}"
{% else -%}
    slurm_prefix = "/opt/slurm"
{% endif -%}
end

-- Validate that the specified prefix exists and contains Slurm
local slurm_bin = pathJoin(slurm_prefix, "bin", "scontrol")
if not isFile(slurm_bin) then
    LmodError("Slurm installation not found at: " .. slurm_prefix .. 
              "\nExpected to find: " .. slurm_bin ..
              "\nPlease check SLURM_INSTALL_PREFIX or use default installation.")
end

-- Basic environment setup based on standard Slurm installation layout
prepend_path("PATH", pathJoin(slurm_prefix, "bin"))
prepend_path("PATH", pathJoin(slurm_prefix, "sbin"))
prepend_path("MANPATH", pathJoin(slurm_prefix, "share/man"))

-- Development support (if headers are available)
prepend_path("CPATH", pathJoin(slurm_prefix, "include"))
prepend_path("PKG_CONFIG_PATH", pathJoin(slurm_prefix, "lib/pkgconfig"))
prepend_path("CMAKE_PREFIX_PATH", slurm_prefix)

-- NOTE: No LD_LIBRARY_PATH - relocatable binaries use RPATH for library discovery
-- This ensures proper relocatability and avoids library path conflicts

-- Set important Slurm-specific environment variables
setenv("SLURM_INSTALL_PREFIX", slurm_prefix)
setenv("SLURM_ROOT", slurm_prefix)

-- Configuration paths (can be overridden by setting SLURM_CONF)
local slurm_conf = os.getenv("SLURM_CONF")
if not slurm_conf then
    -- Default to sysconfdir if it exists, otherwise use etc/slurm under prefix
    local default_conf = "/etc/slurm/slurm.conf"

    if isFile(default_conf) then
        setenv("SLURM_CONF", default_conf)
    else
        -- Set the variable but warn if config doesn't exist
        setenv("SLURM_CONF", default_conf)
        if mode() == "load" then
            LmodMessage("Warning: Slurm configuration file not found at " .. default_conf)
            LmodMessage("You may need to create slurm.conf or set SLURM_CONF manually")
        end
    end
end

-- Relocatability metadata (for troubleshooting and deployment tools)
{% if spec and spec.compiler -%}
setenv("SLURM_BUILD_COMPILER", "{{ spec.compiler }}")
{% endif -%}
{% if spec and spec.target -%}
setenv("SLURM_BUILD_TARGET", "{{ spec.target }}")
{% endif -%}
setenv("SLURM_BUILD_TYPE", "relocatable")

-- Module identification and conflict resolution
{% if spec and spec.name and spec.version -%}
local version = "{{ spec.version }}"
local name = "{{ spec.name }}"
{% else -%}
local version = "25.05"
local name = "slurm"
{% endif -%}

-- Prevent loading multiple Slurm modules simultaneously
conflict(name)

-- Family support for better module management
family("workloadmanager")

-- Module load/unload messages
if mode() == "load" then
    LmodMessage("Loading Slurm " .. version .. " from: " .. slurm_prefix)
elseif mode() == "unload" then
    LmodMessage("Unloading Slurm " .. version)
end
