"""
Harvester para las APIs de bioRxiv y medRxiv
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from .base_harvester import BaseHarvester
from ..utils.database import Article
from ..utils.logger import app_logger


class BioRxivHarvester(BaseHarvester):
    """Harvester para las APIs de bioRxiv y medRxiv."""
    
    def __init__(self, config: Dict[str, Any], server: str = "biorxiv"):
        """
        Inicializa el harvester de bioRxiv/medRxiv.
        
        Args:
            config: Configuración del harvester
            server: Servidor a usar ("biorxiv" o "medrxiv")
        """
        self.server = server
        super().__init__(f"{server.title()}", config)
        
        # Ajustar base URL según el servidor
        if server == "medrxiv":
            self.base_url = config.get('medrxiv_base_url', 'https://api.medrxiv.org')
        else:
            self.base_url = config.get('biorxiv_base_url', 'https://api.biorxiv.org')
    
    def search_articles(self, topics: List[str], 
                       date_range_days: int = 7,
                       max_results: int = 50) -> List[Article]:
        """
        Busca artículos en bioRxiv/medRxiv.
        
        Args:
            topics: Lista de temas de interés
            date_range_days: Días hacia atrás para buscar
            max_results: Número máximo de resultados
            
        Returns:
            Lista de artículos encontrados
        """
        articles = []
        
        # Obtener artículos por rango de fechas
        end_date = datetime.now()
        start_date = end_date - timedelta(days=date_range_days)
        
        app_logger.info(f"Buscando en {self.server} desde {start_date.strftime('%Y-%m-%d')} hasta {end_date.strftime('%Y-%m-%d')}")
        
        # URL del endpoint de detalles por fecha
        details_url = f"{self.base_url}/details/{self.server}/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
        
        # Realizar petición
        response = self._make_request(details_url)
        if not response:
            return articles
        
        try:
            data = response.json()
            
            if 'collection' in data:
                collection = data['collection']
                
                # Filtrar por temas de interés
                filtered_articles = self._filter_by_topics(collection, topics)
                
                # Limitar resultados
                limited_articles = filtered_articles[:max_results]
                
                for item in limited_articles:
                    article = self._parse_item(item)
                    if article:
                        articles.append(article)
                
                app_logger.info(f"Encontrados {len(articles)} artículos en {self.server}")
            
        except json.JSONDecodeError as e:
            app_logger.error(f"Error parseando JSON de {self.server}: {e}")
        
        return articles
    
    def get_article_details(self, article_id: str) -> Optional[Article]:
        """
        Obtiene los detalles completos de un artículo de bioRxiv/medRxiv.
        
        Args:
            article_id: ID del artículo (formato: biorxiv:2023.01.01.123456 o medrxiv:2023.01.01.123456)
            
        Returns:
            Artículo con detalles completos o None
        """
        # Extraer el DOI del preprint
        preprint_doi = article_id.replace(f'{self.server}:', '')
        
        # URL del endpoint de detalles por DOI
        details_url = f"{self.base_url}/details/{self.server}/{preprint_doi}"
        
        response = self._make_request(details_url)
        if not response:
            return None
        
        try:
            data = response.json()
            
            if 'collection' in data and data['collection']:
                return self._parse_item(data['collection'][0])
                    
        except json.JSONDecodeError as e:
            app_logger.error(f"Error parseando detalles de {self.server} {preprint_doi}: {e}")
        
        return None
    
    def _filter_by_topics(self, collection: List[Dict[str, Any]], 
                         topics: List[str]) -> List[Dict[str, Any]]:
        """
        Filtra artículos por temas de interés.
        
        Args:
            collection: Lista de artículos
            topics: Lista de temas de interés
            
        Returns:
            Lista filtrada de artículos
        """
        if not topics:
            return collection
        
        filtered = []
        topics_lower = [topic.lower() for topic in topics]
        
        for item in collection:
            # Buscar en título y abstract
            title = item.get('title', '').lower()
            abstract = item.get('abstract', '').lower()
            category = item.get('category', '').lower()
            
            # Verificar si algún tema aparece en el contenido
            for topic in topics_lower:
                if (topic in title or 
                    topic in abstract or 
                    topic in category or
                    self._topic_matches_category(topic, category)):
                    filtered.append(item)
                    break
        
        return filtered
    
    def _topic_matches_category(self, topic: str, category: str) -> bool:
        """
        Verifica si un tema coincide con una categoría específica.
        
        Args:
            topic: Tema de interés
            category: Categoría del artículo
            
        Returns:
            True si hay coincidencia
        """
        # Mapeo de temas a categorías de bioRxiv/medRxiv
        topic_category_mapping = {
            'bioinformática': ['bioinformatics', 'computational biology', 'systems biology'],
            'bioinformatics': ['bioinformatics', 'computational biology', 'systems biology'],
            'computational biology': ['bioinformatics', 'computational biology', 'systems biology'],
            'programación en biología': ['bioinformatics', 'computational biology'],
            'programming biology': ['bioinformatics', 'computational biology'],
            'análisis de datos biológicos': ['bioinformatics', 'systems biology'],
            'biological data analysis': ['bioinformatics', 'systems biology'],
            'interacción planta-microorganismos': ['plant biology', 'microbiology', 'ecology'],
            'plant-microbe interactions': ['plant biology', 'microbiology', 'ecology'],
            'plant microorganism': ['plant biology', 'microbiology', 'ecology'],
            'educación científica': ['scientific communication and education'],
            'scientific education': ['scientific communication and education'],
            'science education': ['scientific communication and education'],
            'divulgación científica': ['scientific communication and education'],
            'science communication': ['scientific communication and education']
        }
        
        if topic in topic_category_mapping:
            for mapped_category in topic_category_mapping[topic]:
                if mapped_category in category:
                    return True
        
        return False
    
    def _parse_item(self, item: Dict[str, Any]) -> Optional[Article]:
        """
        Parsea un item JSON de bioRxiv/medRxiv a un objeto Article.
        
        Args:
            item: Diccionario con los datos del item
            
        Returns:
            Objeto Article o None si hay error
        """
        try:
            # DOI como identificador
            doi = item.get('doi')
            if not doi:
                return None
            
            article_id = self._generate_article_id(self.server, doi)
            
            # Título
            title = self._clean_text(item.get('title', ''))
            
            # Abstract
            abstract = self._clean_text(item.get('abstract', ''))
            
            # Autores
            authors = []
            authors_str = item.get('authors', '')
            if authors_str:
                # Los autores vienen separados por ';' o ','
                authors = [author.strip() for author in authors_str.replace(';', ',').split(',')]
                authors = [author for author in authors if author]
            
            # Fecha de publicación
            publication_date = None
            date_str = item.get('date')
            if date_str:
                publication_date = self._parse_date(date_str)
            
            # URL
            url = f"https://www.{self.server}.org/content/10.1101/{doi}"
            
            # Categoría como tema
            topics = []
            category = item.get('category')
            if category:
                topics.append(category)
            
            # Información adicional
            version = item.get('version', '1')
            
            return Article(
                id=article_id,
                title=title,
                authors=authors,
                abstract=abstract,
                source=self.server,
                url=url,
                publication_date=publication_date,
                topics=topics,
                doi=doi
            )
            
        except Exception as e:
            app_logger.error(f"Error parseando item de {self.server}: {e}")
            return None
    
    def get_latest_articles(self, max_results: int = 50) -> List[Article]:
        """
        Obtiene los artículos más recientes.
        
        Args:
            max_results: Número máximo de resultados
            
        Returns:
            Lista de artículos más recientes
        """
        # Usar los últimos 3 días para obtener artículos recientes
        return self.search_articles([], date_range_days=3, max_results=max_results)

