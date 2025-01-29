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

    def _sanitize_tag_name(self, name: str) -> str:
        """
        Sanitizes the tag name by replacing invalid characters with underscores
        and ensuring the tag starts with an alphabetic character.
        Includes the file extension in the tag name.
        """
        sanitized = name.replace('/', '_').replace('\\', '_').replace(' ', '_').replace('.', '_')
        if not sanitized or not sanitized[0].isalpha():
            sanitized = 'file_' + sanitized
        return sanitized

    def _generate_structure_lines(self, structure, level=0) -> list:
        """
        Generates lines representing the directory structure in a tree-like format.
        """
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

    def _append_xml_tags(self, structure, lines, file_contents, current_path='', indent_level=1):
        """
        Recursively appends XML tags for directories and files with proper indentation.
        Files include their content within their respective tags.
        """
        indent = "    " * indent_level
        tag_name = self._sanitize_tag_name(structure.name)
        lines.append(f"{indent}<{tag_name}>")
        
        for child in structure.children:
            if child.is_dir:
                child_path = f"{current_path}/{child.name}" if current_path else child.name
                self._append_xml_tags(child, lines, file_contents, current_path=child_path, indent_level=indent_level + 1)
            else:
                file_path = f"{current_path}/{child.name}" if current_path else child.name
                file_content = file_contents.get(file_path, '')
                file_tag = self._sanitize_tag_name(child.name)
                lines.append(f"{indent}    <{file_tag}>")
                # Indent file content by two additional levels for readability
                content_lines = file_content.split('\n')
                for line in content_lines:
                    lines.append(f"{indent}        {line}")
                lines.append(f"{indent}    </{file_tag}>")
        
        lines.append(f"{indent}</{tag_name}>")

    def generate_xml(self, root_path: str, scan_result) -> str:
        """
        Generates the XML representation of the project, including directory and file tags
        with proper extensions and indentation.
        """
        self.logger.info("Starting XML generation")
        try:
            lines = ['<?xml version="1.0" encoding="UTF-8"?>']
            lines.append("<code>")

            # Project context
            project_name = Path(root_path).name
            lines.extend([
                "    <project_context>",
                f"        <project_name>{project_name}</project_name>",
                f"        <generation_timestamp>{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</generation_timestamp>",
                "    </project_context>"
            ])

            # Structure explanation and structure
            lines.extend([
                "    <structure_explanation>",
                f"        {self.STRUCTURE_EXPLANATION.strip()}",
                "    </structure_explanation>",
                "    <structure>"
            ])
            
            # Generate structure using the processed directory structure
            structure_lines = self._generate_structure_lines(scan_result.structure)
            for line in structure_lines:
                lines.append(f"        {line}")
            lines.append("    </structure>")

            # Map file paths to their content for easy access
            file_contents = {file_info['path']: file_info['content'] for file_info in scan_result.files_content}

            # Append directories and files as XML tags with content
            self.logger.info("Appending directories and files as XML tags")
            self._append_xml_tags(scan_result.structure, lines, file_contents)

            lines.append("</code>")
            return "\n".join(lines)

        except Exception as e:
            self.logger.error(f"Error during XML generation: {str(e)}")
            raise