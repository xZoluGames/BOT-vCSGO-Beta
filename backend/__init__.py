# backend/__init__.py
"""
Backend de BOT-vCSGO-Beta
Sistema unificado de scrapers para arbitraje de CS:GO
"""

__version__ = '2.0.0'
__author__ = 'ZoluGames'

# Hacer que los imports sean más fáciles
from .core import (
    BaseScraper,
    ConfigManager,
    get_config_manager,
    ProxyManager,
    Translator,
    get_translator
)

__all__ = [
    'BaseScraper',
    'ConfigManager', 
    'get_config_manager',
    'ProxyManager',
    'Translator',
    'get_translator'
]