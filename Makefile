.PHONY: help install test lint format type-check clean build publish docs

help:
	@echo "Available commands:"
	@echo "  make install      - Install package and dev dependencies"
	@echo "  make test         - Run tests with coverage"
	@echo "  make lint         - Run ruff linter"
	@echo "  make format       - Format code with ruff"
	@echo "  make type-check   - Run pyright type checker"
	@echo "  make clean        - Clean build artifacts"
	@echo "  make build        - Build package"
	@echo "  make publish      - Publish to PyPI"
	@echo "  make docs         - Build mkdocs site"
	@echo "  make unasync      - Regenerate _sync/ from _async/"

install:
	uv sync --group dev

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .
	uv run ruff check --fix .

type-check:
	uv run pyright src/harvest_forecast

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .ruff_cache htmlcov site
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	uv build

publish: build
	uv publish

docs:
	uv run mkdocs build --strict

unasync:
	python scripts/unasync.py
