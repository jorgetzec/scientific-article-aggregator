"""
Clase base para todos los harvesters de APIs científicas
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..utils.logger import app_logger
from ..utils.database import Article


class BaseHarvester(ABC):
    """Clase base abstracta para todos los harvesters de APIs."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Inicializa el harvester base.
        
        Args:
            name: Nombre del harvester
            config: Configuración específica del harvester
        """
        self.name = name
        self.config = config
        self.base_url = config.get('base_url', '')
        self.rate_limit = config.get('rate_limit', 10)  # requests per minute
        self.last_request_time = 0
        
        # Configurar sesión HTTP con reintentos
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Headers comunes
        self.session.headers.update({
            'User-Agent': 'Scientific-Article-Aggregator/1.0 (https://github.com/user/scientific-article-aggregator)'
        })
        
        app_logger.info(f"Inicializado harvester: {self.name}")
    
    def _respect_rate_limit(self):
        """Respeta el límite de velocidad de la API."""
        if self.rate_limit <= 0:
            return
            
        time_since_last = time.time() - self.last_request_time
        min_interval = 60.0 / self.rate_limit  # segundos entre requests
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            app_logger.debug(f"Esperando {sleep_time:.2f}s para respetar rate limit")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, url: str, params: Dict[str, Any] = None, 
                     headers: Dict[str, str] = None) -> Optional[requests.Response]:
        """
        Realiza una petición HTTP respetando el rate limit.
        
        Args:
            url: URL de la petición
            params: Parámetros de la petición
            headers: Headers adicionales
            
        Returns:
            Respuesta HTTP o None si hay error
        """
        self._respect_rate_limit()
        
        try:
            if headers:
                session_headers = self.session.headers.copy()
                session_headers.update(headers)
            else:
                session_headers = self.session.headers
            
            response = self.session.get(
                url, 
                params=params, 
                headers=session_headers,
                timeout=30
            )
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            app_logger.error(f"Error en petición a {url}: {e}")
            return None
    
    @abstractmethod
    def search_articles(self, topics: List[str], 
                       date_range_days: int = 7,
                       max_results: int = 50) -> List[Article]:
        """
        Busca artículos en la API.
        
        Args:
            topics: Lista de temas de interés
            date_range_days: Días hacia atrás para buscar
            max_results: Número máximo de resultados
            
        Returns:
            Lista de artículos encontrados
        """
        pass
    
    @abstractmethod
    def get_article_details(self, article_id: str) -> Optional[Article]:
        """
        Obtiene los detalles completos de un artículo.
        
        Args:
            article_id: ID del artículo
            
        Returns:
            Artículo con detalles completos o None
        """
        pass
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Parsea una fecha desde string a datetime.
        
        Args:
            date_str: Fecha en formato string
            
        Returns:
            Objeto datetime o None si no se puede parsear
        """
        if not date_str:
            return None
            
        # Formatos comunes de fecha
        date_formats = [
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%d %b %Y',
            '%B %d, %Y',
            '%Y/%m/%d',
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        app_logger.warning(f"No se pudo parsear la fecha: {date_str}")
        return None
    
    def _clean_text(self, text: str) -> str:
        """
        Limpia y normaliza texto.
        
        Args:
            text: Texto a limpiar
            
        Returns:
            Texto limpio
        """
        if not text:
            return ""
        
        # Eliminar caracteres de control y espacios extra
        text = ' '.join(text.split())
        
        # Eliminar caracteres especiales problemáticos
        text = text.replace('\x00', '').replace('\r', ' ').replace('\n', ' ')
        
        return text.strip()
    
    def _extract_authors(self, authors_data: Any) -> List[str]:
        """
        Extrae lista de autores desde diferentes formatos.
        
        Args:
            authors_data: Datos de autores en formato variable
            
        Returns:
            Lista de nombres de autores
        """
        if not authors_data:
            return []
        
        authors = []
        
        if isinstance(authors_data, str):
            # Si es string, dividir por comas o "and"
            authors = [a.strip() for a in authors_data.replace(' and ', ', ').split(',')]
        elif isinstance(authors_data, list):
            for author in authors_data:
                if isinstance(author, str):
                    authors.append(author.strip())
                elif isinstance(author, dict):
                    # Extraer nombre del diccionario
                    name = author.get('name') or author.get('fullName') or \
                           f"{author.get('given', '')} {author.get('family', '')}".strip()
                    if name:
                        authors.append(name)
        
        return [a for a in authors if a]
    
    def _generate_article_id(self, source: str, identifier: str) -> str:
        """
        Genera un ID único para el artículo.
        
        Args:
            source: Fuente del artículo
            identifier: Identificador específico de la fuente
            
        Returns:
            ID único del artículo
        """
        return f"{source}:{identifier}"
    
    def get_name(self) -> str:
        """Retorna el nombre del harvester."""
        return self.name
    
    def get_config(self) -> Dict[str, Any]:
        """Retorna la configuración del harvester."""
        return self.config.copy()

