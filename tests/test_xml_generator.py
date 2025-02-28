import pytest
import sys
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from unittest.mock import patch, MagicMock

# Add the project root to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from xml_generator import XMLGenerator
from config_manager import ConfigManager
from file_processor import DirectoryStructure, ScanResult


class TestXMLGenerator:
    def test_sanitize_tag_name(self):
        """Test sanitization of XML tag names."""
        generator = XMLGenerator()
        
        # Test cases
        assert generator._sanitize_tag_name("valid_name") == "valid_name"
        assert generator._sanitize_tag_name("invalid/name") == "invalid_name"
        assert generator._sanitize_tag_name("file.txt") == "file_txt"
        assert generator._sanitize_tag_name("123invalid") == "file_123invalid"
        assert generator._sanitize_tag_name("") == "file_"

    def test_generate_structure_lines(self):
        """Test generation of tree-like structure lines."""
        # Create a test directory structure
        root = DirectoryStructure(name="root")
        dir1 = DirectoryStructure(name="dir1")
        dir2 = DirectoryStructure(name="dir2")
        file1 = DirectoryStructure(name="file1.txt", is_dir=False)
        file2 = DirectoryStructure(name="file2.txt", is_dir=False)
        file3 = DirectoryStructure(name="file3.txt", is_dir=False)
        
        root.children = [dir1, dir2, file1]
        dir1.children = [file2]
        dir2.children = [file3]
        
        generator = XMLGenerator()
        lines = generator._generate_structure_lines(root)
        
        # Verify the structure
        assert lines[0] == "root/"
        assert "dir1/" in lines[1]
        assert "file2.txt" in lines[2]
        assert "dir2/" in lines[3]
        assert "file3.txt" in lines[4]
        assert "file1.txt" in lines[5]

    def test_append_xml_tags(self):
        """Test generation of XML tags from directory structure."""
        # Create a test directory structure
        root = DirectoryStructure(name="root", path="root")
        dir1 = DirectoryStructure(name="dir1", path="root/dir1")
        file1 = DirectoryStructure(name="file1.txt", path="root/file1.txt", is_dir=False)
        file2 = DirectoryStructure(name="file2.txt", path="root/dir1/file2.txt", is_dir=False)
        
        root.children = [dir1, file1]
        dir1.children = [file2]
        
        # Create mock file contents
        file_contents = {
            "root/file1.txt": "File 1 content",
            "root/dir1/file2.txt": "File 2 content"
        }
        
        generator = XMLGenerator()
        lines = []
        generator._append_xml_tags(root, lines, file_contents)
        
        # Verify XML structure
        xml_str = "\n".join(lines)
        assert "<root>" in xml_str
        assert "<dir1>" in xml_str
        assert "<file1_txt>" in xml_str
        assert "<file2_txt>" in xml_str
        assert "File 1 content" in xml_str
        assert "File 2 content" in xml_str
        assert "</file2_txt>" in xml_str
        assert "</dir1>" in xml_str
        assert "</file1_txt>" in xml_str
        assert "</root>" in xml_str

    def test_collect_structure_file_paths(self):
        """Test collection of file paths from structure."""
        # Create a test directory structure
        root = DirectoryStructure(name="root", path="root")
        dir1 = DirectoryStructure(name="dir1", path="root/dir1")
        file1 = DirectoryStructure(name="file1.txt", path="root/file1.txt", is_dir=False)
        file2 = DirectoryStructure(name="file2.txt", path="root/dir1/file2.txt", is_dir=False)
        
        root.children = [dir1, file1]
        dir1.children = [file2]
        
        generator = XMLGenerator()
        paths = generator._collect_structure_file_paths(root)
        
        # Verify paths
        assert "root/file1.txt" in paths
        assert "root/dir1/file2.txt" in paths
        assert len(paths) == 2

    @patch('datetime.datetime')
    def test_generate_xml(self, mock_datetime):
        """Test complete XML generation with structure and content."""
        # Mock datetime for consistent timestamp
        mock_now = MagicMock()
        mock_now.strftime.return_value = "2023-01-01 12:00:00 UTC"
        mock_datetime.now.return_value = mock_now
        
        # Create a test directory structure
        root = DirectoryStructure(name="test_project", path="test_project")
        src_dir = DirectoryStructure(name="src", path="test_project/src")
        main_file = DirectoryStructure(name="main.py", path="test_project/src/main.py", is_dir=False)
        readme_file = DirectoryStructure(name="README.md", path="test_project/README.md", is_dir=False)
        
        root.children = [src_dir, readme_file]
        src_dir.children = [main_file]
        
        # Create mock file contents
        files_content = [
            {
                "path": "test_project/src/main.py",
                "content": "def main():\n    print('Hello')",
                "depth": 2
            },
            {
                "path": "test_project/README.md",
                "content": "# Test Project",
                "depth": 1
            },
            {
                "path": "test_project/orphan.txt",
                "content": "Orphan file not in structure",
                "depth": 1
            }
        ]
        
        scan_result = ScanResult(structure=root, files_content=files_content)
        
        generator = XMLGenerator()
        xml_content = generator.generate_xml("test_project", scan_result)
        
        # Verify XML structure
        assert '<?xml version="1.0" encoding="UTF-8"?>' in xml_content
        assert '<code>' in xml_content
        assert '<project_context>' in xml_content
        assert '<project_name>test_project</project_name>' in xml_content
        # We don't need to check the exact timestamp as it will vary
        assert '<generation_timestamp>' in xml_content
        assert '<structure_explanation>' in xml_content
        assert '<structure>' in xml_content
        assert 'test_project/' in xml_content
        assert '├── src/' in xml_content
        assert '│   └── main.py' in xml_content
        assert '└── README.md' in xml_content
        assert '</structure>' in xml_content
        assert '<test_project>' in xml_content
        assert '<src>' in xml_content
        assert '<main_py>' in xml_content
        assert 'def main():' in xml_content
        assert "print('Hello')" in xml_content
        assert '</main_py>' in xml_content
        assert '</src>' in xml_content
        assert '<README_md>' in xml_content
        assert '# Test Project' in xml_content
        assert '</README_md>' in xml_content
        assert '</test_project>' in xml_content
        assert '<orphan_files>' in xml_content
        assert 'Orphan file not in structure' in xml_content
        assert '</orphan_files>' in xml_content
        assert '</code>' in xml_content
        
        # Verify that the XML is well-formed
        try:
            ET.fromstring(xml_content)
        except Exception as e:
            pytest.fail(f"Generated XML is not well-formed: {str(e)}")

    def test_orphan_files_section(self):
        """Test that files not in structure but with content are added to orphan files section."""
        # Create a test directory structure (without the orphan file)
        root = DirectoryStructure(name="test_project", path="test_project")
        main_file = DirectoryStructure(name="main.py", path="test_project/main.py", is_dir=False)
        root.children = [main_file]
        
        # Create file contents including an orphan file
        files_content = [
            {
                "path": "test_project/main.py",
                "content": "def main(): pass",
                "depth": 1
            },
            {
                "path": "test_project/orphan1.txt",
                "content": "Orphan file 1",
                "depth": 1
            },
            {
                "path": "test_project/orphan2.txt",
                "content": "Orphan file 2",
                "depth": 1
            }
        ]
        
        scan_result = ScanResult(structure=root, files_content=files_content)
        
        generator = XMLGenerator()
        xml_content = generator.generate_xml("test_project", scan_result)
        
        # Verify orphan files section
        assert '<orphan_files>' in xml_content
        assert 'Orphan file 1' in xml_content
        assert 'Orphan file 2' in xml_content
        assert '</orphan_files>' in xml_content
        
        # Count occurrences of orphan file tags
        orphan_tags = re.findall(r'<test_project_orphan\d+_txt>', xml_content)
        assert len(orphan_tags) == 2