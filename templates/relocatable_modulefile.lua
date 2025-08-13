-- -*- lua -*-
-- Relocatable Module file created by slurm-factory using Spack template
-- Based on module file created by spack (https://github.com/spack/spack) on {{ timestamp }}
--
-- {{ spec.short_spec }}
--

whatis([[Name : {{ spec.name }}]])
whatis([[Version : {{ spec.version }}]])
whatis([[Target : {{ spec.target.family }}]])
{% if short_description %}
whatis([[Short description : {{ short_description }}]])
{% endif %}
{% if configure_options %}
whatis([[Configure options : {{ configure_options }}]])
{% endif %}

help([[Name   : {{ spec.name }}]])
help([[Version: {{ spec.version }}]])
help([[Target : {{ spec.target.family }}]])
help()
{% if long_description %}
help([[{{ long_description| textwrap(72)| join() }}]])
{% else %}
help([[{{ spec.name }} package]])
{% endif %}

-- Dynamic relocation support for slurm-factory redistributable packages
-- Check for SLURM_INSTALL_PREFIX environment variable for custom installation path
local slurm_install_prefix = os.getenv("SLURM_INSTALL_PREFIX")
local base_prefix = slurm_install_prefix or "{{ prefix }}"

-- The actual package prefix (either relocated or original)
local pkg_prefix = base_prefix

-- If we're using a custom install prefix, we need to construct the full path
-- Spack installs packages with structure: {base}/{arch}/{name-version-hash}
-- For relocatable packages, we assume the same structure under the custom base
if slurm_install_prefix then
    -- Extract the relative path from the original prefix to preserve directory structure
    local spack_prefix = "{{ prefix }}"
    -- Find the part after the install tree root to preserve architecture and package structure
    local rel_path = string.match(spack_prefix, "/([^/]+/[^/]+)$")
    if rel_path then
        pkg_prefix = pathJoin(slurm_install_prefix, rel_path)
    else
        -- Fallback: just use the custom prefix directly
        pkg_prefix = slurm_install_prefix
    end
end

{% block autoloads %}
{% for module in autoload %}
depends_on("{{ module }}")
{% endfor %}
{% endblock %}

{% block conflict %}
{% for name in conflicts %}
conflict("{{ name }}")
{% endfor %}
{% endblock %}

{% block environment %}
{% for command_name, cmd in environment_modifications %}
{% if command_name == 'PrependPath' %}
-- Check if path starts with original prefix and make it relocatable
{% if cmd.value.startswith(prefix) %}
local rel_path = "{{ cmd.value[prefix|length + 1:] }}"
prepend_path("{{ cmd.name }}", pathJoin(pkg_prefix, rel_path), "{{ cmd.separator }}")
{% else %}
prepend_path("{{ cmd.name }}", "{{ cmd.value }}", "{{ cmd.separator }}")
{% endif %}
{% elif command_name in ('AppendPath', 'AppendFlagsEnv') %}
-- Check if path starts with original prefix and make it relocatable
{% if cmd.value.startswith(prefix) %}
local rel_path = "{{ cmd.value[prefix|length + 1:] }}"
append_path("{{ cmd.name }}", pathJoin(pkg_prefix, rel_path), "{{ cmd.separator }}")
{% else %}
append_path("{{ cmd.name }}", "{{ cmd.value }}", "{{ cmd.separator }}")
{% endif %}
{% elif command_name in ('RemovePath', 'RemoveFlagsEnv') %}
-- Check if path starts with original prefix and make it relocatable
{% if cmd.value.startswith(prefix) %}
local rel_path = "{{ cmd.value[prefix|length + 1:] }}"
remove_path("{{ cmd.name }}", pathJoin(pkg_prefix, rel_path), "{{ cmd.separator }}")
{% else %}
remove_path("{{ cmd.name }}", "{{ cmd.value }}", "{{ cmd.separator }}")
{% endif %}
{% elif command_name == 'SetEnv' %}
-- Special handling for SLURM_ROOT and SLURM_PREFIX to use relocated prefix
{% if cmd.name in ('SLURM_ROOT', 'SLURM_PREFIX') %}
setenv("{{ cmd.name }}", pkg_prefix)
{% elif cmd.value.startswith(prefix) %}
local rel_path = "{{ cmd.value[prefix|length + 1:] }}"
setenv("{{ cmd.name }}", pathJoin(pkg_prefix, rel_path))
{% else %}
setenv("{{ cmd.name }}", "{{ cmd.value }}")
{% endif %}
{% elif command_name == 'UnsetEnv' %}
unsetenv("{{ cmd.name }}")
{% endif %}
{% endfor %}
{# Make sure system man pages are enabled by appending trailing delimiter to MANPATH #}
{% if has_manpath_modifications %}
append_path("MANPATH", "", ":")
{% endif %}
{% endblock %}

-- Provide helpful information about relocation
if slurm_install_prefix then
    -- Only show this message during module load
    if mode() == "load" then
        LmodMessage("slurm-factory: Using relocated installation at " .. pkg_prefix)
    end
end

{% block footer %}
{# In case the module needs to be extended with custom Lua code #}
{% endblock %}
