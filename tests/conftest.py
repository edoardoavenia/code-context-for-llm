import pytest
import os
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Generator, Tuple


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def project_structure(temp_dir: Path) -> Generator[Path, None, None]:
    """
    Creates a standard test project structure with predictable files and directories.
    
    Structure:
    - project_root/
      - src/
        - main.py
        - utils/
          - helper.py
          - data.bin (binary file)
      - docs/
        - README.md
      - tests/
        - test_main.py
      - .git/
        - HEAD
      - .env
      - config.json
    """
    # Create directories
    project_root = temp_dir / "test_project"
    project_root.mkdir()
    
    src_dir = project_root / "src"
    src_dir.mkdir()
    utils_dir = src_dir / "utils"
    utils_dir.mkdir()
    docs_dir = project_root / "docs"
    docs_dir.mkdir()
    tests_dir = project_root / "tests"
    tests_dir.mkdir()
    git_dir = project_root / ".git"
    git_dir.mkdir()
    
    # Create files with content
    (src_dir / "main.py").write_text("def main():\n    print('Hello, world!')\n\nif __name__ == '__main__':\n    main()")
    (utils_dir / "helper.py").write_text("def helper_function():\n    return 'This is a helper function'")
    
    # Create a binary file
    with open(utils_dir / "data.bin", "wb") as f:
        f.write(os.urandom(100))
    
    (docs_dir / "README.md").write_text("# Test Project\n\nThis is a test project for testing purposes.")
    (tests_dir / "test_main.py").write_text("def test_main():\n    assert True")
    (git_dir / "HEAD").write_text("ref: refs/heads/main")
    (project_root / ".env").write_text("SECRET_KEY=test_secret_key")
    (project_root / "config.json").write_text('{"setting": "value"}')
    
    yield project_root
    
    # Cleanup is handled by tempfile.TemporaryDirectory's context manager


@pytest.fixture
def default_config() -> Dict[str, Any]:
    """Returns a default configuration for testing."""
    return {
        "max_file_size_kb": 1024,
        "exclude": {
            "extensions": [".env", ".bin"],
            "files": ["HEAD"],
            "max_depth": 3,
            "max_files": 5
        },
        "exclude_structure": {
            "extensions": [".bin", ".env"],
            "directories": [".git", "tests"],
            "files": ["HEAD", "config.json"],
            "max_depth": 2,
            "max_files": 3
        }
    }


@pytest.fixture
def config_file(temp_dir: Path, default_config: Dict[str, Any]) -> Path:
    """Creates a temporary config.json file with test configuration."""
    config_path = temp_dir / "config.json"
    with open(config_path, "w") as f:
        json.dump(default_config, f, indent=2)
    return config_path


@pytest.fixture
def original_cwd() -> Generator[str, None, None]:
    """Preserve original working directory."""
    original = os.getcwd()
    yield original
    os.chdir(original)