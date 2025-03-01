import json
import logging
from typing import Dict, Any
from dataclasses import dataclass, field

@dataclass
class ConfigurationSchema:
    """Schema for configuration validation."""
    max_file_size_kb: int = 1024
    # Unified exclusion settings applied uniformly for both structure and content
    exclude: Dict[str, Any] = field(default_factory=lambda: {
        'extensions': [],
        'files': [],
        'directories': [],
        'max_depth': 10,
        'max_files': 100
    })

class ConfigManager:
    """Singleton configuration manager that loads and validates configuration."""
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
        Expects a unified exclusion configuration under the key 'exclude'.
        """
        try:
            with open(config_path, 'r') as f:
                user_config = json.load(f)
            
            schema = ConfigurationSchema()
            user_exclude = user_config.get('exclude', {})

            validated_config = {
                'max_file_size_kb': user_config.get('max_file_size_kb', schema.max_file_size_kb),
                'exclude': {
                    'extensions': user_exclude.get('extensions', schema.exclude['extensions']),
                    'files': user_exclude.get('files', schema.exclude['files']),
                    'directories': user_exclude.get('directories', schema.exclude['directories']),
                    'max_depth': user_exclude.get('max_depth', schema.exclude['max_depth']),
                    'max_files': user_exclude.get('max_files', schema.exclude['max_files'])
                }
            }

            if not isinstance(validated_config['max_file_size_kb'], int):
                raise ValueError("max_file_size_kb must be an integer")
            if not isinstance(validated_config['exclude'], dict):
                raise ValueError("exclude must be a dictionary")
            if not isinstance(validated_config['exclude']['max_depth'], int):
                raise ValueError("exclude.max_depth must be an integer")
            if not isinstance(validated_config['exclude']['max_files'], int):
                raise ValueError("exclude.max_files must be an integer")

            self._config = validated_config
            self._logger.info("Configuration loaded successfully")

        except FileNotFoundError:
            self._logger.warning(f"Configuration file {config_path} not found. Using default configuration.")
            default_schema = ConfigurationSchema()
            self._config = {
                'max_file_size_kb': default_schema.max_file_size_kb,
                'exclude': default_schema.exclude
            }
        except json.JSONDecodeError as e:
            self._logger.error(f"Error parsing configuration file: {str(e)}. Using default configuration.")
            default_schema = ConfigurationSchema()
            self._config = {
                'max_file_size_kb': default_schema.max_file_size_kb,
                'exclude': default_schema.exclude
            }
        except Exception as e:
            self._logger.error(f"Unexpected error loading configuration: {str(e)}. Using default configuration.")
            default_schema = ConfigurationSchema()
            self._config = {
                'max_file_size_kb': default_schema.max_file_size_kb,
                'exclude': default_schema.exclude
            }

    def get_config(self) -> dict:
        """Returns the complete configuration."""
        return self._config.copy()

    def get_max_file_size(self) -> int:
        """Returns the maximum file size in KB."""
        return self._config['max_file_size_kb']

    def get_exclude(self) -> dict:
        """Returns the unified exclusion configuration."""
        return self._config['exclude'].copy()

    def reload_config(self, config_path: str = "config.json") -> None:
        """Reloads configuration from file."""
        self._load_config(config_path)
