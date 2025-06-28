"""
Harvester para la API de Europe PMC
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from .base_harvester import BaseHarvester
from ..utils.database import Article
from ..utils.logger import app_logger


class EuropePMCHarvester(BaseHarvester):
    """Harvester para la API de Europe PMC."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa el harvester de Europe PMC.
        
        Args:
            config: Configuración del harvester
        """
        super().__init__("Europe PMC", config)
        
        # Configurar email si está disponible
        email = config.get('email')
        if email:
            self.session.headers.update({'email': email})
    
    def search_articles(self, topics: List[str], 
                       date_range_days: int = 7,
                       max_results: int = 50) -> List[Article]:
        """
        Busca artículos en Europe PMC.
        
        Args:
            topics: Lista de temas de interés
            date_range_days: Días hacia atrás para buscar
            max_results: Número máximo de resultados
            
        Returns:
            Lista de artículos encontrados
        """
        articles = []
        
        # Construir consulta de búsqueda
        search_query = self._build_search_query(topics, date_range_days)
        
        app_logger.info(f"Buscando en Europe PMC: {search_query}")
        
        # URL del endpoint de búsqueda
        search_url = f"{self.base_url}/search"
        
        # Parámetros de la API
        params = {
            'query': search_query,
            'format': 'json',
            'pageSize': min(max_results, 100),  # Máximo 100 por página
            'sort': 'date desc',
            'resultType': 'core'
        }
        
        # Realizar petición
        response = self._make_request(search_url, params)
        if not response:
            return articles
        
        try:
            data = response.json()
            
            if 'resultList' in data and 'result' in data['resultList']:
                results = data['resultList']['result']
                
                for result in results:
                    article = self._parse_result(result)
                    if article:
                        articles.append(article)
                
                app_logger.info(f"Encontrados {len(articles)} artículos en Europe PMC")
            
        except json.JSONDecodeError as e:
            app_logger.error(f"Error parseando JSON de Europe PMC: {e}")
        
        return articles
    
    def get_article_details(self, article_id: str) -> Optional[Article]:
        """
        Obtiene los detalles completos de un artículo de Europe PMC.
        
        Args:
            article_id: ID del artículo (formato: europepmc:PMC123456 o europepmc:12345678)
            
        Returns:
            Artículo con detalles completos o None
        """
        # Extraer el ID de Europe PMC
        pmc_id = article_id.replace('europepmc:', '')
        
        # URL del endpoint de detalles
        details_url = f"{self.base_url}/{pmc_id}"
        
        params = {
            'format': 'json'
        }
        
        response = self._make_request(details_url, params)
        if not response:
            return None
        
        try:
            data = response.json()
            
            if 'resultList' in data and 'result' in data['resultList']:
                results = data['resultList']['result']
                if results:
                    return self._parse_result(results[0])
                    
        except json.JSONDecodeError as e:
            app_logger.error(f"Error parseando detalles de Europe PMC {pmc_id}: {e}")
        
        return None
    
    def _build_search_query(self, topics: List[str], date_range_days: int) -> str:
        """
        Construye la consulta de búsqueda para Europe PMC.
        
        Args:
            topics: Lista de temas de interés
            date_range_days: Días hacia atrás para buscar
            
        Returns:
            Consulta de búsqueda formateada
        """
        # Construir términos de búsqueda
        topic_queries = []
        
        for topic in topics:
            # Buscar en título y abstract
            topic_query = f'(TITLE:"{topic}" OR ABSTRACT:"{topic}")'
            topic_queries.append(topic_query)
        
        # Combinar temas con OR
        topics_query = ' OR '.join(topic_queries) if topic_queries else 'bioinformatics OR "computational biology"'
        
        # Agregar filtro de fecha
        if date_range_days > 0:
            cutoff_date = datetime.now() - timedelta(days=date_range_days)
            date_filter = f' AND FIRST_PDATE:[{cutoff_date.strftime("%Y-%m-%d")} TO {datetime.now().strftime("%Y-%m-%d")}]'
            topics_query += date_filter
        
        # Filtrar solo artículos de acceso abierto
        topics_query += ' AND OPEN_ACCESS:Y'
        
        return topics_query
    
    def _parse_result(self, result: Dict[str, Any]) -> Optional[Article]:
        """
        Parsea un resultado JSON de Europe PMC a un objeto Article.
        
        Args:
            result: Diccionario con los datos del resultado
            
        Returns:
            Objeto Article o None si hay error
        """
        try:
            # ID del artículo
            pmid = result.get('pmid')
            pmcid = result.get('pmcid')
            
            # Usar PMCID si está disponible, sino PMID
            if pmcid:
                identifier = pmcid
            elif pmid:
                identifier = pmid
            else:
                return None
            
            article_id = self._generate_article_id("europepmc", identifier)
            
            # Título
            title = self._clean_text(result.get('title', ''))
            
            # Abstract
            abstract = self._clean_text(result.get('abstractText', ''))
            
            # Autores
            authors = []
            if 'authorList' in result and 'author' in result['authorList']:
                for author in result['authorList']['author']:
                    full_name = author.get('fullName')
                    if full_name:
                        authors.append(full_name)
                    else:
                        # Construir nombre desde partes
                        first_name = author.get('firstName', '')
                        last_name = author.get('lastName', '')
                        if first_name or last_name:
                            authors.append(f"{first_name} {last_name}".strip())
            
            # Fecha de publicación
            publication_date = None
            first_pub_date = result.get('firstPublicationDate')
            if first_pub_date:
                publication_date = self._parse_date(first_pub_date)
            
            # URL
            url = ""
            if pmcid:
                url = f"https://europepmc.org/article/PMC/{pmcid.replace('PMC', '')}"
            elif pmid:
                url = f"https://europepmc.org/article/MED/{pmid}"
            
            # DOI
            doi = result.get('doi')
            
            # Fuente/Journal
            journal = result.get('journalInfo', {}).get('journal', {}).get('title', '')
            
            # Temas (usar MeSH terms si están disponibles)
            topics = []
            if 'meshHeadingList' in result and 'meshHeading' in result['meshHeadingList']:
                for mesh in result['meshHeadingList']['meshHeading']:
                    descriptor_name = mesh.get('descriptorName')
                    if descriptor_name:
                        topics.append(descriptor_name)
            
            # Si no hay MeSH terms, usar el journal como tema
            if not topics and journal:
                topics.append(journal)
            
            # Intentar obtener texto completo si está disponible
            full_text = None
            if result.get('hasTextMinedTerms') == 'Y' or result.get('isOpenAccess') == 'Y':
                full_text = self._get_full_text(identifier)
            
            return Article(
                id=article_id,
                title=title,
                authors=authors,
                abstract=abstract,
                source="europepmc",
                url=url,
                publication_date=publication_date,
                topics=topics,
                doi=doi,
                full_text=full_text
            )
            
        except Exception as e:
            app_logger.error(f"Error parseando resultado de Europe PMC: {e}")
            return None
    
    def _get_full_text(self, identifier: str) -> Optional[str]:
        """
        Intenta obtener el texto completo de un artículo.
        
        Args:
            identifier: ID del artículo (PMID o PMCID)
            
        Returns:
            Texto completo o None si no está disponible
        """
        try:
            # URL para texto completo
            fulltext_url = f"{self.base_url}/{identifier}/fullTextXML"
            
            response = self._make_request(fulltext_url)
            if response and response.status_code == 200:
                # Aquí se podría parsear el XML para extraer el texto
                # Por simplicidad, retornamos una indicación de que está disponible
                return "Full text available via Europe PMC API"
            
        except Exception as e:
            app_logger.debug(f"Texto completo no disponible para {identifier}: {e}")
        
        return None

