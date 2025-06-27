"""
Archivo principal de Scientific Article Aggregator
"""

import argparse
import sys
from pathlib import Path

# Agregar el directorio src al path
sys.path.append(str(Path(__file__).parent))

from utils.config_loader import config_loader
from utils.logger import setup_logging
from utils.database import db_manager


def main():
    """Función principal de la aplicación."""
    parser = argparse.ArgumentParser(
        description="Scientific Article Aggregator - Recolector automático de artículos científicos"
    )
    
    parser.add_argument(
        '--topics',
        type=str,
        help='Temas de interés separados por comas (ej: "bioinformática,programación en biología")'
    )
    
    parser.add_argument(
        '--sources',
        type=str,
        help='Fuentes específicas separadas por comas (ej: "arxiv,europepmc")'
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Número de días hacia atrás para buscar artículos (default: 7)'
    )
    
    parser.add_argument(
        '--max-articles',
        type=int,
        default=50,
        help='Número máximo de artículos por fuente (default: 50)'
    )
    
    parser.add_argument(
        '--generate-posts',
        action='store_true',
        help='Generar posts divulgativos después de recolectar artículos'
    )
    
    parser.add_argument(
        '--update-kg',
        action='store_true',
        help='Actualizar el knowledge graph'
    )
    
    parser.add_argument(
        '--config-dir',
        type=str,
        help='Directorio de configuración personalizado'
    )
    
    args = parser.parse_args()
    
    # Configurar logging
    try:
        settings = config_loader.load_settings()
        logging_config = settings.get('logging', {})
        logger = setup_logging(logging_config)
        logger.info("Iniciando Scientific Article Aggregator")
        
    except Exception as e:
        print(f"Error al configurar logging: {e}")
        return 1
    
    try:
        # Obtener configuración
        if args.topics:
            topics = [topic.strip() for topic in args.topics.split(',')]
        else:
            topics = config_loader.get_topic_list()
        
        logger.info(f"Temas de interés: {topics}")
        
        # Aquí se implementará la lógica principal
        # Por ahora, solo mostramos la configuración
        
        print("🔬 Scientific Article Aggregator")
        print("=" * 50)
        print(f"Temas configurados: {len(topics)}")
        for i, topic in enumerate(topics, 1):
            print(f"  {i}. {topic}")
        
        print(f"\nArtículos en base de datos: {db_manager.get_article_count()}")
        
        sources_summary = db_manager.get_sources_summary()
        if sources_summary:
            print("\nArtículos por fuente:")
            for source, count in sources_summary.items():
                print(f"  {source}: {count} artículos")
        
        logger.info("Aplicación ejecutada exitosamente")
        return 0
        
    except Exception as e:
        logger.error(f"Error durante la ejecución: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

