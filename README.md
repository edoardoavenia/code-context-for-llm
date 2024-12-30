```markdown
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
├── main.py
└── src/
    └── utils.py
</structure>
<main.py>
<![CDATA[
File content of main.py goes here.
]]>
</main.py>
<src_utils.py>
<![CDATA[
File content of src/utils.py goes here.
]]>
</src_utils.py>
</code >
```

## Configuration
Configure via `config.json`:
```json
{
    "max_file_size_kb": 1024,
    "exclude": {
        "content": {
            "extensions": [".env", ".pyc", ".log"],
            "files": ["LICENSE", "useless_file.txt"],
            "directories": ["__pycache__", ".git", "venv"]
        },
        "structure": {
            "extensions": [".env", ".pyc", ".log", ".pdf"],
            "files": ["LICENSE", "useless_file.txt", ".gitignore"],
            "directories": ["__pycache__", ".git", "venv"]
        }
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
*   **`<[filepath]>`**:  Each file's content is placed within a tag named after its relative path from the project root. For example, the content of `src/utils.py` will be within the `<src_utils.py>` tag.
    *   **`<![CDATA[ ... ]]>`**:  The content of each file is wrapped in a CDATA section. This ensures that special characters within the file content (like `<`, `>`, and `&`) are treated as literal characters and do not interfere with the XML structure.

## XML Format and .txt Extension

The generated output is a valid XML document, ensuring consistency and parsability for LLMs. However, for ease of reading and handling, the output file is saved with a `.txt` extension. This allows you to open and inspect the file content easily with standard text editors without them trying to interpret it strictly as an XML file. It's important that the content within the `.txt` file adheres to XML standards for proper interpretation by LLMs.

## Error Handling
- Invalid UTF-8 files are skipped, and their content is not included.
- Files exceeding the configured `max_file_size_kb` are skipped.
- Errors encountered during file reading or XML generation are logged to the console with timestamps.
```
