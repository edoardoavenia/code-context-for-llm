from pathlib import Path
from logger_config import setup_logger
from config_manager import ConfigManager
from dataclasses import dataclass, field
from typing import List, Dict, Optional

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
        self.files_content = []  # Ensure initialization

    def _setup_logging(self):
        self.logger = setup_logger(__name__)

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
        return True

    def _read_file_content(self, file_path: Path, chunk_size: int = 4096) -> Optional[str]:
        """
        Reads the file once in binary mode.
        Reads the first chunk (default 4 KB) to verify UTF-8 encoding.
        If valid, reads the remainder and returns the decoded content.
        Returns None if the file is not UTF-8 encoded or an error occurs.
        """
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(chunk_size)
                try:
                    # Validate UTF-8 encoding using only the first chunk.
                    chunk.decode('utf-8')
                except UnicodeDecodeError:
                    self.logger.info("File %s is not UTF-8 encoded.", file_path)
                    return None
                # Read the rest of the file.
                remainder = f.read()
                full_bytes = chunk + remainder
                content = full_bytes.decode('utf-8')
                return content
        except Exception as e:
            self.logger.error("Error reading file %s: %s", file_path, str(e))
            return None

    def _process_directory(self, path: Path, root_path: Path, current_depth: int = 0, current_rel_path: str = "") -> Optional[DirectoryStructure]:
        """
        Recursively builds the directory structure and extracts file contents.
        Applies unified exclusion settings and a per-branch counter for items.
        """
        max_depth = self.config['exclude']['max_depth']
        max_files = self.config['exclude']['max_files']

        if current_depth > max_depth:
            return None

        # Local counter for items in this directory branch.
        local_count = 0

        current_dir_rel_path = f"{current_rel_path}/{path.name}" if current_rel_path else path.name
        dir_structure = DirectoryStructure(name=path.name, path=current_dir_rel_path, depth=current_depth)

        try:
            items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
            for item in items:
                # Skip symlinks to prevent cyclic traversal.
                if item.is_symlink():
                    self.logger.debug("Skipping symlink: %s", item)
                    continue

                # Process directories
                if item.is_dir():
                    if item.name in self.config['exclude']['directories']:
                        continue
                    if local_count < max_files:
                        child_structure = self._process_directory(item, root_path, current_depth + 1, current_dir_rel_path)
                        if child_structure:
                            dir_structure.children.append(child_structure)
                            local_count += 1
                else:
                    # Process files uniformly for both structure and content
                    if item.suffix in self.config['exclude']['extensions'] or item.name in self.config['exclude']['files']:
                        continue
                    if local_count < max_files:
                        file_rel_path = f"{current_dir_rel_path}/{item.name}"
                        file_node = DirectoryStructure(name=item.name, path=file_rel_path, is_dir=False, depth=current_depth)
                        dir_structure.children.append(file_node)
                        # Process file content if the file qualifies
                        if self._should_include_file(item):
                            content = self._read_file_content(item)
                            if content is not None:
                                self.files_content.append({
                                    'path': file_rel_path,
                                    'content': content,
                                    'depth': current_depth
                                })
                        local_count += 1
        except Exception as e:
            self.logger.error("Error processing directory %s: %s", path, str(e))

        return dir_structure

    def scan_directory(self, root_path: str) -> ScanResult:
        """
        Scans the project directory to build the structure tree and extract file contents.
        Uses unified exclusion settings and independent per-branch counters.
        """
        root_path_obj = Path(root_path)
        if not root_path_obj.exists():
            raise FileNotFoundError(f"Path does not exist: {root_path}")

        self.logger.info("Starting directory scan: %s", root_path_obj)
        self.files_content = []  # Reset extracted file contents

        structure = self._process_directory(root_path_obj, root_path_obj)
        result = ScanResult(
            structure=structure,
            files_content=self.files_content
        )
        self.logger.info("Scan completed. %d files processed", len(self.files_content))
        return result
