# backend/core/__init__.py
"""
Módulo core de BOT-vCSGO-Beta
Contiene las clases base y utilidades principales
"""

from .base_scraper import BaseScraper
from .config_manager import ConfigManager, get_config_manager
from .proxy_manager import ProxyManager
from .translator import Translator, get_translator

__all__ = [
    'BaseScraper',
    'ConfigManager',
    'get_config_manager',
    'ProxyManager',
    'Translator',
    'get_translator'
]

# Versión del módulo core
__version__ = '2.0.0'