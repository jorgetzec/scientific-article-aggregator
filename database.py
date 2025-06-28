"""
Módulo de base de datos para Scientific Article Aggregator
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Article:
    """Clase para representar un artículo científico."""
    id: str
    title: str
    authors: List[str]
    abstract: str
    source: str
    url: str
    publication_date: datetime
    topics: List[str]
    doi: Optional[str] = None
    full_text: Optional[str] = None
    summary: Optional[str] = None
    post_content: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DatabaseManager:
    """Gestor de la base de datos SQLite."""
    
    def __init__(self, db_path: str = "data/articles.db"):
        """
        Inicializa el gestor de base de datos.
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Inicializa las tablas de la base de datos."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Tabla de artículos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS articles (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    authors TEXT NOT NULL,  -- JSON array
                    abstract TEXT,
                    source TEXT NOT NULL,
                    url TEXT,
                    publication_date TEXT,
                    topics TEXT,  -- JSON array
                    doi TEXT,
                    full_text TEXT,
                    summary TEXT,
                    post_content TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de entidades para el knowledge graph
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,  -- author, institution, concept, etc.
                    frequency INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de relaciones para el knowledge graph
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_entity_id INTEGER,
                    target_entity_id INTEGER,
                    relationship_type TEXT,
                    weight REAL DEFAULT 1.0,
                    article_id TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (source_entity_id) REFERENCES entities (id),
                    FOREIGN KEY (target_entity_id) REFERENCES entities (id),
                    FOREIGN KEY (article_id) REFERENCES articles (id)
                )
            ''')
            
            # Tabla de configuración de temas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    keywords TEXT,  -- JSON array
                    active BOOLEAN DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Índices para mejorar el rendimiento
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_date ON articles(publication_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_relationships_article ON relationships(article_id)')
            
            conn.commit()
    
    def save_article(self, article: Article) -> bool:
        """
        Guarda un artículo en la base de datos.
        
        Args:
            article: Instancia del artículo a guardar
            
        Returns:
            True si se guardó exitosamente, False en caso contrario
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Convertir listas a JSON
                authors_json = json.dumps(article.authors)
                topics_json = json.dumps(article.topics)
                
                # Convertir fechas a string
                pub_date_str = article.publication_date.isoformat() if article.publication_date else None
                created_at_str = datetime.now().isoformat()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO articles 
                    (id, title, authors, abstract, source, url, publication_date, 
                     topics, doi, full_text, summary, post_content, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article.id, article.title, authors_json, article.abstract,
                    article.source, article.url, pub_date_str, topics_json,
                    article.doi, article.full_text, article.summary,
                    article.post_content, created_at_str, created_at_str
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error al guardar artículo {article.id}: {e}")
            return False
    
    def get_article(self, article_id: str) -> Optional[Article]:
        """
        Obtiene un artículo por su ID.
        
        Args:
            article_id: ID del artículo
            
        Returns:
            Instancia del artículo o None si no se encuentra
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM articles WHERE id = ?', (article_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_article(row)
                return None
                
        except Exception as e:
            print(f"Error al obtener artículo {article_id}: {e}")
            return None
    
    def get_articles_by_source(self, source: str, limit: int = 100) -> List[Article]:
        """
        Obtiene artículos por fuente.
        
        Args:
            source: Nombre de la fuente
            limit: Número máximo de artículos a retornar
            
        Returns:
            Lista de artículos
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM articles WHERE source = ? 
                    ORDER BY publication_date DESC LIMIT ?
                ''', (source, limit))
                
                rows = cursor.fetchall()
                return [self._row_to_article(row) for row in rows]
                
        except Exception as e:
            print(f"Error al obtener artículos de {source}: {e}")
            return []
    
    def get_recent_articles(self, days: int = 7, limit: int = 100) -> List[Article]:
        """
        Obtiene artículos recientes.
        
        Args:
            days: Número de días hacia atrás
            limit: Número máximo de artículos a retornar
            
        Returns:
            Lista de artículos recientes
        """
        try:
            from datetime import timedelta
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM articles 
                    WHERE publication_date >= ? 
                    ORDER BY publication_date DESC LIMIT ?
                ''', (cutoff_date, limit))
                
                rows = cursor.fetchall()
                return [self._row_to_article(row) for row in rows]
                
        except Exception as e:
            print(f"Error al obtener artículos recientes: {e}")
            return []
    
    def search_articles(self, query: str, limit: int = 50) -> List[Article]:
        """
        Busca artículos por texto.
        
        Args:
            query: Término de búsqueda
            limit: Número máximo de artículos a retornar
            
        Returns:
            Lista de artículos que coinciden con la búsqueda
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                search_term = f"%{query}%"
                cursor.execute('''
                    SELECT * FROM articles 
                    WHERE title LIKE ? OR abstract LIKE ? OR summary LIKE ?
                    ORDER BY publication_date DESC LIMIT ?
                ''', (search_term, search_term, search_term, limit))
                
                rows = cursor.fetchall()
                return [self._row_to_article(row) for row in rows]
                
        except Exception as e:
            print(f"Error al buscar artículos: {e}")
            return []
    
    def _row_to_article(self, row: Tuple) -> Article:
        """
        Convierte una fila de la base de datos a un objeto Article.
        
        Args:
            row: Fila de la base de datos
            
        Returns:
            Instancia de Article
        """
        (id, title, authors_json, abstract, source, url, pub_date_str,
         topics_json, doi, full_text, summary, post_content, created_at, updated_at) = row
        
        # Convertir JSON a listas
        authors = json.loads(authors_json) if authors_json else []
        topics = json.loads(topics_json) if topics_json else []
        
        # Convertir fechas
        pub_date = datetime.fromisoformat(pub_date_str) if pub_date_str else None
        created_at_dt = datetime.fromisoformat(created_at) if created_at else None
        updated_at_dt = datetime.fromisoformat(updated_at) if updated_at else None
        
        return Article(
            id=id,
            title=title,
            authors=authors,
            abstract=abstract,
            source=source,
            url=url,
            publication_date=pub_date,
            topics=topics,
            doi=doi,
            full_text=full_text,
            summary=summary,
            post_content=post_content,
            created_at=created_at_dt,
            updated_at=updated_at_dt
        )
    
    def get_article_count(self) -> int:
        """
        Obtiene el número total de artículos en la base de datos.
        
        Returns:
            Número total de artículos
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM articles')
                return cursor.fetchone()[0]
        except Exception as e:
            print(f"Error al contar artículos: {e}")
            return 0
    
    def get_sources_summary(self) -> Dict[str, int]:
        """
        Obtiene un resumen de artículos por fuente.
        
        Returns:
            Diccionario con el conteo de artículos por fuente
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT source, COUNT(*) FROM articles GROUP BY source')
                return dict(cursor.fetchall())
        except Exception as e:
            print(f"Error al obtener resumen de fuentes: {e}")
            return {}


# Instancia global del gestor de base de datos
db_manager = DatabaseManager()

