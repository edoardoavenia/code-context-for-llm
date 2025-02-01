# XML Project Context Generator

Tool for converting project files and structure into a standardized XML format. This tool is designed to provide complete codebase context for LLMs by automatically scanning directories, extracting file contents, and building a structured XML representation. The XML output now supports independent filtering for directory structure and file content, and includes an additional section for files whose content was extracted but do not appear in the structure tree.

## Requirements
- Python 3.6+
- UTF-8 encoded source files

## Usage

Run the tool from the command line by specifying the project directory:

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
    "content_exclude": {
        "extensions": [".env", ".pyc", ".log"],
        "files": ["LICENSE", "useless_file.txt"],
        "max_depth": 15,
        "max_files": 25
    },
    "structure_exclude": {
        "extensions": [".pyc", ".log", ".pdf"],
        "files": ["LICENSE", "useless_file.txt", ".gitignore"],
        "directories": ["__pycache__", ".git", "venv", ".pytest_cache", "tests", "output"],
        "max_depth": 10,
        "max_files": 50
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
```

## Configuration

The configuration is now split into two separate sections:

- **content_exclude**: Controls which files are processed for content extraction.
  - `extensions`: List of file extensions to exclude when extracting content.
  - `files`: Specific file names to exclude from content extraction.
  - `max_depth`: Maximum directory depth for processing file contents.
  - `max_files`: Maximum number of files per directory level to extract content from.

- **structure_exclude**: Controls which files and directories appear in the directory structure.
  - `extensions`: List of file extensions to exclude from the structure.
  - `files`: Specific file names to exclude from the structure.
  - `directories`: Directory names to exclude from the structure.
  - `max_depth`: Maximum directory depth to display in the structure.
  - `max_files`: Maximum number of items (files/directories) to show per level in the structure.

## Output Location

The output XML file is saved to the `output` directory with a filename pattern of:

```
project_structure_[projectname]_[timestamp].txt
```

This revised README accurately reflects the new, decoupled configuration system and the independent handling of file structure and content in the XML output.