"""
Extractor de texto completo de artículos científicos
"""

import requests
import re
from typing import Optional, Dict, Any
from pathlib import Path
import tempfile
import os

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

from ..utils.logger import app_logger


class TextExtractor:
    """Extractor de texto completo de artículos científicos."""
    
    def __init__(self):
        """Inicializa el extractor de texto."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Scientific-Article-Aggregator/1.0 (Academic Research)'
        })
    
    def extract_full_text(self, article_url: str, article_doi: str = None) -> Optional[str]:
        """
        Extrae el texto completo de un artículo.
        
        Args:
            article_url: URL del artículo
            article_doi: DOI del artículo (opcional)
            
        Returns:
            Texto completo extraído o None si no es posible
        """
        app_logger.info(f"Intentando extraer texto completo de: {article_url}")
        
        # Intentar diferentes métodos de extracción
        methods = [
            self._extract_from_pdf_url,
            self._extract_from_html_page,
            self._extract_from_open_access_sources
        ]
        
        for method in methods:
            try:
                text = method(article_url, article_doi)
                if text and len(text.strip()) > 100:  # Mínimo de contenido
                    app_logger.info(f"Texto extraído exitosamente ({len(text)} caracteres)")
                    return self._clean_extracted_text(text)
            except Exception as e:
                app_logger.debug(f"Método {method.__name__} falló: {e}")
                continue
        
        app_logger.warning(f"No se pudo extraer texto completo de: {article_url}")
        return None
    
    def _extract_from_pdf_url(self, url: str, doi: str = None) -> Optional[str]:
        """
        Extrae texto de un PDF accesible por URL.
        
        Args:
            url: URL del artículo
            doi: DOI del artículo
            
        Returns:
            Texto extraído del PDF o None
        """
        if not PDF_AVAILABLE:
            return None
        
        # Intentar encontrar enlace directo al PDF
        pdf_urls = self._find_pdf_urls(url, doi)
        
        for pdf_url in pdf_urls:
            try:
                response = self.session.get(pdf_url, timeout=30)
                response.raise_for_status()
                
                # Verificar que es realmente un PDF
                if 'application/pdf' not in response.headers.get('content-type', ''):
                    continue
                
                # Guardar temporalmente y extraer texto
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                    tmp_file.write(response.content)
                    tmp_path = tmp_file.name
                
                try:
                    text = self._extract_text_from_pdf_file(tmp_path)
                    return text
                finally:
                    os.unlink(tmp_path)
                    
            except Exception as e:
                app_logger.debug(f"Error extrayendo PDF de {pdf_url}: {e}")
                continue
        
        return None
    
    def _extract_from_html_page(self, url: str, doi: str = None) -> Optional[str]:
        """
        Extrae texto de una página HTML.
        
        Args:
            url: URL del artículo
            doi: DOI del artículo
            
        Returns:
            Texto extraído del HTML o None
        """
        if not BS4_AVAILABLE:
            return None
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Intentar diferentes selectores comunes para contenido de artículos
            content_selectors = [
                'article',
                '.article-content',
                '.article-body',
                '.content',
                '.main-content',
                '#content',
                '.paper-content',
                '.full-text'
            ]
            
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    text = ' '.join([elem.get_text() for elem in elements])
                    if len(text.strip()) > 500:  # Contenido sustancial
                        return text
            
            # Si no encuentra selectores específicos, usar el body completo
            body = soup.find('body')
            if body:
                # Remover scripts, estilos y navegación
                for tag in body(['script', 'style', 'nav', 'header', 'footer']):
                    tag.decompose()
                
                text = body.get_text()
                if len(text.strip()) > 500:
                    return text
            
        except Exception as e:
            app_logger.debug(f"Error extrayendo HTML de {url}: {e}")
        
        return None
    
    def _extract_from_open_access_sources(self, url: str, doi: str = None) -> Optional[str]:
        """
        Intenta extraer texto de fuentes de acceso abierto conocidas.
        
        Args:
            url: URL del artículo
            doi: DOI del artículo
            
        Returns:
            Texto extraído o None
        """
        if not doi:
            return None
        
        # URLs de acceso abierto conocidas
        oa_sources = [
            f"https://www.ncbi.nlm.nih.gov/pmc/articles/{doi}/",
            f"https://europepmc.org/article/MED/{doi}",
            f"https://arxiv.org/abs/{doi}",
            f"https://www.biorxiv.org/content/10.1101/{doi}",
            f"https://www.medrxiv.org/content/10.1101/{doi}"
        ]
        
        for oa_url in oa_sources:
            try:
                text = self._extract_from_html_page(oa_url)
                if text:
                    return text
            except Exception:
                continue
        
        return None
    
    def _find_pdf_urls(self, url: str, doi: str = None) -> list:
        """
        Encuentra posibles URLs de PDF para un artículo.
        
        Args:
            url: URL del artículo
            doi: DOI del artículo
            
        Returns:
            Lista de URLs de PDF candidatas
        """
        pdf_urls = []
        
        # URLs directas comunes
        if url.endswith('.pdf'):
            pdf_urls.append(url)
        
        # Patrones comunes de PDF
        base_url = url.rstrip('/')
        pdf_patterns = [
            f"{base_url}.pdf",
            f"{base_url}/pdf",
            f"{base_url}.full.pdf",
            url.replace('/abs/', '/pdf/') + '.pdf',  # arXiv
            url.replace('/content/', '/content/') + '.full.pdf'  # bioRxiv/medRxiv
        ]
        
        pdf_urls.extend(pdf_patterns)
        
        # Si hay DOI, intentar URLs estándar
        if doi:
            doi_pdf_urls = [
                f"https://arxiv.org/pdf/{doi}.pdf",
                f"https://www.biorxiv.org/content/biorxiv/early/{doi}.full.pdf",
                f"https://www.medrxiv.org/content/medrxiv/early/{doi}.full.pdf"
            ]
            pdf_urls.extend(doi_pdf_urls)
        
        return list(set(pdf_urls))  # Eliminar duplicados
    
    def _extract_text_from_pdf_file(self, pdf_path: str) -> Optional[str]:
        """
        Extrae texto de un archivo PDF.
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Returns:
            Texto extraído o None
        """
        if not PDF_AVAILABLE:
            return None
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_parts = []
                
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                
                full_text = '\n'.join(text_parts)
                return full_text if full_text.strip() else None
                
        except Exception as e:
            app_logger.debug(f"Error extrayendo texto de PDF {pdf_path}: {e}")
            return None
    
    def _clean_extracted_text(self, text: str) -> str:
        """
        Limpia el texto extraído.
        
        Args:
            text: Texto a limpiar
            
        Returns:
            Texto limpio
        """
        if not text:
            return ""
        
        # Normalizar espacios en blanco
        text = re.sub(r'\s+', ' ', text)
        
        # Remover caracteres de control
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Remover líneas muy cortas que suelen ser ruido
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if len(line) > 10:  # Mantener solo líneas con contenido sustancial
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()
    
    def extract_abstract_and_keywords(self, text: str) -> Dict[str, str]:
        """
        Extrae abstract y palabras clave del texto completo.
        
        Args:
            text: Texto completo del artículo
            
        Returns:
            Diccionario con abstract y keywords extraídos
        """
        result = {'abstract': '', 'keywords': ''}
        
        if not text:
            return result
        
        # Buscar abstract
        abstract_patterns = [
            r'(?i)abstract\s*:?\s*(.*?)(?=\n\s*(?:keywords|introduction|1\.|background))',
            r'(?i)summary\s*:?\s*(.*?)(?=\n\s*(?:keywords|introduction|1\.|background))',
            r'(?i)resumen\s*:?\s*(.*?)(?=\n\s*(?:palabras|introduction|1\.|background))'
        ]
        
        for pattern in abstract_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                result['abstract'] = match.group(1).strip()
                break
        
        # Buscar keywords
        keyword_patterns = [
            r'(?i)keywords?\s*:?\s*(.*?)(?=\n\s*(?:introduction|1\.|background))',
            r'(?i)key\s*words?\s*:?\s*(.*?)(?=\n\s*(?:introduction|1\.|background))',
            r'(?i)palabras\s*clave\s*:?\s*(.*?)(?=\n\s*(?:introducción|1\.|antecedentes))'
        ]
        
        for pattern in keyword_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                result['keywords'] = match.group(1).strip()
                break
        
        return result

