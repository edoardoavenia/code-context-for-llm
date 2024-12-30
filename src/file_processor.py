from pathlib import Path
import yaml
import logging
import filetype
from typing import List, Dict

class FileProcessor:
    def __init__(self, config_path: str = "config.yaml"):
        """Inizializza il processor con la configurazione"""
        self.config = self._load_config(config_path)
        self._setup_logging()
        
    def _load_config(self, config_path: str) -> dict:
        """Carica la configurazione dal file yaml"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise Exception(f"Errore nel caricamento della configurazione: {str(e)}")

    def _setup_logging(self):
        """Setup logging base"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _should_ignore_file(self, file_path: Path) -> bool:
        """Controlla se il file deve essere ignorato basandosi sulla configurazione"""
        # Controlla dimensione
        if file_path.stat().st_size > self.config['max_file_size_kb'] * 1024:
            self.logger.info(f"File ignorato (troppo grande): {file_path}")
            return True

        # Controlla estensione
        if file_path.suffix in self.config['exclude']['extensions']:
            return True

        # Controlla nome file specifico
        if file_path.name in self.config['exclude']['files']:
            return True

        return False

    def _should_ignore_directory(self, dir_path: Path) -> bool:
        """Controlla se la directory deve essere ignorata"""
        return dir_path.name in self.config['exclude']['directories']

    def _is_text_file(self, file_path: Path) -> bool:
        """
        Determina se un file è un file di testo leggibile (UTF-8).
        Utilizza filetype per controllare il mime type.
        """
        try:
            kind = filetype.guess(str(file_path))
            if kind is None:
                # filetype non è sicuro quindi controlliamo anche se non ha estensione
                return file_path.suffix == "" or file_path.suffix in [".py", ".json", ".yaml", ".yml", ".md", ".txt",".log",".ini",".conf",".toml"]

            mime_type = kind.mime
            return mime_type.startswith('text/') or mime_type in ['application/json', 'application/x-yaml', 'application/x-sh'] #aggiunte mime types comuni
        except Exception as e:
            self.logger.debug(f"Errore nel determinare il tipo di file {file_path}: {e}")
            return False


    def scan_directory(self, root_path: str) -> List[Dict[str, str]]:
        """
        Scansiona la directory e restituisce la lista dei file da processare
        
        Returns:
            List[Dict[str, str]]: Lista di dict con 'path' e 'content' dei file
        """
        root_path = Path(root_path)
        if not root_path.exists():
            raise FileNotFoundError(f"Il percorso {root_path} non esiste")

        self.logger.info(f"Inizio scansione directory: {root_path}")
        files_to_process = []

        def _scan(path: Path):
            for item in path.iterdir():
                if item.is_dir():
                    if self._should_ignore_directory(item):
                        self.logger.debug(f"Directory ignorata: {item}")
                        continue
                    _scan(item)
                elif item.is_file():
                    if self._should_ignore_file(item):
                        self.logger.debug(f"File ignorato (config): {item}")
                        continue
                    if not self._is_text_file(item):
                       self.logger.debug(f"File ignorato (non text): {item}")
                       continue

                    try:
                        with open(item, 'r', encoding='utf-8') as f:
                           content = f.read()
                           files_to_process.append({
                                'path': str(item.relative_to(root_path)),
                                'content': content
                           })
                        self.logger.debug(f"File processato: {item}")
                    except Exception as e:
                        self.logger.error(f"Errore nella lettura del file {item}: {str(e)}")
                        continue
        _scan(root_path)

        self.logger.info(f"Scansione completata. {len(files_to_process)} file processati")
        return files_to_process