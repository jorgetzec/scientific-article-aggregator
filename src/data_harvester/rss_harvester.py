"""
Harvester para RSS feeds personalizados
"""

import feedparser
import requests
from datetime import datetime
from typing import List, Dict, Any
from ..utils.database import Article
from ..utils.logger import app_logger


class RSSHarvester:
    """Harvester para RSS feeds."""
    
    def __init__(self):
        """Inicializa el harvester RSS."""
        self.name = "rss"
    
    def harvest(self, rss_url: str, max_articles: int = 10) -> List[Article]:
        """
        Recolecta artículos de un RSS feed.
        
        Args:
            rss_url: URL del RSS feed
            max_articles: Número máximo de artículos a recolectar
            
        Returns:
            Lista de artículos recolectados
        """
        try:
            app_logger.info(f"Recolectando artículos de RSS: {rss_url}")
            
            # Parsear el RSS feed
            feed = feedparser.parse(rss_url)
            
            if feed.bozo:
                app_logger.warning(f"RSS feed malformado: {rss_url}")
                return []
            
            articles = []
            
            for entry in feed.entries[:max_articles]:
                try:
                    # Extraer información del artículo
                    title = entry.get('title', 'Sin título')
                    link = entry.get('link', '')
                    
                    # Extraer autores
                    authors = []
                    if hasattr(entry, 'authors') and entry.authors:
                        authors = [author.get('name', '') for author in entry.authors]
                    elif hasattr(entry, 'author'):
                        authors = [entry.author]
                    
                    # Extraer fecha
                    pub_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        pub_date = datetime(*entry.updated_parsed[:6])
                    
                    # Extraer resumen/abstract
                    abstract = ""
                    if hasattr(entry, 'summary'):
                        abstract = entry.summary
                    elif hasattr(entry, 'description'):
                        abstract = entry.description
                    
                    # Extraer contenido completo si está disponible
                    full_text = ""
                    if hasattr(entry, 'content') and entry.content:
                        full_text = entry.content[0].get('value', '')
                    
                    # Crear ID único
                    article_id = f"rss:{link.replace('://', '_').replace('/', '_').replace(':', '_')}"
                    
                    # Crear artículo
                    article = Article(
                        id=article_id,
                        title=title,
                        authors=authors,
                        abstract=abstract,
                        source="rss",
                        url=link,
                        publication_date=pub_date,
                        topics=[],  # RSS no suele tener temas predefinidos
                        full_text=full_text
                    )
                    
                    articles.append(article)
                    
                except Exception as e:
                    app_logger.error(f"Error procesando entrada RSS: {e}")
                    continue
            
            app_logger.info(f"Recolectados {len(articles)} artículos de RSS")
            return articles
            
        except Exception as e:
            app_logger.error(f"Error recolectando RSS {rss_url}: {e}")
            return []
    
    def validate_rss_url(self, rss_url: str) -> bool:
        """
        Valida si una URL de RSS es válida.
        
        Args:
            rss_url: URL del RSS feed
            
        Returns:
            True si es válido, False en caso contrario
        """
        try:
            # Verificar que la URL sea accesible
            response = requests.get(rss_url, timeout=10)
            if response.status_code != 200:
                return False
            
            # Intentar parsear el RSS
            feed = feedparser.parse(rss_url)
            return not feed.bozo and len(feed.entries) > 0
            
        except Exception as e:
            app_logger.error(f"Error validando RSS URL {rss_url}: {e}")
            return False


# Instancia global
rss_harvester = RSSHarvester() 