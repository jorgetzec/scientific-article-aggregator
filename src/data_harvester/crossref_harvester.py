"""
Harvester para la API de Crossref
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from .base_harvester import BaseHarvester
from ..utils.database import Article
from ..utils.logger import app_logger


class CrossrefHarvester(BaseHarvester):
    """Harvester para la API de Crossref."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa el harvester de Crossref.
        
        Args:
            config: Configuración del harvester
        """
        super().__init__("Crossref", config)
        
        # Configurar mailto para acceso prioritario
        mailto = config.get('mailto')
        if mailto:
            self.session.headers.update({'mailto': mailto})
    
    def search_articles(self, topics: List[str], 
                       date_range_days: int = 7,
                       max_results: int = 50) -> List[Article]:
        """
        Busca artículos en Crossref.
        
        Args:
            topics: Lista de temas de interés
            date_range_days: Días hacia atrás para buscar
            max_results: Número máximo de resultados
            
        Returns:
            Lista de artículos encontrados
        """
        articles = []
        
        # URL del endpoint de búsqueda
        search_url = f"{self.base_url}/works"
        
        # Construir consulta de búsqueda
        search_query = self._build_search_query(topics)
        
        app_logger.info(f"Buscando en Crossref: {search_query}")
        
        # Parámetros de la API
        params = {
            'query': search_query,
            'rows': min(max_results, 100),  # Máximo 100 por página
            'sort': 'published',
            'order': 'desc',
            'filter': self._build_date_filter(date_range_days)
        }
        
        # Realizar petición
        response = self._make_request(search_url, params)
        if not response:
            return articles
        
        try:
            data = response.json()
            
            if 'message' in data and 'items' in data['message']:
                items = data['message']['items']
                
                for item in items:
                    article = self._parse_item(item)
                    if article:
                        articles.append(article)
                
                app_logger.info(f"Encontrados {len(articles)} artículos en Crossref")
            
        except json.JSONDecodeError as e:
            app_logger.error(f"Error parseando JSON de Crossref: {e}")
        
        return articles
    
    def get_article_details(self, article_id: str) -> Optional[Article]:
        """
        Obtiene los detalles completos de un artículo de Crossref.
        
        Args:
            article_id: ID del artículo (formato: crossref:10.1234/example)
            
        Returns:
            Artículo con detalles completos o None
        """
        # Extraer el DOI
        doi = article_id.replace('crossref:', '')
        
        # URL del endpoint de detalles
        details_url = f"{self.base_url}/works/{doi}"
        
        response = self._make_request(details_url)
        if not response:
            return None
        
        try:
            data = response.json()
            
            if 'message' in data:
                return self._parse_item(data['message'])
                    
        except json.JSONDecodeError as e:
            app_logger.error(f"Error parseando detalles de Crossref {doi}: {e}")
        
        return None
    
    def _build_search_query(self, topics: List[str]) -> str:
        """
        Construye la consulta de búsqueda para Crossref.
        
        Args:
            topics: Lista de temas de interés
            
        Returns:
            Consulta de búsqueda formateada
        """
        # Combinar todos los temas en una consulta
        if topics:
            return ' OR '.join(f'"{topic}"' for topic in topics)
        else:
            return 'bioinformatics OR "computational biology"'
    
    def _build_date_filter(self, date_range_days: int) -> str:
        """
        Construye el filtro de fecha para Crossref.
        
        Args:
            date_range_days: Días hacia atrás para buscar
            
        Returns:
            Filtro de fecha formateado
        """
        if date_range_days <= 0:
            return ""
        
        cutoff_date = datetime.now() - timedelta(days=date_range_days)
        return f"from-pub-date:{cutoff_date.strftime('%Y-%m-%d')}"
    
    def _parse_item(self, item: Dict[str, Any]) -> Optional[Article]:
        """
        Parsea un item JSON de Crossref a un objeto Article.
        
        Args:
            item: Diccionario con los datos del item
            
        Returns:
            Objeto Article o None si hay error
        """
        try:
            # DOI como identificador
            doi = item.get('DOI')
            if not doi:
                return None
            
            article_id = self._generate_article_id("crossref", doi)
            
            # Título
            title = ""
            if 'title' in item and item['title']:
                title = self._clean_text(item['title'][0])
            
            # Abstract (si está disponible)
            abstract = ""
            if 'abstract' in item:
                abstract = self._clean_text(item['abstract'])
            
            # Autores
            authors = []
            if 'author' in item:
                for author in item['author']:
                    given = author.get('given', '')
                    family = author.get('family', '')
                    if given or family:
                        full_name = f"{given} {family}".strip()
                        authors.append(full_name)
            
            # Fecha de publicación
            publication_date = None
            if 'published-print' in item:
                date_parts = item['published-print'].get('date-parts', [[]])[0]
                if len(date_parts) >= 3:
                    try:
                        publication_date = datetime(date_parts[0], date_parts[1], date_parts[2])
                    except (ValueError, IndexError):
                        pass
            elif 'published-online' in item:
                date_parts = item['published-online'].get('date-parts', [[]])[0]
                if len(date_parts) >= 3:
                    try:
                        publication_date = datetime(date_parts[0], date_parts[1], date_parts[2])
                    except (ValueError, IndexError):
                        pass
            
            # URL
            url = item.get('URL', f"https://doi.org/{doi}")
            
            # Fuente/Journal
            source_info = "crossref"
            if 'container-title' in item and item['container-title']:
                source_info = item['container-title'][0]
            
            # Temas (usar subject si está disponible)
            topics = []
            if 'subject' in item:
                topics = item['subject']
            
            # Si no hay subjects, usar el tipo de contenido
            if not topics:
                content_type = item.get('type', 'article')
                topics.append(content_type)
            
            # Publisher como información adicional
            publisher = item.get('publisher', '')
            
            return Article(
                id=article_id,
                title=title,
                authors=authors,
                abstract=abstract,
                source="crossref",
                url=url,
                publication_date=publication_date,
                topics=topics,
                doi=doi
            )
            
        except Exception as e:
            app_logger.error(f"Error parseando item de Crossref: {e}")
            return None
    
    def get_journal_articles(self, journal_issn: str, 
                           date_range_days: int = 7,
                           max_results: int = 50) -> List[Article]:
        """
        Obtiene artículos de una revista específica por ISSN.
        
        Args:
            journal_issn: ISSN de la revista
            date_range_days: Días hacia atrás para buscar
            max_results: Número máximo de resultados
            
        Returns:
            Lista de artículos de la revista
        """
        articles = []
        
        # URL del endpoint de búsqueda
        search_url = f"{self.base_url}/works"
        
        # Parámetros de la API
        params = {
            'filter': f"issn:{journal_issn},{self._build_date_filter(date_range_days)}",
            'rows': min(max_results, 100),
            'sort': 'published',
            'order': 'desc'
        }
        
        # Realizar petición
        response = self._make_request(search_url, params)
        if not response:
            return articles
        
        try:
            data = response.json()
            
            if 'message' in data and 'items' in data['message']:
                items = data['message']['items']
                
                for item in items:
                    article = self._parse_item(item)
                    if article:
                        articles.append(article)
                
                app_logger.info(f"Encontrados {len(articles)} artículos de la revista {journal_issn}")
            
        except json.JSONDecodeError as e:
            app_logger.error(f"Error parseando JSON de Crossref para revista {journal_issn}: {e}")
        
        return articles

