# GO-FastAPI Project Guidelines

## Commands
- **Install**: `poetry install`
- **Run API locally**: `make start` (runs on localhost:8080/docs)
- **Run API dev**: `make start-dev` (runs on localhost:8081/docs)
- **Run all tests**: `make test`
- **Run unit tests**: `make unit-tests` or `poetry run pytest -v tests/unit/*.py`
- **Run integration tests**: `make integration-tests` or `poetry run pytest tests/integration/step_defs/*.py`
- **Run specific test**: `poetry run pytest tests/unit/test_file.py::TestClass::test_method -v`
- **Lint code**: `make lint` or `poetry run tox -e lint-fix`

## Code Style
- **Formatting**: Black with 120 character line length
- **Linting**: Ruff for code quality (PEP 8 and beyond)
- **Python versions**: Target 3.9, 3.10+
- **Naming**: snake_case for variables/functions, PascalCase for classes
- **Imports**: Sorted with isort (enforced by Ruff)
- **Docstrings**: Required with concise descriptions
- **Error handling**: Prefer FastAPI's exception system for API errors
- **Maximum complexity**: Function complexity kept below 10 (McCabe)
- **FastAPI parameters**: Use `examples` instead of `example` in FastAPI params (currently has deprecation warnings)