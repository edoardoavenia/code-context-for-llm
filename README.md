# XML Project Context Generator

This tool converts a project's files and structure into a standardized XML format, providing complete codebase context for language models. The XML output supports a unified configuration for filtering both the directory structure and file content. It also supports an optional configuration file parameter.

## Requirements
- Python 3.6+
- UTF-8 encoded source files

## Usage
Run the tool from the command line by specifying the project directory. Optionally, you can provide a custom configuration file using the --config parameter. If no configuration file is provided, the tool uses config.json as default.

Example:
python src/main.py /path/to/your/project --config /path/to/custom_config.json

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
The configuration is now unified. All exclusion settings (extensions, file names, directories, maximum depth, and maximum number of files) are contained in a single key named "exclude" within the configuration file.

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