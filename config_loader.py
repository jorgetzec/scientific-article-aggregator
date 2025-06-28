"""
Cargador de configuración para Scientific Article Aggregator
"""

import os
import yaml
from typing import Dict, Any
from pathlib import Path


class ConfigLoader:
    """Clase para cargar y gestionar la configuración de la aplicación."""
    
    def __init__(self, config_dir: str = None):
        """
        Inicializa el cargador de configuración.
        
        Args:
            config_dir: Directorio donde se encuentran los archivos de configuración
        """
        if config_dir is None:
            # Obtener el directorio raíz del proyecto
            project_root = Path(__file__).parent.parent.parent
            config_dir = project_root / "config"
        
        self.config_dir = Path(config_dir)
        self._settings = None
        self._api_keys = None
    
    def load_settings(self) -> Dict[str, Any]:
        """
        Carga la configuración principal desde settings.yaml.
        
        Returns:
            Diccionario con la configuración
        """
        if self._settings is None:
            settings_path = self.config_dir / "settings.yaml"
            
            if not settings_path.exists():
                raise FileNotFoundError(f"No se encontró el archivo de configuración: {settings_path}")
            
            with open(settings_path, 'r', encoding='utf-8') as file:
                self._settings = yaml.safe_load(file)
        
        return self._settings
    
    def load_api_keys(self) -> Dict[str, Any]:
        """
        Carga las claves de API desde api_keys.yaml.
        
        Returns:
            Diccionario con las claves de API
        """
        if self._api_keys is None:
            api_keys_path = self.config_dir / "api_keys.yaml"
            
            if not api_keys_path.exists():
                # Intentar cargar desde variables de entorno
                self._api_keys = self._load_from_env()
            else:
                with open(api_keys_path, 'r', encoding='utf-8') as file:
                    self._api_keys = yaml.safe_load(file)
        
        return self._api_keys
    
    def _load_from_env(self) -> Dict[str, Any]:
        """
        Carga las claves de API desde variables de entorno.
        
        Returns:
            Diccionario con las claves de API desde variables de entorno
        """
        return {
            'lens': {
                'api_key': os.getenv('LENS_API_KEY'),
                'base_url': os.getenv('LENS_BASE_URL', 'https://api.lens.org')
            },
            'ieee': {
                'api_key': os.getenv('IEEE_API_KEY'),
                'base_url': os.getenv('IEEE_BASE_URL', 'https://ieeexploreapi.ieee.org')
            },
            'arxiv': {
                'base_url': os.getenv('ARXIV_BASE_URL', 'http://export.arxiv.org/api/query'),
                'max_results': int(os.getenv('ARXIV_MAX_RESULTS', '100'))
            },
            'europepmc': {
                'base_url': os.getenv('EUROPEPMC_BASE_URL', 'https://www.ebi.ac.uk/europepmc/webservices/rest'),
                'email': os.getenv('EUROPEPMC_EMAIL')
            },
            'doaj': {
                'base_url': os.getenv('DOAJ_BASE_URL', 'https://doaj.org/api/v2')
            },
            'biorxiv': {
                'base_url': os.getenv('BIORXIV_BASE_URL', 'https://api.biorxiv.org')
            },
            'medrxiv': {
                'base_url': os.getenv('MEDRXIV_BASE_URL', 'https://api.medrxiv.org')
            },
            'crossref': {
                'base_url': os.getenv('CROSSREF_BASE_URL', 'https://api.crossref.org'),
                'mailto': os.getenv('CROSSREF_MAILTO')
            }
        }
    
    def get_topic_list(self) -> list:
        """
        Obtiene la lista de temas de interés.
        
        Returns:
            Lista de temas de interés
        """
        settings = self.load_settings()
        return settings.get('topics', [])
    
    def get_search_config(self) -> Dict[str, Any]:
        """
        Obtiene la configuración de búsqueda.
        
        Returns:
            Diccionario con la configuración de búsqueda
        """
        settings = self.load_settings()
        return settings.get('search', {})
    
    def get_text_processing_config(self) -> Dict[str, Any]:
        """
        Obtiene la configuración de procesamiento de texto.
        
        Returns:
            Diccionario con la configuración de procesamiento de texto
        """
        settings = self.load_settings()
        return settings.get('text_processing', {})
    
    def get_database_config(self) -> Dict[str, Any]:
        """
        Obtiene la configuración de la base de datos.
        
        Returns:
            Diccionario con la configuración de la base de datos
        """
        settings = self.load_settings()
        return settings.get('database', {})


# Instancia global del cargador de configuración
config_loader = ConfigLoader()

