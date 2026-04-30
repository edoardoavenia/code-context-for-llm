# XML Project Context Generator

This tool converts a project's files and structure into a standardized XML format, providing complete codebase context for language models. The XML output supports a unified configuration for filtering both the directory structure and file content. It also supports an optional configuration file parameter. Recent improvements include a centralized logging setup, robust configuration validation (ensuring max_depth is never zero), optimized UTF‑8 verification with a single file read, and a per-branch file counter to avoid unnecessary exclusion of valid files.

## Requirements
- Python 3.6+
- UTF-8 encoded source files

## Usage

### Basic Usage (XML Generation)
Run the tool from the command line by specifying the project directory. Optionally, you can provide a custom configuration file using the --config parameter. If no configuration file is provided, the tool uses config.json as default.

```bash
python src/main.py /path/to/your/project --config /path/to/custom_config.json
```

This generates an XML file in the `output/` directory containing the complete project structure and file contents.

### Inspect Mode (Tree View with Character Counts)
The tool provides an **inspect mode** (`-i` or `--inspect`) that displays a colored tree view of the project with character counts, without generating XML output.

#### Show Files and Directories
Display the complete directory tree with character counts for all files and total counts for directories:

```bash
python src/main.py /path/to/your/project -i
```

Example output:
```
tests/ (45.632 chars total)
├── .gitignore (97 chars)
├── conftest.py (3.126 chars)
├── pytest.ini (288 chars)
├── test_file_processor.py (11.564 chars)
└── test_xml_generator.py (8.813 chars)
```

#### Show Only Directories
Display only directories with their total character counts (useful for quick project overview):

```bash
python src/main.py /path/to/your/project -i -d
```

Example output:
```
code-context-for-llm/ (139.293 chars total)
├── .claude/ (125 chars total)
├── repo.git/ (26.952 chars total)
│   ├── info/ (240 chars total)
│   └── refs/ (0 chars total)
├── src/ (28.639 chars total)
└── tests/ (45.632 chars total)
```

### Color Output
Character counts are **automatically colored** based on relative size within the project:
- 🟢 **Green**: smallest files/directories (0-25%)
- 🟡 **Yellow**: small-medium (25-50%)
- 🟠 **Orange**: medium-large (50-75%)
- 🔴 **Red**: largest files/directories (75-100%)

Colors are **automatically detected**:
- ✅ Enabled when output goes to an interactive terminal
- ❌ Disabled when output is piped/redirected

To manually disable colors:
```bash
python src/main.py /path/to/your/project -i --no-color
# or
NO_COLOR=1 python src/main.py /path/to/your/project -i
```

### Command-Line Options
- `path`: Project directory to analyze (required)
- `--config PATH`: Custom configuration file (default: config.json)
- `-i, --inspect`: Inspect mode - show tree with character counts only (no XML output)
- `-d, --directories-only`: Show only directories (use with `-i`)
- `--no-color`: Disable colored output

## Example Output
<?xml version="1.0" encoding="UTF-8"?>
<code>
    <project_context>
        <project_name>sample_project</project_name>
        <generation_timestamp>YYYY-MM-DD HH:MM:SS UTC</generation_timestamp>
    </project_context>
    <structure_explanation>
        This section represents the directory structure of the project.
        It includes all UTF-8 encoded files that were not excluded based on the
        unified configuration, which applies exclusions by name, extension,
        or size, and directories by name.
    </structure_explanation>
    <structure>
        sample_project/
        ├── src/
        │   ├── utils/
        │   │   └── helper.py
        │   └── main.py
        ├── docs/
        │   └── README.md
        └── config.json
    </structure>
    <src>
        <utils>
            <helper_py>
                def helper_function():
                    return "This is a helper function"
            </helper_py>
        </utils>
        <main_py>
            def main():
                print("Main function")
        </main_py>
    </src>
    <docs>
        <README_md>
            # Sample Project

            This is a sample README file.
        </README_md>
    </docs>
    <config_json>
{
    "max_file_size_kb": 10000,
    "exclude": {
        "extensions": [".env", ".pyc", ".log", ".cache", ".tmp", ".pdf"],
        "files": ["LICENSE", ".gitignore", "poetry.lock", "package-lock.json", "requirements.txt"],
        "directories": ["__pycache__", ".git", "venv", ".pytest_cache", "tests", "dist", "node_modules"],
        "max_depth": 20,
        "max_files": 30
    }
}
    </config_json>
    <orphan_files>
        <!-- Files extracted from content processing that did not appear in the structure -->
        <example_file>
            File content goes here...
        </example_file>
    </orphan_files>
</code>

## Configuration
The configuration is unified. All exclusion settings—extensions, file names, directories, maximum depth, and maximum number of files—are contained in a single key named "exclude" within the configuration file. Additionally, the tool now validates the configuration to ensure that max_depth is never zero, and it employs internal optimizations (such as a single-pass file read for UTF‑8 verification and content extraction, and a per-branch file counter) to improve performance.

By default, the tool reads from config.json. You can override this behavior by specifying a custom configuration file with the --config parameter.

Example configuration (config.json):
{
  "max_file_size_kb": 10000,
  "exclude": {
    "extensions": [".env", ".pyc", ".log", ".cache", ".tmp", ".pdf"],
    "files": ["LICENSE", ".gitignore", "poetry.lock", "package-lock.json", "requirements.txt"],
    "directories": ["__pycache__", ".git", "venv", ".pytest_cache", "tests", "dist", "node_modules"],
    "max_depth": 20,
    "max_files": 30
  }
}