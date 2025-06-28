"""
Gestor de harvesters para coordinar la recolección de datos de múltiples APIs
"""

from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from .arxiv_harvester import ArxivHarvester
from .europepmc_harvester import EuropePMCHarvester
from .crossref_harvester import CrossrefHarvester
from .biorxiv_harvester import BioRxivHarvester
from ..utils.config_loader import config_loader
from ..utils.database import db_manager, Article
from ..utils.logger import app_logger


class HarvesterManager:
    """Gestor para coordinar múltiples harvesters de APIs científicas."""
    
    def __init__(self):
        """Inicializa el gestor de harvesters."""
        self.harvesters = {}
        self._initialize_harvesters()
    
    def _initialize_harvesters(self):
        """Inicializa todos los harvesters disponibles."""
        try:
            api_config = config_loader.load_api_keys()
            
            # Inicializar arXiv harvester
            if 'arxiv' in api_config:
                self.harvesters['arxiv'] = ArxivHarvester(api_config['arxiv'])
                app_logger.info("Harvester de arXiv inicializado")
            
            # Inicializar Europe PMC harvester
            if 'europepmc' in api_config:
                self.harvesters['europepmc'] = EuropePMCHarvester(api_config['europepmc'])
                app_logger.info("Harvester de Europe PMC inicializado")
            
            # Inicializar Crossref harvester
            if 'crossref' in api_config:
                self.harvesters['crossref'] = CrossrefHarvester(api_config['crossref'])
                app_logger.info("Harvester de Crossref inicializado")
            
            # Inicializar bioRxiv harvester
            if 'biorxiv' in api_config:
                self.harvesters['biorxiv'] = BioRxivHarvester(api_config['biorxiv'], 'biorxiv')
                app_logger.info("Harvester de bioRxiv inicializado")
            
            # Inicializar medRxiv harvester
            if 'medrxiv' in api_config:
                self.harvesters['medrxiv'] = BioRxivHarvester(api_config['medrxiv'], 'medrxiv')
                app_logger.info("Harvester de medRxiv inicializado")
            
            app_logger.info(f"Inicializados {len(self.harvesters)} harvesters")
            
        except Exception as e:
            app_logger.error(f"Error inicializando harvesters: {e}")
    
    def harvest_all_sources(self, topics: List[str], 
                           date_range_days: int = 7,
                           max_articles_per_source: int = 50,
                           sources: Optional[List[str]] = None,
                           parallel: bool = True) -> Dict[str, List[Article]]:
        """
        Recolecta artículos de todas las fuentes disponibles.
        
        Args:
            topics: Lista de temas de interés
            date_range_days: Días hacia atrás para buscar
            max_articles_per_source: Número máximo de artículos por fuente
            sources: Lista específica de fuentes a usar (None para usar todas)
            parallel: Si ejecutar en paralelo o secuencialmente
            
        Returns:
            Diccionario con artículos por fuente
        """
        results = {}
        
        # Determinar qué harvesters usar
        active_harvesters = self.harvesters.copy()
        if sources:
            active_harvesters = {k: v for k, v in self.harvesters.items() if k in sources}
        
        if not active_harvesters:
            app_logger.warning("No hay harvesters disponibles")
            return results
        
        app_logger.info(f"Iniciando recolección de {len(active_harvesters)} fuentes: {list(active_harvesters.keys())}")
        
        if parallel:
            results = self._harvest_parallel(active_harvesters, topics, date_range_days, max_articles_per_source)
        else:
            results = self._harvest_sequential(active_harvesters, topics, date_range_days, max_articles_per_source)
        
        # Guardar artículos en la base de datos
        total_saved = 0
        for source, articles in results.items():
            saved_count = 0
            for article in articles:
                if db_manager.save_article(article):
                    saved_count += 1
            
            app_logger.info(f"Guardados {saved_count}/{len(articles)} artículos de {source}")
            total_saved += saved_count
        
        app_logger.info(f"Recolección completada: {total_saved} artículos guardados en total")
        return results
    
    def _harvest_parallel(self, harvesters: Dict[str, Any], 
                         topics: List[str], 
                         date_range_days: int,
                         max_articles_per_source: int) -> Dict[str, List[Article]]:
        """
        Ejecuta la recolección en paralelo.
        
        Args:
            harvesters: Diccionario de harvesters a usar
            topics: Lista de temas de interés
            date_range_days: Días hacia atrás para buscar
            max_articles_per_source: Número máximo de artículos por fuente
            
        Returns:
            Diccionario con artículos por fuente
        """
        results = {}
        
        with ThreadPoolExecutor(max_workers=min(len(harvesters), 5)) as executor:
            # Enviar tareas
            future_to_source = {}
            for source, harvester in harvesters.items():
                future = executor.submit(
                    self._harvest_single_source,
                    source, harvester, topics, date_range_days, max_articles_per_source
                )
                future_to_source[future] = source
            
            # Recoger resultados
            for future in as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    articles = future.result()
                    results[source] = articles
                    app_logger.info(f"Completada recolección de {source}: {len(articles)} artículos")
                except Exception as e:
                    app_logger.error(f"Error en recolección de {source}: {e}")
                    results[source] = []
        
        return results
    
    def _harvest_sequential(self, harvesters: Dict[str, Any], 
                           topics: List[str], 
                           date_range_days: int,
                           max_articles_per_source: int) -> Dict[str, List[Article]]:
        """
        Ejecuta la recolección secuencialmente.
        
        Args:
            harvesters: Diccionario de harvesters a usar
            topics: Lista de temas de interés
            date_range_days: Días hacia atrás para buscar
            max_articles_per_source: Número máximo de artículos por fuente
            
        Returns:
            Diccionario con artículos por fuente
        """
        results = {}
        
        for source, harvester in harvesters.items():
            try:
                articles = self._harvest_single_source(
                    source, harvester, topics, date_range_days, max_articles_per_source
                )
                results[source] = articles
                app_logger.info(f"Completada recolección de {source}: {len(articles)} artículos")
                
                # Pequeña pausa entre fuentes para ser respetuoso con las APIs
                time.sleep(1)
                
            except Exception as e:
                app_logger.error(f"Error en recolección de {source}: {e}")
                results[source] = []
        
        return results
    
    def _harvest_single_source(self, source: str, harvester: Any, 
                              topics: List[str], 
                              date_range_days: int,
                              max_articles_per_source: int) -> List[Article]:
        """
        Recolecta artículos de una sola fuente.
        
        Args:
            source: Nombre de la fuente
            harvester: Instancia del harvester
            topics: Lista de temas de interés
            date_range_days: Días hacia atrás para buscar
            max_articles_per_source: Número máximo de artículos
            
        Returns:
            Lista de artículos recolectados
        """
        app_logger.info(f"Iniciando recolección de {source}")
        start_time = time.time()
        
        try:
            articles = harvester.search_articles(
                topics=topics,
                date_range_days=date_range_days,
                max_results=max_articles_per_source
            )
            
            elapsed_time = time.time() - start_time
            app_logger.info(f"Recolección de {source} completada en {elapsed_time:.2f}s: {len(articles)} artículos")
            
            return articles
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            app_logger.error(f"Error en recolección de {source} después de {elapsed_time:.2f}s: {e}")
            return []
    
    def get_available_sources(self) -> List[str]:
        """
        Obtiene la lista de fuentes disponibles.
        
        Returns:
            Lista de nombres de fuentes disponibles
        """
        return list(self.harvesters.keys())
    
    def get_harvester(self, source: str) -> Optional[Any]:
        """
        Obtiene un harvester específico.
        
        Args:
            source: Nombre de la fuente
            
        Returns:
            Instancia del harvester o None si no existe
        """
        return self.harvesters.get(source)
    
    def test_harvesters(self) -> Dict[str, bool]:
        """
        Prueba la conectividad de todos los harvesters.
        
        Returns:
            Diccionario con el estado de cada harvester
        """
        results = {}
        
        for source, harvester in self.harvesters.items():
            try:
                # Hacer una búsqueda simple para probar conectividad
                test_articles = harvester.search_articles(
                    topics=['test'],
                    date_range_days=1,
                    max_results=1
                )
                results[source] = True
                app_logger.info(f"Harvester {source}: OK")
                
            except Exception as e:
                results[source] = False
                app_logger.error(f"Harvester {source}: ERROR - {e}")
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de la base de datos por fuente.
        
        Returns:
            Diccionario con estadísticas
        """
        stats = {
            'total_articles': db_manager.get_article_count(),
            'sources': db_manager.get_sources_summary(),
            'available_harvesters': len(self.harvesters),
            'harvester_names': list(self.harvesters.keys())
        }
        
        return stats


# Instancia global del gestor de harvesters
harvester_manager = HarvesterManager()

