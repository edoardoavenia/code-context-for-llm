import json
import logging
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class ConfigurationSchema:
    """Schema for configuration validation."""
    max_file_size_kb: int = 1024
    # Default settings for file content filtering (exclusions)
    exclude: Dict[str, Any] = None
    # Default settings for structure filtering (exclusions)
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
    """Singleton configuration manager that loads and validates configuration,
    separating file content and structure exclusion settings.
    """
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
        """
        Loads and validates configuration from file.
        Separates file content exclusion (content_exclude) from directory structure exclusion (structure_exclude)
        to allow independent control.
        """
        try:
            # Load user configuration from file
            with open(config_path, 'r') as f:
                user_config = json.load(f)

            # Create schema with defaults
            schema = ConfigurationSchema()

            # Merge user config with defaults while separating the two concerns
            validated_config = {
                'max_file_size_kb': user_config.get('max_file_size_kb', schema.max_file_size_kb),
                'content_exclude': {
                    'extensions': user_config.get('content_exclude', {}).get('extensions', schema.exclude['extensions']),
                    'files': user_config.get('content_exclude', {}).get('files', schema.exclude['files']),
                    'max_depth': user_config.get('content_exclude', {}).get('max_depth', schema.exclude['max_depth']),
                    'max_files': user_config.get('content_exclude', {}).get('max_files', schema.exclude['max_files'])
                },
                'structure_exclude': {
                    'extensions': user_config.get('exclude_structure', {}).get('extensions', schema.exclude_structure['extensions']),
                    'directories': user_config.get('exclude_structure', {}).get('directories', schema.exclude_structure['directories']),
                    'files': user_config.get('exclude_structure', {}).get('files', schema.exclude_structure['files']),
                    'max_depth': user_config.get('exclude_structure', {}).get('max_depth', schema.exclude_structure['max_depth']),
                    'max_files': user_config.get('exclude_structure', {}).get('max_files', schema.exclude_structure['max_files'])
                }
            }

            # Validate types for critical parameters
            if not isinstance(validated_config['max_file_size_kb'], int):
                raise ValueError("max_file_size_kb must be an integer")
            if not isinstance(validated_config['content_exclude'], dict):
                raise ValueError("content_exclude must be a dictionary")
            if not isinstance(validated_config['structure_exclude'], dict):
                raise ValueError("structure_exclude must be a dictionary")
            if not isinstance(validated_config['content_exclude']['max_depth'], int):
                raise ValueError("content_exclude.max_depth must be an integer")
            if not isinstance(validated_config['content_exclude']['max_files'], int):
                raise ValueError("content_exclude.max_files must be an integer")
            if not isinstance(validated_config['structure_exclude']['max_depth'], int):
                raise ValueError("structure_exclude.max_depth must be an integer")
            if not isinstance(validated_config['structure_exclude']['max_files'], int):
                raise ValueError("structure_exclude.max_files must be an integer")

            self._config = validated_config
            self._logger.info("Configuration loaded successfully")

        except FileNotFoundError:
            self._logger.warning(f"Configuration file {config_path} not found. Using default configuration.")
            default_schema = ConfigurationSchema()
            self._config = {
                'max_file_size_kb': default_schema.max_file_size_kb,
                'content_exclude': default_schema.exclude,
                'structure_exclude': default_schema.exclude_structure
            }
        except json.JSONDecodeError as e:
            self._logger.error(f"Error parsing configuration file: {str(e)}. Using default configuration.")
            default_schema = ConfigurationSchema()
            self._config = {
                'max_file_size_kb': default_schema.max_file_size_kb,
                'content_exclude': default_schema.exclude,
                'structure_exclude': default_schema.exclude_structure
            }
        except Exception as e:
            self._logger.error(f"Unexpected error loading configuration: {str(e)}. Using default configuration.")
            default_schema = ConfigurationSchema()
            self._config = {
                'max_file_size_kb': default_schema.max_file_size_kb,
                'content_exclude': default_schema.exclude,
                'structure_exclude': default_schema.exclude_structure
            }

    def get_config(self) -> dict:
        """Returns the complete configuration."""
        return self._config.copy()

    def get_max_file_size(self) -> int:
        """Returns the maximum file size in KB."""
        return self._config['max_file_size_kb']

    def get_content_exclude(self) -> dict:
        """Returns the file content exclusion configuration."""
        return self._config['content_exclude'].copy()

    def get_structure_exclude(self) -> dict:
        """Returns the directory structure exclusion configuration."""
        return self._config['structure_exclude'].copy()

    def reload_config(self, config_path: str = "config.json") -> None:
        """Reloads configuration from file."""
        self._load_config(config_path)