import pytest
import sys
from pathlib import Path
import os
import tempfile
import json
from unittest.mock import patch, MagicMock

# Add the project root to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from file_processor import FileProcessor, DirectoryStructure, ScanResult
from config_manager import ConfigManager


class TestFileProcessor:
    def test_init(self):
        """Test initialization of FileProcessor."""
        processor = FileProcessor()
        assert processor.config is not None
        assert processor.structure_items_count == {}
        assert processor.content_files_by_depth == {}

    def test_is_utf8_with_text_file(self, temp_dir):
        """Test UTF-8 detection with a valid text file."""
        text_file = temp_dir / "utf8_file.txt"
        text_file.write_text("This is a UTF-8 encoded file.", encoding="utf-8")
        
        processor = FileProcessor()
        assert processor._is_utf8(text_file) is True

    def test_is_utf8_with_binary_file(self, temp_dir):
        """Test UTF-8 detection with a binary file."""
        binary_file = temp_dir / "binary_file.bin"
        with open(binary_file, "wb") as f:
            f.write(os.urandom(100))
        
        processor = FileProcessor()
        assert processor._is_utf8(binary_file) is False

    def test_should_include_content(self, temp_dir, monkeypatch):
        """Test content inclusion logic based on file properties."""
        # Create test files
        small_txt_file = temp_dir / "small.txt"
        small_txt_file.write_text("Small file", encoding="utf-8")
        
        large_txt_file = temp_dir / "large.txt"
        large_txt_file.write_text("Large file" * 1000, encoding="utf-8")
        
        excluded_ext_file = temp_dir / "excluded.env"
        excluded_ext_file.write_text("ENV file", encoding="utf-8")
        
        excluded_name_file = temp_dir / "excluded_name.txt"
        excluded_name_file.write_text("Excluded by name", encoding="utf-8")
        
        # Setup mock config
        mock_config = {
            "max_file_size_kb": 2,  # Small size to test the size check
            "content_exclude": {
                "extensions": [".env"],
                "files": ["excluded_name.txt"],
                "max_depth": 10,
                "max_files": 10
            },
            "structure_exclude": {
                "extensions": [],
                "directories": [],
                "files": [],
                "max_depth": 10,
                "max_files": 10
            }
        }
        
        processor = FileProcessor()
        processor.config = mock_config
        
        # Test file checks
        assert processor._should_include_content(small_txt_file) is True
        assert processor._should_include_content(large_txt_file) is False  # Excluded by size
        assert processor._should_include_content(excluded_ext_file) is False  # Excluded by extension
        assert processor._should_include_content(excluded_name_file) is False  # Excluded by name

    def test_scan_directory_structure_depth_limit(self, project_structure, monkeypatch):
        """Test that structure depth limit is respected."""
        # Create a deeper directory structure
        deep_dir = project_structure / "deep1" / "deep2" / "deep3" / "deep4"
        deep_dir.mkdir(parents=True)
        (deep_dir / "deep_file.txt").write_text("Deep file")
        
        # Set up config with depth limit of 2
        mock_config = {
            "max_file_size_kb": 1024,
            "content_exclude": {
                "extensions": [],
                "files": [],
                "max_depth": 5,  # Allow deeper content extraction
                "max_files": 100
            },
            "structure_exclude": {
                "extensions": [],
                "directories": [],
                "files": [],
                "max_depth": 2,  # Limit structure depth to 2
                "max_files": 100
            }
        }
        
        # Mock ConfigManager to return our custom config
        with patch.object(ConfigManager, 'get_config', return_value=mock_config):
            processor = FileProcessor()
            result = processor.scan_directory(str(project_structure))
            
            # Verify the structure depth doesn't exceed 2
            def check_depth(node, current_depth=0):
                if current_depth > 2:
                    return False
                for child in node.children:
                    if child.is_dir and not check_depth(child, current_depth + 1):
                        return False
                return True
            
            assert check_depth(result.structure)
            
    def test_scan_directory_content_depth_limit(self, project_structure, monkeypatch):
        """Test that content depth limit is respected."""
        # Create a deeper directory structure with files
        deep_dir = project_structure / "deep1" / "deep2" / "deep3"
        deep_dir.mkdir(parents=True)
        deep_file = deep_dir / "deep_file.txt"
        deep_file.write_text("Deep file content")
        
        # Set up config with content depth limit of 2
        mock_config = {
            "max_file_size_kb": 1024,
            "content_exclude": {
                "extensions": [],
                "files": [],
                "max_depth": 2,  # Limit content extraction to depth 2
                "max_files": 100
            },
            "structure_exclude": {
                "extensions": [],
                "directories": [],
                "files": [],
                "max_depth": 5,  # Allow deeper structure
                "max_files": 100
            }
        }
        
        # Mock ConfigManager
        with patch.object(ConfigManager, 'get_config', return_value=mock_config):
            processor = FileProcessor()
            result = processor.scan_directory(str(project_structure))
            
            # Get all file paths that had content extracted
            content_paths = [file_info['path'] for file_info in result.files_content]
            
            # Check if deep file's content was extracted
            deep_file_rel_path = f"test_project/deep1/deep2/deep3/deep_file.txt"
            assert deep_file_rel_path not in content_paths

    def test_scan_directory_max_files_limit(self, project_structure, monkeypatch):
        """Test that max files limit is respected for both structure and content."""
        # Create many files in a directory
        many_files_dir = project_structure / "many_files"
        many_files_dir.mkdir()
        for i in range(10):
            (many_files_dir / f"file{i}.txt").write_text(f"Content of file {i}")
        
        # Set up config with max files limits
        mock_config = {
            "max_file_size_kb": 1024,
            "content_exclude": {
                "extensions": [],
                "files": [],
                "max_depth": 10,
                "max_files": 3  # Limit content extraction to 3 files per directory
            },
            "structure_exclude": {
                "extensions": [],
                "directories": [],
                "files": [],
                "max_depth": 10,
                "max_files": 5  # Limit structure to 5 files per directory
            }
        }
        
        # Mock ConfigManager
        with patch.object(ConfigManager, 'get_config', return_value=mock_config):
            processor = FileProcessor()
            result = processor.scan_directory(str(project_structure))
            
            # Count files in the "many_files" directory in the structure
            many_files_node = None
            for child in result.structure.children:
                if child.name == "many_files" and child.is_dir:
                    many_files_node = child
                    break
            
            assert many_files_node is not None
            structure_file_count = sum(1 for child in many_files_node.children if not child.is_dir)
            assert structure_file_count <= 5
            
            # Count files from "many_files" directory in the content
            many_files_prefix = "test_project/many_files/"
            content_file_count = sum(1 for file_info in result.files_content 
                                     if file_info['path'].startswith(many_files_prefix))
            assert content_file_count <= 3

    def test_decoupled_exclusion_behavior(self, project_structure, monkeypatch):
        """Test that structure and content exclusion settings work independently."""
        # Create test setup
        test_dir = project_structure / "test_decoupled"
        test_dir.mkdir()
        
        # File excluded from structure but included in content
        structure_excluded = test_dir / "structure_excluded.conf"
        structure_excluded.write_text("Structure excluded but content included")
        
        # File excluded from content but included in structure
        content_excluded = test_dir / "content_excluded.txt"
        content_excluded.write_text("Content excluded but structure included")
        
        # File included in both
        both_included = test_dir / "both_included.txt"
        both_included.write_text("Included in both")
        
        # File excluded from both
        both_excluded = test_dir / "both_excluded.log"
        both_excluded.write_text("Excluded from both")
        
        # Set up config with different exclusion rules
        mock_config = {
            "max_file_size_kb": 1024,
            "content_exclude": {
                "extensions": [".log"],
                "files": ["content_excluded.txt"],
                "max_depth": 10,
                "max_files": 100
            },
            "structure_exclude": {
                "extensions": [".log"],
                "directories": [],
                "files": ["structure_excluded.conf"],
                "max_depth": 10,
                "max_files": 100
            }
        }
        
        # Mock ConfigManager
        with patch.object(ConfigManager, 'get_config', return_value=mock_config):
            processor = FileProcessor()
            result = processor.scan_directory(str(project_structure))
            
            # Find the test_decoupled node in the structure
            test_node = None
            for child in result.structure.children:
                if child.name == "test_decoupled" and child.is_dir:
                    test_node = child
                    break
            
            assert test_node is not None
            
            # Check structure inclusion/exclusion
            structure_files = [child.name for child in test_node.children if not child.is_dir]
            assert "structure_excluded.conf" not in structure_files
            assert "content_excluded.txt" in structure_files
            assert "both_included.txt" in structure_files
            assert "both_excluded.log" not in structure_files
            
            # Check content inclusion/exclusion
            test_dir_prefix = "test_project/test_decoupled/"
            content_files = [file_info['path'].split('/')[-1] 
                             for file_info in result.files_content 
                             if file_info['path'].startswith(test_dir_prefix)]
            
            assert "structure_excluded.conf" in content_files
            assert "content_excluded.txt" not in content_files
            assert "both_included.txt" in content_files
            assert "both_excluded.log" not in content_files