"""
Sistema de logging para Scientific Article Aggregator
"""

import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


class Logger:
    """Clase para gestionar el logging de la aplicación."""
    
    def __init__(self, name: str = "scientific_aggregator"):
        """
        Inicializa el logger.
        
        Args:
            name: Nombre del logger
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self._configured = False
    
    def configure(self, 
                  level: str = "INFO", 
                  log_file: Optional[str] = None,
                  max_file_size: str = "10MB",
                  backup_count: int = 5):
        """
        Configura el logger.
        
        Args:
            level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Ruta del archivo de log
            max_file_size: Tamaño máximo del archivo de log
            backup_count: Número de archivos de backup a mantener
        """
        if self._configured:
            return
        
        # Configurar nivel
        log_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.setLevel(log_level)
        
        # Formato de log
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Handler para archivo si se especifica
        if log_file:
            # Crear directorio si no existe
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convertir tamaño máximo a bytes
            size_bytes = self._parse_size(max_file_size)
            
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=size_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        self._configured = True
    
    def _parse_size(self, size_str: str) -> int:
        """
        Convierte una cadena de tamaño a bytes.
        
        Args:
            size_str: Cadena de tamaño (ej: "10MB", "1GB")
            
        Returns:
            Tamaño en bytes
        """
        size_str = size_str.upper()
        
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            # Asumir bytes si no hay sufijo
            return int(size_str)
    
    def debug(self, message: str):
        """Log a debug message."""
        self.logger.debug(message)
    
    def info(self, message: str):
        """Log an info message."""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log a warning message."""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log an error message."""
        self.logger.error(message)
    
    def critical(self, message: str):
        """Log a critical message."""
        self.logger.critical(message)


def setup_logging(config: dict = None) -> Logger:
    """
    Configura el logging global de la aplicación.
    
    Args:
        config: Configuración de logging
        
    Returns:
        Instancia del logger configurado
    """
    if config is None:
        config = {
            'level': 'INFO',
            'file': 'logs/app.log',
            'max_file_size': '10MB',
            'backup_count': 5
        }
    
    logger = Logger()
    logger.configure(
        level=config.get('level', 'INFO'),
        log_file=config.get('file'),
        max_file_size=config.get('max_file_size', '10MB'),
        backup_count=config.get('backup_count', 5)
    )
    
    return logger


# Logger global
app_logger = Logger()

