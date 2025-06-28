"""
Validador de datos para artículos científicos
"""

import re
from datetime import datetime, date
from typing import Optional, Dict, Any
from ..utils.logger import app_logger


class DataValidator:
    """Validador y limpiador de datos de artículos científicos."""
    
    def __init__(self):
        """Inicializa el validador."""
        self.current_year = datetime.now().year
        
    def validate_and_clean_article(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida y limpia los datos de un artículo.
        
        Args:
            article_data: Datos del artículo
            
        Returns:
            Datos limpios y validados
        """
        cleaned_data = article_data.copy()
        
        # Validar y limpiar título
        if 'title' in cleaned_data:
            cleaned_data['title'] = self._clean_title(cleaned_data['title'])
        
        # Validar y limpiar abstract
        if 'abstract' in cleaned_data:
            cleaned_data['abstract'] = self._clean_abstract(cleaned_data['abstract'])
        
        # Validar y corregir fecha de publicación
        if 'publication_date' in cleaned_data:
            cleaned_data['publication_date'] = self._validate_publication_date(cleaned_data['publication_date'])
        
        # Validar y limpiar autores
        if 'authors' in cleaned_data:
            cleaned_data['authors'] = self._clean_authors(cleaned_data['authors'])
        
        # Validar y limpiar URL
        if 'url' in cleaned_data:
            cleaned_data['url'] = self._validate_url(cleaned_data['url'])
        
        # Validar y limpiar temas
        if 'topics' in cleaned_data:
            cleaned_data['topics'] = self._clean_topics(cleaned_data['topics'])
        
        return cleaned_data
    
    def _clean_title(self, title: str) -> str:
        """Limpia y valida el título."""
        if not title:
            return ""
        
        # Remover caracteres extraños
        title = re.sub(r'[^\w\s\-\.\,\:\;\?\!\(\)\[\]]', '', title)
        
        # Remover espacios extra
        title = re.sub(r'\s+', ' ', title).strip()
        
        # Capitalizar correctamente
        title = title.title()
        
        return title
    
    def _clean_abstract(self, abstract: str) -> str:
        """Limpia y valida el abstract."""
        if not abstract:
            return ""
        
        # Remover texto duplicado
        abstract = re.sub(r'([^.]*?)(\1)+', r'\1', abstract)
        
        # Remover fragmentos incompletos al final
        abstract = re.sub(r'\b[A-Z][a-z]*\s*$', '', abstract)
        
        # Limpiar espacios extra
        abstract = re.sub(r'\s+', ' ', abstract).strip()
        
        # Asegurar que termine con punto
        if abstract and not abstract.endswith('.'):
            abstract += '.'
        
        return abstract
    
    def _validate_publication_date(self, pub_date) -> Optional[date]:
        """Valida y corrige la fecha de publicación."""
        if not pub_date:
            return None
        
        try:
            # Si ya es un objeto date, validar el año
            if isinstance(pub_date, date):
                if pub_date.year > self.current_year + 1:
                    # Fecha en el futuro, usar año actual
                    return date(self.current_year, pub_date.month, pub_date.day)
                return pub_date
            
            # Si es string, intentar parsear
            if isinstance(pub_date, str):
                # Patrones comunes de fecha
                date_patterns = [
                    r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
                    r'(\d{1,2})/(\d{1,2})/(\d{4})',  # MM/DD/YYYY
                    r'(\d{4})/(\d{1,2})/(\d{1,2})',  # YYYY/MM/DD
                    r'(\d{1,2})-(\d{1,2})-(\d{4})',  # MM-DD-YYYY
                ]
                
                for pattern in date_patterns:
                    match = re.search(pattern, pub_date)
                    if match:
                        groups = match.groups()
                        if len(groups) == 3:
                            year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                            
                            # Corregir año si es obviamente incorrecto
                            if year > self.current_year + 1:
                                year = self.current_year
                            elif year < 1900:
                                year = self.current_year
                            
                            # Validar mes y día
                            if 1 <= month <= 12 and 1 <= day <= 31:
                                return date(year, month, day)
                
                # Si no coincide con patrones, intentar parsear con datetime
                parsed_date = datetime.strptime(pub_date, '%Y-%m-%d').date()
                if parsed_date.year > self.current_year + 1:
                    return date(self.current_year, parsed_date.month, parsed_date.day)
                return parsed_date
                
        except Exception as e:
            app_logger.warning(f"Error validando fecha {pub_date}: {e}")
            return None
        
        return None
    
    def _clean_authors(self, authors) -> list:
        """Limpia y valida la lista de autores."""
        if not authors:
            return []
        
        if isinstance(authors, str):
            # Separar por comas o puntos y coma
            authors = re.split(r'[,;]', authors)
        
        cleaned_authors = []
        for author in authors:
            if isinstance(author, str) and author.strip():
                # Limpiar nombre del autor
                clean_author = author.strip()
                clean_author = re.sub(r'\s+', ' ', clean_author)
                
                # Capitalizar correctamente
                clean_author = clean_author.title()
                
                if len(clean_author) > 2:  # Evitar nombres muy cortos
                    cleaned_authors.append(clean_author)
        
        return cleaned_authors[:10]  # Máximo 10 autores
    
    def _validate_url(self, url: str) -> str:
        """Valida y limpia la URL."""
        if not url:
            return ""
        
        # Remover espacios
        url = url.strip()
        
        # Asegurar que tenga protocolo
        if url and not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Validar formato básico
        if re.match(r'https?://[^\s]+', url):
            return url
        
        return ""
    
    def _clean_topics(self, topics) -> list:
        """Limpia y valida la lista de temas."""
        if not topics:
            return []
        
        if isinstance(topics, str):
            # Separar por comas
            topics = re.split(r'[,;]', topics)
        
        cleaned_topics = []
        for topic in topics:
            if isinstance(topic, str) and topic.strip():
                clean_topic = topic.strip()
                clean_topic = re.sub(r'\s+', ' ', clean_topic)
                
                if len(clean_topic) > 1:  # Evitar temas muy cortos
                    cleaned_topics.append(clean_topic)
        
        return cleaned_topics[:5]  # Máximo 5 temas
    
    def validate_text_quality(self, text: str) -> Dict[str, Any]:
        """
        Evalúa la calidad del texto.
        
        Args:
            text: Texto a evaluar
            
        Returns:
            Diccionario con métricas de calidad
        """
        if not text:
            return {
                'quality_score': 0,
                'issues': ['Texto vacío'],
                'word_count': 0,
                'sentence_count': 0
            }
        
        issues = []
        score = 100
        
        # Contar palabras
        words = text.split()
        word_count = len(words)
        
        # Contar oraciones
        sentences = re.split(r'[.!?]+', text)
        sentence_count = len([s for s in sentences if s.strip()])
        
        # Verificar longitud mínima
        if word_count < 10:
            issues.append('Texto muy corto')
            score -= 30
        
        # Verificar repeticiones
        if len(set(words)) / word_count < 0.5:
            issues.append('Mucha repetición de palabras')
            score -= 20
        
        # Verificar fragmentos incompletos
        incomplete_sentences = len([s for s in sentences if s.strip() and not s.strip().endswith(('.', '!', '?'))])
        if incomplete_sentences > 0:
            issues.append('Oraciones incompletas')
            score -= 15
        
        # Verificar caracteres extraños
        strange_chars = len(re.findall(r'[^\w\s\-\.\,\:\;\?\!\(\)\[\]]', text))
        if strange_chars > len(text) * 0.1:
            issues.append('Muchos caracteres extraños')
            score -= 10
        
        return {
            'quality_score': max(0, score),
            'issues': issues,
            'word_count': word_count,
            'sentence_count': sentence_count
        }


# Instancia global del validador
data_validator = DataValidator() 