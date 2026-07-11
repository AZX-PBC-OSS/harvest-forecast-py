# Installation

harvest-forecast-py is a pure-Python library with three runtime dependencies. It runs on Python 3.12+ and works with any modern project setup.

## Requirements

!!! warning "Python 3.12+ required"
    harvest-forecast-py requires **Python 3.12 or newer**. It uses modern type syntax such as `str | None` and `list[str]` that is only fully supported on 3.12+. It is tested on Python 3.12, 3.13, and 3.14.

The library has three runtime dependencies:

| Dependency | Purpose |
| :-- | :-- |
| [httpx](https://www.python-httpx.org/) `>=0.28` | HTTP client (async and sync) |
| [pydantic](https://docs.pydantic.dev/) `>=2.0` | Response model validation |
| [tenacity](https://github.com/jd/tenacity) `>=9.0` | Retry logic with backoff |

## Installing with pip

Install from [PyPI](https://pypi.org/project/harvest-forecast-py/) using pip:

```bash
pip install harvest-forecast-py
```

## Installing with uv

If you use [uv](https://github.com/astral-sh/uv) for dependency management:

```bash
uv add harvest-forecast-py
```

## Verifying the installation

Confirm the package is installed and check the version:

```bash
python -c "import harvest_forecast; print(harvest_forecast.__version__)"
```

You should see the installed version printed, for example:

```text
0.1.0
```

!!! tip "Troubleshooting"
    If you see `ModuleNotFoundError: No module named 'harvest_forecast'`, make sure the virtual environment where you installed the package is the same one you are running Python from. Activate the environment (or use `uv run`) and try again.

## Next steps

Now that harvest-forecast-py is installed, learn how to authenticate and list resources in minutes:

:material-arrow-right: [Quick Start](quick-start.md)
