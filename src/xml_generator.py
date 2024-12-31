import logging
from pathlib import Path
from config_manager import ConfigManager
from datetime import datetime

class XMLGenerator:
    STRUCTURE_EXPLANATION = """
    This section represents the directory structure of the project.
    It includes all UTF-8 encoded files that were not excluded based on the
    configuration file, which allows excluding files by name, extension,
    or size, and directories by name.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = ConfigManager().get_config()

    def _sanitize_tag_name(self, path: str) -> str:
        # Replace directory separators and spaces with underscore
        sanitized = path.replace('/', '_').replace('\\', '_').replace(' ', '_')
        # Remove file extension
        sanitized = Path(sanitized).stem
        # Ensure valid XML tag name
        if not sanitized or not sanitized[0].isalpha():
            sanitized = 'file_' + sanitized
        return sanitized

    def _generate_structure(self, root_path: str) -> list:
        root_path = Path(root_path)
        structure_lines = []

        def should_include(item: Path) -> bool:
            if item.is_dir():
                return item.name not in self.config['exclude_structure']['directories']
            return (item.name not in self.config['exclude_structure']['files'] and
                    item.suffix not in self.config['exclude_structure']['extensions'])

        def add_to_structure(path: Path, level: int = 0):
            try:
                items = sorted(
                    [item for item in path.iterdir() if should_include(item)],
                    key=lambda x: (x.is_file(), x.name.lower())
                )

                if level == 0:
                    structure_lines.append(f"{path.name}/")

                for i, item in enumerate(items):
                    is_last = (i == len(items) - 1)
                    prefix = "│   " * level + ("└── " if is_last else "├── ")
                    structure_lines.append(f"{prefix}{item.name}{'/' if item.is_dir() else ''}")

                    if item.is_dir():
                        add_to_structure(item, level + 1)

            except Exception as e:
                self.logger.error(f"Error processing directory {path}: {str(e)}")

        add_to_structure(root_path)
        return structure_lines

    def generate_xml(self, root_path: str, files: list) -> str:
        self.logger.info("Starting XML generation")
        try:
            lines = ['<?xml version="1.0" encoding="UTF-8"?>']
            lines.append("<code>")

            # Project context
            project_name = Path(root_path).name
            lines.extend([
                "<project_context>",
                f"    <project_name>{project_name}</project_name>",
                f"    <generation_timestamp>{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</generation_timestamp>",
                "</project_context>"
            ])

            # Structure
            lines.extend([
                "<structure_explanation>",
                f"    {self.STRUCTURE_EXPLANATION.strip()}",
                "</structure_explanation>",
                "<structure>"
            ])
            lines.extend(self._generate_structure(root_path))
            lines.append("</structure>")

            # File contents
            for file_info in files:
                try:
                    tag_name = self._sanitize_tag_name(file_info['path'])
                    lines.append(f"<{tag_name}>")
                    lines.append(file_info['content'])
                    lines.append(f"</{tag_name}>")
                except Exception as e:
                    self.logger.error(f"Error processing file {file_info.get('path', 'unknown')}: {str(e)}")

            lines.append("</code>")
            return "\n".join(lines)

        except Exception as e:
            self.logger.error(f"Error during XML generation: {str(e)}")
            raise