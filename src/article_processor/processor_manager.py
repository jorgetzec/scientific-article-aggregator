"""
Gestor de procesamiento de artículos que coordina extracción, resumen y generación de posts
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import os

from .text_extractor import TextExtractor
from .summarizer import ArticleSummarizer
from .post_generator import PostGenerator
from ..utils.database import db_manager, Article
from ..utils.logger import app_logger
from ..utils.config_loader import config_loader


class ArticleProcessorManager:
    """Gestor para coordinar el procesamiento completo de artículos."""
    
    def __init__(self):
        """Inicializa el gestor de procesamiento."""
        self.text_extractor = TextExtractor()
        self.summarizer = ArticleSummarizer()
        self.post_generator = PostGenerator()
        
        # Configuración
        self.config = config_loader.load_settings()
        self.output_config = self.config.get('output', {})
        self.markdown_dir = Path(self.output_config.get('markdown_dir', 'outputs/posts'))
        self.markdown_dir.mkdir(parents=True, exist_ok=True)
    
    def process_articles(self, article_ids: List[str] = None, 
                        max_articles: int = None,
                        generate_posts: bool = True,
                        save_markdown: bool = True) -> Dict[str, Any]:
        """
        Procesa artículos para generar resúmenes y posts.
        
        Args:
            article_ids: Lista específica de IDs de artículos a procesar
            max_articles: Número máximo de artículos a procesar
            generate_posts: Si generar posts divulgativos
            save_markdown: Si guardar posts en archivos markdown
            
        Returns:
            Diccionario con estadísticas del procesamiento
        """
        app_logger.info("Iniciando procesamiento de artículos")
        
        # Obtener artículos a procesar
        if article_ids:
            articles = [db_manager.get_article(aid) for aid in article_ids]
            articles = [a for a in articles if a is not None]
        else:
            articles = self._get_articles_to_process(max_articles)
        
        if not articles:
            app_logger.warning("No hay artículos para procesar")
            return {'processed': 0, 'summaries': 0, 'posts': 0, 'saved_files': 0}
        
        app_logger.info(f"Procesando {len(articles)} artículos")
        
        # Estadísticas
        stats = {
            'processed': 0,
            'summaries': 0,
            'posts': 0,
            'saved_files': 0,
            'errors': 0
        }
        
        # Procesar cada artículo
        for article in articles:
            try:
                result = self._process_single_article(
                    article, 
                    generate_posts=generate_posts,
                    save_markdown=save_markdown
                )
                
                # Actualizar estadísticas
                stats['processed'] += 1
                if result['summary_generated']:
                    stats['summaries'] += 1
                if result['post_generated']:
                    stats['posts'] += 1
                if result['file_saved']:
                    stats['saved_files'] += 1
                
                app_logger.info(f"Procesado: {article.title[:50]}...")
                
            except Exception as e:
                app_logger.error(f"Error procesando artículo {article.id}: {e}")
                stats['errors'] += 1
        
        app_logger.info(f"Procesamiento completado: {stats}")
        return stats
    
    def _process_single_article(self, article: Article,
                               generate_posts: bool = True,
                               save_markdown: bool = True) -> Dict[str, bool]:
        """
        Procesa un solo artículo.
        
        Args:
            article: Artículo a procesar
            generate_posts: Si generar posts divulgativos
            save_markdown: Si guardar en archivos markdown
            
        Returns:
            Diccionario con resultados del procesamiento
        """
        result = {
            'summary_generated': False,
            'post_generated': False,
            'file_saved': False
        }
        
        # 1. Extraer texto completo si no está disponible
        if not article.full_text and article.url:
            try:
                full_text = self.text_extractor.extract_full_text(article.url, article.doi)
                if full_text:
                    article.full_text = full_text
                    # Actualizar en la base de datos
                    db_manager.save_article(article)
                    app_logger.debug(f"Texto completo extraído para {article.id}")
            except Exception as e:
                app_logger.debug(f"No se pudo extraer texto completo para {article.id}: {e}")
        
        # 2. Generar resumen si no existe
        if not article.summary:
            try:
                summary = self.summarizer.generate_summary(
                    article.title,
                    article.abstract,
                    article.full_text
                )
                
                if summary:
                    article.summary = summary
                    result['summary_generated'] = True
                    app_logger.debug(f"Resumen generado para {article.id}")
            except Exception as e:
                app_logger.error(f"Error generando resumen para {article.id}: {e}")
        else:
            result['summary_generated'] = True
        
        # 3. Generar post divulgativo si se solicita
        if generate_posts and not article.post_content:
            try:
                post = self.post_generator.generate_post(article, article.summary)
                
                if post:
                    article.post_content = post
                    result['post_generated'] = True
                    app_logger.debug(f"Post generado para {article.id}")
            except Exception as e:
                app_logger.error(f"Error generando post para {article.id}: {e}")
        elif article.post_content:
            result['post_generated'] = True
        
        # 4. Guardar cambios en la base de datos
        if result['summary_generated'] or result['post_generated']:
            db_manager.save_article(article)
        
        # 5. Guardar archivo markdown si se solicita
        if save_markdown and article.post_content:
            try:
                file_saved = self._save_markdown_file(article)
                result['file_saved'] = file_saved
            except Exception as e:
                app_logger.error(f"Error guardando archivo markdown para {article.id}: {e}")
        
        return result
    
    def _get_articles_to_process(self, max_articles: int = None) -> List[Article]:
        """
        Obtiene artículos que necesitan procesamiento.
        
        Args:
            max_articles: Número máximo de artículos
            
        Returns:
            Lista de artículos a procesar
        """
        # Priorizar artículos sin resumen o post
        articles_needing_processing = []
        
        # Obtener artículos recientes
        recent_articles = db_manager.get_recent_articles(days=30, limit=max_articles or 100)
        
        for article in recent_articles:
            # Priorizar artículos que necesitan procesamiento
            if not article.summary or not article.post_content:
                articles_needing_processing.append(article)
        
        # Limitar si se especifica
        if max_articles:
            articles_needing_processing = articles_needing_processing[:max_articles]
        
        return articles_needing_processing
    
    def _save_markdown_file(self, article: Article) -> bool:
        """
        Guarda el post del artículo en un archivo markdown.
        
        Args:
            article: Artículo con post generado
            
        Returns:
            True si se guardó exitosamente
        """
        if not article.post_content:
            return False
        
        try:
            # Generar nombre de archivo seguro
            safe_title = self._create_safe_filename(article.title)
            date_str = datetime.now().strftime("%Y-%m-%d")
            filename = f"{date_str}_{safe_title}.md"
            
            file_path = self.markdown_dir / filename
            
            # Crear contenido del archivo
            file_content = self._create_markdown_file_content(article)
            
            # Guardar archivo
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_content)
            
            app_logger.info(f"Archivo markdown guardado: {file_path}")
            return True
            
        except Exception as e:
            app_logger.error(f"Error guardando archivo markdown: {e}")
            return False
    
    def _create_safe_filename(self, title: str) -> str:
        """
        Crea un nombre de archivo seguro desde un título.
        
        Args:
            title: Título del artículo
            
        Returns:
            Nombre de archivo seguro
        """
        import re
        
        # Tomar solo los primeros 50 caracteres
        safe_title = title[:50]
        
        # Reemplazar caracteres problemáticos
        safe_title = re.sub(r'[^\w\s-]', '', safe_title)
        safe_title = re.sub(r'[-\s]+', '-', safe_title)
        safe_title = safe_title.strip('-')
        
        return safe_title.lower()
    
    def _create_markdown_file_content(self, article: Article) -> str:
        """
        Crea el contenido completo del archivo markdown.
        
        Args:
            article: Artículo con post generado
            
        Returns:
            Contenido del archivo markdown
        """
        content_parts = []
        
        # Metadatos YAML front matter
        front_matter = [
            "---",
            f"title: \"{article.title}\"",
            f"date: {datetime.now().isoformat()}",
            f"source: {article.source}",
            f"url: {article.url}",
        ]
        
        if article.authors:
            authors_yaml = ', '.join([f'"{author}"' for author in article.authors[:3]])
            front_matter.append(f"authors: [{authors_yaml}]")
        
        if article.topics:
            topics_yaml = ', '.join([f'"{topic}"' for topic in article.topics[:5]])
            front_matter.append(f"topics: [{topics_yaml}]")
        
        if article.doi:
            front_matter.append(f"doi: {article.doi}")
        
        front_matter.append("---")
        front_matter.append("")
        
        content_parts.extend(front_matter)
        
        # Contenido del post
        content_parts.append(article.post_content)
        
        # Información adicional
        if self.output_config.get('include_metadata', True):
            content_parts.extend([
                "",
                "## Información Adicional",
                "",
                f"**Resumen técnico**: {article.summary or 'No disponible'}",
                "",
                f"**Abstract original**: {article.abstract or 'No disponible'}",
                "",
                f"**Generado**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"**Procesado por**: Scientific Article Aggregator v1.0"
            ])
        
        return '\n'.join(content_parts)
    
    def generate_daily_summary(self, date: datetime = None) -> str:
        """
        Genera un resumen diario de artículos procesados.
        
        Args:
            date: Fecha para el resumen (por defecto hoy)
            
        Returns:
            Resumen diario en formato markdown
        """
        if date is None:
            date = datetime.now()
        
        app_logger.info(f"Generando resumen diario para {date.strftime('%Y-%m-%d')}")
        
        # Obtener artículos del día
        articles = db_manager.get_recent_articles(days=1, limit=50)
        
        if not articles:
            return "No se procesaron artículos hoy."
        
        # Crear resumen
        summary_parts = [
            f"# Resumen Científico Diario - {date.strftime('%d de %B, %Y')}",
            "",
            f"Hoy se procesaron **{len(articles)} artículos** de diversas fuentes científicas.",
            ""
        ]
        
        # Agrupar por fuente
        by_source = {}
        for article in articles:
            if article.source not in by_source:
                by_source[article.source] = []
            by_source[article.source].append(article)
        
        summary_parts.append("## Artículos por Fuente")
        summary_parts.append("")
        
        for source, source_articles in by_source.items():
            summary_parts.append(f"### {source.title()} ({len(source_articles)} artículos)")
            summary_parts.append("")
            
            for article in source_articles[:3]:  # Máximo 3 por fuente
                summary_parts.append(f"- **{article.title}**")
                if article.summary:
                    summary_parts.append(f"  {article.summary[:100]}...")
                summary_parts.append("")
        
        # Temas más frecuentes
        all_topics = []
        for article in articles:
            all_topics.extend(article.topics)
        
        if all_topics:
            from collections import Counter
            topic_counts = Counter(all_topics)
            top_topics = topic_counts.most_common(5)
            
            summary_parts.extend([
                "## Temas Más Frecuentes",
                ""
            ])
            
            for topic, count in top_topics:
                summary_parts.append(f"- {topic}: {count} artículos")
            
            summary_parts.append("")
        
        # Estadísticas
        summary_parts.extend([
            "## Estadísticas",
            "",
            f"- Total de artículos procesados: {len(articles)}",
            f"- Fuentes consultadas: {len(by_source)}",
            f"- Artículos con resumen: {sum(1 for a in articles if a.summary)}",
            f"- Posts divulgativos generados: {sum(1 for a in articles if a.post_content)}",
            "",
            f"*Generado automáticamente el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        ])
        
        daily_summary = '\n'.join(summary_parts)
        
        # Guardar resumen diario
        if self.output_config.get('create_daily_summary', True):
            summary_filename = f"resumen_diario_{date.strftime('%Y-%m-%d')}.md"
            summary_path = self.markdown_dir / summary_filename
            
            try:
                with open(summary_path, 'w', encoding='utf-8') as f:
                    f.write(daily_summary)
                app_logger.info(f"Resumen diario guardado: {summary_path}")
            except Exception as e:
                app_logger.error(f"Error guardando resumen diario: {e}")
        
        return daily_summary
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del procesamiento de artículos.
        
        Returns:
            Diccionario con estadísticas
        """
        total_articles = db_manager.get_article_count()
        
        # Contar artículos con diferentes tipos de contenido
        # Nota: En una implementación real, esto requeriría consultas SQL más específicas
        # Por simplicidad, usamos una aproximación
        
        stats = {
            'total_articles': total_articles,
            'articles_with_summary': 0,
            'articles_with_posts': 0,
            'markdown_files': len(list(self.markdown_dir.glob('*.md'))),
            'sources': db_manager.get_sources_summary()
        }
        
        return stats


# Instancia global del gestor de procesamiento
processor_manager = ArticleProcessorManager()

