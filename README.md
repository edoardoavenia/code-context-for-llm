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
<code>
<structure>
project/
├── src/
│   ├── models/
│   │   └── user.py
│   └── utils/
│       └── helpers.py
└── config.json
</structure>

<src/models/user.py>
class User:
    def __init__(self, name):
        self.name = name
        
    def get_info(self):
        return {"name": self.name}
</src/models/user.py>

<src/utils/helpers.py>
def validate_user(user):
    return user.name != ""
</src/utils/helpers.py>

<config.json>
{
    "version": "1.0",
    "environment": "development"
}
</config.json>
</code>
```

## Configuration
Configure via config.json:
```json
{
    "max_file_size_kb": 1024,
    "exclude": {
        "extensions": [".env", ".pyc", ".log", ".git"],
        "files": ["LICENSE"]
    },
    "exclude_structure": {
        "extensions": [".pdf", ".png", ".jpg"],
        "directories": ["__pycache__", ".git", "venv"],
        "files": ["LICENSE"]
    }
}
```

### Configuration Options
- `max_file_size_kb`: Skip files larger than this size
- `exclude`: Files to skip when processing content
- `exclude_structure`: Files/folders to hide from structure view

## Output Location
Files are saved to: `output/project_structure_[projectname]_[timestamp].xml`

## Error Handling
- Invalid UTF-8 files are skipped
- Oversized files are skipped (configurable)
- Errors are logged to console with timestamps