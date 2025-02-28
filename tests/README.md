# Test Suite for XML Project Context Generator

This test suite provides comprehensive testing for the XML Project Context Generator, with a focus on validating the decoupled configuration management for structure and content exclusions.

## Test Organization

The test suite is organized into several modules:

- `test_config_manager.py`: Tests for the configuration loading and validation
- `test_file_processor.py`: Tests for file processing and directory structure building
- `test_xml_generator.py`: Tests for XML generation and tag handling
- `test_integration.py`: End-to-end tests of the entire pipeline

## Running Tests

Run the entire test suite:

```bash
python -m pytest
```

Run a specific test module:

```bash
python -m pytest tests/test_config_manager.py
```

Run a specific test:

```bash
python -m pytest tests/test_integration.py::TestIntegration::test_decoupled_exclusions_integration
```

## Test Fixtures

The `conftest.py` file provides shared fixtures used across multiple test modules:

- `temp_dir`: Creates a temporary directory for test files
- `project_structure`: Creates a standardized test project structure
- `default_config`: Provides a default configuration for testing
- `config_file`: Creates a temporary config.json file with test settings

## Test Coverage

The test suite covers:

1. Configuration Management:
   - Loading and validation of configuration
   - Proper handling of defaults and error cases
   - Decoupled structure and content exclusion settings

2. File Processing:
   - UTF-8 file detection
   - File inclusion/exclusion for content and structure based on separate criteria
   - Directory recursion with depth limits
   - File count limits per directory level
   - Proper tree structure building
   
3. XML Generation:
   - XML tag sanitization
   - Structure visualization
   - Content extraction and formatting
   - Orphan file handling (files with content but not in structure)
   
4. Integration:
   - End-to-end pipeline functionality
   - Verification of structure and content exclusion independence