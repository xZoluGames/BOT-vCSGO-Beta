# backend/core/logger_config.py
from loguru import logger
import sys

def setup_logger():
    # Remover handler por defecto
    logger.remove()
    
    # Consola - Solo info importante
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{extra[scraper]}</cyan> - {message}",
        level="INFO",
        filter=lambda record: record["level"].no >= 20
    )
    
    # Archivo - Todo
    logger.add(
        "logs/{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="7 days",
        level="DEBUG"
    )