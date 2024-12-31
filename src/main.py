import argparse
from pathlib import Path
import logging
from datetime import datetime
from file_processor import FileProcessor
from xml_generator import XMLGenerator
import re
import sys

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def sanitize_project_name(project_name: str) -> str:
    sanitized = re.sub(r'[^a-zA-Z0-9\-_]', '_', project_name)
    if not sanitized or not sanitized[0].isalpha():
        sanitized = 'project_' + sanitized
    return sanitized

def validate_path(path: str) -> Path:
    try:
        path_obj = Path(path).resolve()
        if not path_obj.exists():
            raise ValueError(f"Path does not exist: {path}")
        if not path_obj.is_dir():
            raise ValueError(f"Path is not a directory: {path}")
        return path_obj
    except Exception as e:
        raise ValueError(f"Invalid path: {path}")

def save_output(content: str, project_name: str) -> str:
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    safe_name = sanitize_project_name(project_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"project_structure_{safe_name}_{timestamp}.txt"
    
    output_path = output_dir / filename
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return str(output_path)

def main():
    logger = setup_logging()

    parser = argparse.ArgumentParser(
        description="Generate XML project representation for LLMs"
    )
    parser.add_argument(
        "path",
        help="Project directory path",
        type=str
    )

    try:
        args = parser.parse_args()
        project_path = validate_path(args.path)
        processor = FileProcessor()
        generator = XMLGenerator()

        files = processor.scan_directory(str(project_path))
        xml_content = generator.generate_xml(str(project_path), files)
        
        project_name = project_path.name
        output_file = save_output(xml_content, project_name)
        logger.info(f"File saved: {output_file}")

    except Exception as e:
        logger.error(str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()