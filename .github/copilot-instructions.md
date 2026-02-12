# GitHub Copilot Instructions for slurm-factory

## Python Command Execution

** DO NOT EVER INTERRUPT A TERMINAL BY TRYING TO EXECUTE A COMMAND WHEN THERE IS A RUNNING PROCESS **
** DO NOT EVER INTERRUPT A TERMINAL BY TRYING TO EXECUTE A COMMAND WHEN THERE IS A RUNNING PROCESS **
** DO NOT EVER INTERRUPT A TERMINAL BY TRYING TO EXECUTE A COMMAND WHEN THERE IS A RUNNING PROCESS **
** DO NOT EVER INTERRUPT A TERMINAL BY TRYING TO EXECUTE A COMMAND WHEN THERE IS A RUNNING PROCESS **
** DO NOT EVER INTERRUPT A TERMINAL BY TRYING TO EXECUTE A COMMAND WHEN THERE IS A RUNNING PROCESS **
** DO NOT EVER INTERRUPT A TERMINAL BY TRYING TO EXECUTE A COMMAND WHEN THERE IS A RUNNING PROCESS **
** DO NOT EVER INTERRUPT A TERMINAL BY TRYING TO EXECUTE A COMMAND WHEN THERE IS A RUNNING PROCESS **

**ALWAYS use `uv run` for Python commands in this project.**

This project uses `uv` for dependency management and virtual environment handling. All Python commands must be prefixed with `uv run`.

### Examples:

✅ **CORRECT:**
- `uv run vdeployer deploy --kubeflow --metallb --jupyterhub --chart-values=./tests/examples/test-values.yaml`
- `uv pip install .`
- `just unit`
- `just fmt`
- `just lint`


❌ **INCORRECT:**
- `python script.py`
- `pytest tests/`
- `pyright`
- `ruff check`

### Just Commands (Primary Development Workflow):

**Testing:**
- `just test` - Run tests with coverage (builds library first)
- `just unit` - Run unit tests without building library

**Code Quality:**
- `just typecheck` - Run static type checker (pyright)
- `just lint` - Check code against style standards (ruff)
- `just fmt` - Apply coding style standards (ruff format + fix)

**Building:**
- `just build-lib` - Build native Go library using Docker
- `just build-lib-local` - Build native Go library locally (requires Go)
- `just build-wheel` - Build Python wheel with bundled library

**Development:**
- `just lock` - Regenerate uv.lock file
- `just clean` - Clean build artifacts
- `just install` - Install package in development mode

### Installation Commands:
- Install dependencies: `uv sync`
- Add new dependency: `uv add package-name`
- Add dev dependency: `uv add --dev package-name`
- Regenerate lock: `just lock`

## Project Structure

This is a Python library that wraps the Go kustomize API using:
- `uv` for dependency management
- `pytest` for testing
- `just` for task automation
- `cffi` for FFI bindings
- Docker for building the Go shared library

## Testing Patterns

When writing tests, ensure:
1. Use `uv run pytest` to execute tests
2. Place tests in the `tests/` directory
3. Use `pytest.mark.asyncio` for async tests
4. Skip tests gracefully if library not built: `pytest.skip("Library not built yet")`

## Never Forget

**EVERY Python command MUST start with `uv run`** - this is critical for proper dependency resolution and virtual environment isolation in this project.