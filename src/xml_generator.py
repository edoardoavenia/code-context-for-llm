import xml.etree.ElementTree as ET
from typing import List, Dict
import logging
from pathlib import Path
from xml.sax.saxutils import escape
import json

class XMLGenerator:
    DEFAULT_CONFIG = {
        'exclude_structure': {
            'extensions': [],
            'directories': [],
            'files': []
        }
    }

    def __init__(self, config_path: str = "config.json"):
        """Initializes the XML generator"""
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: str) -> dict:
        """Loads the configuration from the json file with default values"""
        try:
            with open(config_path, 'r') as f:
                user_config = json.load(f) or {}
            
            # Deep merge of user configuration with defaults
            config = self.DEFAULT_CONFIG.copy()
            
            # Updates exclude_structure if specified
            if 'exclude_structure' in user_config:
                for key in ['extensions', 'directories', 'files']:
                    if user_config['exclude_structure'] and key in user_config['exclude_structure']:
                        config['exclude_structure'][key] = user_config['exclude_structure'][key] or []
            
            return config
        except Exception as e:
            self.logger.warning(f"Error loading configuration: {str(e)}. Using default configuration.")
            return self.DEFAULT_CONFIG

    def _generate_structure(self, root_path: str) -> List[str]:
        """
        Generates the representation of the directory structure
        """
        root_path = Path(root_path)
        structure_lines = []
        
        def add_to_structure(path: Path, prefix: str = "", is_last: bool = True):
            if path != root_path:
                connector = "└── " if is_last else "├── "
                structure_lines.append(f"{prefix}{connector}{path.name}")
                prefix += "    " if is_last else "│   "

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
                    structure_lines.append(f"{prefix}{connector}{item.name}")

        add_to_structure(root_path)
        return structure_lines

    def generate_xml(self, root_path: str, files: List[Dict[str, str]]) -> str:
        """
        Generates the XML document with structure and contents
        
        Args:
            root_path: Root path of the project
            files: List of dict with 'path' and 'content' of the files
            
        Returns:
            str: Complete XML document
        """
        self.logger.info("Starting XML generation")
        
        # Start the XML document
        output = ["<code>"]
        
        # Add structure
        output.append("<structure>")
        structure = self._generate_structure(root_path)
        output.extend(structure)
        output.append("</structure>\n")
        
        # Add file contents
        for file_info in files:
            tag_name = file_info['path']
            content = escape(file_info['content'])  # Escape XML characters
            output.append(f"<{tag_name}>")
            output.append(content)
            output.append(f"</{tag_name}>\n")
        
        output.append("</code>")
        xml_content = "\n".join(output)
        
        self.logger.info("XML generation completed")
        return xml_content