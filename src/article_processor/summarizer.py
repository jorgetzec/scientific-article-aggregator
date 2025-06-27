"""
Generador de resúmenes de artículos científicos sin tecnicismos
"""

import re
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..utils.logger import app_logger
from ..utils.config_loader import config_loader


class ArticleSummarizer:
    """Generador de resúmenes de artículos científicos."""
    
    def __init__(self):
        """Inicializa el generador de resúmenes."""
        self.config = config_loader.get_text_processing_config()
        self.max_summary_length = self.config.get('max_summary_length', 300)
        self.remove_jargon = self.config.get('remove_technical_jargon', True)
        
        # Diccionario de términos técnicos y sus equivalentes simples
        self.jargon_replacements = {
            # Bioinformática
            'bioinformatics': 'análisis computacional de datos biológicos',
            'genomics': 'estudio de los genes',
            'proteomics': 'estudio de las proteínas',
            'transcriptomics': 'estudio de la expresión génica',
            'phylogenetic': 'evolutivo',
            'phylogeny': 'evolución',
            'orthologous': 'genes similares entre especies',
            'paralogous': 'genes duplicados en la misma especie',
            'homologous': 'genes relacionados evolutivamente',
            
            # Metodología
            'algorithm': 'método computacional',
            'heuristic': 'método aproximado',
            'optimization': 'mejora',
            'clustering': 'agrupación',
            'classification': 'clasificación',
            'regression': 'predicción numérica',
            'machine learning': 'aprendizaje automático',
            'deep learning': 'aprendizaje profundo',
            'neural network': 'red neuronal',
            
            # Estadística
            'statistical significance': 'significancia estadística',
            'p-value': 'valor p',
            'confidence interval': 'intervalo de confianza',
            'correlation': 'correlación',
            'regression': 'regresión',
            'variance': 'varianza',
            'standard deviation': 'desviación estándar',
            
            # Biología molecular
            'gene expression': 'expresión génica',
            'protein folding': 'plegamiento de proteínas',
            'molecular dynamics': 'dinámica molecular',
            'binding affinity': 'afinidad de unión',
            'enzyme kinetics': 'cinética enzimática',
            'metabolic pathway': 'ruta metabólica',
            
            # Términos generales
            'methodology': 'metodología',
            'implementation': 'implementación',
            'validation': 'validación',
            'benchmark': 'comparación',
            'dataset': 'conjunto de datos',
            'database': 'base de datos',
            'repository': 'repositorio',
            'framework': 'marco de trabajo'
        }
    
    def generate_summary(self, article_title: str, 
                        article_abstract: str,
                        article_text: str = None) -> str:
        """
        Genera un resumen sin tecnicismos de un artículo.
        
        Args:
            article_title: Título del artículo
            article_abstract: Abstract del artículo
            article_text: Texto completo del artículo (opcional)
            
        Returns:
            Resumen generado
        """
        app_logger.info(f"Generando resumen para: {article_title[:50]}...")
        
        # Extraer información estructurada del abstract y texto completo
        structured_info = self._extract_structured_information(article_abstract, article_text)
        
        if not structured_info['has_content']:
            return "No hay suficiente información para generar un resumen."
        
        # Generar resumen específico basado en la información extraída
        summary = self._create_specific_summary(structured_info)
        
        # Limitar longitud
        summary = self._limit_length(summary, self.max_summary_length)
        
        app_logger.info(f"Resumen generado ({len(summary.split())} palabras)")
        return summary
    
    def _extract_structured_information(self, abstract: str, full_text: str = None) -> Dict[str, Any]:
        """
        Extrae información estructurada del artículo.
        
        Args:
            abstract: Abstract del artículo
            full_text: Texto completo del artículo
            
        Returns:
            Diccionario con información estructurada
        """
        info = {
            'has_content': False,
            'problem': '',
            'methodology': '',
            'results': '',
            'conclusions': '',
            'data_info': '',
            'key_numbers': []
        }
        
        # Combinar abstract y texto completo
        combined_text = abstract or ""
        if full_text:
            combined_text += f" {full_text}"
        
        if not combined_text.strip():
            return info
        
        info['has_content'] = True
        
        # Extraer problema/objetivo
        info['problem'] = self._extract_problem_statement(combined_text)
        
        # Extraer metodología
        info['methodology'] = self._extract_methodology_details(combined_text)
        
        # Extraer resultados
        info['results'] = self._extract_results_details(combined_text)
        
        # Extraer conclusiones
        info['conclusions'] = self._extract_conclusions_details(combined_text)
        
        # Extraer información sobre datos
        info['data_info'] = self._extract_data_information(combined_text)
        
        # Extraer números clave
        info['key_numbers'] = self._extract_key_numbers(combined_text)
        
        return info
    
    def _extract_problem_statement(self, text: str) -> str:
        """Extrae la declaración del problema o objetivo."""
        # Buscar patrones que indiquen el problema u objetivo
        problem_patterns = [
            r'(?i)(?:we\s+)?(?:aim|aimed|goal|objective|purpose|problem|challenge|issue)(?:s)?\s+(?:is|was|were|to|of)\s+([^.]{20,150})',
            r'(?i)(?:this\s+)?(?:study|research|work|paper)\s+(?:aims|addresses|tackles|solves|investigates)\s+([^.]{20,150})',
            r'(?i)(?:the\s+)?(?:main|primary|key)\s+(?:goal|objective|aim|purpose)\s+(?:is|was)\s+([^.]{20,150})',
            r'(?i)(?:we\s+)?(?:propose|present|develop|introduce)\s+([^.]{20,150})\s+(?:to|for|that)',
        ]
        
        for pattern in problem_patterns:
            matches = re.findall(pattern, text)
            if matches:
                problem = matches[0].strip()
                return self._clean_and_simplify_text(problem)
        
        # Si no encuentra patrones específicos, buscar en las primeras oraciones
        sentences = self._split_into_sentences(text)
        for sentence in sentences[:3]:
            if any(word in sentence.lower() for word in ['problem', 'challenge', 'aim', 'goal', 'objective']):
                return self._clean_and_simplify_text(sentence)
        
        return ""
    
    def _extract_methodology_details(self, text: str) -> str:
        """Extrae detalles específicos de la metodología."""
        methodology_patterns = [
            r'(?i)(?:we\s+)?(?:used|employed|applied|implemented|developed|created)\s+([^.]{20,200})',
            r'(?i)(?:the\s+)?(?:method|approach|algorithm|technique|procedure)\s+(?:involves|consists|includes)\s+([^.]{20,200})',
            r'(?i)(?:our\s+)?(?:methodology|approach|method)\s+(?:is|was|consists)\s+([^.]{20,200})',
            r'(?i)(?:we\s+)?(?:analyzed|processed|examined|evaluated)\s+([^.]{20,200})',
        ]
        
        methodology_details = []
        
        for pattern in methodology_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                detail = self._clean_and_simplify_text(match.strip())
                if detail and len(detail) > 15:
                    methodology_details.append(detail)
        
        # Buscar información sobre datasets y herramientas
        dataset_info = self._extract_dataset_info(text)
        if dataset_info:
            methodology_details.append(dataset_info)
        
        return '. '.join(methodology_details[:3])  # Máximo 3 detalles
    
    def _extract_results_details(self, text: str) -> str:
        """Extrae detalles específicos de los resultados."""
        results_patterns = [
            r'(?i)(?:we\s+)?(?:found|discovered|observed|showed|demonstrated|achieved)\s+([^.]{20,200})',
            r'(?i)(?:the\s+)?(?:results|findings|outcomes)\s+(?:show|indicate|reveal|suggest)\s+([^.]{20,200})',
            r'(?i)(?:our\s+)?(?:analysis|experiments|evaluation)\s+(?:revealed|showed|indicated)\s+([^.]{20,200})',
            r'(?i)(?:performance|accuracy|improvement)\s+(?:of|was|reached)\s+([^.]{20,100})',
        ]
        
        results_details = []
        
        for pattern in results_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                detail = self._clean_and_simplify_text(match.strip())
                if detail and len(detail) > 15:
                    results_details.append(detail)
        
        return '. '.join(results_details[:3])  # Máximo 3 resultados
    
    def _extract_conclusions_details(self, text: str) -> str:
        """Extrae detalles específicos de las conclusiones."""
        conclusion_patterns = [
            r'(?i)(?:we\s+)?(?:conclude|concluded)\s+(?:that\s+)?([^.]{20,200})',
            r'(?i)(?:in\s+)?(?:conclusion|summary),?\s+([^.]{20,200})',
            r'(?i)(?:this\s+)?(?:study|research|work)\s+(?:demonstrates|shows|proves)\s+([^.]{20,200})',
            r'(?i)(?:these\s+)?(?:findings|results)\s+(?:suggest|indicate|imply)\s+([^.]{20,200})',
        ]
        
        conclusion_details = []
        
        for pattern in conclusion_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                detail = self._clean_and_simplify_text(match.strip())
                if detail and len(detail) > 15:
                    conclusion_details.append(detail)
        
        return '. '.join(conclusion_details[:2])  # Máximo 2 conclusiones
    
    def _extract_data_information(self, text: str) -> str:
        """Extrae información sobre los datos utilizados."""
        data_patterns = [
            r'(?i)(?:we\s+)?(?:used|analyzed|collected)\s+([^.]*(?:dataset|data|samples|participants)[^.]{0,100})',
            r'(?i)(?:the\s+)?(?:dataset|data)\s+(?:contains|includes|consists)\s+([^.]{20,150})',
            r'(?i)(?:a\s+total\s+of|we\s+collected)\s+([^.]*(?:samples|participants|data points)[^.]{0,100})',
        ]
        
        for pattern in data_patterns:
            matches = re.findall(pattern, text)
            if matches:
                data_info = matches[0].strip()
                return self._clean_and_simplify_text(data_info)
        
        return ""
    
    def _extract_dataset_info(self, text: str) -> str:
        """Extrae información específica sobre datasets."""
        # Buscar menciones de datasets conocidos o números específicos
        dataset_mentions = re.findall(r'(?i)(?:dataset|database|corpus)\s+(?:of|with|containing)\s+([^.]{10,100})', text)
        if dataset_mentions:
            return f"utilizando un dataset {dataset_mentions[0].strip()}"
        
        # Buscar números de muestras
        sample_numbers = re.findall(r'(\d+(?:,\d+)*)\s+(?:samples|participants|subjects|cases|instances)', text)
        if sample_numbers:
            return f"analizando {sample_numbers[0]} muestras"
        
        return ""
    
    def _extract_key_numbers(self, text: str) -> List[str]:
        """Extrae números clave del texto."""
        key_numbers = []
        
        # Buscar porcentajes
        percentages = re.findall(r'(\d+(?:\.\d+)?%)', text)
        key_numbers.extend(percentages[:3])
        
        # Buscar métricas de rendimiento
        performance_metrics = re.findall(r'(?:accuracy|precision|recall|f1|auc)(?:\s+of)?\s+(\d+(?:\.\d+)?%?)', text, re.IGNORECASE)
        key_numbers.extend([metric[1] if isinstance(metric, tuple) else metric for metric in performance_metrics[:2]])
        
        # Buscar mejoras
        improvements = re.findall(r'(?:improvement|increase|reduction)(?:\s+of)?\s+(\d+(?:\.\d+)?%?)', text, re.IGNORECASE)
        key_numbers.extend([imp[1] if isinstance(imp, tuple) else imp for imp in improvements[:2]])
        
        return key_numbers[:5]  # Máximo 5 números clave
    
    def _clean_and_simplify_text(self, text: str) -> str:
        """Limpia y simplifica un fragmento de texto."""
        if not text:
            return ""
        
        # Simplificar jerga técnica
        simplified = self._simplify_jargon(text)
        
        # Limpiar texto
        simplified = self._clean_text(simplified)
        
        # Capitalizar primera letra
        if simplified:
            simplified = simplified[0].upper() + simplified[1:]
        
        return simplified
    
    def _create_specific_summary(self, info: Dict[str, Any]) -> str:
        """
        Crea un resumen específico basado en la información estructurada.
        
        Args:
            info: Información estructurada extraída
            
        Returns:
            Resumen específico
        """
        summary_parts = []
        
        # Comenzar con el problema/objetivo si está disponible
        if info['problem']:
            summary_parts.append(f"Los investigadores abordaron {info['problem']}")
        
        # Agregar metodología específica
        if info['methodology']:
            summary_parts.append(f"Para esto, {info['methodology']}")
        
        # Agregar información de datos si está disponible
        if info['data_info']:
            summary_parts.append(f"El estudio se basó en {info['data_info']}")
        
        # Agregar resultados específicos
        if info['results']:
            summary_parts.append(f"Los resultados mostraron que {info['results']}")
        
        # Agregar números clave si están disponibles
        if info['key_numbers']:
            numbers_text = ', '.join(info['key_numbers'][:3])
            summary_parts.append(f"Con métricas clave de {numbers_text}")
        
        # Agregar conclusiones
        if info['conclusions']:
            summary_parts.append(f"Los autores concluyen que {info['conclusions']}")
        
        # Si no hay suficiente información específica, crear un resumen básico
        if not summary_parts:
            summary_parts.append("Este estudio presenta nuevos hallazgos en su área de investigación")
            if info['methodology']:
                summary_parts.append(f"utilizando {info['methodology']}")
            if info['results']:
                summary_parts.append(f"Los resultados indican {info['results']}")
        
        # Unir las partes
        summary = '. '.join(summary_parts)
        
        # Asegurar que termine con punto
        if summary and not summary.endswith('.'):
            summary += '.'
        
        return summary
    
    def _clean_text(self, text: str) -> str:
        """Limpia un fragmento de texto."""
        if not text:
            return ""
        
        # Normalizar espacios en blanco
        text = re.sub(r'\s+', ' ', text)
        
        # Remover caracteres de control
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        return text.strip()
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Divide el texto en oraciones.
        
        Args:
            text: Texto a dividir
            
        Returns:
            Lista de oraciones
        """
        if not text:
            return []
        
        # Patrón simple para dividir oraciones
        sentences = re.split(r'[.!?]+', text)
        
        # Limpiar y filtrar oraciones
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:  # Filtrar oraciones muy cortas
                cleaned_sentences.append(sentence)
        
        return cleaned_sentences
    
    def _simplify_jargon(self, text: str) -> str:
        """
        Simplifica el lenguaje técnico en el texto.
        
        Args:
            text: Texto con posible jerga técnica
            
        Returns:
            Texto con jerga simplificada
        """
        simplified_text = text
        
        # Reemplazar términos técnicos
        for jargon, simple in self.jargon_replacements.items():
            # Reemplazo case-insensitive
            pattern = re.compile(re.escape(jargon), re.IGNORECASE)
            simplified_text = pattern.sub(simple, simplified_text)
        
        # Simplificar números y estadísticas complejas
        simplified_text = self._simplify_statistics(simplified_text)
        
        return simplified_text
    
    def _simplify_statistics(self, text: str) -> str:
        """
        Simplifica estadísticas complejas.
        
        Args:
            text: Texto con estadísticas
            
        Returns:
            Texto con estadísticas simplificadas
        """
        # Simplificar p-values
        text = re.sub(r'p\s*[<>=]\s*0\.0+1', 'estadísticamente significativo', text)
        text = re.sub(r'p\s*[<>=]\s*0\.05', 'estadísticamente significativo', text)
        
        # Simplificar porcentajes muy precisos
        text = re.sub(r'(\d+\.\d{3,})%', lambda m: f"{round(float(m.group(1)))}%", text)
        
        # Simplificar notación científica
        text = re.sub(r'(\d+\.?\d*)\s*[×x]\s*10\^?-?\d+', 'un número muy pequeño', text)
        
        return text
    
    def _limit_length(self, text: str, max_words: int) -> str:
        """
        Limita la longitud del texto a un número máximo de palabras.
        
        Args:
            text: Texto a limitar
            max_words: Número máximo de palabras
            
        Returns:
            Texto limitado
        """
        if not text:
            return ""
        
        words = text.split()
        if len(words) <= max_words:
            return text
        
        # Truncar y asegurar que termine en una oración completa
        truncated_words = words[:max_words]
        truncated_text = ' '.join(truncated_words)
        
        # Buscar el último punto para terminar en oración completa
        last_period = truncated_text.rfind('.')
        if last_period > len(truncated_text) * 0.7:  # Si el punto está en el último 30%
            return truncated_text[:last_period + 1]
        else:
            return truncated_text + '...'

