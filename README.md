# XML Project Context Generator

Tool for converting project files and structure into a standardized XML format, designed to provide complete codebase context when working with LLMs. Automatically handles file scanning, content extraction, and structuring into a consistent XML format that LLMs can easily process.

## Requirements
- Python 3.6+
- UTF-8 encoded source files

## Usage
```bash
python src/main.py /path/to/your/project
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
│   │   └── helper.py
│   └── main.py
├── docs/
│   └── README.md
└── config.json
</structure>
<src_utils_helper>
def helper_function():
    return "This is a helper function"
</src_utils_helper>
<src_main>
def main():
    print("Main function")
</src_main>
</code>
```

## Configuration
Configure via `config.json`:
```json
{
    "max_file_size_kb": 1024,
        "exclude": {
        "extensions": [".env", ".pyc", ".log"],
        "files": ["LICENSE", "useless_file.txt"]
    },
    "exclude_structure": {
        "extensions": [".env", ".pyc", ".log", ".pdf"],
        "files": ["LICENSE", "useless_file.txt", ".gitignore"],
        "directories": ["__pycache__", ".git", "venv"]
    }
}
```

### Configuration Options
- `max_file_size_kb`: Skip files larger than this size.
- `exclude`: Files to skip when processing content.
- `exclude_structure`: Files and directories to exclude from the structure representation.

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
*   **`<[filepath]>`**: Each file's content is placed within a simplified tag derived from its relative path from the project root. For example, the content of `src/utils/helper.py` will be within the `<src_utils_helper>` tag. The content is included directly without any special wrapping or escaping.

## XML Format and .txt Extension

The generated output is a simplified XML document, optimized for LLM processing while maintaining structural consistency. The output file is saved with a `.txt` extension for ease of handling and viewing. While the output follows basic XML structure rules (proper tag opening/closing), it prioritizes simplicity and readability over strict XML compliance, making it ideal for LLM consumption.

## Error Handling
- Invalid UTF-8 files are skipped, and their content is not included.
- Files exceeding the configured `max_file_size_kb` are skipped.
- Directory traversal attempts and malicious file paths are blocked.
- Errors encountered during file reading or XML generation are logged to the console with timestamps.

## Key Features
- Simplified XML generation optimized for LLM processing
- Clean, readable output without unnecessary XML complexities
- Maintains structural consistency while prioritizing simplicity
- Automatic file type detection and UTF-8 validation
- Configurable file and directory exclusions
- Comprehensive error logging