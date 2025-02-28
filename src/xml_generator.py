import logging
from pathlib import Path
from config_manager import ConfigManager
from datetime import datetime

class XMLGenerator:
    """
    Generates an XML representation of the project.
    This implementation decouples file content inclusion from the directory structure,
    allowing independent control over structure and content exclusions.
    """
    STRUCTURE_EXPLANATION = """
    This section represents the directory structure of the project.
    It includes all UTF-8 encoded files that were not excluded based on the
    configuration file, which allows excluding files by name, extension,
    or size, and directories by name.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = ConfigManager().get_config()

    def _sanitize_tag_name(self, name: str) -> str:
        """
        Sanitizes the tag name by replacing invalid characters with underscores
        and ensuring the tag starts with an alphabetic character.
        """
        sanitized = name.replace('/', '_').replace('\\', '_').replace(' ', '_').replace('.', '_')
        if not sanitized or not sanitized[0].isalpha():
            sanitized = 'file_' + sanitized
        return sanitized

    def _generate_structure_lines(self, structure, level=0) -> list:
        """
        Generates textual lines representing the directory structure in a tree-like format.
        """
        lines = []
        if level == 0:
            lines.append(f"{structure.name}/")
        if not structure.children:
            return lines
        for i, child in enumerate(structure.children):
            is_last = (i == len(structure.children) - 1)
            prefix = "│   " * level + ("└── " if is_last else "├── ")
            suffix = '/' if child.is_dir else ''
            lines.append(f"{prefix}{child.name}{suffix}")
            if child.is_dir:
                child_lines = self._generate_structure_lines(child, level + 1)
                lines.extend(child_lines)
        return lines

    def _append_xml_tags(self, structure, lines, file_contents, current_path='', indent_level=1):
        """
        Recursively appends XML tags for directories and files.
        Files are populated with their content if available.
        """
        indent = "    " * indent_level
        tag_name = self._sanitize_tag_name(structure.name)
        lines.append(f"{indent}<{tag_name}>")
        for child in structure.children:
            if child.is_dir:
                child_path = f"{current_path}/{child.name}" if current_path else child.name
                self._append_xml_tags(child, lines, file_contents, current_path=child_path, indent_level=indent_level + 1)
            else:
                file_path = child.path  # Use the stored relative path
                file_tag = self._sanitize_tag_name(child.name)
                lines.append(f"{indent}    <{file_tag}>")
                content = file_contents.get(file_path, '')
                # Indent file content for readability
                content_lines = content.split('\n')
                for line in content_lines:
                    lines.append(f"{indent}        {line}")
                lines.append(f"{indent}    </{file_tag}>")
        lines.append(f"{indent}</{tag_name}>")

    def _collect_structure_file_paths(self, structure) -> set:
        """
        Recursively collects file paths from the structure tree.
        """
        paths = set()
        if not structure.is_dir:
            paths.add(structure.path)
        for child in structure.children:
            paths.update(self._collect_structure_file_paths(child))
        return paths

    def generate_xml(self, root_path: str, scan_result) -> str:
        """
        Generates the XML representation of the project.
        After building the structure from the directory scan, it appends any
        orphan file contents (files that were extracted but not included in the structure)
        in a separate section.
        """
        self.logger.info("Starting XML generation")
        try:
            lines = ['<?xml version="1.0" encoding="UTF-8"?>']
            lines.append("<code>")

            # Project context metadata
            project_name = Path(root_path).name
            lines.extend([
                "    <project_context>",
                f"        <project_name>{project_name}</project_name>",
                f"        <generation_timestamp>{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</generation_timestamp>",
                "    </project_context>"
            ])

            # Structure explanation and textual representation of the directory tree
            lines.extend([
                "    <structure_explanation>",
                f"        {self.STRUCTURE_EXPLANATION.strip()}",
                "    </structure_explanation>",
                "    <structure>"
            ])
            structure_lines = self._generate_structure_lines(scan_result.structure)
            for line in structure_lines:
                lines.append(f"        {line}")
            lines.append("    </structure>")

            # Build a mapping from file paths to their content for quick lookup
            file_contents = {file_info['path']: file_info['content'] for file_info in scan_result.files_content}

            # Append XML tags based on the structure tree
            self.logger.info("Appending directories and files as XML tags")
            self._append_xml_tags(scan_result.structure, lines, file_contents)

            # Identify orphan files: files with content that are not present in the structure tree
            structure_file_paths = self._collect_structure_file_paths(scan_result.structure)
            orphan_files = {path: content for path, content in file_contents.items() if path not in structure_file_paths}

            if orphan_files:
                lines.append("    <orphan_files>")
                for path, content in sorted(orphan_files.items()):
                    file_tag = self._sanitize_tag_name(path.replace('/', '_'))
                    lines.append(f"        <{file_tag}>")
                    content_lines = content.split('\n')
                    for line in content_lines:
                        lines.append(f"            {line}")
                    lines.append(f"        </{file_tag}>")
                lines.append("    </orphan_files>")

            lines.append("</code>")
            return "\n".join(lines)

        except Exception as e:
            self.logger.error(f"Error during XML generation: {str(e)}")
            raise
