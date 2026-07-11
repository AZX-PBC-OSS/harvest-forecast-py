# Contributing to harvest-forecast-py

Thank you for your interest in contributing to harvest-forecast-py! We appreciate your time and effort in making this library better for everyone.

## Development Setup

### Prerequisites

- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/) - Fast Python package installer and resolver

### Getting Started

1. **Clone the repository:**
   ```bash
   git clone https://github.com/AZX-PBC-OSS/harvest-forecast-py.git
   cd harvest-forecast-py
   ```

2. **Install dependencies:**

   This project uses `uv` for dependency management. Install development dependencies with:
   ```bash
   uv sync --group dev
   ```

   This will create a virtual environment and install all necessary dependencies including pytest, pyright, ruff, and other development tools.

## Running Tests

**IMPORTANT: Always use `uv run` to execute pytest and other development commands.**

Using `uv run` ensures that:
- Commands run in the correct virtual environment
- All dependencies are properly resolved
- You're using the exact versions specified in the project
- No conflicts with globally installed packages

### Test Commands

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/_async/test_client.py

# Run specific test function
uv run pytest tests/_async/test_client.py::test_list_people

# Run with verbose output
uv run pytest -v

# Run with coverage report
uv run pytest --cov=harvest_forecast --cov-report=html

# Run tests matching a pattern
uv run pytest -k "test_assignment"

# Run tests with output from print statements
uv run pytest -s
```

### Understanding Test Output

The project is configured with the following pytest settings (in `pyproject.toml`):
- `asyncio_mode = "auto"` — async tests run without explicit markers
- `--strict-markers` and `--strict-config` — fail on unknown markers/config
- `--timeout=5` — individual test timeout of 5 seconds
- Coverage is collected for the `harvest_forecast` package
- HTML coverage reports are generated in `htmlcov/`
- Tests must maintain at least 95% code coverage
- Coverage reports exclude test files and implementation details

### Async and Sync Tests

Tests are written in `tests/_async/` and auto-generated to `tests/_sync/` via the unasync script. Both suites run in CI. If you edit tests in `tests/_async/`, run `python scripts/unasync.py` to regenerate `tests/_sync/`.

## Code Quality

### Type Checking

The project uses `pyright` for type checking:

```bash
# Run type checking
uv run pyright src/harvest_forecast

# Type check specific file
uv run pyright src/harvest_forecast/_async/client.py
```

### Linting and Formatting

The project uses `ruff` for both linting and formatting:

```bash
# Check for linting issues
uv run ruff check src/harvest_forecast

# Auto-fix linting issues
uv run ruff check --fix src/harvest_forecast

# Format code
uv run ruff format src/harvest_forecast

# Check formatting without making changes
uv run ruff format --check src/harvest_forecast
```

### Unasync

The sync client (`src/harvest_forecast/_sync/`) is auto-generated from the async client (`src/harvest_forecast/_async/`). If you edit `_async/` source, regenerate the sync code:

```bash
# Regenerate _sync/ from _async/
python scripts/unasync.py

# Verify generated files are up to date (runs in CI)
python scripts/unasync.py --check
```

### Running All Quality Checks

Before submitting a PR, run all quality checks:

```bash
# Run tests with coverage
uv run pytest

# Run type checking
uv run pyright src/harvest_forecast

# Run linting
uv run ruff check .

# Check formatting
uv run ruff format --check .

