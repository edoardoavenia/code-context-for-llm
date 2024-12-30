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
    """Salva l'output in un file nella cartella output"""
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_dir / f"project_structure_{project_name}_{timestamp}.xml"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    return str(filename)

def main():
    """Entry point principale"""
    logger = setup_logging()
    
    # Parse argomenti
    parser = argparse.ArgumentParser(
        description="Genera rappresentazione XML di un progetto per LLM"
    )
    parser.add_argument(
        "path",
        help="Percorso della directory del progetto"
    )
    args = parser.parse_args()
    
    try:
        # Inizializza processor e generator
        processor = FileProcessor()
        generator = XMLGenerator()
        
        # Processa i file
        logger.info(f"Inizio processing del progetto: {args.path}")
        files = processor.scan_directory(args.path)
        
        # Genera XML
        xml_content = generator.generate_xml(args.path, files)
        
        # Salva output
        project_name = Path(args.path).name
        output_file = save_output(xml_content, project_name)
        logger.info(f"File salvato correttamente: {output_file}")
        
    except Exception as e:
        logger.error(f"Errore durante l'esecuzione: {str(e)}")
        raise

if __name__ == "__main__":
    main()