from pathlib import Path
import yaml
import logging
from typing import List, Dict

class FileProcessor:
    DEFAULT_CONFIG = {
        'max_file_size_kb': 1024,
        'exclude': {
            'extensions': [],
            'files': [],
        },
        'exclude_structure': {
            'extensions': [],
            'directories': [],
            'files': []
        }
    }

    def __init__(self, config_path: str = "config.yaml"):
        """Initializes the processor with the configuration"""
        self.config = self._load_config(config_path)
        self._setup_logging()

    def _load_config(self, config_path: str) -> dict:
        """Loads the configuration from the yaml file with default values"""
        try:
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f) or {}
            
            # Deep merge of user configuration with defaults
            config = self.DEFAULT_CONFIG.copy()
            
            # Updates max_file_size_kb if specified
            if 'max_file_size_kb' in user_config:
                config['max_file_size_kb'] = user_config['max_file_size_kb']
            
            # Updates exclude if specified
            if 'exclude' in user_config:
                for key in ['extensions', 'files']:
                    if user_config['exclude'] and key in user_config['exclude']:
                        config['exclude'][key] = user_config['exclude'][key] or []
            
            # Updates exclude_structure if specified
            if 'exclude_structure' in user_config:
                for key in ['extensions', 'directories', 'files']:
                    if user_config['exclude_structure'] and key in user_config['exclude_structure']:
                        config['exclude_structure'][key] = user_config['exclude_structure'][key] or []
            
            return config
        except Exception as e:
            self.logger.warning(f"Error loading configuration: {str(e)}. Using default configuration.")
            return self.DEFAULT_CONFIG

    def _setup_logging(self):
        """Setup logging base"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _should_ignore_file(self, file_path: Path) -> bool:
        """Checks if the file should be ignored based on the configuration"""
        # Check size
        if file_path.stat().st_size > self.config['max_file_size_kb'] * 1024:
            self.logger.info(f"File ignored (too large): {file_path}")
            return True

        # Check extension
        if file_path.suffix in self.config['exclude']['extensions']:
            return True

        # Check specific file name
        if file_path.name in self.config['exclude']['files']:
            return True

        return False
    
    def _is_utf8(self, file_path: Path) -> bool:
        """
        Verifies if a file is encoded in UTF-8.
        """
        try:
            with open(file_path, 'rb') as f:
                f.read().decode('utf-8')
            return True
        except UnicodeDecodeError:
            return False

    def scan_directory(self, root_path: str) -> List[Dict[str, str]]:
        """
        Scans the directory and returns the list of files to process
        
        Returns:
            List[Dict[str, str]]: List of dict with 'path' and 'content' of the files
        """
        root_path = Path(root_path)
        if not root_path.exists():
            raise FileNotFoundError(f"The path {root_path} does not exist")

        self.logger.info(f"Starting directory scan: {root_path}")
        files_to_process = []

        def _scan(path: Path):
            for item in path.iterdir():
                if item.is_dir():
                    if item.name in self.config['exclude_structure']['directories']:
                        self.logger.debug(f"Ignored directory: {item}")
                        continue
                    _scan(item)
                elif item.is_file():
                    if self._should_ignore_file(item):
                        self.logger.debug(f"File ignored (config): {item}")
                        continue
                    if not self._is_utf8(item):
                        self.logger.debug(f"File ignored (not UTF-8): {item}")
                        continue
                    
                    try:
                        with open(item, 'r', encoding='utf-8') as f:
                            content = f.read()
                            files_to_process.append({
                                'path': str(item.relative_to(root_path)),
                                'content': content
                            })
                        self.logger.debug(f"File processed: {item}")
                    except Exception as e:
                        self.logger.error(f"Error reading file {item}: {str(e)}")
                        continue

        _scan(root_path)
        
        self.logger.info(f"Scan completed. {len(files_to_process)} files processed")
        return files_to_process