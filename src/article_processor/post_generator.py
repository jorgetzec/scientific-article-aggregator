"""
Generador de posts divulgativos estilo profesional
"""

import re
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

from ..utils.logger import app_logger
from ..utils.config_loader import config_loader
from ..utils.database import Article


class PostGenerator:
    """Generador de posts divulgativos estilo profesional."""
    
    def __init__(self):
        """Inicializa el generador de posts."""
        self.config = config_loader.get_text_processing_config()
        self.max_post_length = self.config.get('max_post_length', 1500)
        
    def generate_post(self, article: Article, summary: str = None) -> str:
        """
        Genera un post divulgativo profesional.
        
        Args:
            article: Artículo científico
            summary: Resumen del artículo (opcional)
            
        Returns:
            Post divulgativo generado
        """
        app_logger.info(f"Generando post para: {article.title[:50]}...")
        
        # Extraer información estructurada del artículo
        structured_info = self._extract_article_information(article, summary)
        
        # Estructura del post
        post_sections = []
        
        # 1. Título profesional
        title = self._create_professional_title(article.title, structured_info)
        post_sections.append(f"# {title}\n")
        
        # 2. Introducción
        introduction = self._create_introduction(structured_info)
        post_sections.append(f"{introduction}\n")
        
        # 3. Contexto y problema
        if structured_info['problem']:
            context = self._create_context_section(structured_info)
            post_sections.append(f"## Contexto y Desafío\n\n{context}\n")
        
        # 4. Metodología
        if structured_info['methodology']:
            methodology = self._create_methodology_section(structured_info)
            post_sections.append(f"## Metodología\n\n{methodology}\n")
        
        # 5. Resultados principales
        if structured_info['findings']:
            results = self._create_results_section(structured_info)
            post_sections.append(f"## Resultados Principales\n\n{results}\n")
        
        # 6. Implicaciones
        implications = self._create_implications_section(structured_info, article)
        if implications:
            post_sections.append(f"## Implicaciones\n\n{implications}\n")
        
        # 7. Conclusión
        conclusion = self._create_conclusion_section(structured_info)
        post_sections.append(f"## Conclusión\n\n{conclusion}\n")
        
        # 8. Referencias
        references = self._create_references_section(article)
        post_sections.append(f"---\n\n{references}")
        
        # Unir todas las secciones
        full_post = '\n'.join(post_sections)
        
        # Limitar longitud si es necesario
        if len(full_post.split()) > self.max_post_length:
            full_post = self._trim_post(full_post, self.max_post_length)
        
        app_logger.info(f"Post generado ({len(full_post.split())} palabras)")
        return full_post
    
    def _extract_article_information(self, article: Article, summary: str = None) -> Dict[str, str]:
        """
        Extrae información estructurada específica del artículo.
        
        Args:
            article: Artículo científico
            summary: Resumen del artículo
            
        Returns:
            Diccionario con información estructurada
        """
        # Combinar todo el texto disponible
        combined_text = ""
        if article.abstract:
            combined_text += article.abstract + " "
        if article.full_text:
            combined_text += article.full_text + " "
        if summary:
            combined_text += summary
        
        info = {
            'problem': '',
            'methodology': '',
            'findings': '',
            'key_metrics': '',
            'conclusions': '',
            'research_area': self._identify_research_area(article)
        }
        
        if combined_text:
            # Usar el mismo extractor que el summarizer
            from .summarizer import ArticleSummarizer
            summarizer = ArticleSummarizer()
            structured_data = summarizer._extract_structured_information(article.abstract, article.full_text)
            
            # Adaptar la información para el post
            info['problem'] = self._clean_text(structured_data.get('problem', ''))
            info['methodology'] = self._clean_text(structured_data.get('methodology', ''))
            info['findings'] = self._clean_text(structured_data.get('results', ''))
            info['key_metrics'] = self._format_metrics_for_post(structured_data.get('key_numbers', []))
            info['conclusions'] = self._clean_text(structured_data.get('conclusions', ''))
        
        return info
    
    def _clean_text(self, text: str) -> str:
        """Limpia y mejora el texto."""
        if not text:
            return ""
        
        # Remover texto duplicado
        text = re.sub(r'([^.]*?)(\1)+', r'\1', text)
        
        # Remover fragmentos incompletos
        text = re.sub(r'\b[A-Z][a-z]*\s*$', '', text)
        
        # Limpiar espacios extra
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Asegurar que termine con punto
        if text and not text.endswith('.'):
            text += '.'
        
        return text
    
    def _format_metrics_for_post(self, metrics: List[str]) -> str:
        """Formatea las métricas clave para el post."""
        if not metrics:
            return ""
        
        metrics_text = []
        for metric in metrics[:3]:  # Máximo 3 métricas
            if metric and len(metric.strip()) > 5:
                metrics_text.append(f"• {metric.strip()}")
        
        if metrics_text:
            return "\n".join(metrics_text)
        return ""
    
    def _create_professional_title(self, original_title: str, structured_info: Dict[str, str] = None) -> str:
        """
        Crea un título profesional.
        
        Args:
            original_title: Título original del artículo
            structured_info: Información estructurada del artículo
            
        Returns:
            Título profesional
        """
        if not original_title:
            return "Avance Científico Relevante"
        
        # Simplificar el título
        simplified = self._simplify_title(original_title)
        
        # Agregar contexto basado en el área de investigación
        research_area = structured_info.get('research_area', 'general') if structured_info else 'general'
        
        if research_area == 'bioinformatics':
            return f"Avance en Bioinformática: {simplified}"
        elif research_area == 'ai_ml':
            return f"Desarrollo en Inteligencia Artificial: {simplified}"
        elif research_area == 'plant_microbe':
            return f"Investigación en Interacciones Biológicas: {simplified}"
        elif research_area == 'education':
            return f"Estudio en Educación: {simplified}"
        else:
            return f"Investigación Científica: {simplified}"
    
    def _create_introduction(self, structured_info: Dict[str, str]) -> str:
        """Crea una introducción profesional."""
        if structured_info.get('findings'):
            return f"Un nuevo estudio ha revelado hallazgos significativos en el campo de la investigación científica. Los resultados obtenidos muestran {structured_info['findings'].lower()}, lo que representa un avance importante en nuestra comprensión del tema."
        else:
            return "Una investigación reciente ha abordado un desafío importante en el ámbito científico, proporcionando nuevas perspectivas y metodologías que podrían tener implicaciones significativas para el campo."
    
    def _create_context_section(self, structured_info: Dict[str, str]) -> str:
        """Crea la sección de contexto y problema."""
        problem = structured_info.get('problem', '')
        if problem:
            return f"El estudio aborda {problem.lower()} Esta investigación es particularmente relevante porque aborda una necesidad crítica en el campo y proporciona una base sólida para futuros desarrollos."
        else:
            return "La investigación se centra en un área de creciente importancia científica, donde los avances tecnológicos y metodológicos están abriendo nuevas posibilidades de estudio y aplicación."
    
    def _create_methodology_section(self, structured_info: Dict[str, str]) -> str:
        """Crea la sección de metodología."""
        methodology = structured_info.get('methodology', '')
        if methodology:
            return f"Los investigadores emplearon {methodology.lower()} Esta metodología fue seleccionada por su capacidad para proporcionar resultados confiables y reproducibles, asegurando la validez científica de los hallazgos."
        else:
            return "La metodología utilizada en este estudio combina técnicas establecidas con enfoques innovadores, permitiendo una evaluación comprehensiva de los datos y resultados obtenidos."
    
    def _create_results_section(self, structured_info: Dict[str, str]) -> str:
        """Crea la sección de resultados."""
        findings = structured_info.get('findings', '')
        metrics = structured_info.get('key_metrics', '')
        
        results_text = ""
        if findings:
            results_text += f"Los resultados principales del estudio indican que {findings.lower()}"
        
        if metrics:
            results_text += f"\n\nEntre los hallazgos más destacados se encuentran:\n{metrics}"
        
        if not results_text:
            results_text = "Los resultados obtenidos muestran patrones consistentes y estadísticamente significativos, confirmando la validez de las hipótesis planteadas y proporcionando evidencia sólida para las conclusiones del estudio."
        
        return results_text
    
    def _create_implications_section(self, structured_info: Dict[str, str], article: Article) -> str:
        """Crea la sección de implicaciones."""
        implications = []
        
        if structured_info.get('findings'):
            implications.append(f"Los hallazgos de esta investigación tienen implicaciones directas para el campo, ya que {structured_info['findings'].lower()}")
        
        if structured_info.get('methodology'):
            implications.append("La metodología desarrollada en este estudio puede ser aplicada a problemas similares en otras áreas de investigación, ampliando su impacto y utilidad.")
        
        research_area = structured_info.get('research_area', 'general')
        if research_area == 'bioinformatics':
            implications.append("Estos resultados contribuyen al desarrollo de herramientas y métodos más efectivos para el análisis de datos biológicos, con aplicaciones potenciales en medicina personalizada y biotecnología.")
        elif research_area == 'ai_ml':
            implications.append("Los avances metodológicos presentados en este trabajo pueden mejorar la eficiencia y precisión de sistemas de inteligencia artificial en diversas aplicaciones.")
        elif research_area == 'plant_microbe':
            implications.append("Esta investigación proporciona insights valiosos para el desarrollo de estrategias agrícolas más sostenibles y efectivas.")
        else:
            implications.append("Los resultados de este estudio establecen nuevas direcciones para la investigación futura y pueden influir en el desarrollo de políticas y prácticas en el campo.")
        
        return " ".join(implications)
    
    def _create_conclusion_section(self, structured_info: Dict[str, str]) -> str:
        """Crea la sección de conclusión."""
        conclusion_parts = []
        
        if structured_info.get('findings'):
            conclusion_parts.append(f"Este estudio demuestra que {structured_info['findings'].lower()}")
        
        conclusion_parts.append("Los resultados obtenidos representan un paso importante hacia una mejor comprensión de los fenómenos estudiados y abren nuevas posibilidades para investigaciones futuras.")
        
        research_area = structured_info.get('research_area', 'general')
        if research_area == 'bioinformatics':
            conclusion_parts.append("Esta investigación contribuye significativamente al campo de la bioinformática y establece bases sólidas para desarrollos tecnológicos futuros.")
        elif research_area == 'ai_ml':
            conclusion_parts.append("Los avances presentados en este trabajo marcan el camino hacia sistemas de inteligencia artificial más sofisticados y útiles.")
        else:
            conclusion_parts.append("La metodología y los hallazgos presentados en este estudio tienen el potencial de influir significativamente en el desarrollo del campo y sus aplicaciones prácticas.")
        
        return " ".join(conclusion_parts)
    
    def _create_references_section(self, article: Article) -> str:
        """Crea la sección de referencias."""
        references = []
        
        # Título del artículo original
        references.append(f"**Artículo original**: {article.title}")
        
        # Autores
        if article.authors:
            authors_str = ', '.join(article.authors[:3])
            if len(article.authors) > 3:
                authors_str += f" et al."
            references.append(f"**Autores**: {authors_str}")
        
        # Fuente
        references.append(f"**Fuente**: {article.source}")
        
        # Fecha de publicación
        if hasattr(article, 'publication_date') and article.publication_date:
            try:
                date_str = article.publication_date.strftime("%B %Y")
                references.append(f"**Fecha de publicación**: {date_str}")
            except:
                references.append(f"**Fecha de publicación**: {article.publication_date}")
        
        # URL del artículo
        if article.url:
            references.append(f"**Enlace**: [{article.url}]({article.url})")
        
        # Temas
        if article.topics:
            topics_str = ', '.join(article.topics[:3])
            references.append(f"**Temas**: {topics_str}")
        
        # Nota sobre divulgación
        references.append("**Nota**: Este es un resumen divulgativo basado en el artículo científico original. Para información técnica detallada, consulta la publicación completa.")
        
        return '\n\n'.join(references)
    
    def _identify_research_area(self, article) -> str:
        """Identifica el área de investigación del artículo."""
        text_to_analyze = f"{article.title} {article.abstract or ''}".lower()
        
        if any(term in text_to_analyze for term in ['bioinformatics', 'bioinformática', 'computational biology', 'genomics']):
            return 'bioinformatics'
        elif any(term in text_to_analyze for term in ['machine learning', 'deep learning', 'ai', 'artificial intelligence']):
            return 'ai_ml'
        elif any(term in text_to_analyze for term in ['plant', 'microbe', 'planta', 'microbio', 'interaction']):
            return 'plant_microbe'
        elif any(term in text_to_analyze for term in ['education', 'educación', 'teaching', 'learning']):
            return 'education'
        else:
            return 'general'
    
    def _simplify_title(self, title: str) -> str:
        """Simplifica un título técnico."""
        if not title:
            return "Investigación Científica"
        
        # Remover jerga muy técnica
        simplified = title
        
        # Reemplazos comunes
        replacements = {
            'bioinformatics': 'análisis de datos biológicos',
            'computational': 'computacional',
            'algorithm': 'método',
            'machine learning': 'aprendizaje automático',
            'deep learning': 'inteligencia artificial',
            'optimization': 'optimización',
            'analysis': 'análisis',
            'methodology': 'metodología',
            'framework': 'marco de trabajo'
        }
        
        for tech_term, simple_term in replacements.items():
            simplified = re.sub(tech_term, simple_term, simplified, flags=re.IGNORECASE)
        
        # Limitar longitud
        if len(simplified) > 80:
            simplified = simplified[:77] + "..."
        
        return simplified
    
    def _trim_post(self, post: str, max_words: int) -> str:
        """Recorta el post a un número máximo de palabras."""
        words = post.split()
        if len(words) <= max_words:
            return post
        
        # Mantener secciones completas
        sections = post.split('\n\n')
        trimmed_sections = []
        current_length = 0
        
        for section in sections:
            section_words = len(section.split())
            if current_length + section_words <= max_words:
                trimmed_sections.append(section)
                current_length += section_words
            else:
                break
        
        return '\n\n'.join(trimmed_sections) 