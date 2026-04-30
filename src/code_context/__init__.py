"""Convert a project's structure and source files into a single XML document."""
from code_context.config import Config, ExcludeConfig, load_config
from code_context.scanner import FileNode, Scanner, scan
from code_context.xml_writer import generate_xml

__version__ = "0.2.0"
__all__ = [
    "Config",
    "ExcludeConfig",
    "FileNode",
    "Scanner",
    "generate_xml",
    "load_config",
    "scan",
]
