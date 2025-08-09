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
    rm -rf jupyterlab_firefox_launcher/labextension
    rm -rf lib/
    rm -rf dist/
    uv build --no-cache


# Apply coding style standards to code
[group("lint")]
fmt: lock
    {{uv_run}} ruff format {{src_dir}} {{tests_dir}} --exclude=data
    {{uv_run}} ruff check --fix {{src_dir}} {{tests_dir}} --exclude=data

# Check code against coding style standards
[group("lint")]
lint: lock
    {{uv_run}} codespell {{src_dir}} --skip=data
    {{uv_run}} ruff check {{src_dir}} --exclude=data

# Run static type checker on code
[group("lint")]
typecheck: lock
    {{uv_run}} pyright {{src_dir}} --exclude=data

# Run tests
[group("test")]
test: lock
    {{uv_run}} pytest {{tests_dir}} --ignore=data

# Run tests with coverage
[group("test")]
test-cov: lock
    {{uv_run}} pytest {{tests_dir}} --ignore=data --cov={{src_dir}} --cov-report=term-missing

# Run unit tests only
[group("test")]
unit: lock
    {{uv_run}} pytest {{tests_dir}} -v --tb=short

# Run all quality checks (lint, typecheck, test)
[group("test")]
check: lint typecheck test
