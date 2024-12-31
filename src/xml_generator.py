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
        sanitized = path.replace('/', '_').replace('\\', '_').replace(' ', '_')
        sanitized = Path(sanitized).stem
        if not sanitized or not sanitized[0].isalpha():
            sanitized = 'file_' + sanitized
        return sanitized

    def _generate_structure_lines(self, structure, level=0) -> list:
        lines = []
        if level == 0:
            lines.append(f"{structure.name}/")
            
        if not structure.children:
            return lines

        # Process children
        for i, child in enumerate(structure.children):
            is_last = (i == len(structure.children) - 1)
            prefix = "│   " * level + ("└── " if is_last else "├── ")
            suffix = '/' if child.is_dir else ''
            lines.append(f"{prefix}{child.name}{suffix}")
            
            if child.is_dir:
                child_lines = self._generate_structure_lines(child, level + 1)
                lines.extend(child_lines)

        return lines

    def generate_xml(self, root_path: str, scan_result) -> str:
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
            
            # Generate structure using the processed directory structure
            structure_lines = self._generate_structure_lines(scan_result.structure)
            lines.extend(structure_lines)
            lines.append("</structure>")

            # Process files content
            for file_info in scan_result.files_content:
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