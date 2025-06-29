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
    saved: bool = False
    saved_at: Optional[datetime] = None


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
                    saved BOOLEAN DEFAULT 0,  -- Campo para marcar artículos guardados
                    saved_at TEXT,  -- Fecha cuando se guardó
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Migrar base de datos existente si es necesario
            self._migrate_database(cursor)
            
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
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_saved ON articles(saved)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_relationships_article ON relationships(article_id)')
            
            conn.commit()
    
    def _migrate_database(self, cursor):
        """Migra la base de datos existente para agregar nuevas columnas."""
        try:
            # Verificar si las columnas saved y saved_at existen
            cursor.execute("PRAGMA table_info(articles)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Agregar columna saved si no existe
            if 'saved' not in columns:
                cursor.execute('ALTER TABLE articles ADD COLUMN saved BOOLEAN DEFAULT 0')
                print("Columna 'saved' agregada a la tabla articles")
            
            # Agregar columna saved_at si no existe
            if 'saved_at' not in columns:
                cursor.execute('ALTER TABLE articles ADD COLUMN saved_at TEXT')
                print("Columna 'saved_at' agregada a la tabla articles")
                
        except Exception as e:
            print(f"Error en migración de base de datos: {e}")
    
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
                     topics, doi, full_text, summary, post_content, saved, saved_at, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article.id, article.title, authors_json, article.abstract,
                    article.source, article.url, pub_date_str, topics_json,
                    article.doi, article.full_text, article.summary,
                    article.post_content, getattr(article, 'saved', False),
                    getattr(article, 'saved_at', None), created_at_str, created_at_str
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
         topics_json, doi, full_text, summary, post_content, saved, saved_at, created_at, updated_at) = row
        
        # Convertir JSON a listas
        authors = json.loads(authors_json) if authors_json else []
        topics = json.loads(topics_json) if topics_json else []
        
        # Convertir fechas de forma segura
        def safe_parse_date(date_str):
            if not date_str:
                return None
            
            # Si es un número, no es una fecha válida
            if isinstance(date_str, (int, float)) or (isinstance(date_str, str) and date_str.isdigit()):
                print(f"Valor numérico encontrado donde se esperaba fecha: {date_str}")
                return None
            
            try:
                return datetime.fromisoformat(date_str)
            except (ValueError, TypeError):
                try:
                    # Intentar con formato alternativo
                    return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                except (ValueError, TypeError):
                    try:
                        # Intentar con formato de timestamp
                        if date_str.isdigit() and len(date_str) == 10:
                            return datetime.fromtimestamp(int(date_str))
                        elif date_str.isdigit() and len(date_str) == 13:
                            return datetime.fromtimestamp(int(date_str) / 1000)
                    except (ValueError, TypeError):
                        pass
                    
                    print(f"Error parseando fecha: {date_str} (tipo: {type(date_str)})")
                    return None
        
        pub_date = safe_parse_date(pub_date_str)
        created_at_dt = safe_parse_date(created_at)
        updated_at_dt = safe_parse_date(updated_at)
        saved_at_dt = safe_parse_date(saved_at)
        
        article = Article(
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
        
        # Agregar campos adicionales
        article.saved = bool(saved)
        article.saved_at = saved_at_dt
        
        return article
    
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
    
    def delete_article(self, article_id: str) -> bool:
        """
        Elimina un artículo de la base de datos.
        
        Args:
            article_id: ID del artículo a eliminar
            
        Returns:
            True si se eliminó exitosamente, False en caso contrario
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM articles WHERE id = ?', (article_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error al eliminar artículo {article_id}: {e}")
            return False
    
    def delete_old_articles(self, days_old: int = 30) -> int:
        """
        Elimina artículos más antiguos que el número de días especificado.
        
        Args:
            days_old: Número de días de antigüedad para eliminar
            
        Returns:
            Número de artículos eliminados
        """
        try:
            from datetime import timedelta
            cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM articles WHERE publication_date < ?', (cutoff_date,))
                deleted_count = cursor.rowcount
                conn.commit()
                return deleted_count
        except Exception as e:
            print(f"Error al eliminar artículos antiguos: {e}")
            return 0
    
    def clear_database(self) -> bool:
        """
        Limpia completamente la base de datos eliminando todos los datos.
        
        Returns:
            True si se limpió exitosamente, False en caso contrario
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Eliminar todos los datos de las tablas
                cursor.execute('DELETE FROM relationships')
                cursor.execute('DELETE FROM entities')
                cursor.execute('DELETE FROM articles')
                cursor.execute('DELETE FROM topics')
                
                # Reiniciar los contadores de auto-incremento
                cursor.execute('DELETE FROM sqlite_sequence')
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error al limpiar la base de datos: {e}")
            return False
    
    def get_saved_articles(self, limit: int = 100) -> List[Article]:
        """
        Obtiene artículos marcados como guardados.
        
        Args:
            limit: Número máximo de artículos a retornar
            
        Returns:
            Lista de artículos guardados
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM articles WHERE saved = 1 
                    ORDER BY saved_at DESC LIMIT ?
                ''', (limit,))
                
                rows = cursor.fetchall()
                return [self._row_to_article(row) for row in rows]
                
        except Exception as e:
            print(f"Error al obtener artículos guardados: {e}")
            return []
    
    def mark_article_as_saved(self, article_id: str) -> bool:
        """
        Marca un artículo como guardado.
        
        Args:
            article_id: ID del artículo
            
        Returns:
            True si se marcó exitosamente, False en caso contrario
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                saved_at = datetime.now().isoformat()
                cursor.execute('''
                    UPDATE articles SET saved = 1, saved_at = ?, updated_at = ?
                    WHERE id = ?
                ''', (saved_at, saved_at, article_id))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            print(f"Error al marcar artículo {article_id} como guardado: {e}")
            return False
    
    def unmark_article_as_saved(self, article_id: str) -> bool:
        """
        Desmarca un artículo como guardado.
        
        Args:
            article_id: ID del artículo
            
        Returns:
            True si se desmarcó exitosamente, False en caso contrario
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                updated_at = datetime.now().isoformat()
                cursor.execute('''
                    UPDATE articles SET saved = 0, saved_at = NULL, updated_at = ?
                    WHERE id = ?
                ''', (updated_at, article_id))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            print(f"Error al desmarcar artículo {article_id}: {e}")
            return False
    
    def clean_invalid_dates(self) -> int:
        """
        Limpia fechas inválidas en la base de datos (como años futuros).
        
        Returns:
            Número de registros corregidos
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Buscar fechas con años futuros o inválidos
                cursor.execute('''
                    SELECT id, publication_date FROM articles 
                    WHERE publication_date IS NOT NULL
                ''')
                
                rows = cursor.fetchall()
                corrected_count = 0
                
                for row in rows:
                    article_id, pub_date_str = row
                    
                    if not pub_date_str:
                        continue
                    
                    try:
                        # Intentar parsear la fecha
                        pub_date = datetime.fromisoformat(pub_date_str)
                        
                        # Verificar si el año es razonable (entre 1900 y año actual + 1)
                        current_year = datetime.now().year
                        if pub_date.year < 1900 or pub_date.year > current_year + 1:
                            # Corregir la fecha a None
                            cursor.execute('''
                                UPDATE articles SET publication_date = NULL 
                                WHERE id = ?
                            ''', (article_id,))
                            corrected_count += 1
                            print(f"Fecha corregida para artículo {article_id}: {pub_date_str} -> NULL")
                            
                    except (ValueError, TypeError):
                        # Si no se puede parsear, eliminar la fecha
                        cursor.execute('''
                            UPDATE articles SET publication_date = NULL 
                            WHERE id = ?
                        ''', (article_id,))
                        corrected_count += 1
                        print(f"Fecha inválida eliminada para artículo {article_id}: {pub_date_str}")
                
                conn.commit()
                return corrected_count
                
        except Exception as e:
            print(f"Error al limpiar fechas inválidas: {e}")
            return 0


# Instancia global del gestor de base de datos
db_manager = DatabaseManager()

