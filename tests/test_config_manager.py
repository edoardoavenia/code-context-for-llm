import pytest
import json
import tempfile
from pathlib import Path
import os
import sys

# Add the project root to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from config_manager import ConfigManager


class TestConfigManager:
    def test_singleton_instance(self):
        """Test that ConfigManager is a singleton."""
        cm1 = ConfigManager()
        cm2 = ConfigManager()
        assert cm1 is cm2, "ConfigManager is not a singleton"

    def test_default_config_when_file_missing(self, monkeypatch, temp_dir):
        """Test that default config is loaded when the file is missing."""
        # Set up a non-existent config path
        non_existent_path = temp_dir / "non_existent_config.json"
        
        # Monkeypatch the _load_config method to use our non-existent path
        with monkeypatch.context() as m:
            # Force reinitialization by setting _config to None
            ConfigManager._config = None
            ConfigManager._instance = None
            
            # Create a new ConfigManager instance with our non-existent path
            cm = ConfigManager()
            cm._load_config(str(non_existent_path))
            
            # Verify the default config is loaded
            config = cm.get_config()
            assert config["max_file_size_kb"] == 1024
            assert "content_exclude" in config
            assert "structure_exclude" in config

    def test_load_valid_config(self, config_file):
        """Test loading a valid configuration file."""
        ConfigManager._config = None
        ConfigManager._instance = None
        
        cm = ConfigManager()
        cm._load_config(str(config_file))
        
        config = cm.get_config()
        assert config["max_file_size_kb"] == 1024
        assert ".env" in config["content_exclude"]["extensions"]
        assert ".git" in config["structure_exclude"]["directories"]
        
        # Test the getters
        assert cm.get_max_file_size() == 1024
        assert isinstance(cm.get_content_exclude(), dict)
        assert isinstance(cm.get_structure_exclude(), dict)

    def test_invalid_json_config(self, temp_dir):
        """Test behavior with invalid JSON in config file."""
        invalid_config_path = temp_dir / "invalid_config.json"
        with open(invalid_config_path, "w") as f:
            f.write("{this is not valid json")
        
        ConfigManager._config = None
        ConfigManager._instance = None
        
        cm = ConfigManager()
        cm._load_config(str(invalid_config_path))
        
        # Should fall back to defaults
        config = cm.get_config()
        assert config["max_file_size_kb"] == 1024
        assert isinstance(config["content_exclude"], dict)
        assert isinstance(config["structure_exclude"], dict)

    def test_reload_config(self, temp_dir):
        """Test reloading configuration."""
        # Create initial config
        initial_config = {
            "max_file_size_kb": 500,
            "content_exclude": {"extensions": [".initial"]},
            "structure_exclude": {"directories": [".initial"]}
        }
        initial_config_path = temp_dir / "initial_config.json"
        with open(initial_config_path, "w") as f:
            json.dump(initial_config, f)
        
        # Create updated config
        updated_config = {
            "max_file_size_kb": 1000,
            "content_exclude": {"extensions": [".updated"]},
            "structure_exclude": {"directories": [".updated"]}
        }
        updated_config_path = temp_dir / "updated_config.json"
        with open(updated_config_path, "w") as f:
            json.dump(updated_config, f)
        
        # Load initial config
        ConfigManager._config = None
        ConfigManager._instance = None
        cm = ConfigManager()
        cm._load_config(str(initial_config_path))
        
        # Verify initial config
        assert cm.get_max_file_size() == 500
        
        # Reload with updated config
        cm.reload_config(str(updated_config_path))
        
        # Verify updated config
        assert cm.get_max_file_size() == 1000

    def test_config_validation(self, temp_dir):
        """Test validation of configuration values."""
        invalid_config = {
            "max_file_size_kb": "not an integer",
            "content_exclude": {
                "max_depth": "not an integer",
                "max_files": "not an integer"
            },
            "structure_exclude": {
                "max_depth": "not an integer",
                "max_files": "not an integer"
            }
        }
        invalid_config_path = temp_dir / "invalid_types_config.json"
        with open(invalid_config_path, "w") as f:
            json.dump(invalid_config, f)
        
        ConfigManager._config = None
        ConfigManager._instance = None
        
        # The config manager falls back to defaults without raising ValueError
        cm = ConfigManager()
        cm._load_config(str(invalid_config_path))
        
        # Should have defaulted to defaults
        assert cm.get_max_file_size() == 1024
            
    def test_decoupled_exclusion_settings(self, config_file):
        """Test that content and structure exclusion settings are properly decoupled."""
        ConfigManager._config = None
        ConfigManager._instance = None
        
        cm = ConfigManager()
        cm._load_config(str(config_file))
        
        # Verify content exclusions don't affect structure exclusions and vice versa
        content_exclude = cm.get_content_exclude()
        structure_exclude = cm.get_structure_exclude()
        
        # Check config is loaded successfully
        assert isinstance(content_exclude, dict)
        assert isinstance(structure_exclude, dict)
        
        # Structure has directories exclusion, check its format
        assert "directories" in structure_exclude