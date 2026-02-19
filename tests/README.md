# PySetItUp Test Suite

This directory contains the test suite for the PySetItUp Python rewrite.

## Test Structure

```
tests/
├── conftest.py          # Pytest configuration and shared fixtures
├── unit/                # Unit tests (fast, isolated, mocked)
│   ├── test_errors.py
│   ├── test_logging.py
│   ├── test_system_env.py
│   ├── test_state_models.py
│   └── test_state_manager.py
├── integration/         # Integration tests (real subprocess calls)
└── e2e/                # End-to-end tests (full workflows)
```

## Running Tests

### Install Dependencies

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync
```

### Run All Unit Tests

```bash
uv run pytest tests/unit -v
```

### Run Specific Test File

```bash
uv run pytest tests/unit/test_state_manager.py -v
```

### Run Specific Test

```bash
uv run pytest tests/unit/test_state_manager.py::TestStateLoading::test_load_state_from_existing_file -v
```

### Run with Coverage

```bash
uv run pytest tests/unit --cov=pysetitup --cov-report=html
open htmlcov/index.html
```

### Run Integration Tests

```bash
uv run pytest tests/integration -v -m integration
```

### Run E2E Tests (requires macOS)

```bash
uv run pytest tests/e2e -v -m e2e
```

### Run All Tests

```bash
uv run pytest tests/ -v
```

## Test Markers

- `@pytest.mark.asyncio` - Async tests
- `@pytest.mark.integration` - Integration tests (slower, real subprocess)
- `@pytest.mark.e2e` - End-to-end tests (full workflows)

## Writing Tests

### Unit Test Template

```python
"""Unit tests for pysetitup.module.file module."""

import pytest
from pysetitup.module.file import function_to_test


class TestFunctionName:
    """Test the function_to_test function."""

    def test_basic_functionality(self) -> None:
        """Test basic functionality."""
        result = function_to_test()
        assert result == expected_value

    def test_edge_case(self) -> None:
        """Test edge case handling."""
        with pytest.raises(ExpectedException):
            function_to_test(invalid_input)
```

### Using Fixtures

```python
def test_with_temp_directory(temp_dir: Path) -> None:
    """Test using temporary directory fixture."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("content")
    assert test_file.exists()
```

## Coverage Goals

- **Unit Tests**: >80% coverage
- **Critical Paths**: 100% coverage for state management, error handling
- **Integration Tests**: Real subprocess parsing, API interactions
- **E2E Tests**: Full installation workflows (dry-run mode)
