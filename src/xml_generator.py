import xml.etree.ElementTree as ET
from typing import List, Dict
import logging
from pathlib import Path
from xml.sax.saxutils import escape

class XMLGenerator:
    def __init__(self):
        """Inizializza il generatore XML"""
        self.logger = logging.getLogger(__name__)

    def _generate_structure(self, root_path: str) -> List[str]:
        """
        Genera la rappresentazione della struttura delle directory
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
                    add_to_structure(item, prefix, is_last_item)
                else:
                    connector = "└── " if is_last_item else "├── "
                    structure_lines.append(f"{prefix}{connector}{item.name}")

        add_to_structure(root_path)
        return structure_lines

    def generate_xml(self, root_path: str, files: List[Dict[str, str]]) -> str:
        """
        Genera il documento XML con struttura e contenuti
        
        Args:
            root_path: Percorso root del progetto
            files: Lista di dict con 'path' e 'content' dei file
            
        Returns:
            str: Documento XML completo
        """
        self.logger.info("Inizio generazione XML")
        
        # Inizia il documento XML
        output = ["<code>"]
        
        # Aggiungi struttura
        output.append("<structure>")
        structure = self._generate_structure(root_path)
        output.extend(structure)
        output.append("</structure>\n")
        
        # Aggiungi contenuti file
        for file_info in files:
            tag_name = file_info['path']
            content = escape(file_info['content'])  # Escape caratteri XML
            output.append(f"<{tag_name}>")
            output.append(content)
            output.append(f"</{tag_name}>\n")
        
        output.append("</code>")
        xml_content = "\n".join(output)
        
        self.logger.info("Generazione XML completata")
        return xml_content