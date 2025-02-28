import pytest
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the project root to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

import main


class TestCLI:
    """Tests for the command-line interface functionality."""
    
    def test_sanitize_project_name(self):
        """Test project name sanitization."""
        # Test valid name
        assert main.sanitize_project_name("valid_name") == "valid_name"
        
        # Test name with invalid characters
        assert main.sanitize_project_name("invalid@name") == "invalid_name"
        
        # Test name starting with non-alphabetic character
        assert main.sanitize_project_name("123invalid") == "project_123invalid"
        
        # Test empty name
        assert main.sanitize_project_name("") == "project_"

    def test_validate_path_existing_dir(self, temp_dir):
        """Test path validation with existing directory."""
        path = main.validate_path(str(temp_dir))
        assert path == temp_dir.resolve()

    def test_validate_path_nonexistent_path(self):
        """Test path validation with non-existent path."""
        with pytest.raises(ValueError) as exc_info:
            main.validate_path("/path/does/not/exist")
        assert "Invalid path" in str(exc_info.value)

    def test_validate_path_file_not_dir(self, temp_dir):
        """Test path validation with a file instead of a directory."""
        file_path = temp_dir / "test_file.txt"
        file_path.write_text("test")
        
        with pytest.raises(ValueError) as exc_info:
            main.validate_path(str(file_path))
        assert "Invalid path" in str(exc_info.value)

    @patch('argparse.ArgumentParser.parse_args')
    @patch('main.validate_path')
    @patch('main.FileProcessor')
    @patch('main.XMLGenerator')
    @patch('main.save_output')
    def test_main_success_path(self, mock_save, mock_xml_gen, mock_processor, 
                               mock_validate, mock_parse_args, temp_dir):
        """Test successful execution path of the main function."""
        # Setup mocks
        mock_args = MagicMock()
        mock_args.path = str(temp_dir)
        mock_parse_args.return_value = mock_args
        
        mock_path = MagicMock()
        mock_path.name = "test_project"
        mock_validate.return_value = mock_path
        
        mock_processor_instance = mock_processor.return_value
        mock_files = MagicMock()
        mock_processor_instance.scan_directory.return_value = mock_files
        
        mock_xml_instance = mock_xml_gen.return_value
        mock_xml_content = "<xml>test</xml>"
        mock_xml_instance.generate_xml.return_value = mock_xml_content
        
        mock_output_file = "output/test_file.txt"
        mock_save.return_value = mock_output_file
        
        # Call the main function
        with patch('sys.exit') as mock_exit:
            main.main()
            
            # Verify main did not exit with an error
            mock_exit.assert_not_called()
        
        # Verify the function calls
        mock_validate.assert_called_once_with(str(temp_dir))
        mock_processor.assert_called_once()
        mock_processor_instance.scan_directory.assert_called_once_with(str(mock_path))
        mock_xml_gen.assert_called_once()
        mock_xml_instance.generate_xml.assert_called_once_with(str(mock_path), mock_files)
        mock_save.assert_called_once_with(mock_xml_content, "test_project")

    @patch('argparse.ArgumentParser.parse_args')
    @patch('main.validate_path')
    def test_main_error_path(self, mock_validate, mock_parse_args, temp_dir):
        """Test error handling in the main function."""
        # Setup mocks
        mock_args = MagicMock()
        mock_args.path = str(temp_dir)
        mock_parse_args.return_value = mock_args
        
        # Make validate_path raise an error
        mock_validate.side_effect = ValueError("Test error")
        
        # Call the main function
        with patch('sys.exit') as mock_exit:
            main.main()
            
            # Verify main exited with an error
            mock_exit.assert_called_once_with(1)

    def test_save_output(self, temp_dir, monkeypatch):
        """Test saving output to a file."""
        # Change working directory to temp dir
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create output directory if it doesn't exist
            output_dir = temp_dir / "output"
            if not output_dir.exists():
                output_dir.mkdir()
            
            # Test saving output
            content = "<xml>test content</xml>"
            project_name = "test_project"
            
            # Mock datetime to have a predictable filename
            mock_datetime = MagicMock()
            mock_datetime.now().strftime.return_value = "20230101_120000"
            with patch('main.datetime', mock_datetime):
                output_path = main.save_output(content, project_name)
                
                # Verify the file exists
                # Just check that the path contains the expected filename pattern
                assert "project_structure_test_project_20230101_120000.txt" in output_path
                assert Path(output_path).exists()
                
                # Verify the content
                with open(output_path, 'r', encoding='utf-8') as f:
                    assert f.read() == content
        
        finally:
            os.chdir(original_cwd)