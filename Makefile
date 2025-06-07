# Makefile for LoA Firewall

# Python and Poetry commands
PYTHON := python3
POETRY := poetry
PYTEST := $(POETRY) run pytest

# Source directories
SRC_DIR := src
TEST_DIR := tests
EXAMPLES_DIR := examples

# Default target
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  install        - Install dependencies with Poetry"
	@echo "  test           - Run all unit and integration tests"
	@echo "  test-unit      - Run only unit tests (no server required)"
	@echo "  test-demo      - Run demo.py unit tests only"
	@echo "  test-integration - Run existing integration scripts"
	@echo "  test-coverage  - Run tests with coverage report"
	@echo "  lint           - Run code linting (if available)"
	@echo "  format         - Format code (if available)" 
	@echo "  clean          - Clean up temporary files"
	@echo "  run            - Run the firewall server"
	@echo "  demo           - Run the firewall demo"

# Install dependencies
.PHONY: install
install:
	$(POETRY) install

# Run all tests (unit + integration)
.PHONY: test
test:
	@echo "Running all unit and integration tests..."
	@if $(PYTHON) -c "import pytest" 2>/dev/null; then \
		$(PYTHON) -m pytest $(TEST_DIR) -v; \
	else \
		echo "pytest not found, using unittest..."; \
		$(PYTHON) -m unittest discover $(TEST_DIR) -v; \
	fi

# Run only unit tests (no server required)
.PHONY: test-unit
test-unit:
	@echo "Running unit tests only..."
	@if $(PYTHON) -c "import pytest" 2>/dev/null; then \
		$(PYTHON) -m pytest $(TEST_DIR)/test_demo.py -v; \
	else \
		echo "pytest not found, using unittest..."; \
		$(PYTHON) -m unittest tests.test_demo -v; \
	fi

# Run demo tests only
.PHONY: test-demo
test-demo:
	@echo "Running demo unit tests..."
	@if $(PYTHON) -c "import pytest" 2>/dev/null; then \
		$(PYTHON) -m pytest $(TEST_DIR)/test_demo.py -v; \
	else \
		echo "pytest not found, using unittest..."; \
		$(PYTHON) -m unittest tests.test_demo -v; \
	fi

# Run tests with coverage (if pytest-cov is available)
.PHONY: test-coverage
test-coverage:
	@echo "Running tests with coverage..."
	$(PYTHON) -m pytest $(TEST_DIR) --cov=$(SRC_DIR) --cov-report=html --cov-report=term-missing -v

# Run existing integration-style tests
.PHONY: test-integration
test-integration:
	@echo "Running standalone integration tests (requires server running)..."
	@echo "Note: These tests are in the integration_tests/ directory"
	@for script in integration_tests/test_*.py; do \
		if [ -f "$$script" ]; then \
			echo "Running $$script..."; \
			$(PYTHON) "$$script" || echo "Warning: $$script failed"; \
		fi; \
	done

# Clean up temporary files
.PHONY: clean
clean:
	@echo "Cleaning up temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/

# Run the firewall server
.PHONY: run
run:
	@echo "Starting LoA Firewall server..."
	$(PYTHON) run.py

# Run the demo (requires server to be running)
.PHONY: demo
demo:
	@echo "Running firewall demo..."
	$(PYTHON) $(EXAMPLES_DIR)/demos/demo.py

# Run demo with custom URL
.PHONY: demo-custom
demo-custom:
	@if [ -z "$(URL)" ]; then \
		echo "Usage: make demo-custom URL=http://your-server:port"; \
		exit 1; \
	fi
	@echo "Running firewall demo against $(URL)..."
	$(PYTHON) $(EXAMPLES_DIR)/demos/demo.py $(URL)

# Linting (if tools are available)
.PHONY: lint
lint:
	@echo "Running code linting..."
	@if command -v flake8 >/dev/null 2>&1; then \
		flake8 $(SRC_DIR) $(TEST_DIR) $(EXAMPLES_DIR) --max-line-length=100; \
	else \
		echo "flake8 not found, skipping lint check"; \
	fi

# Code formatting (if tools are available)
.PHONY: format
format:
	@echo "Formatting code..."
	@if command -v black >/dev/null 2>&1; then \
		black $(SRC_DIR) $(TEST_DIR) $(EXAMPLES_DIR) --line-length=100; \
	else \
		echo "black not found, skipping code formatting"; \
	fi

# Type checking (if mypy is available)
.PHONY: typecheck
typecheck:
	@echo "Running type checking..."
	@if command -v mypy >/dev/null 2>&1; then \
		mypy $(SRC_DIR) --ignore-missing-imports; \
	else \
		echo "mypy not found, skipping type check"; \
	fi

# Development setup - install and run basic checks
.PHONY: setup
setup: install
	@echo "Development environment setup complete!"
	@echo "Run 'make test' to run unit tests"
	@echo "Run 'make run' to start the firewall server"
	@echo "Run 'make demo' to run the demo (after starting server)"

# All checks - useful for CI/CD
.PHONY: check
check: test lint typecheck
	@echo "All checks completed!"

# Quick test run (just the new demo tests)
.PHONY: quick-test
quick-test: test-demo
	@echo "Quick test completed!"