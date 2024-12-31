import argparse
from pathlib import Path
import logging
from datetime import datetime
from file_processor import FileProcessor
from xml_generator import XMLGenerator
import re
import sys

def setup_logging():
    """Setup logging base"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def sanitize_project_name(project_name: str) -> str:
    """Sanitizes the project name to prevent directory traversal attacks"""
    # Remove any characters that aren't alphanumeric, underscore, or hyphen
    sanitized = re.sub(r'[^a-zA-Z0-9\-_]', '_', project_name)
    
    # Ensure it starts with a letter or underscore
    if not sanitized or not sanitized[0].isalpha():
        sanitized = 'project_' + sanitized
        
    return sanitized

def validate_path(path: str) -> Path:
    """Validates the input path"""
    try:
        path_obj = Path(path).resolve()
        if not path_obj.exists():
            raise ValueError(f"Il path non esiste: {path}")
        if not path_obj.is_dir():
            raise ValueError(f"Il path non è una directory: {path}")
        return path_obj
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        raise ValueError(f"Path non valido: {path}")

def save_output(content: str, project_name: str) -> str:
    """Saves the output to a file in the output folder"""
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
    """Main entry point"""
    logger = setup_logging()

    parser = argparse.ArgumentParser(
        description="Genera una rappresentazione XML del progetto per LLM"
    )
    parser.add_argument(
        "path",
        help="Path della directory del progetto",
        type=str
    )

    try:
        args = parser.parse_args()
        
        # Valida il path di input
        project_path = validate_path(args.path)
        
        # Inizializza processor e generator
        processor = FileProcessor()
        generator = XMLGenerator()

        # Processa i file
        files = processor.scan_directory(str(project_path))
        
        # Genera XML
        xml_content = generator.generate_xml(str(project_path), files)
        
        # Salva output
        project_name = project_path.name
        output_file = save_output(xml_content, project_name)
        logger.info(f"File salvato: {output_file}")

    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Operazione interrotta dall'utente")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Errore durante l'esecuzione: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()