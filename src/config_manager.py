from pathlib import Path
import json
import logging
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class ConfigurationSchema:
    """Schema for configuration validation"""
    max_file_size_kb: int = 1024
    exclude: Dict[str, Any] = None
    exclude_structure: Dict[str, Any] = None

    def __post_init__(self):
        if self.exclude is None:
            self.exclude = {
                'extensions': [],
                'files': [],
                'max_depth': 10,
                'max_files': 100
            }
        if self.exclude_structure is None:
            self.exclude_structure = {
                'extensions': [],
                'directories': [],
                'files': [],
                'max_depth': 10,
                'max_files': 100
            }

class ConfigManager:
    """Singleton configuration manager"""
    _instance = None
    _config = None
    _logger = logging.getLogger(__name__)

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            self._load_config()

    def _load_config(self, config_path: str = "config.json") -> None:
        """Loads and validates configuration from file"""
        try:
            # Load user configuration
            with open(config_path, 'r') as f:
                user_config = json.load(f)

            # Create schema with defaults
            schema = ConfigurationSchema()

            # Validate and merge configuration
            validated_config = {
                'max_file_size_kb': user_config.get('max_file_size_kb', schema.max_file_size_kb),
                'exclude': {
                    'extensions': user_config.get('exclude', {}).get('extensions', schema.exclude['extensions']),
                    'files': user_config.get('exclude', {}).get('files', schema.exclude['files']),
                    'max_depth': user_config.get('exclude', {}).get('max_depth', schema.exclude['max_depth']),
                    'max_files': user_config.get('exclude', {}).get('max_files', schema.exclude['max_files'])
                },
                'exclude_structure': {
                    'extensions': user_config.get('exclude_structure', {}).get('extensions', schema.exclude_structure['extensions']),
                    'directories': user_config.get('exclude_structure', {}).get('directories', schema.exclude_structure['directories']),
                    'files': user_config.get('exclude_structure', {}).get('files', schema.exclude_structure['files']),
                    'max_depth': user_config.get('exclude_structure', {}).get('max_depth', schema.exclude_structure['max_depth']),
                    'max_files': user_config.get('exclude_structure', {}).get('max_files', schema.exclude_structure['max_files'])
                }
            }

            # Validate types
            if not isinstance(validated_config['max_file_size_kb'], int):
                raise ValueError("max_file_size_kb must be an integer")
            if not isinstance(validated_config['exclude'], dict):
                raise ValueError("exclude must be a dictionary")
            if not isinstance(validated_config['exclude_structure'], dict):
                raise ValueError("exclude_structure must be a dictionary")
            if not isinstance(validated_config['exclude']['max_depth'], int):
                raise ValueError("exclude.max_depth must be an integer")
            if not isinstance(validated_config['exclude']['max_files'], int):
                raise ValueError("exclude.max_files must be an integer")
            if not isinstance(validated_config['exclude_structure']['max_depth'], int):
                raise ValueError("exclude_structure.max_depth must be an integer")
            if not isinstance(validated_config['exclude_structure']['max_files'], int):
                raise ValueError("exclude_structure.max_files must be an integer")

            self._config = validated_config
            self._logger.info("Configuration loaded successfully")

        except FileNotFoundError:
            self._logger.warning(f"Configuration file {config_path} not found. Using default configuration.")
            self._config = ConfigurationSchema().__dict__
        except json.JSONDecodeError as e:
            self._logger.error(f"Error parsing configuration file: {str(e)}. Using default configuration.")
            self._config = ConfigurationSchema().__dict__
        except Exception as e:
            self._logger.error(f"Unexpected error loading configuration: {str(e)}. Using default configuration.")
            self._config = ConfigurationSchema().__dict__

    def get_config(self) -> dict:
        """Returns the current configuration"""
        return self._config.copy()

    def get_max_file_size(self) -> int:
        """Returns max file size in KB"""
        return self._config['max_file_size_kb']

    def get_exclude_extensions(self) -> list:
        """Returns list of excluded extensions"""
        return self._config['exclude']['extensions']

    def get_exclude_files(self) -> list:
        """Returns list of excluded files"""
        return self._config['exclude']['files']

    def get_exclude_structure(self) -> dict:
        """Returns structure exclusion configuration"""
        return self._config['exclude_structure'].copy()

    def reload_config(self, config_path: str = "config.json") -> None:
        """Reloads configuration from file"""
        self._load_config(config_path)