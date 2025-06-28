"""
Scheduler para automatización diaria de recolección y procesamiento
"""

import schedule
import time
from datetime import datetime
from typing import List

from ..utils.logger import app_logger
from ..data_harvester.harvester_manager import harvester_manager
from ..article_processor.processor_manager import processor_manager
from ..knowledge_graph.graph_builder import graph_builder
from ..utils.database import db_manager


class DailyScheduler:
    """Scheduler para automatización diaria."""
    
    def __init__(self):
        """Inicializa el scheduler."""
        self.default_topics = [
            "bioinformatics",
            "computational biology", 
            "machine learning",
            "data analysis",
            "plant microbe interaction",
            "scientific education"
        ]
        self.is_running = False
    
    def setup_daily_schedule(self, time_str: str = "08:00"):
        """
        Configura la ejecución diaria.
        
        Args:
            time_str: Hora de ejecución en formato HH:MM
        """
        app_logger.info(f"Configurando ejecución diaria a las {time_str}")
        
        # Programar tarea diaria
        schedule.every().day.at(time_str).do(self.run_daily_tasks)
        
        app_logger.info("Scheduler configurado exitosamente")
    
    def run_daily_tasks(self):
        """Ejecuta las tareas diarias."""
        app_logger.info("=== Iniciando tareas diarias ===")
        
        try:
            # 1. Recolectar artículos
            app_logger.info("1. Recolectando artículos...")
            harvest_stats = harvester_manager.harvest_all_sources(
                topics=self.default_topics,
                max_articles_per_source=10
            )
            app_logger.info(f"Recolección completada: {harvest_stats}")
            
            # 2. Procesar artículos
            app_logger.info("2. Procesando artículos...")
            process_stats = processor_manager.process_articles(max_articles=20)
            app_logger.info(f"Procesamiento completado: {process_stats}")
            
            # 3. Actualizar knowledge graph
            app_logger.info("3. Actualizando knowledge graph...")
            articles = db_manager.get_recent_articles(days=30, limit=100)
            graph_builder.build_graph(articles)
            app_logger.info("Knowledge graph actualizado")
            
            # 4. Generar resumen diario
            app_logger.info("4. Generando resumen diario...")
            daily_summary = processor_manager.generate_daily_summary()
            app_logger.info("Resumen diario generado")
            
            app_logger.info("=== Tareas diarias completadas exitosamente ===")
            
        except Exception as e:
            app_logger.error(f"Error en tareas diarias: {e}")
    
    def run_scheduler(self):
        """Ejecuta el scheduler en modo continuo."""
        app_logger.info("Iniciando scheduler en modo continuo...")
        self.is_running = True
        
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # Verificar cada minuto
    
    def stop_scheduler(self):
        """Detiene el scheduler."""
        app_logger.info("Deteniendo scheduler...")
        self.is_running = False
    
    def run_tasks_now(self):
        """Ejecuta las tareas inmediatamente (para pruebas)."""
        app_logger.info("Ejecutando tareas inmediatamente...")
        self.run_daily_tasks()


# Instancia global del scheduler
daily_scheduler = DailyScheduler()

