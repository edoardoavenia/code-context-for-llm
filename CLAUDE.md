# CLAUDE.md - Project Guide

## Commands
- Run application: `python src/main.py /path/to/project`
- Run tests: `python -m unittest discover -s tests`
- Run specific test: `python -m unittest tests.test_module.TestClass.test_method`
- Format code: `black src/`
- Type check: `mypy src/`

## Code Style Guidelines
- **Imports**: Group standard library, third-party, and local imports with a blank line between groups
- **Type Annotations**: Use type hints for function parameters and return values
- **Error Handling**: Use try/except blocks with specific exceptions and descriptive error messages
- **Naming**:
  - Classes: PascalCase (e.g., `FileProcessor`, `XMLGenerator`)
  - Methods/Functions: snake_case (e.g., `scan_directory`, `generate_xml`)
  - Variables: snake_case (e.g., `file_path`, `content_exclude`)
  - Constants: UPPER_SNAKE_CASE
- **Documentation**: Use docstrings for classes and methods, explaining purpose and parameters
- **Logging**: Use the logging module with appropriate levels (INFO, ERROR, etc.)
- **Dataclasses**: Use dataclasses for data containers
- **Code Organization**: Group related functionality in separate modules