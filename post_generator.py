"""
Generador de posts divulgativos estilo Medium
"""

import re
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

from ..utils.logger import app_logger
from ..utils.config_loader import config_loader
from ..utils.database import Article


class PostGenerator:
    """Generador de posts divulgativos estilo Medium."""
    
    def __init__(self):
        """Inicializa el generador de posts."""
        self.config = config_loader.get_text_processing_config()
        self.max_post_length = self.config.get('max_post_length', 1500)
        self.casual_tone = self.config.get('casual_tone', True)
        
        # Plantillas para diferentes tipos de contenido
        self.templates = {
            'research_finding': [
                "¿Sabías que {finding}? Un nuevo estudio ha revelado {details}.",
                "Los investigadores han hecho un descubrimiento fascinante: {finding}. {details}",
                "La ciencia nos sorprende una vez más. {finding}, según muestra {details}."
            ],
            'methodology': [
                "Los científicos han desarrollado una nueva forma de {method}. {details}",
                "Una innovadora metodología permite {method}. {details}",
                "¿Cómo se puede {method}? Los investigadores han encontrado la respuesta: {details}"
            ],
            'application': [
                "Esta investigación podría cambiar la forma en que {application}. {details}",
                "Las implicaciones de este estudio son enormes para {application}. {details}",
                "Imagina un futuro donde {application}. Este estudio nos acerca a esa realidad: {details}"
            ]
        }
    
    def generate_post(self, article: Article, summary: str = None) -> str:
        """
        Genera un post divulgativo estilo Medium.
        
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
        
        # 1. Título atractivo
        catchy_title = self._create_catchy_title(article.title, structured_info)
        post_sections.append(f"# {catchy_title}\n")
        
        # 2. Hook inicial específico
        hook = self._create_specific_hook(structured_info)
        post_sections.append(f"{hook}\n")
        
        # 3. El problema que aborda
        if structured_info['problem']:
            post_sections.append(f"## El desafío\n\n{structured_info['problem']}\n")
        
        # 4. La metodología (cómo lo resolvieron)
        if structured_info['methodology']:
            post_sections.append(f"## Cómo lo abordaron\n\n{structured_info['methodology']}\n")
        
        # 5. Los hallazgos específicos
        if structured_info['findings']:
            post_sections.append(f"## Lo que descubrieron\n\n{structured_info['findings']}\n")
        
        # 6. Los números que importan
        if structured_info['key_metrics']:
            post_sections.append(f"## Los números clave\n\n{structured_info['key_metrics']}\n")
        
        # 7. Por qué es importante
        implications = self._create_specific_implications(structured_info, article)
        if implications:
            post_sections.append(f"## Por qué importa\n\n{implications}\n")
        
        # 8. Conclusión específica
        conclusion = self._create_specific_conclusion(structured_info)
        post_sections.append(f"## En resumen\n\n{conclusion}\n")
        
        # 9. Metadatos
        metadata = self._create_metadata_section(article)
        post_sections.append(f"---\n\n{metadata}")
        
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
            info['problem'] = self._format_problem_for_post(structured_data.get('problem', ''))
            info['methodology'] = self._format_methodology_for_post(structured_data.get('methodology', ''))
            info['findings'] = self._format_findings_for_post(structured_data.get('results', ''))
            info['key_metrics'] = self._format_metrics_for_post(structured_data.get('key_numbers', []))
            info['conclusions'] = structured_data.get('conclusions', '')
        
        return info
    
    def _format_problem_for_post(self, problem: str) -> str:
        """Formatea el problema para el post."""
        if not problem:
            return ""
        
        # Hacer más conversacional
        if problem.startswith("Los investigadores abordaron"):
            problem = problem.replace("Los investigadores abordaron", "")
        
        return f"Los científicos se enfrentaron a un desafío importante: {problem.strip()}. Este problema es crucial porque afecta directamente nuestra comprensión y capacidad de avanzar en el área."
    
    def _format_methodology_for_post(self, methodology: str) -> str:
        """Formatea la metodología para el post."""
        if not methodology:
            return ""
        
        return f"Para abordar este desafío, los investigadores {methodology}. Esta aproximación les permitió obtener datos confiables y resultados reproducibles."
    
    def _format_findings_for_post(self, findings: str) -> str:
        """Formatea los hallazgos para el post."""
        if not findings:
            return ""
        
        # Hacer más específico y emocionante
        findings_formatted = findings
        if findings.startswith("Los resultados mostraron que"):
            findings_formatted = findings.replace("Los resultados mostraron que", "")
        
        return f"Los hallazgos fueron reveladores: {findings_formatted.strip()}. Estos resultados representan un avance significativo en nuestra comprensión del tema."
    
    def _format_metrics_for_post(self, metrics: List[str]) -> str:
        """Formatea las métricas clave para el post."""
        if not metrics:
            return ""
        
        metrics_text = []
        for metric in metrics[:4]:  # Máximo 4 métricas
            metrics_text.append(f"• **{metric}**")
        
        intro = "Los números hablan por sí solos:" if len(metrics) > 1 else "El resultado clave:"
        return f"{intro}\n\n" + "\n".join(metrics_text)
    
    def _create_specific_hook(self, structured_info: Dict[str, str]) -> str:
        """
        Crea un hook específico basado en la información del artículo.
        
        Args:
            structured_info: Información estructurada del artículo
            
        Returns:
            Hook específico
        """
        # Usar los hallazgos más impactantes para el hook
        if structured_info['findings']:
            return f"**{structured_info['findings'].split('.')[0]}.**\n\nEsto es lo que acaba de descubrir un equipo de investigadores, y las implicaciones podrían cambiar nuestra perspectiva sobre el tema."
        
        elif structured_info['problem']:
            return f"**¿Qué pasaría si pudiéramos resolver {structured_info['problem'].lower()}?**\n\nUn nuevo estudio nos acerca a esa posibilidad con resultados que superan las expectativas."
        
        else:
            return "**La ciencia acaba de darnos una nueva perspectiva sobre un problema complejo.**\n\nLos resultados de esta investigación podrían cambiar la forma en que entendemos y abordamos desafíos importantes en el área."
    
    def _create_specific_implications(self, structured_info: Dict[str, str], article: Article) -> str:
        """
        Crea implicaciones específicas basadas en el contenido real del artículo.
        
        Args:
            structured_info: Información estructurada
            article: Artículo científico
            
        Returns:
            Implicaciones específicas
        """
        implications = []
        research_area = structured_info['research_area']
        
        # Implicaciones basadas en los hallazgos específicos
        if structured_info['findings']:
            if research_area == 'bioinformatics':
                implications.append(f"🧬 **Para la medicina personalizada**: {structured_info['findings']} podría llevar a tratamientos más precisos y efectivos.")
            elif research_area == 'ai_ml':
                implications.append(f"🤖 **Para la inteligencia artificial**: {structured_info['findings']} abre nuevas posibilidades en automatización y toma de decisiones.")
            elif research_area == 'plant_microbe':
                implications.append(f"🌱 **Para la agricultura**: {structured_info['findings']} podría mejorar la productividad y sostenibilidad de los cultivos.")
            else:
                implications.append(f"🔬 **Para la investigación**: {structured_info['findings']} establece nuevas bases para futuros estudios.")
        
        # Implicaciones basadas en la metodología
        if structured_info['methodology']:
            implications.append(f"⚙️ **Para la metodología científica**: La aproximación utilizada ({structured_info['methodology']}) podría aplicarse a problemas similares en otras áreas.")
        
        # Implicaciones basadas en las métricas
        if structured_info['key_metrics']:
            implications.append(f"📊 **Para la evaluación**: Las métricas obtenidas establecen nuevos estándares de referencia en el campo.")
        
        return '\n\n'.join(implications[:3])  # Máximo 3 implicaciones
    
    def _create_specific_conclusion(self, structured_info: Dict[str, str]) -> str:
        """
        Crea una conclusión específica basada en el contenido del artículo.
        
        Args:
            structured_info: Información estructurada
            
        Returns:
            Conclusión específica
        """
        conclusion_parts = []
        
        # Resumir el impacto principal
        if structured_info['findings']:
            conclusion_parts.append(f"Este estudio demuestra que {structured_info['findings'].lower()}")
        
        # Mencionar la metodología si es innovadora
        if structured_info['methodology'] and any(word in structured_info['methodology'].lower() for word in ['nuevo', 'innovador', 'primera vez', 'novel']):
            conclusion_parts.append(f"La metodología utilizada ({structured_info['methodology']}) representa un avance metodológico importante")
        
        # Perspectiva futura
        research_area = structured_info['research_area']
        if research_area == 'bioinformatics':
            conclusion_parts.append("abriendo nuevas posibilidades para la medicina de precisión")
        elif research_area == 'ai_ml':
            conclusion_parts.append("marcando el camino hacia sistemas más inteligentes y eficientes")
        elif research_area == 'plant_microbe':
            conclusion_parts.append("contribuyendo a una agricultura más sostenible y productiva")
        else:
            conclusion_parts.append("estableciendo nuevas direcciones para la investigación futura")
        
        if conclusion_parts:
            return '. '.join(conclusion_parts) + '.'
        else:
            return "Esta investigación representa un paso importante hacia una mejor comprensión de los desafíos complejos en su área, con implicaciones que se extenderán más allá del laboratorio."
    
    def _create_catchy_title(self, original_title: str, structured_info: Dict[str, str] = None) -> str:
        """
        Crea un título atractivo para el post.
        
        Args:
            original_title: Título original del artículo
            structured_info: Información estructurada del artículo
            
        Returns:
            Título atractivo
        """
        if not original_title:
            return "Un Descubrimiento Científico Fascinante"
        
        # Usar información específica si está disponible
        if structured_info and structured_info.get('findings'):
            # Crear título basado en los hallazgos
            findings = structured_info['findings']
            if 'reveladores' in findings:
                return f"🔬 Revelación: {self._simplify_title(original_title)}"
            elif any(word in findings.lower() for word in ['mejora', 'mejor', 'superior']):
                return f"💡 Breakthrough: {self._simplify_title(original_title)}"
            else:
                return f"🎯 Descubrimiento: {self._simplify_title(original_title)}"
        
        # Fallback al método original
        title_lower = original_title.lower()
        
        if any(term in title_lower for term in ['new', 'novel', 'first', 'nuevo', 'primera']):
            return f"🔬 Breakthrough: {self._simplify_title(original_title)}"
        elif any(term in title_lower for term in ['improve', 'better', 'enhance', 'mejor', 'mejora']):
            return f"💡 Innovación: {self._simplify_title(original_title)}"
        elif any(term in title_lower for term in ['discover', 'find', 'reveal', 'descubr', 'encontr']):
            return f"🎯 Descubrimiento: {self._simplify_title(original_title)}"
        elif any(term in title_lower for term in ['ai', 'machine learning', 'deep learning', 'inteligencia artificial']):
            return f"🤖 IA en Acción: {self._simplify_title(original_title)}"
        elif any(term in title_lower for term in ['plant', 'microbe', 'planta', 'microbio']):
            return f"🌱 Naturaleza: {self._simplify_title(original_title)}"
        else:
            return f"🔬 Ciencia: {self._simplify_title(original_title)}"

    def _identify_research_area(self, article) -> str:
        """
        Identifica el área de investigación del artículo.
        
        Args:
            article: Artículo científico
            
        Returns:
            Área de investigación identificada
        """
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
        """
        Simplifica un título técnico.
        
        Args:
            title: Título técnico
            
        Returns:
            Título simplificado
        """
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
            'analysis': 'análisis'
        }
        
        for tech_term, simple_term in replacements.items():
            simplified = re.sub(tech_term, simple_term, simplified, flags=re.IGNORECASE)
        
        # Limitar longitud
        if len(simplified) > 80:
            simplified = simplified[:77] + "..."
        
        return simplified


    def _create_metadata_section(self, article) -> str:
        """
        Crea la sección de metadatos.
        
        Args:
            article: Artículo científico
            
        Returns:
            Sección de metadatos
        """
        metadata_parts = []
        
        # Información del artículo
        metadata_parts.append(f"**📄 Artículo original**: [{article.title}]({article.url})")
        
        # Autores
        if article.authors:
            authors_str = ', '.join(article.authors[:3])  # Máximo 3 autores
            if len(article.authors) > 3:
                authors_str += f" y {len(article.authors) - 3} más"
            metadata_parts.append(f"**👥 Autores**: {authors_str}")
        
        # Fuente
        metadata_parts.append(f"**🔗 Fuente**: {article.source}")
        
        # Fecha
        if hasattr(article, 'publication_date') and article.publication_date:
            date_str = article.publication_date.strftime("%B %Y")
            metadata_parts.append(f"**📅 Publicado**: {date_str}")
        
        # Temas
        if article.topics:
            topics_str = ', '.join(article.topics[:3])
            metadata_parts.append(f"**🏷️ Temas**: {topics_str}")
        
        # Nota sobre divulgación
        metadata_parts.append("**ℹ️ Nota**: Este es un resumen divulgativo. Para detalles técnicos completos, consulta el artículo original.")
        
        return '\n\n'.join(metadata_parts)

