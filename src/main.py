import argparse
from pathlib import Path
import logging
from datetime import datetime
from file_processor import FileProcessor
from xml_generator import XMLGenerator

def setup_logging():
    """Setup logging base"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def save_output(content: str, project_name: str) -> str:
    """Saves the output to a file in the output folder"""
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_dir / f"project_structure_{project_name}_{timestamp}.xml"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    return str(filename)

def main():
    """Main entry point"""
    logger = setup_logging()
    
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Generates XML representation of a project for LLM"
    )
    parser.add_argument(
        "path",
        help="Path to the project directory"
    )
    args = parser.parse_args()
    
    try:
        # Initialize processor and generator
        processor = FileProcessor()
        generator = XMLGenerator()
        
        # Process files
        logger.info(f"Starting processing of project: {args.path}")
        files = processor.scan_directory(args.path)
        
        # Generate XML
        xml_content = generator.generate_xml(args.path, files)
        
        # Save output
        project_name = Path(args.path).name
        output_file = save_output(xml_content, project_name)
        logger.info(f"File saved successfully: {output_file}")
        
    except Exception as e:
        logger.error(f"Error during execution: {str(e)}")
        raise

if __name__ == "__main__":
    main()