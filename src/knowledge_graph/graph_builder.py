"""
Constructor de knowledge graph para artículos científicos
"""

import networkx as nx
from typing import List, Dict, Any, Tuple
from collections import defaultdict, Counter
import re

from ..utils.database import db_manager, Article
from ..utils.logger import app_logger


class KnowledgeGraphBuilder:
    """Constructor de knowledge graph para artículos científicos."""
    
    def __init__(self):
        """Inicializa el constructor de knowledge graph."""
        self.graph = nx.Graph()
        self.topic_similarity_threshold = 0.3
        self.author_collaboration_weight = 2.0
        self.topic_weight = 1.0
        
    def build_graph(self, articles: List[Article] = None) -> nx.Graph:
        """
        Construye el knowledge graph a partir de los artículos.
        
        Args:
            articles: Lista de artículos (si no se proporciona, usa todos)
            
        Returns:
            Grafo de conocimiento construido
        """
        app_logger.info("Construyendo knowledge graph")
        
        if articles is None:
            articles = db_manager.get_recent_articles(days=365, limit=100)
        
        if not articles:
            app_logger.warning("No hay artículos para construir el grafo")
            return self.graph
        
        # Limpiar grafo anterior
        self.graph.clear()
        
        # Agregar nodos (artículos)
        self._add_article_nodes(articles)
        
        # Agregar conexiones por temas
        self._add_topic_connections(articles)
        
        # Agregar conexiones por autores
        self._add_author_connections(articles)
        
        # Agregar conexiones por fuente
        self._add_source_connections(articles)
        
        app_logger.info(f"Knowledge graph construido: {len(self.graph.nodes)} nodos, {len(self.graph.edges)} conexiones")
        
        return self.graph
    
    def _add_article_nodes(self, articles: List[Article]):
        """Agrega nodos de artículos al grafo."""
        for article in articles:
            # Crear identificador único
            node_id = f"article_{article.id}"
            
            # Agregar nodo con metadatos
            self.graph.add_node(
                node_id,
                type='article',
                title=article.title,
                source=article.source,
                authors=article.authors or [],
                topics=article.topics or [],
                url=article.url,
                publication_date=article.publication_date,
                summary=article.summary or "",
                node_size=self._calculate_node_size(article)
            )
    
    def _add_topic_connections(self, articles: List[Article]):
        """Agrega conexiones basadas en temas compartidos."""
        # Crear índice de artículos por tema
        topic_to_articles = defaultdict(list)
        
        for article in articles:
            node_id = f"article_{article.id}"
            for topic in article.topics or []:
                topic_to_articles[topic].append(node_id)
        
        # Conectar artículos que comparten temas
        for topic, article_nodes in topic_to_articles.items():
            if len(article_nodes) > 1:
                for i in range(len(article_nodes)):
                    for j in range(i + 1, len(article_nodes)):
                        node1, node2 = article_nodes[i], article_nodes[j]
                        
                        # Calcular peso de la conexión
                        weight = self._calculate_topic_weight(node1, node2, topic)
                        
                        if self.graph.has_edge(node1, node2):
                            # Incrementar peso existente
                            self.graph[node1][node2]['weight'] += weight
                            self.graph[node1][node2]['shared_topics'].append(topic)
                        else:
                            # Crear nueva conexión
                            self.graph.add_edge(
                                node1, node2,
                                type='topic_similarity',
                                weight=weight,
                                shared_topics=[topic]
                            )
    
    def _add_author_connections(self, articles: List[Article]):
        """Agrega conexiones basadas en autores compartidos."""
        # Crear índice de artículos por autor
        author_to_articles = defaultdict(list)
        
        for article in articles:
            node_id = f"article_{article.id}"
            for author in article.authors or []:
                author_to_articles[author].append(node_id)
        
        # Conectar artículos que comparten autores
        for author, article_nodes in author_to_articles.items():
            if len(article_nodes) > 1:
                for i in range(len(article_nodes)):
                    for j in range(i + 1, len(article_nodes)):
                        node1, node2 = article_nodes[i], article_nodes[j]
                        
                        weight = self.author_collaboration_weight
                        
                        if self.graph.has_edge(node1, node2):
                            # Incrementar peso existente
                            self.graph[node1][node2]['weight'] += weight
                            if 'shared_authors' not in self.graph[node1][node2]:
                                self.graph[node1][node2]['shared_authors'] = []
                            self.graph[node1][node2]['shared_authors'].append(author)
                        else:
                            # Crear nueva conexión
                            self.graph.add_edge(
                                node1, node2,
                                type='author_collaboration',
                                weight=weight,
                                shared_authors=[author]
                            )
    
    def _add_source_connections(self, articles: List[Article]):
        """Agrega conexiones débiles basadas en la misma fuente."""
        # Crear índice de artículos por fuente
        source_to_articles = defaultdict(list)
        
        for article in articles:
            node_id = f"article_{article.id}"
            source_to_articles[article.source].append(node_id)
        
        # Conectar artículos de la misma fuente (peso bajo)
        for source, article_nodes in source_to_articles.items():
            if len(article_nodes) > 1:
                # Solo conectar algunos artículos para evitar sobrecarga
                for i in range(min(5, len(article_nodes))):
                    for j in range(i + 1, min(i + 3, len(article_nodes))):
                        node1, node2 = article_nodes[i], article_nodes[j]
                        
                        # Solo agregar si no existe conexión más fuerte
                        if not self.graph.has_edge(node1, node2):
                            self.graph.add_edge(
                                node1, node2,
                                type='same_source',
                                weight=0.1,
                                source=source
                            )
    
    def _calculate_node_size(self, article: Article) -> float:
        """Calcula el tamaño del nodo basado en la importancia del artículo."""
        size = 10  # Tamaño base
        
        # Incrementar por número de autores
        if article.authors:
            size += len(article.authors) * 2
        
        # Incrementar por número de temas
        if article.topics:
            size += len(article.topics) * 3
        
        # Incrementar si tiene resumen
        if article.summary:
            size += 5
        
        return min(size, 50)  # Limitar tamaño máximo
    
    def _calculate_topic_weight(self, node1: str, node2: str, topic: str) -> float:
        """Calcula el peso de conexión por tema compartido."""
        # Peso base por tema
        weight = self.topic_weight
        
        # Incrementar peso para temas específicos importantes
        important_topics = [
            'bioinformatics', 'machine learning', 'deep learning',
            'computational biology', 'data analysis'
        ]
        
        if any(important in topic.lower() for important in important_topics):
            weight *= 1.5
        
        return weight
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del knowledge graph.
        
        Returns:
            Diccionario con estadísticas
        """
        if not self.graph.nodes:
            return {
                'nodes': 0,
                'edges': 0,
                'density': 0,
                'components': 0
            }
        
        stats = {
            'nodes': len(self.graph.nodes),
            'edges': len(self.graph.edges),
            'density': nx.density(self.graph),
            'components': nx.number_connected_components(self.graph)
        }
        
        # Estadísticas por tipo de conexión
        edge_types = defaultdict(int)
        for _, _, data in self.graph.edges(data=True):
            edge_types[data.get('type', 'unknown')] += 1
        
        stats['edge_types'] = dict(edge_types)
        
        # Top nodos por grado
        degrees = dict(self.graph.degree())
        top_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:5]
        
        stats['top_connected_articles'] = []
        for node_id, degree in top_nodes:
            if node_id in self.graph.nodes:
                node_data = self.graph.nodes[node_id]
                stats['top_connected_articles'].append({
                    'title': node_data.get('title', 'Unknown'),
                    'connections': degree,
                    'source': node_data.get('source', 'Unknown')
                })
        
        return stats
    
    def get_related_articles(self, article_id: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Obtiene artículos relacionados a un artículo específico.
        
        Args:
            article_id: ID del artículo
            max_results: Número máximo de resultados
            
        Returns:
            Lista de artículos relacionados con sus pesos
        """
        node_id = f"article_{article_id}"
        
        if node_id not in self.graph.nodes:
            return []
        
        # Obtener vecinos con sus pesos
        neighbors = []
        for neighbor in self.graph.neighbors(node_id):
            edge_data = self.graph[node_id][neighbor]
            node_data = self.graph.nodes[neighbor]
            
            neighbors.append({
                'article_id': neighbor.replace('article_', ''),
                'title': node_data.get('title', 'Unknown'),
                'source': node_data.get('source', 'Unknown'),
                'weight': edge_data.get('weight', 0),
                'connection_type': edge_data.get('type', 'unknown'),
                'shared_topics': edge_data.get('shared_topics', []),
                'shared_authors': edge_data.get('shared_authors', [])
            })
        
        # Ordenar por peso y retornar los mejores
        neighbors.sort(key=lambda x: x['weight'], reverse=True)
        return neighbors[:max_results]


# Instancia global del constructor de knowledge graph
graph_builder = KnowledgeGraphBuilder()