# Verify sync code is up to date
python scripts/unasync.py --check
```

Or use the Makefile:

```bash
make test type-check lint format
```

## Making Changes

### Workflow

1. **Create a feature branch:**
   ```bash
   git checkout -b feat/your-feature-name
   ```

   Or for bug fixes:
   ```bash
   git checkout -b fix/bug-description
   ```

2. **Make your changes:**
   - Write clear, readable code
   - Follow existing code patterns and conventions
   - Add type hints to all functions and methods
   - Keep functions focused and modular
   - If editing async client code, always edit `src/harvest_forecast/_async/` — never edit `_sync/` directly

3. **Write tests:**
   - Add tests in `tests/_async/` for all new functionality
   - Run `python scripts/unasync.py` to generate sync tests
   - Use `respx` for HTTP mocking — no real network calls in tests
   - Use `RetryPolicy.no_wait()` or `RetryPolicy.fast_test()` for sub-second runs
   - Test edge cases and error conditions
   - Run tests with `uv run pytest`

4. **Update documentation:**
   - Update README.md if adding new features
   - Add docstrings to new functions and classes
   - Update type hints and examples

5. **Verify your changes:**
   ```bash
   # Run all tests
   uv run pytest

   # Check types
   uv run pyright src/harvest_forecast

   # Check linting
   uv run ruff check .

   # Check formatting
   uv run ruff format --check .

   # Verify unasync is up to date
   python scripts/unasync.py --check
   ```

## Pull Request Process

### Before Submitting

1. **Ensure all tests pass:**
   ```bash
   uv run pytest
   ```

2. **Ensure type checking passes:**
   ```bash
   uv run pyright src/harvest_forecast
   ```

3. **Ensure code is properly formatted:**
   ```bash
   uv run ruff format .
   uv run ruff check --fix .
   ```

4. **Verify sync code is up to date:**
   ```bash
   python scripts/unasync.py --check
   ```

5. **Verify coverage hasn't decreased:**
   ```bash
   uv run pytest --cov=harvest_forecast --cov-report=term-missing
   ```

   Coverage should remain at or above 95%.

### Submitting Your PR

1. **Push your branch:**
   ```bash
   git push origin feat/your-feature-name
   ```

2. **Create a pull request on GitHub**

3. **In your PR description:**
   - Clearly describe what changes you made
   - Explain why the changes are needed
   - Reference any related issues
   - Include examples of new functionality (if applicable)
   - List any breaking changes

## Code Review

### What to Expect

- All changes must pass automated tests and type checking
- Code reviewers will check for:
  - Implementation correctness
  - Code clarity and maintainability
  - Adequate test coverage
  - Documentation completeness
  - Adherence to project conventions

- You may be asked to make revisions
- Reviews are constructive — they help improve code quality

### Addressing Feedback

When reviewers request changes:

1. Make the requested changes in your branch
2. Run tests again: `uv run pytest`
3. Push the updates: `git push origin feat/your-feature-name`
4. Respond to reviewer comments

## Development Tips

### Virtual Environment

The `uv run` command automatically manages the virtual environment. You don't need to manually activate it.

If you prefer to activate the environment manually:
```bash
# uv creates a .venv directory
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows
```

However, we recommend using `uv run` for consistency.

### Interactive Testing

You can use `uv run python` to start a Python interpreter with the correct environment:

```bash
uv run python
```

Then test your changes interactively:
```python
import asyncio
from harvest_forecast import ForecastClient, RetryPolicy

async def main():
    async with ForecastClient(
        access_token="your-token",
        account_id="123456",
        user_agent="my-app (you@example.com)",
        retry=RetryPolicy.no_wait(),
    ) as client:
        people = await client.list_people()
        print(people)

asyncio.run(main())
```

### Debugging Tests

To debug a specific test with pdb:

```bash
# Add breakpoint() in your test or code
# Then run with -s to see output
uv run pytest -s tests/_async/test_client.py::test_specific_function
```

### Coverage Reports

After running tests with coverage, view the HTML report:

```bash
uv run pytest --cov=harvest_forecast --cov-report=html
# Open htmlcov/index.html in your browser
```

## Code Style Guidelines

### General Principles

- Write clear, self-documenting code
- Use meaningful variable and function names
- Keep functions short and focused (ideally under 50 lines)
- Avoid deep nesting (max 3–4 levels)
- Comments should explain "why", not "what"
- Use modern Python conventions (`X | None`, built-in generics, `pathlib`)

### Type Hints

Always use type hints on all public boundaries:

```python
# Good
def list_assignments(self, filter: AssignmentFilter) -> list[Assignment]:
    ...

# Bad
def list_assignments(self, filter):
    ...
```

### Docstrings

Use Google-style docstrings for public APIs:

```python
def list_people(self) -> list[Person]:
    """List all people in the Forecast account.

    Returns:
        A list of all people, fully paginated.

    Raises:
        ForecastAuthError: If the access token is invalid.
        ForecastHTTPError: If the API returns an error.
    """
```

## Getting Help

- **Questions?** Open a [GitHub Discussion](https://github.com/AZX-PBC-OSS/harvest-forecast-py/discussions)
- **Bug Reports?** Open an [Issue](https://github.com/AZX-PBC-OSS/harvest-forecast-py/issues)
- **Feature Requests?** Open an [Issue](https://github.com/AZX-PBC-OSS/harvest-forecast-py/issues) with the `enhancement` label

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Thank You!

Your contributions help make harvest-forecast-py better for everyone. We appreciate your time and effort!
