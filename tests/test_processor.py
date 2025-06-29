#!/usr/bin/env python3
"""
Script de prueba para el procesador de artículos
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
from src.utils.database import db_manager
from src.article_processor.processor_manager import processor_manager


def main():
    """Función principal de prueba."""
    print("📝 Probando Scientific Article Aggregator - Procesador de Artículos")
    print("=" * 70)
    
    # Configurar logging
    try:
        settings = config_loader.load_settings()
        logging_config = settings.get('logging', {})
        logger = setup_logging(logging_config)
        logger.info("Iniciando pruebas del procesador de artículos")
        
    except Exception as e:
        print(f"Error configurando logging: {e}")
        return 1
    
    # Verificar que hay artículos en la base de datos
    total_articles = db_manager.get_article_count()
    print(f"\n📊 Artículos disponibles en la base de datos: {total_articles}")
    
    if total_articles == 0:
        print("❌ No hay artículos en la base de datos. Ejecuta primero test_harvesters.py")
        return 1
    
    # Obtener algunos artículos para procesar
    recent_articles = db_manager.get_recent_articles(days=30, limit=5)
    print(f"📋 Artículos recientes para procesar: {len(recent_articles)}")
    
    if not recent_articles:
        print("❌ No se encontraron artículos recientes para procesar")
        return 1
    
    # Mostrar artículos que se van a procesar
    print("\n🔍 Artículos a procesar:")
    for i, article in enumerate(recent_articles, 1):
        print(f"  {i}. {article.title[:60]}...")
        print(f"     Fuente: {article.source}")
        print(f"     Resumen: {'✅' if article.summary else '❌'}")
        print(f"     Post: {'✅' if article.post_content else '❌'}")
        print()
    
    # Procesar artículos
    print("🚀 Iniciando procesamiento de artículos...")
    
    try:
        # Procesar solo los primeros 3 artículos para la prueba
        article_ids = [article.id for article in recent_articles[:3]]
        
        stats = processor_manager.process_articles(
            article_ids=article_ids,
            generate_posts=True,
            save_markdown=True
        )
        
        print(f"\n✅ Procesamiento completado!")
        print(f"📊 Estadísticas:")
        print(f"  - Artículos procesados: {stats['processed']}")
        print(f"  - Resúmenes generados: {stats['summaries']}")
        print(f"  - Posts generados: {stats['posts']}")
        print(f"  - Archivos markdown guardados: {stats['saved_files']}")
        print(f"  - Errores: {stats['errors']}")
        
        # Mostrar ejemplo de contenido generado
        if stats['processed'] > 0:
            print("\n📄 Ejemplo de contenido generado:")
            
            # Obtener el primer artículo procesado
            processed_article = db_manager.get_article(article_ids[0])
            
            if processed_article and processed_article.summary:
                print(f"\n🔸 Resumen:")
                print(f"  {processed_article.summary[:200]}...")
            
            if processed_article and processed_article.post_content:
                print(f"\n🔸 Post (primeras líneas):")
                post_lines = processed_article.post_content.split('\n')[:5]
                for line in post_lines:
                    if line.strip():
                        print(f"  {line}")
        
        # Verificar archivos markdown generados
        markdown_dir = Path("outputs/posts")
        if markdown_dir.exists():
            markdown_files = list(markdown_dir.glob("*.md"))
            print(f"\n📁 Archivos markdown generados: {len(markdown_files)}")
            
            if markdown_files:
                print("  Archivos:")
                for file_path in markdown_files[-3:]:  # Mostrar los últimos 3
                    print(f"    - {file_path.name}")
        
        # Generar resumen diario
        print("\n📅 Generando resumen diario...")
        daily_summary = processor_manager.generate_daily_summary()
        
        if daily_summary:
            print("✅ Resumen diario generado")
            print(f"📄 Primeras líneas del resumen:")
            summary_lines = daily_summary.split('\n')[:5]
            for line in summary_lines:
                if line.strip():
                    print(f"  {line}")
        
        # Mostrar estadísticas finales
        print("\n📈 Estadísticas finales del procesamiento:")
        final_stats = processor_manager.get_processing_statistics()
        print(f"  - Total de artículos: {final_stats['total_articles']}")
        print(f"  - Archivos markdown: {final_stats['markdown_files']}")
        print(f"  - Fuentes: {len(final_stats['sources'])}")
        
        logger.info("Pruebas del procesador completadas exitosamente")
        
    except Exception as e:
        logger.error(f"Error durante el procesamiento: {e}")
        print(f"❌ Error durante el procesamiento: {e}")
        return 1
    
    print("\n🎉 Pruebas del procesador completadas exitosamente!")
    return 0


if __name__ == "__main__":
    sys.exit(main())

