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
]])

-- Relocatable prefix logic
local slurm_prefix = os.getenv("SLURM_INSTALL_PREFIX")
if not slurm_prefix then
{% if spec and spec.prefix -%}
    slurm_prefix = "{{ spec.prefix }}"
{% else -%}
    slurm_prefix = "/opt/slurm"
{% endif -%}
end

-- Basic environment setup based on standard Slurm installation layout
prepend_path("PATH", pathJoin(slurm_prefix, "bin"))
prepend_path("PATH", pathJoin(slurm_prefix, "sbin"))
prepend_path("MANPATH", pathJoin(slurm_prefix, "share/man"))

-- Library paths
prepend_path("LD_LIBRARY_PATH", pathJoin(slurm_prefix, "lib"))
prepend_path("PKG_CONFIG_PATH", pathJoin(slurm_prefix, "lib/pkgconfig"))

-- Include paths for development (if headers are available)
prepend_path("CPATH", pathJoin(slurm_prefix, "include"))

-- Set important Slurm-specific environment variables
setenv("SLURM_INSTALL_PREFIX", slurm_prefix)

-- Configuration paths (can be overridden by setting SLURM_CONF)
if not os.getenv("SLURM_CONF") then
    setenv("SLURM_CONF", pathJoin(slurm_prefix, "etc/slurm/slurm.conf"))
end

-- Module identification
{% if spec and spec.name and spec.version -%}
local version = "{{ spec.version }}"
local name = "{{ spec.name }}"
{% else -%}
local version = "25.05"
local name = "slurm"
{% endif -%}

conflict(name)
