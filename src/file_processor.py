from pathlib import Path
import logging
from config_manager import ConfigManager
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class DirectoryStructure:
    name: str
    is_dir: bool = True
    children: List['DirectoryStructure'] = field(default_factory=list)
    depth: int = 0

@dataclass
class ScanResult:
    structure: DirectoryStructure
    files_content: List[Dict] = field(default_factory=list)

class FileProcessor:
    def __init__(self):
        self._setup_logging()
        self.config = ConfigManager().get_config()
        self.files_by_depth = {}
        self.structure_items_count = {}

    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _should_ignore_file(self, file_path: Path) -> bool:
        if file_path.stat().st_size > self.config['max_file_size_kb'] * 1024:
            return True
        if file_path.suffix in self.config['exclude']['extensions']:
            return True
        if file_path.name in self.config['exclude']['files']:
            return True
        return False
    
    def _is_utf8(self, file_path: Path) -> bool:
        try:
            with open(file_path, 'rb') as f:
                f.read().decode('utf-8')
            return True
        except UnicodeDecodeError:
            return False

    def _get_depth(self, path: Path, root_path: Path) -> int:
        try:
            return len(path.relative_to(root_path).parts) - 1
        except ValueError:
            return 0

    def _process_directory(self, path: Path, root_path: Path, current_depth: int = 0) -> DirectoryStructure:
        if current_depth > self.config['exclude_structure']['max_depth']:
            return None

        # Initialize structure counter for this depth if not exists
        if current_depth not in self.structure_items_count:
            self.structure_items_count[current_depth] = 0

        # Create directory structure
        dir_structure = DirectoryStructure(name=path.name, depth=current_depth)
        
        try:
            # Get and sort all items
            items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
            
            # Process each item
            for item in items:
                # Check if we've reached the max items for this depth
                if self.structure_items_count[current_depth] >= self.config['exclude_structure']['max_files']:
                    break

                if item.is_dir():
                    if item.name not in self.config['exclude_structure']['directories']:
                        child_structure = self._process_directory(item, root_path, current_depth + 1)
                        if child_structure:
                            dir_structure.children.append(child_structure)
                            self.structure_items_count[current_depth] += 1
                
                else:  # is file
                    # Structure processing
                    if (item.suffix not in self.config['exclude_structure']['extensions'] and
                        item.name not in self.config['exclude_structure']['files']):
                        child_structure = DirectoryStructure(name=item.name, is_dir=False, depth=current_depth)
                        dir_structure.children.append(child_structure)
                        self.structure_items_count[current_depth] += 1

                    # Content processing
                    if current_depth <= self.config['exclude']['max_depth']:
                        if not self._should_ignore_file(item) and self._is_utf8(item):
                            if current_depth not in self.files_by_depth:
                                self.files_by_depth[current_depth] = 0
                            
                            if self.files_by_depth[current_depth] < self.config['exclude']['max_files']:
                                try:
                                    with open(item, 'r', encoding='utf-8') as f:
                                        self.files_content.append({
                                            'path': str(item.relative_to(root_path)),
                                            'content': f.read(),
                                            'depth': current_depth
                                        })
                                        self.files_by_depth[current_depth] += 1
                                except Exception as e:
                                    self.logger.error(f"Error reading file {item}: {str(e)}")

        except Exception as e:
            self.logger.error(f"Error processing directory {path}: {str(e)}")
        
        return dir_structure

    def scan_directory(self, root_path: str) -> ScanResult:
        root_path = Path(root_path)
        if not root_path.exists():
            raise FileNotFoundError(f"Path does not exist: {root_path}")

        self.logger.info(f"Starting directory scan: {root_path}")
        self.files_content = []
        self.files_by_depth.clear()
        self.structure_items_count.clear()

        structure = self._process_directory(root_path, root_path)
        
        result = ScanResult(
            structure=structure,
            files_content=self.files_content
        )

        self.logger.info(f"Scan completed. {len(self.files_content)} files processed")
        return result