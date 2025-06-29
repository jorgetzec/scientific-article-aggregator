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
        
        # Guardar el artículo como atributo para acceso en otros métodos
        self.article = article
        
        # Extraer información estructurada del artículo
        structured_info = self._extract_article_information(article, summary)
        
        # Verificar que tenemos suficiente información
        if not self._has_sufficient_content(structured_info, article):
            app_logger.warning(f"Contenido insuficiente para generar post para: {article.title}")
            return self._generate_minimal_post(article)
        
        # Estructura del post
        post_sections = []
        
        # 1. Título profesional
        title = self._create_professional_title(article.title, structured_info)
        post_sections.append(f"# {title}\n")
        
        # 2. Introducción específica
        introduction = self._create_introduction(structured_info, article)
        post_sections.append(f"{introduction}\n")
        
        # 3. Contexto y problema específico
        if structured_info['problem']:
            context = self._create_specific_context_section(structured_info, article)
            post_sections.append(f"## Contexto y Desafío\n\n{context}\n")
        
        # 4. Metodología específica
        if structured_info['methodology']:
            methodology = self._create_specific_methodology_section(structured_info, article)
            post_sections.append(f"## Metodología\n\n{methodology}\n")
        
        # 5. Resultados específicos
        if structured_info['findings']:
            results = self._create_specific_results_section(structured_info, article)
            post_sections.append(f"## Resultados Principales\n\n{results}\n")
        
        # 6. Implicaciones específicas
        implications = self._create_specific_implications_section(structured_info, article)
        if implications:
            post_sections.append(f"## Implicaciones\n\n{implications}\n")
        
        # 7. Conclusión específica
        conclusion = self._create_specific_conclusion_section(structured_info, article)
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
    
    def _has_sufficient_content(self, structured_info: Dict[str, str], article: Article) -> bool:
        """Verifica si hay suficiente contenido para generar un post útil."""
        # Verificar que tenemos al menos título y abstract
        if not article.title or not article.abstract:
            return False
        
        # Verificar que tenemos al menos algunos hallazgos o metodología
        has_findings = bool(structured_info.get('findings', '').strip())
        has_methodology = bool(structured_info.get('methodology', '').strip())
        has_problem = bool(structured_info.get('problem', '').strip())
        
        return has_findings or has_methodology or has_problem
    
    def _generate_minimal_post(self, article: Article) -> str:
        """Genera un post mínimo cuando no hay suficiente contenido."""
        post_parts = [
            f"# {article.title}",
            "",
            "## Resumen",
            "",
            article.abstract or "Resumen no disponible",
            "",
            "## Información del Artículo",
            "",
            f"**Autores**: {', '.join(article.authors) if article.authors else 'No especificados'}",
            f"**Fuente**: {article.source}",
            f"**Fecha**: {article.publication_date.strftime('%B %Y') if article.publication_date else 'No especificada'}",
            "",
            "**Nota**: Este artículo requiere procesamiento adicional para generar un análisis más detallado.",
            "",
            "---",
            "",
            self._create_references_section(article)
        ]
        
        return '\n'.join(post_parts)
    
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
    
    def _create_introduction(self, structured_info: Dict[str, str], article: Article) -> str:
        """Crea una introducción específica basada en el contenido real."""
        introduction_parts = []
        
        # Usar el título para contextualizar
        if article.title:
            title_keywords = self._extract_keywords_from_title(article.title)
            if title_keywords:
                introduction_parts.append(f"La investigación titulada \"{article.title}\" aborda aspectos fundamentales de {', '.join(title_keywords[:2])}.")
        
        # Usar el problema identificado
        if structured_info.get('problem'):
            problem = structured_info['problem']
            introduction_parts.append(f"El estudio se centra en {problem.lower()}")
        
        # Usar los hallazgos principales
        if structured_info.get('findings'):
            findings = structured_info['findings']
            introduction_parts.append(f"Los resultados obtenidos revelan que {findings.lower()}")
        
        # Si no tenemos información específica, usar el abstract
        if not introduction_parts and article.abstract:
            abstract_start = article.abstract[:200] + "..." if len(article.abstract) > 200 else article.abstract
            introduction_parts.append(abstract_start)
        
        if introduction_parts:
            return " ".join(introduction_parts)
        else:
            return "Esta investigación científica presenta hallazgos relevantes en su campo de estudio."
    
    def _create_specific_context_section(self, structured_info: Dict[str, str], article: Article) -> str:
        """Crea la sección de contexto específica."""
        context_parts = []
        
        if structured_info.get('problem'):
            problem = structured_info['problem']
            context_parts.append(f"El estudio aborda {problem.lower()}")
            
            # Agregar contexto adicional basado en el área de investigación
            research_area = structured_info.get('research_area', 'general')
            if research_area == 'bioinformatics':
                context_parts.append("Esta investigación es particularmente relevante en el contexto actual de la bioinformática, donde la necesidad de herramientas computacionales eficientes para el análisis de datos biológicos es cada vez más crítica.")
            elif research_area == 'ai_ml':
                context_parts.append("En el campo de la inteligencia artificial y el aprendizaje automático, este tipo de investigación contribuye al desarrollo de algoritmos más eficientes y precisos.")
            elif research_area == 'plant_microbe':
                context_parts.append("La comprensión de las interacciones entre plantas y microorganismos es fundamental para el desarrollo de estrategias agrícolas sostenibles.")
        
        # Si no tenemos problema específico, usar el abstract
        if not context_parts and article.abstract:
            abstract_sentences = article.abstract.split('.')
            if len(abstract_sentences) > 1:
                context_parts.append(abstract_sentences[0] + ".")
        
        if context_parts:
            return " ".join(context_parts)
        else:
            return "La investigación se centra en un área de creciente importancia científica, abordando desafíos metodológicos y conceptuales relevantes para el campo."
    
    def _create_specific_methodology_section(self, structured_info: Dict[str, str], article: Article) -> str:
        """Crea la sección de metodología específica."""
        if structured_info.get('methodology'):
            methodology = structured_info['methodology']
            return f"Los investigadores emplearon {methodology.lower()} Esta metodología fue seleccionada por su capacidad para abordar específicamente los objetivos del estudio y proporcionar resultados confiables."
        
        # Si no tenemos metodología específica, intentar extraer del abstract
        if article.abstract:
            methodology_keywords = self._extract_methodology_keywords(article.abstract)
            if methodology_keywords:
                return f"La metodología utilizada incluye {', '.join(methodology_keywords)}. Este enfoque metodológico permite una evaluación comprehensiva de los datos y resultados obtenidos."
        
        return "La metodología utilizada en este estudio combina técnicas establecidas con enfoques innovadores, permitiendo una evaluación comprehensiva de los datos y resultados obtenidos."
    
    def _create_specific_results_section(self, structured_info: Dict[str, str], article: Article) -> str:
        """Crea la sección de resultados específica."""
        results_parts = []
        
        if structured_info.get('findings'):
            findings = structured_info['findings']
            results_parts.append(f"Los resultados principales del estudio indican que {findings.lower()}")
        
        if structured_info.get('key_metrics'):
            metrics = structured_info['key_metrics']
            results_parts.append(f"\n\nEntre los hallazgos más destacados se encuentran:\n{metrics}")
        
        # Si no tenemos hallazgos específicos, intentar extraer del abstract
        if not results_parts and article.abstract:
            results_keywords = self._extract_results_keywords(article.abstract)
            if results_keywords:
                results_parts.append(f"Los resultados obtenidos muestran {', '.join(results_keywords)}.")
        
        if results_parts:
            return " ".join(results_parts)
        else:
            return "Los resultados obtenidos muestran patrones consistentes y estadísticamente significativos, confirmando la validez de las hipótesis planteadas."
    
    def _create_specific_implications_section(self, structured_info: Dict[str, str], article: Article) -> str:
        """Crea la sección de implicaciones específica."""
        implications = []
        
        if structured_info.get('findings'):
            findings = structured_info['findings']
            implications.append(f"Los hallazgos de esta investigación tienen implicaciones directas para el campo, ya que {findings.lower()}")
        
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
    
    def _create_specific_conclusion_section(self, structured_info: Dict[str, str], article: Article) -> str:
        """Crea la sección de conclusión específica."""
        conclusion_parts = []
        
        if structured_info.get('findings'):
            findings = structured_info['findings']
            conclusion_parts.append(f"Este estudio demuestra que {findings.lower()}")
        
        conclusion_parts.append("Los resultados obtenidos representan un paso importante hacia una mejor comprensión de los fenómenos estudiados y abren nuevas posibilidades para investigaciones futuras.")
        
        research_area = structured_info.get('research_area', 'general')
        if research_area == 'bioinformatics':
            conclusion_parts.append("Esta investigación contribuye significativamente al campo de la bioinformática y establece bases sólidas para desarrollos tecnológicos futuros.")
        elif research_area == 'ai_ml':
            conclusion_parts.append("Los avances presentados en este trabajo marcan el camino hacia sistemas de inteligencia artificial más sofisticados y útiles.")
        else:
            conclusion_parts.append("La metodología y los hallazgos presentados en este estudio tienen el potencial de influir significativamente en el desarrollo del campo y sus aplicaciones prácticas.")
        
        return " ".join(conclusion_parts)
    
    def _extract_keywords_from_title(self, title: str) -> List[str]:
        """Extrae palabras clave del título."""
        # Remover palabras comunes
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can'}
        
        words = re.findall(r'\b[a-zA-Z]+\b', title.lower())
        keywords = [word for word in words if word not in common_words and len(word) > 3]
        
        return keywords[:5]  # Máximo 5 palabras clave
    
    def _extract_methodology_keywords(self, text: str) -> List[str]:
        """Extrae palabras clave relacionadas con metodología."""
        methodology_terms = ['analysis', 'method', 'approach', 'technique', 'algorithm', 'model', 'framework', 'protocol', 'procedure', 'experiment', 'study', 'investigation', 'evaluation', 'assessment', 'measurement', 'calculation', 'computation', 'simulation']
        
        found_terms = []
        for term in methodology_terms:
            if term.lower() in text.lower():
                found_terms.append(term)
        
        return found_terms[:3]  # Máximo 3 términos
    
    def _extract_results_keywords(self, text: str) -> List[str]:
        """Extrae palabras clave relacionadas con resultados."""
        results_terms = ['result', 'finding', 'outcome', 'conclusion', 'discovery', 'observation', 'evidence', 'data', 'statistic', 'percentage', 'improvement', 'increase', 'decrease', 'change', 'difference', 'correlation', 'relationship']
        
        found_terms = []
        for term in results_terms:
            if term.lower() in text.lower():
                found_terms.append(term)
        
        return found_terms[:3]  # Máximo 3 términos
    
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