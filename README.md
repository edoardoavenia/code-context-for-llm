# XML Project Context Generator

Tool for converting project files and structure into a standardized XML format, designed to provide complete codebase context when working with LLMs. Automatically handles file scanning, content extraction, and structuring into a consistent XML format that LLMs can easily process.

## Requirements
- Python 3.6+
- UTF-8 encoded source files

## Usage
```bash
python src/main_py /path/to/your/project
```

## Example Output
```xml
<?xml version="1.0" encoding="UTF-8"?>
<code>
    <project_context>
        <project_name>sample_project</project_name>
        <generation_timestamp>YYYY-MM-DD HH:MM:SS UTC</generation_timestamp>
    </project_context>
    <structure_explanation>
        This section represents the directory structure of the project.
        It includes all UTF-8 encoded files that were not excluded based on the
        configuration file, which allows excluding files by name, extension,
        or size, and directories by name.
    </structure_explanation>
    <structure>
        sample_project/
        ├── src/
        │   ├── utils/
        │   │   └── helper_py
        │   └── main_py
        ├── docs/
        │   └── README_md
        └── config_json
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
    "max_file_size_kb": 1024,
    "exclude": {
        "extensions": [".env", ".pyc", ".log"],
        "files": ["LICENSE", "useless_file.txt","poetry.lock",".env"],
        "directories": ["__pycache__", ".git", "venv",".pytest_cache","tests","output"],
        "max_depth": 15,
        "max_files": 25
    },
    "exclude_structure": {
        "extensions": [".pyc", ".log", ".pdf"],
        "files": ["LICENSE", "useless_file.txt", ".gitignore"],
        "directories": ["__pycache__", ".git", "venv",".pytest_cache","output"],
        "max_depth": 10,
        "max_files": 50
    }
}
    </config_json>
</code>
```

## Configuration
Configure via `config_json`:
```json
{
    "max_file_size_kb": 1024,
    "exclude": {
        "extensions": [".env", ".pyc", ".log"],
        "files": ["LICENSE", "useless_file.txt"],
        "max_depth": 4,
        "max_files": 10
    },
    "exclude_structure": {
        "extensions": [".env", ".pyc", ".log", ".pdf"],
        "files": ["LICENSE", "useless_file.txt", ".gitignore"],
        "directories": ["__pycache__", ".git", "venv"],
        "max_depth": 4,
        "max_files": 10
    }
}
```

### Configuration Options
- `max_file_size_kb`: Skip files larger than this size
- `exclude.extensions`: File extensions to skip when processing content
- `exclude.files`: Specific files to skip when processing content
- `exclude.max_depth`: Maximum directory depth for file content inclusion
- `exclude.max_files`: Maximum number of files to include per directory level for content
- `exclude_structure.extensions`: File extensions to skip in directory structure
- `exclude_structure.files`: Specific files to skip in directory structure
- `exclude_structure.directories`: Directory names to skip in structure
- `exclude_structure.max_depth`: Maximum depth for directory structure visualization
- `exclude_structure.max_files`: Maximum number of items (files/directories) to show per level in structure

## Output Location
Files are saved to: `output/project_structure_[projectname]_[timestamp].txt`

## Understanding the XML Output

The output is structured as a valid XML file, providing a clear and organized representation of your project for LLMs. Here's a breakdown of the main sections:

*   **`<?xml version="1.0" encoding="UTF-8"?>`**:  The standard XML declaration specifying the version and encoding.
*   **`<code>`**: The root element encapsulating the entire project context.
*   **`<project_context>`**: Contains metadata about the generated output.
    *   **`<project_name>`**: The name of the project directory.
    *   **`<generation_timestamp>`**: The date and time when the XML was generated (in UTC).
*   **`<structure_explanation>`**: Provides a description of the `<structure>` section, indicating that it represents the project's directory structure, taking into account the exclusions defined in the configuration file.
*   **`<structure>`**: Presents the hierarchical directory structure of the project. Directories are indicated with a trailing `/`. The structure reflects the files and directories that were not excluded by the configuration.
*   **`<[folder_name]>`**: Each folder is represented as an XML tag, containing nested folders and files. For example, the `<src>` tag contains `<main_py>` and other nested tags.
    *   **`<[filename.extension]>`**: Each file's content is placed within a tag that includes the file's extension (e.g., `<main_py>`). The content is included directly with proper indentation for readability.

## Key Features
- Simplified XML generation optimized for LLM processing
- **File Extensions:** File tags now include their full name with extensions (e.g., `README_md` instead of `README`)
- **Folders Representation:** Directories are now represented as XML tags, ensuring a structured and hierarchical format.
- **Proper Indentation:** The XML output is now correctly indented to improve readability and maintainability.
- Clean, readable output without unnecessary XML complexities
- Maintains structural consistency while prioritizing simplicity
- Automatic file type detection and UTF-8 validation
- Configurable file and directory exclusions
- Depth and file count limits for both structure and content
- Comprehensive error logging

