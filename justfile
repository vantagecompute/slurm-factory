uv := require("uv")

export PY_COLORS := "1"
export PYTHONBREAKPOINT := "pdb.set_trace"

uv_run := "uv run --frozen --extra dev"

src_dir := "slurm_factory"
tests_dir := "tests"

[private]
default:
    @just help

# Regenerate uv.lock
[group("dev")]
lock:
    uv lock --no-cache

# Create a development environment
[group("dev")]
env: lock
    uv sync --extra dev

# Upgrade uv.lock with the latest dependencies
[group("dev")]
upgrade:
    uv lock --upgrade

[group("dev")]
build: lock
    uv build --no-cache


# Apply coding style standards to code
[group("lint")]
fmt: lock
    {{uv_run}} ruff format {{src_dir}} --exclude=data
    {{uv_run}} ruff check --fix {{src_dir}} --exclude=data

# Check code against coding style standards
[group("lint")]
lint: lock
    {{uv_run}} codespell {{src_dir}} --skip=data
    {{uv_run}} ruff check {{src_dir}} --exclude=data

# Run static type checker on code
[group("lint")]
typecheck: lock
    {{uv_run}} pyright {{src_dir}} --exclude=data

# Run unit tests only
[group("test")]
unit: lock
    {{uv_run}} pytest {{tests_dir}} -v --tb=short --ignore=data --cov={{src_dir}} --cov-report=term-missing


# Print spack.yaml configuration for CPU-only build (standard)
[group("config")]
show-config-cpu:
    {{uv_run}} python -c "from slurm_factory.spack_yaml import generate_yaml_string; print(generate_yaml_string('25.05', False, False))"

# Print spack.yaml configuration for GPU-enabled build
[group("config")]
show-config-gpu:
    {{uv_run}} python -c "from slurm_factory.spack_yaml import generate_yaml_string; print(generate_yaml_string('25.05', True, False))"

# Print spack.yaml configuration for minimal build (CPU-only, no OpenMPI)
[group("config")]
show-config-minimal:
    {{uv_run}} python -c "from slurm_factory.spack_yaml import generate_yaml_string; print(generate_yaml_string('25.05', False, True))"

# Print spack.yaml configuration for minimal GPU build (with GPU support, no OpenMPI)
[group("config")]
show-config-minimal-gpu:
    {{uv_run}} python -c "from slurm_factory.spack_yaml import generate_yaml_string; print(generate_yaml_string('25.05', True, True))"

# Print spack.yaml configuration with verification enabled (for CI/debugging)
[group("config")]
show-config-verify:
    {{uv_run}} python -c "from slurm_factory.spack_yaml import generate_yaml_string; print(generate_yaml_string('25.05', False, False, True))"

# List all available Slurm versions
[group("config")]
show-versions:
    {{uv_run}} python -c "from slurm_factory.constants import SLURM_VERSIONS; print('Available Slurm versions:'); [print(f'  {k}: {v}') for k, v in SLURM_VERSIONS.items()]"