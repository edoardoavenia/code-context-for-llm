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
    Applies the unified exclusion settings uniformly.
    """
    def __init__(self):
        self._setup_logging()
        # Retrieve the full configuration, including unified exclusion settings.
        self.config = ConfigManager().get_config()
        self.logger.info("Using unified exclusion configuration: %s", self.config['exclude'])
        self.items_count = {}  # Unified counter for items processed per depth

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

    def _should_include_file(self, file_path: Path) -> bool:
        """
        Determines if the file qualifies for inclusion based on unified exclusion settings.
        Checks file size, extension, and filename.
        """
        try:
            if file_path.stat().st_size > self.config['max_file_size_kb'] * 1024:
                return False
        except Exception as e:
            self.logger.error("Error accessing file size for %s: %s", file_path, str(e))
            return False
        if file_path.suffix in self.config['exclude']['extensions']:
            return False
        if file_path.name in self.config['exclude']['files']:
            return False
        if not self._is_utf8(file_path):
            return False
        return True

    def _process_directory(self, path: Path, root_path: Path, current_depth: int = 0, current_rel_path: str = "") -> DirectoryStructure:
        """
        Recursively builds the directory structure and extracts file contents.
        Applies unified exclusion settings and unified counters for both structure and content.
        """
        max_depth = self.config['exclude']['max_depth']
        max_files = self.config['exclude']['max_files']

        if current_depth > max_depth:
            return None

        if current_depth not in self.items_count:
            self.items_count[current_depth] = 0

        current_dir_rel_path = f"{current_rel_path}/{path.name}" if current_rel_path else path.name
        dir_structure = DirectoryStructure(name=path.name, path=current_dir_rel_path, depth=current_depth)

        try:
            items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
            for item in items:
                # Process directories
                if item.is_dir():
                    if item.name in self.config['exclude']['directories']:
                        continue
                    if self.items_count[current_depth] < max_files:
                        child_structure = self._process_directory(item, root_path, current_depth + 1, current_dir_rel_path)
                        if child_structure:
                            dir_structure.children.append(child_structure)
                            self.items_count[current_depth] += 1
                else:
                    # Process files uniformly for both structure and content
                    if item.suffix in self.config['exclude']['extensions'] or item.name in self.config['exclude']['files']:
                        continue
                    if self.items_count[current_depth] < max_files:
                        file_rel_path = f"{current_dir_rel_path}/{item.name}"
                        file_node = DirectoryStructure(name=item.name, path=file_rel_path, is_dir=False, depth=current_depth)
                        dir_structure.children.append(file_node)
                        # Process file content if the file qualifies
                        if self._should_include_file(item):
                            try:
                                with open(item, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                self.files_content.append({
                                    'path': file_rel_path,
                                    'content': content,
                                    'depth': current_depth
                                })
                            except Exception as e:
                                self.logger.error("Error reading file %s: %s", item, str(e))
                        self.items_count[current_depth] += 1
        except Exception as e:
            self.logger.error("Error processing directory %s: %s", path, str(e))

        return dir_structure

    def scan_directory(self, root_path: str) -> ScanResult:
        """
        Scans the project directory to build the structure tree and extract file contents.
        Uses unified exclusion settings and counters.
        """
        root_path_obj = Path(root_path)
        if not root_path_obj.exists():
            raise FileNotFoundError(f"Path does not exist: {root_path}")

        self.logger.info("Starting directory scan: %s", root_path_obj)
        self.files_content = []  # Reset extracted file contents
        self.items_count.clear()

        structure = self._process_directory(root_path_obj, root_path_obj)
        result = ScanResult(
            structure=structure,
            files_content=self.files_content
        )
        self.logger.info("Scan completed. %d files processed", len(self.files_content))
        return result
