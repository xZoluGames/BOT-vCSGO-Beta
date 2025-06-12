# backend/core/translator.py
"""
Sistema de traducción simplificado para BOT-vCSGO-Beta
Compatible con el sistema antiguo de Languages/
"""

import json
import os
from pathlib import Path
from typing import Dict, Any

class Translator:
    """Gestor de traducciones compatible con el sistema antiguo"""
    
    def __init__(self, script_name: str, lang_code: str = 'es'):
        self.script_name = script_name
        self.lang_code = lang_code
        self.translations = self.load_translations()
    
    def load_translations(self) -> Dict[str, str]:
        """Carga las traducciones desde el archivo JSON"""
        # Intentar múltiples ubicaciones para compatibilidad
        possible_paths = [
            # Nueva ubicación
            Path('config') / 'languages' / self.lang_code / f'{self.script_name}_{self.lang_code}.json',
            # Ubicación antigua
            Path('Languages') / self.lang_code / f'{self.script_name}_{self.lang_code}.json',
            # Ubicación de desarrollo
            Path(__file__).parent.parent.parent / 'Languages' / self.lang_code / f'{self.script_name}_{self.lang_code}.json'
        ]
        
        for path in possible_paths:
            if path.exists():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception as e:
                    print(f"Error cargando traducciones desde {path}: {e}")
        
        # Si no se encuentra archivo, retornar diccionario vacío
        return {}
    
    def gettext(self, key: str, **kwargs) -> str:
        """
        Obtiene una traducción y la formatea con los parámetros dados
        
        Args:
            key: Clave de traducción
            **kwargs: Parámetros para formatear
            
        Returns:
            Texto traducido o la clave si no se encuentra
        """
        template = self.translations.get(key, key)
        
        try:
            return template.format(**kwargs)
        except Exception:
            # Si hay error al formatear, retornar el template sin formato
            return template

# Traducciones por defecto para scrapers
DEFAULT_TRANSLATIONS = {
    'waxpeer': {
        'es': {
            'data_saved': 'Datos guardados correctamente en {filename}',
            'data_fetched': 'Datos obtenidos de Waxpeer correctamente. Total de ítems: {count}',
            'unexpected_format': 'Formato de datos inesperado en la respuesta de Waxpeer.',
            'error_fetching_data': 'Error al obtener datos de Waxpeer: {error}',
            'waiting': 'Esperando {seconds} segundos para la próxima actualización...'
        },
        'en': {
            'data_saved': 'Data saved successfully to {filename}',
            'data_fetched': 'Data fetched from Waxpeer successfully. Total items: {count}',
            'unexpected_format': 'Unexpected data format in Waxpeer response.',
            'error_fetching_data': 'Error fetching data from Waxpeer: {error}',
            'waiting': 'Waiting {seconds} seconds for the next update...'
        }
    },
    'csdeals': {
        'es': {
            'success_message': 'Datos de CsDeals obtenidos correctamente. Total de ítems: {total_items}',
            'unexpected_format': 'Formato de datos inesperado en la respuesta de CsDeals.',
            'fetch_error': 'Error al obtener datos de CsDeals: {error}',
            'waiting_message': 'Esperando {seconds} segundos para la próxima actualización...'
        },
        'en': {
            'success_message': 'Successfully fetched CsDeals data. Total items: {total_items}',
            'unexpected_format': 'Unexpected data format in CsDeals response.',
            'fetch_error': 'Error fetching CsDeals data: {error}',
            'waiting_message': 'Waiting {seconds} seconds for the next update...'
        }
    },
    'rentabilidad': {
        'es': {
            'CLEAR_CONSOLE': 'LIMPIAR_CONSOLA',
            'PROFITEABLE_FLIPS': '=== COMPRAS RENTABLES ===',
            'ITEM_NAME': 'Item',
            'BUY_PRICE': 'Comprar en',
            'STEAM': 'Steam',
            'AFTER_FEE': 'después de la tarifa',
            'SELL_PRICE': 'Vender en',
            'FOR': 'por',
            'LINK': 'Link',
            'PROFITABILITY': 'Rentabilidad',
            'ERROR_CALCULATING_PROFITABILITY': 'Error al calcular rentabilidad',
            'WAITING_FOR_NEXT_UPDATE': 'Esperando próxima actualización...'
        },
        'en': {
            'CLEAR_CONSOLE': 'CLEAR_CONSOLE',
            'PROFITEABLE_FLIPS': '=== PROFITABLE FLIPS ===',
            'ITEM_NAME': 'Item',
            'BUY_PRICE': 'Buy at',
            'STEAM': 'Steam',
            'FOR': 'for',
            'AFTER_FEE': 'after fee',
            'SELL_PRICE': 'Sell at',
            'LINK': 'Link',
            'PROFITABILITY': 'Profitability',
            'ERROR_CALCULATING_PROFITABILITY': 'Error calculating profitability',
            'WAITING_FOR_NEXT_UPDATE': 'Waiting for next update...'
        }
    }
}

def get_translator(script_name: str, lang_code: str = None) -> Translator:
    """
    Obtiene un traductor para un script específico
    
    Args:
        script_name: Nombre del script (ej: 'waxpeer', 'csdeals')
        lang_code: Código de idioma (None = usar configuración)
        
    Returns:
        Instancia de Translator
    """
    if lang_code is None:
        # Intentar obtener desde configuración
        try:
            from .config_manager import get_config_manager
            config = get_config_manager()
            lang_code = config.get_language_config()
        except:
            lang_code = 'es'  # Por defecto español
    
    translator = Translator(script_name, lang_code)
    
    # Si no hay traducciones cargadas, usar las por defecto
    if not translator.translations and script_name in DEFAULT_TRANSLATIONS:
        translator.translations = DEFAULT_TRANSLATIONS[script_name].get(lang_code, {})
    
    return translator