"""
Harvester para la API de arXiv
"""

import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from urllib.parse import quote

from .base_harvester import BaseHarvester
from ..utils.database import Article
from ..utils.logger import app_logger


class ArxivHarvester(BaseHarvester):
    """Harvester para la API de arXiv."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa el harvester de arXiv.
        
        Args:
            config: Configuración del harvester
        """
        super().__init__("arXiv", config)
        
        # Namespace para XML de arXiv
        self.namespaces = {
            'atom': 'http://www.w3.org/2005/Atom',
            'arxiv': 'http://arxiv.org/schemas/atom'
        }
    
    def search_articles(self, topics: List[str], 
                       date_range_days: int = 7,
                       max_results: int = 50) -> List[Article]:
        """
        Busca artículos en arXiv.
        
        Args:
            topics: Lista de temas de interés
            date_range_days: Días hacia atrás para buscar
            max_results: Número máximo de resultados
            
        Returns:
            Lista de artículos encontrados
        """
        articles = []
        
        # Construir consulta de búsqueda
        search_query = self._build_search_query(topics)
        
        app_logger.info(f"Buscando en arXiv: {search_query}")
        
        # Parámetros de la API
        params = {
            'search_query': search_query,
            'start': 0,
            'max_results': min(max_results, 100),  # arXiv limita a 100 por petición
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }
        
        # Realizar petición
        response = self._make_request(self.base_url, params)
        if not response:
            return articles
        
        # Parsear respuesta XML
        try:
            root = ET.fromstring(response.content)
            entries = root.findall('atom:entry', self.namespaces)
            
            for entry in entries:
                article = self._parse_entry(entry)
                if article and self._is_within_date_range(article.publication_date, date_range_days):
                    articles.append(article)
            
            app_logger.info(f"Encontrados {len(articles)} artículos en arXiv")
            
        except ET.ParseError as e:
            app_logger.error(f"Error parseando XML de arXiv: {e}")
        
        return articles
    
    def get_article_details(self, article_id: str) -> Optional[Article]:
        """
        Obtiene los detalles completos de un artículo de arXiv.
        
        Args:
            article_id: ID del artículo (formato: arxiv:1234.5678)
            
        Returns:
            Artículo con detalles completos o None
        """
        # Extraer el ID de arXiv
        arxiv_id = article_id.replace('arxiv:', '')
        
        params = {
            'id_list': arxiv_id,
            'max_results': 1
        }
        
        response = self._make_request(self.base_url, params)
        if not response:
            return None
        
        try:
            root = ET.fromstring(response.content)
            entries = root.findall('atom:entry', self.namespaces)
            
            if entries:
                return self._parse_entry(entries[0])
                
        except ET.ParseError as e:
            app_logger.error(f"Error parseando detalles de arXiv {arxiv_id}: {e}")
        
        return None
    
    def _build_search_query(self, topics: List[str]) -> str:
        """
        Construye la consulta de búsqueda para arXiv.
        
        Args:
            topics: Lista de temas de interés
            
        Returns:
            Consulta de búsqueda formateada
        """
        # Mapear temas a categorías de arXiv
        category_mapping = {
            'bioinformática': 'q-bio.QM OR cs.CE OR stat.AP',
            'bioinformatics': 'q-bio.QM OR cs.CE OR stat.AP',
            'computational biology': 'q-bio.QM OR cs.CE',
            'programación en biología': 'q-bio.QM OR cs.CE',
            'programming biology': 'q-bio.QM OR cs.CE',
            'análisis de datos biológicos': 'q-bio.QM OR stat.AP',
            'biological data analysis': 'q-bio.QM OR stat.AP',
            'interacción planta-microorganismos': 'q-bio.PE OR q-bio.MN',
            'plant-microbe interactions': 'q-bio.PE OR q-bio.MN',
            'plant microorganism': 'q-bio.PE OR q-bio.MN',
            'educación científica': 'physics.ed-ph',
            'scientific education': 'physics.ed-ph',
            'science education': 'physics.ed-ph',
            'divulgación científica': 'physics.soc-ph',
            'science communication': 'physics.soc-ph'
        }
        
        # Construir consulta combinando categorías y términos de búsqueda
        query_parts = []
        
        for topic in topics:
            topic_lower = topic.lower()
            
            # Buscar en categorías específicas si hay mapeo
            if topic_lower in category_mapping:
                query_parts.append(f"cat:({category_mapping[topic_lower]})")
            
            # También buscar en título y abstract
            topic_quoted = quote(topic)
            query_parts.append(f'ti:"{topic}" OR abs:"{topic}"')
        
        # Combinar con OR
        if query_parts:
            return ' OR '.join(f"({part})" for part in query_parts)
        else:
            # Consulta por defecto para biología computacional
            return 'cat:(q-bio.QM OR cs.CE OR stat.AP)'
    
    def _parse_entry(self, entry: ET.Element) -> Optional[Article]:
        """
        Parsea una entrada XML de arXiv a un objeto Article.
        
        Args:
            entry: Elemento XML de la entrada
            
        Returns:
            Objeto Article o None si hay error
        """
        try:
            # ID del artículo
            id_elem = entry.find('atom:id', self.namespaces)
            if id_elem is None:
                return None
            
            arxiv_id = id_elem.text.split('/')[-1]  # Extraer ID de la URL
            article_id = self._generate_article_id("arxiv", arxiv_id)
            
            # Título
            title_elem = entry.find('atom:title', self.namespaces)
            title = self._clean_text(title_elem.text) if title_elem is not None else ""
            
            # Abstract
            summary_elem = entry.find('atom:summary', self.namespaces)
            abstract = self._clean_text(summary_elem.text) if summary_elem is not None else ""
            
            # Autores
            authors = []
            author_elems = entry.findall('atom:author', self.namespaces)
            for author_elem in author_elems:
                name_elem = author_elem.find('atom:name', self.namespaces)
                if name_elem is not None:
                    authors.append(name_elem.text.strip())
            
            # Fecha de publicación
            published_elem = entry.find('atom:published', self.namespaces)
            publication_date = None
            if published_elem is not None:
                publication_date = self._parse_date(published_elem.text)
            
            # URL
            url = id_elem.text if id_elem is not None else ""
            
            # DOI (si está disponible)
            doi = None
            doi_elem = entry.find('arxiv:doi', self.namespaces)
            if doi_elem is not None:
                doi = doi_elem.text
            
            # Categorías como temas
            topics = []
            category_elems = entry.findall('atom:category', self.namespaces)
            for cat_elem in category_elems:
                term = cat_elem.get('term')
                if term:
                    topics.append(term)
            
            return Article(
                id=article_id,
                title=title,
                authors=authors,
                abstract=abstract,
                source="arxiv",
                url=url,
                publication_date=publication_date,
                topics=topics,
                doi=doi
            )
            
        except Exception as e:
            app_logger.error(f"Error parseando entrada de arXiv: {e}")
            return None
    
    def _is_within_date_range(self, pub_date: Optional[datetime], 
                             date_range_days: int) -> bool:
        """
        Verifica si la fecha de publicación está dentro del rango especificado.
        
        Args:
            pub_date: Fecha de publicación
            date_range_days: Días hacia atrás
            
        Returns:
            True si está dentro del rango
        """
        if not pub_date:
            return True  # Incluir si no hay fecha
        
        cutoff_date = datetime.now() - timedelta(days=date_range_days)
        return pub_date >= cutoff_date

