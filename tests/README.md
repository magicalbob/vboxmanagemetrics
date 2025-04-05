# VBoxManageMetrics Tests

This directory contains unit tests for the VBoxManageMetrics exporter.

## Dependencies

Ensure you have the following installed:

```bash
pip install pytest pytest-cov
```

## Running Tests

To run all tests:

```bash
cd /path/to/vboxmanagemetrics
python -m pytest tests/
```

To run specific test files:

```bash
python -m pytest tests/test_vboxmanagemetrics.py
python -m pytest tests/test_parsing_functions.py
```

To run tests with coverage:

```bash
python -m pytest tests/ --cov=vboxmanagemetrics --cov-report=term
```

## Test Structure

- `test_vboxmanagemetrics.py`: Main tests for the module
- `test_flask_integration.py`: Tests for Flask application integration
- `test_parsing_functions.py`: Tests for metric name normalization and value parsing
- `test_command_execution.py`: Tests for VBoxManage command execution
- `conftest.py`: Shared fixtures and test configuration
- `pytest.ini`: Configuration for pytest

## Mocking Strategy

The tests use Python's `unittest.mock` to simulate VBoxManage command outputs without requiring actual VirtualBox installations or VMs. This allows the tests to run in any environment.
