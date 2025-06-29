#!/usr/bin/env python3
"""
Script de prueba para los harvesters de APIs científicas
"""

import sys
import os
from pathlib import Path

# Agregar el directorio del proyecto al path (tests/ -> ..)
project_root = Path(__file__).parent.parent  # Subir un nivel desde tests/ a la raíz
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Cambiar al directorio del proyecto
os.chdir(project_root)

from src.utils.config_loader import config_loader
from src.utils.logger import setup_logging
from src.data_harvester.harvester_manager import harvester_manager


def main():
    """Función principal de prueba."""
    print("🔬 Probando Scientific Article Aggregator - Harvesters")
    print("=" * 60)
    
    # Configurar logging
    try:
        settings = config_loader.load_settings()
        logging_config = settings.get('logging', {})
        logger = setup_logging(logging_config)
        logger.info("Iniciando pruebas de harvesters")
        
    except Exception as e:
        print(f"Error configurando logging: {e}")
        return 1
    
    # Probar conectividad de harvesters
    print("\n📡 Probando conectividad de harvesters...")
    harvester_status = harvester_manager.test_harvesters()
    
    for source, status in harvester_status.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {source}")
    
    # Mostrar estadísticas
    print("\n📊 Estadísticas actuales:")
    stats = harvester_manager.get_statistics()
    print(f"  Total de artículos en BD: {stats['total_articles']}")
    print(f"  Harvesters disponibles: {stats['available_harvesters']}")
    print(f"  Fuentes: {', '.join(stats['harvester_names'])}")
    
    if stats['sources']:
        print("  Artículos por fuente:")
        for source, count in stats['sources'].items():
            print(f"    {source}: {count}")
    
    # Prueba de recolección con un tema simple
    print("\n🔍 Probando recolección de artículos...")
    test_topics = ["bioinformatics"]
    
    try:
        results = harvester_manager.harvest_all_sources(
            topics=test_topics,
            date_range_days=30,  # Últimos 30 días para tener más resultados
            max_articles_per_source=5,  # Solo 5 artículos por fuente para prueba
            parallel=False  # Secuencial para mejor debugging
        )
        
        print(f"\n📋 Resultados de la recolección:")
        total_articles = 0
        for source, articles in results.items():
            print(f"  {source}: {len(articles)} artículos")
            total_articles += len(articles)
            
            # Mostrar el primer artículo como ejemplo
            if articles:
                article = articles[0]
                print(f"    Ejemplo: {article.title[:80]}...")
        
        print(f"\n✅ Total recolectado: {total_articles} artículos")
        
        # Actualizar estadísticas
        updated_stats = harvester_manager.get_statistics()
        print(f"📊 Total en BD después de la prueba: {updated_stats['total_articles']} artículos")
        
    except Exception as e:
        logger.error(f"Error durante la recolección de prueba: {e}")
        print(f"❌ Error durante la recolección: {e}")
        return 1
    
    print("\n🎉 Pruebas completadas exitosamente!")
    return 0


if __name__ == "__main__":
    sys.exit(main())

