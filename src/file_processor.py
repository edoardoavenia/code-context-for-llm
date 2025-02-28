from pathlib import Path
import logging
from config_manager import ConfigManager
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class DirectoryStructure:
    """
    Data class representing a directory or file node.
    The 'path' attribute holds the relative path from the root.
    """
    name: str
    path: str = ""  # Relative path from the root directory
    is_dir: bool = True
    children: List['DirectoryStructure'] = field(default_factory=list)
    depth: int = 0

@dataclass
class ScanResult:
    """Holds the directory structure and extracted file contents."""
    structure: DirectoryStructure
    files_content: List[Dict] = field(default_factory=list)

class FileProcessor:
    """
    Processes directories to build a structure tree and extract file contents.
    The structure filtering (for display) and content extraction (for file data)
    are decoupled to allow independent configuration and control.
    """
    def __init__(self):
        self._setup_logging()
        self.config = ConfigManager().get_config()
        self.structure_items_count = {}  # Counter for structure items per depth
        self.content_files_by_depth = {}   # Counter for file content extraction per depth

    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _is_utf8(self, file_path: Path) -> bool:
        """Checks whether the file is UTF-8 encoded."""
        try:
            with open(file_path, 'rb') as f:
                f.read().decode('utf-8')
            return True
        except UnicodeDecodeError:
            return False

    def _should_include_content(self, file_path: Path) -> bool:
        """
        Determines if the file qualifies for content extraction based on
        content exclusion settings.
        """
        try:
            if file_path.stat().st_size > self.config['max_file_size_kb'] * 1024:
                return False
        except Exception as e:
            self.logger.error(f"Error accessing file size for {file_path}: {str(e)}")
            return False
        if file_path.suffix in self.config['content_exclude']['extensions']:
            return False
        if file_path.name in self.config['content_exclude']['files']:
            return False
        if not self._is_utf8(file_path):
            return False
        return True

    def _process_directory(self, path: Path, root_path: Path, current_depth: int = 0, current_rel_path: str = "") -> DirectoryStructure:
        """
        Recursively builds the directory structure using structure exclusion settings,
        and independently extracts file contents using content exclusion settings.
        """
        # Abort structure recursion if depth exceeds structure exclusion limit
        if current_depth > self.config['structure_exclude']['max_depth']:
            return None

        # Initialize counter for the current depth (structure)
        if current_depth not in self.structure_items_count:
            self.structure_items_count[current_depth] = 0

        # Compute the current relative path
        current_dir_rel_path = f"{current_rel_path}/{path.name}" if current_rel_path else path.name

        # Create the directory node with its relative path
        dir_structure = DirectoryStructure(name=path.name, path=current_dir_rel_path, depth=current_depth)

        try:
            items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
            for item in items:
                if item.is_dir():
                    # Apply structure exclusion for directories
                    if item.name not in self.config['structure_exclude']['directories']:
                        child_structure = self._process_directory(item, root_path, current_depth + 1, current_dir_rel_path)
                        if child_structure:
                            dir_structure.children.append(child_structure)
                            self.structure_items_count[current_depth] += 1
                else:
                    # For structure: add file node if it passes structure filters
                    if (item.suffix not in self.config['structure_exclude']['extensions'] and
                        item.name not in self.config['structure_exclude']['files']):
                        if self.structure_items_count[current_depth] < self.config['structure_exclude']['max_files']:
                            file_rel_path = f"{current_dir_rel_path}/{item.name}"
                            file_node = DirectoryStructure(name=item.name, path=file_rel_path, is_dir=False, depth=current_depth)
                            dir_structure.children.append(file_node)
                            self.structure_items_count[current_depth] += 1

                    # For content extraction: process file independently of structure inclusion
                    if current_depth <= self.config['content_exclude']['max_depth']:
                        if self._should_include_content(item):
                            if current_depth not in self.content_files_by_depth:
                                self.content_files_by_depth[current_depth] = 0
                            if self.content_files_by_depth[current_depth] < self.config['content_exclude']['max_files']:
                                try:
                                    with open(item, 'r', encoding='utf-8') as f:
                                        content = f.read()
                                    file_rel_path = f"{current_dir_rel_path}/{item.name}"
                                    # Append file content record regardless of structure node inclusion
                                    self.files_content.append({
                                        'path': file_rel_path,
                                        'content': content,
                                        'depth': current_depth
                                    })
                                    self.content_files_by_depth[current_depth] += 1
                                except Exception as e:
                                    self.logger.error(f"Error reading file {item}: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error processing directory {path}: {str(e)}")

        return dir_structure

    def scan_directory(self, root_path: str) -> ScanResult:
        """
        Scans the project directory to build the structure tree and extract file contents.
        Both processes use independent filtering criteria.
        """
        root_path_obj = Path(root_path)
        if not root_path_obj.exists():
            raise FileNotFoundError(f"Path does not exist: {root_path}")

        self.logger.info(f"Starting directory scan: {root_path_obj}")
        self.files_content = []  # Reset extracted file contents
        self.structure_items_count.clear()
        self.content_files_by_depth.clear()

        structure = self._process_directory(root_path_obj, root_path_obj)
        result = ScanResult(
            structure=structure,
            files_content=self.files_content
        )
        self.logger.info(f"Scan completed. {len(self.files_content)} files processed")
        return result
