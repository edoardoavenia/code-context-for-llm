import xml.etree.ElementTree as ET
from typing import List, Dict, Tuple
import logging
from pathlib import Path
from config_manager import ConfigManager
from datetime import datetime
import re
from xml.sax.saxutils import escape

class XMLGenerator:
    """Generates XML representation of project structure and contents"""

    # Placeholder to avoid CDATA section closure
    CDATA_END_PLACEHOLDER = "__CDATA_END__"

    # XML 1.0 valid characters (precompiled regex for performance)
    XML_VALID_CHARS = re.compile(r'[^\x09\x0A\x0D\x20-\x7E\x85\xA0-\xFF]')

    STRUCTURE_EXPLANATION = """
    This section represents the directory structure of the project.
    It includes all UTF-8 encoded files that were not excluded based on the
    configuration file, which allows excluding files by name, extension,
    or size, and directories by name.
    """

    def __init__(self):
        """Initializes the XML generator"""
        self.logger = logging.getLogger(__name__)
        self.config = ConfigManager().get_config()

    def _clean_xml_string(self, text: str) -> str:
        """
        Removes any characters that are invalid in XML 1.0
        """
        return self.XML_VALID_CHARS.sub('', text)

    def _sanitize_tag_name(self, name: str) -> str:
        """
        Creates a valid XML tag name from any string
        """
        # Remove any character that isn't alphanumeric, underscore, hyphen, or dot
        sanitized = re.sub(r'[^a-zA-Z0-9\-_.]', '_', name)

        # Ensure it starts with a letter or underscore
        if not sanitized or not (sanitized[0].isalpha() or sanitized[0] == '_'):
            sanitized = '_' + sanitized

        # Remove consecutive special characters
        sanitized = re.sub(r'[_\-\.]{2,}', '_', sanitized)

        # Ensure it's not empty
        return sanitized if sanitized else '_file'

    def _create_tag_name(self, path: str) -> str:
        """
        Creates a valid XML tag name from a file path
        """
        # Replace directory separators with underscore
        path = path.replace('/', '_').replace('\\', '_')

        # Sanitize the entire path as one tag name
        return self._sanitize_tag_name(path)

    def _wrap_content(self, content: str) -> str:
        """
        Prepares content for XML insertion, using CDATA when necessary
        """
        # Replace '__CDATA_END__' with a placeholder to avoid CDATA section closure
        content = content.replace("__CDATA_END__", self.CDATA_END_PLACEHOLDER)
        content = content.replace("]]>", "]]]]><![CDATA[>")

        # Wrap content in CDATA section
        return f"<![CDATA[{content}]]>"

    def _generate_structure(self, root_path: str) -> List[str]:
        """Generate directory structure representation using Unicode tree characters"""
        root_path = Path(root_path)
        structure_lines = []

        def should_include(item: Path) -> bool:
            """Check if item should be included based on configuration"""
            if item.is_dir():
                return item.name not in self.config['exclude_structure']['directories']
            return (item.name not in self.config['exclude_structure']['files'] and
                    item.suffix not in self.config['exclude_structure']['extensions'])

        def add_to_structure(path: Path, level: int = 0):
            try:
                # Get filtered and sorted items
                items = [item for item in path.iterdir() if should_include(item)]
                items.sort(key=lambda x: (x.is_file(), x.name.lower()))

                if level == 0:
                    structure_lines.append(f"{path.name}/")

                for i, item in enumerate(items):
                    is_last = (i == len(items) - 1)
                    
                    # Create prefix based on level and position
                    prefix = "│   " * level
                    
                    # Add item line
                    if is_last:
                        line = f"{prefix}└── {item.name}"
                    else:
                        line = f"{prefix}├── {item.name}"
                    
                    if item.is_dir():
                        line += "/"
                    
                    structure_lines.append(line)

                    # If directory, process its contents
                    if item.is_dir():
                        add_to_structure(item, level + 1)

            except Exception as e:
                self.logger.error(f"Error processing directory {path}: {str(e)}")
                return

        add_to_structure(root_path)
        return structure_lines

    def _generate_project_context(self, root_path: str) -> List[str]:
        """Generates the project context section."""
        project_name = Path(root_path).name
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        return [
            "<project_context>",
            f"    <project_name>{escape(project_name)}</project_name>",
            f"    <generation_timestamp>{timestamp}</generation_timestamp>",
            "</project_context>"
        ]

    def generate_xml(self, root_path: str, files: List[Dict[str, str]]) -> str:
        """
        Generates the XML document with structure and contents
        """
        self.logger.info("Starting XML generation")

        try:
            # Start with XML declaration and root element
            output = ['<?xml version="1.0" encoding="UTF-8"?>']
            output.append("<code>")

            # Add project context section
            output.extend(self._generate_project_context(root_path))

            # Add structure section - without XML sanitization for tree structure
            output.append("<structure_explanation>")
            output.append(f"    {self.STRUCTURE_EXPLANATION.strip()}")
            output.append("</structure_explanation>")
            output.append("<structure>")
            
            # Add the tree structure directly without cleaning
            structure = self._generate_structure(root_path)
            for line in structure:
                output.append(line)
            
            output.append("</structure>")

            # Process each file
            for file_info in files:
                try:
                    # Create valid XML tag from path
                    tag_name = self._create_tag_name(file_info['path'])
                    self.logger.debug(f"Processing file: {file_info['path']} -> tag: {tag_name}")

                    # Clean and wrap content
                    content = self._wrap_content(file_info['content'])

                    # Add to output
                    output.append(f"<{tag_name}>")
                    output.append(content)
                    output.append(f"</{tag_name}>")

                except Exception as e:
                    self.logger.error(f"Error processing file {file_info.get('path', 'unknown')}: {str(e)}")
                    continue

            # Close root element
            output.append("</code>")

            # Join with newlines
            xml_content = "\n".join(output)

            # Validate final output
            try:
                ET.fromstring(xml_content)
                self.logger.info("XML generation completed successfully")
                return xml_content
            except ET.ParseError as e:
                self.logger.error(f"Generated invalid XML: {str(e)}")
                # Log problematic sections for debugging
                lines = xml_content.split('\n')
                error_line = e.position[0]
                context_start = max(0, error_line - 5)
                context_end = min(len(lines), error_line + 5)
                self.logger.debug("XML context around error:")
                for i in range(context_start, context_end):
                    self.logger.debug(f"Line {i+1}: {lines[i]}")
                raise ValueError(f"Generated XML is invalid: {str(e)}")

        except Exception as e:
            self.logger.error(f"Error during XML generation: {str(e)}")
            raise