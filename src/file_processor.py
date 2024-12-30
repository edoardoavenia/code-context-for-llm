from pathlib import Path
import yaml
import logging
from typing import List, Dict

class FileProcessor:
    DEFAULT_CONFIG = {
        'max_file_size_kb': 1024,
        'exclude': {
            'extensions': [],
            'files': [],
        },
        'exclude_structure': {
            'extensions': [],
            'directories': [],
            'files': []
        }
    }

    def __init__(self, config_path: str = "config.yaml"):
        """Inizializza il processor con la configurazione"""
        self.config = self._load_config(config_path)
        self._setup_logging()

    def _load_config(self, config_path: str) -> dict:
        """Carica la configurazione dal file yaml con valori di default"""
        try:
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f) or {}
            
            # Deep merge della configurazione utente con i default
            config = self.DEFAULT_CONFIG.copy()
            
            # Aggiorna max_file_size_kb se specificato
            if 'max_file_size_kb' in user_config:
                config['max_file_size_kb'] = user_config['max_file_size_kb']
            
            # Aggiorna exclude se specificato
            if 'exclude' in user_config:
                for key in ['extensions', 'files']:
                    if user_config['exclude'] and key in user_config['exclude']:
                        config['exclude'][key] = user_config['exclude'][key] or []
            
            # Aggiorna exclude_structure se specificato
            if 'exclude_structure' in user_config:
                for key in ['extensions', 'directories', 'files']:
                    if user_config['exclude_structure'] and key in user_config['exclude_structure']:
                        config['exclude_structure'][key] = user_config['exclude_structure'][key] or []
            
            return config
        except Exception as e:
            self.logger.warning(f"Errore nel caricamento della configurazione: {str(e)}. Uso configurazione di default.")
            return self.DEFAULT_CONFIG

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
    
    def _is_utf8(self, file_path: Path) -> bool:
        """
        Verifica se un file è codificato in UTF-8.
        """
        try:
            with open(file_path, 'rb') as f:
                f.read().decode('utf-8')
            return True
        except UnicodeDecodeError:
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
                    if item.name in self.config['exclude_structure']['directories']:
                        self.logger.debug(f"Directory ignorata: {item}")
                        continue
                    _scan(item)
                elif item.is_file():
                    if self._should_ignore_file(item):
                        self.logger.debug(f"File ignorato (config): {item}")
                        continue
                    if not self._is_utf8(item):
                        self.logger.debug(f"File ignorato (non UTF-8): {item}")
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