# code-context-for-llm

Convert a project's structure and source files into a single, well-formed XML
document suitable as context for a large language model.

The tool walks a project directory, applies configurable exclusions, validates
that each file is UTF-8, and emits one XML document with:

- the project name and a UTC generation timestamp,
- a tree drawing of the included structure,
- the content of every included file under a sanitized tag.

It also offers an **inspect** mode that prints the same tree with per-entry
character counts and adaptive colors, useful for quickly seeing what would
end up in the LLM context and how big each part is.

## Requirements

- Python 3.10 or newer
- UTF-8 encoded source files (non-UTF-8 files are skipped)

## Installation

```bash
pip install -e .
```

This installs the `code-context` console script. The package can also be run
without installation:

```bash
PYTHONPATH=src python -m code_context PATH
```

## Usage

### Generate XML output

```bash
code-context /path/to/project
```

The XML is written to `output/project_structure_<name>_<timestamp>.txt` in the
current working directory.

### Inspect mode

Print a colored tree with character counts and exit (no file is written):

```bash
code-context /path/to/project -i
```

```
proj/ (46.212 chars total)
├── src/ (28.639 chars total)
│   ├── main.py (4.821 chars)
│   └── util.py (1.244 chars)
└── README.md (2.062 chars)
```

Show only directories:

```bash
code-context /path/to/project -i -d
```

### Color output

Counts are shaded by relative size, on independent scales for files and
directories: green (smallest 25%), yellow, orange, red (largest 25%).

Colors are auto-detected: enabled on a real terminal, disabled when output is
redirected. Disable manually with `--no-color` or by setting the
[`NO_COLOR`](https://no-color.org) environment variable.

### CLI reference

```
code-context PATH [--config FILE] [-i] [-d] [--no-color]

  PATH                 Project directory to scan.
  --config FILE        Custom configuration file (default: bundled config.json).
  -i, --inspect        Show tree with character counts; do not write XML.
  -d, --directories-only   With --inspect, hide files.
  --no-color           Disable colored output.
```

## Configuration

Configuration lives in `config.json` next to the package, or in any file
passed via `--config`. Format:

```json
{
  "max_file_size_kb": 1024,
  "exclude": {
    "extensions": [".png", ".pyc"],
    "files": [".env", "package-lock.json"],
    "directories": ["node_modules", ".git"],
    "max_depth": 20,
    "max_files": 300
  }
}
```

| Key                         | Meaning                                                |
|-----------------------------|--------------------------------------------------------|
| `max_file_size_kb`          | Files larger than this are skipped.                    |
| `exclude.extensions`        | Suffixes (with leading dot) to skip.                   |
| `exclude.files`             | Exact file names to skip.                              |
| `exclude.directories`       | Directory names to skip entirely (recursive).          |
| `exclude.max_depth`         | Maximum recursion depth.                               |
| `exclude.max_files`         | Maximum entries kept per directory branch.             |

A file is included **iff** it passes every filter (extension, name, size,
UTF-8 readability). Structure and content always agree by construction.

Invalid or missing configuration falls back to safe defaults with a warning
in the log; the tool never crashes on a bad config.

## Library usage

```python
from code_context import Config, ExcludeConfig, scan, generate_xml

config = Config(
    max_file_size_kb=512,
    exclude=ExcludeConfig(
        extensions=(".png", ".pyc"),
        directories=("node_modules", ".git"),
        max_depth=10,
        max_files=200,
    ),
)
root = scan("/path/to/project", config)
xml = generate_xml("project_name", root)
```

The returned `FileNode` is a slot-based dataclass with `name`, `rel_path`,
`is_dir`, `children`, `content`, and a `walk()` iterator.

## Output format

```xml
<?xml version="1.0" encoding="UTF-8"?>
<code>
    <project_context>
        <project_name>sample</project_name>
        <generation_timestamp>2026-04-30 12:00:00 UTC</generation_timestamp>
    </project_context>
    <structure_explanation>...</structure_explanation>
    <structure>
        sample/
        ├── src/
        │   └── main.py
        └── README.md
    </structure>
    <sample>
        <src>
            <main_py>
                def main():
                    print("hi")
            </main_py>
        </src>
        <README_md>
                # sample
        </README_md>
    </sample>
</code>
```

Special characters in source content (`<`, `>`, `&`) are XML-escaped, so the
document is always re-parseable.

## Development

```bash
pip install -e ".[dev]"
pytest                # run the test suite
ruff check src tests  # lint
```

The repository ships with one default `config.json` for general use and a
focused test suite covering configuration loading, scanning, XML generation,
inspect mode, the CLI, and an integration test.

## License

MIT — see [LICENSE](LICENSE).
