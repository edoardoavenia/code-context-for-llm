import xml.etree.ElementTree as ET
from typing import List, Dict, Tuple
import logging
from pathlib import Path
from xml.sax.saxutils import escape
import re
from config_manager import ConfigManager

class XMLGenerator:
    """Generates XML representation of project structure and contents"""
    
    # Characters that require content to be wrapped in CDATA
    CDATA_TRIGGERS = ['<', '>', '&', ']]>']
    
    # XML 1.0 valid characters (precompiled regex for performance)
    XML_VALID_CHARS = re.compile(r'[^\x09\x0A\x0D\x20-\x7E\x85\xA0-\xFF]')
    
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
        # Clean invalid XML characters
        content = self._clean_xml_string(content)
        
        if not self._needs_cdata(content):
            return escape(content)
        
        # Handle content containing CDATA end marker
        if "]]>" in content:
            sections = content.split("]]>")
            return "".join(f"<![CDATA[{section}]]>" for section in sections)
        
        return f"<![CDATA[{content}]]>"

    def _needs_cdata(self, content: str) -> bool:
        """Check if content needs CDATA wrapping"""
        return any(trigger in content for trigger in self.CDATA_TRIGGERS)

    def _generate_structure(self, root_path: str) -> List[str]:
        """Generate directory structure representation"""
        root_path = Path(root_path)
        structure_lines = []
        
        def add_to_structure(path: Path, prefix: str = "", is_last: bool = True):
            if path != root_path:
                connector = "└── " if is_last else "├── "
                structure_lines.append(f"{prefix}{connector}{escape(path.name)}")
                prefix += "    " if is_last else "│   "

            try:
                items = sorted(list(path.iterdir()), key=lambda x: (x.is_file(), x.name))
                
                for index, item in enumerate(items):
                    is_last_item = index == len(items) - 1
                    
                    if item.is_dir():
                        if item.name in self.config['exclude_structure']['directories']:
                            self.logger.debug(f"Ignored directory (structure): {item}")
                            continue
                        add_to_structure(item, prefix, is_last_item)
                    else:
                        if (item.name in self.config['exclude_structure']['files'] or 
                            item.suffix in self.config['exclude_structure']['extensions']):
                            self.logger.debug(f"Ignored file (structure): {item}")
                            continue
                        connector = "└── " if is_last_item else "├── "
                        structure_lines.append(f"{prefix}{connector}{escape(item.name)}")
            
            except Exception as e:
                self.logger.error(f"Error processing directory {path}: {str(e)}")
                return

        add_to_structure(root_path)
        return structure_lines

    def generate_xml(self, root_path: str, files: List[Dict[str, str]]) -> str:
        """
        Generates the XML document with structure and contents
        """
        self.logger.info("Starting XML generation")
        
        try:
            # Start with XML declaration and root element
            output = ['<?xml version="1.0" encoding="UTF-8"?>']
            output.append("<code>")
            
            # Add structure section
            output.append("<structure>")
            structure = self._generate_structure(root_path)
            output.extend(self._clean_xml_string(line) for line in structure)
            output.append("</structure>")
            
            # Process each file
            for file_info in files:
                try:
                    # Create valid XML tag from path
                    tag_name = self._create_tag_name(file_info['path'])
                    self.logger.debug(f"Processing file: {file_info['path']} -> tag: {tag_name}")
                    
                    # Wrap content appropriately
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