# backend/core/config_manager.py

import json
import os
import sys
from typing import Dict, Any, Optional
from pathlib import Path
import yaml
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class ConfigManager:
    """
    Gestor centralizado de configuración para BOT-vCSGO-Beta
    Maneja todas las configuraciones del proyecto de forma unificada
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Inicializa el gestor de configuración
        
        Args:
            base_path: Ruta base del proyecto. Si no se proporciona, la detecta automáticamente
        """
        if base_path is None:
            # Detectar si estamos en desarrollo o en un ejecutable compilado
            if getattr(sys, 'frozen', False):
                self.base_path = Path(sys._MEIPASS)
            else:
                # Subir dos niveles desde backend/core hasta la raíz del proyecto
                self.base_path = Path(__file__).parent.parent.parent
        else:
            self.base_path = Path(base_path)
            
        self.config_path = self.base_path / "config"
        self.json_path = self.base_path / "JSON"
        self.logs_path = self.base_path / "logs"
        
        # Crear directorios si no existen
        self.json_path.mkdir(exist_ok=True)
        self.logs_path.mkdir(exist_ok=True)
        
        # Cache de configuraciones cargadas
        self._config_cache = {}
        
        # Cargar configuración principal
        self.settings = self._load_settings()
        
        # Asegurar que existan las claves necesarias
        self._ensure_default_settings()
        
    def _load_settings(self) -> Dict[str, Any]:
        """Carga la configuración principal del proyecto"""
        settings_file = self.config_path / "settings.json"
        
        if not settings_file.exists():
            # Crear configuración por defecto si no existe
            default_settings = self._get_default_settings()
            self._save_json(settings_file, default_settings)
            return default_settings
            
        return self._load_json(settings_file)
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """Retorna la configuración por defecto del proyecto"""
        return {
            "project_name": "BOT-vCSGO-Beta",
            "version": "2.0.0",
            "language": "es",
            "update_intervals": {
                "steam": 3600,      # 1 hora
                "fast_platforms": 60,    # 1 minuto
                "slow_platforms": 300    # 5 minutos
            },
            "proxy_settings": {
                "enabled": False,    # Por defecto sin proxy
                "rotation_enabled": True,
                "timeout": 10,
                "max_retries": 5,
                "retry_delay": 2
            },
            "logging": {
                "level": "INFO",
                "format": "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} | {message}",
                "rotation": "1 day",
                "retention": "7 days"
            },
            "database": {
                "type": "sqlite",
                "path": "csgo_arbitrage.db"
            }
        }
    
    def _ensure_default_settings(self):
        """Asegura que todas las claves necesarias existan en settings"""
        default = self._get_default_settings()
        
        # Función recursiva para mergear configuraciones
        def deep_merge(base: dict, updates: dict) -> dict:
            for key, value in updates.items():
                if key not in base:
                    base[key] = value
                elif isinstance(base[key], dict) and isinstance(value, dict):
                    deep_merge(base[key], value)
            return base
        
        # Mergear defaults con settings actuales
        self.settings = deep_merge(self.settings, default)
        
        # Guardar cambios si hubo actualizaciones
        self._save_json(self.config_path / "settings.json", self.settings)
    
    def get_scraper_config(self, platform: str) -> Dict[str, Any]:
        """
        Obtiene la configuración específica de un scraper
        
        Args:
            platform: Nombre de la plataforma (ej: 'waxpeer', 'csdeals')
            
        Returns:
            Configuración del scraper
        """
        # Intentar cargar desde caché
        cache_key = f"scraper_{platform}"
        if cache_key in self._config_cache:
            return self._config_cache[cache_key]
            
        # Cargar configuración de plataformas
        platforms_file = self.config_path / "scrapers" / "platforms.json"
        if not platforms_file.exists():
            # Crear archivo con configuraciones por defecto
            default_platforms = self._get_default_platforms_config()
            self._save_json(platforms_file, default_platforms)
            platforms_config = default_platforms
        else:
            platforms_config = self._load_json(platforms_file)
            
        # Obtener configuración específica de la plataforma
        platform_config = platforms_config.get(platform.lower(), {})
        
        # Mezclar con configuración global
        scraper_config = {
            "platform_name": platform,
            "use_proxy": self.settings["proxy_settings"]["enabled"],
            "timeout": self.settings["proxy_settings"]["timeout"],
            "max_retries": self.settings["proxy_settings"]["max_retries"],
            "retry_delay": self.settings["proxy_settings"]["retry_delay"],
            **platform_config  # La configuración específica sobrescribe la global
        }
        
        # Guardar en caché
        self._config_cache[cache_key] = scraper_config
        
        return scraper_config
    
    def _get_default_platforms_config(self) -> Dict[str, Any]:
        """Retorna la configuración por defecto de las plataformas"""
        return {
            "waxpeer": {
                "api_url": "https://api.waxpeer.com/v1/prices?game=csgo&minified=0&single=0",
                "update_interval": 60,
                "requires_auth": True,
                "api_key_env": "WAXPEER_API_KEY"
            },
            "csdeals": {
                "api_url": "https://cs.deals/API/IPricing/GetLowestPrices/v1?appid=730",
                "update_interval": 60,
                "requires_auth": False
            },
            "steam": {
                "base_url": "https://steamcommunity.com/market/",
                "update_interval": 3600,
                "requires_auth": False,
                "rate_limit": 20  # requests por minuto
            },
            "empire": {
                "api_url": "https://csgoempire.com/api/v2/trading/items",
                "update_interval": 30,
                "requires_auth": True,
                "api_key_env": "EMPIRE_API_KEY"
            },
            "skinport": {
                "api_url": "https://api.skinport.com/v1/items?app_id=730&currency=USD",
                "update_interval": 300,
                "requires_auth": False
            },
            "manncostore": {
                "base_url": "https://mannco.store/items/get",
                "update_interval": 300,
                "requires_selenium": True
            },
            "cstrade": {
                "api_url": "https://cdn.cs.trade:2096/api/prices_CSGO",
                "update_interval": 60,
                "requires_auth": False,
                "bonus_rate": 50  # Tasa de bono específica de CsTrade
            },
            "waxpeer": {
                "api_url": "https://api.waxpeer.com/v1/prices?game=csgo&minified=0&single=0",
                "update_interval": 60,
                "requires_auth": False
            },
            "bitskins": {
                "api_url": "https://api.bitskins.com/market/insell/730",
                "update_interval": 60,
                "requires_auth": False
            },
            "tradeit": {
                "base_url": "https://tradeit.gg/api/v2/inventory/data",
                "update_interval": 120,
                "requires_selenium": True
            }
        }
    
    def get_notification_thresholds(self) -> Dict[str, float]:
        """Obtiene los umbrales de rentabilidad para notificaciones"""
        thresholds_file = self.config_path / "notifications" / "thresholds.json"
        
        if not thresholds_file.exists():
            # Valores por defecto de tu configuración actual
            default_thresholds = {
                "profitability_csdeals": 0.5,
                "profitability_cstrade": 0.5,
                "profitability_manncostore": 0.5,
                "profitability_rapidskins": 0.5,
                "profitability_skinport": 0.5,
                "profitability_tradeit": -0.1,
                "profitability_waxpeer": 0.5,
                "profitability_empire": 0.5,
                "profitability_marketcsgo": 0.5,
                "profitability_bitskins": 0.5,
                "profitability_skinout": 0.5,
                "profitability_white": 0.5,
                "profitability_skindeck": 0.5
            }
            self._save_json(thresholds_file, default_thresholds)
            return default_thresholds
            
        return self._load_json(thresholds_file)
    
    def get_api_key(self, service: str) -> Optional[str]:
        """
        Obtiene una API key del entorno o archivo de configuración
        
        Args:
            service: Nombre del servicio (ej: 'WAXPEER', 'EMPIRE')
            
        Returns:
            API key o None si no se encuentra
        """
        # Primero intentar desde variable de entorno
        env_key = f"{service.upper()}_API_KEY"
        api_key = os.getenv(env_key)
        
        if api_key:
            return api_key
            
        # Si no está en env, intentar desde archivo (NO RECOMENDADO para producción)
        api_keys_file = self.config_path / "api_keys.json"
        if api_keys_file.exists():
            api_keys = self._load_json(api_keys_file)
            return api_keys.get(service.lower())
            
        return None
    
    def get_language_config(self) -> str:
        """Obtiene el idioma configurado"""
        return self.settings.get("language", "es")
    
    def get_proxy_list(self) -> list:
        """Carga la lista de proxies desde archivo"""
        proxy_file = self.base_path / "proxy.txt"
        
        if not proxy_file.exists():
            return []
            
        with open(proxy_file, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    
    def set_proxy_enabled(self, enabled: bool):
        """Habilita o deshabilita el uso de proxies globalmente"""
        self.settings["proxy_settings"]["enabled"] = enabled
        self._save_json(self.config_path / "settings.json", self.settings)
        # Limpiar caché para forzar recarga
        self._config_cache.clear()
    
    def get_update_interval(self, platform: str) -> int:
        """Obtiene el intervalo de actualización para una plataforma"""
        scraper_config = self.get_scraper_config(platform)
        return scraper_config.get("update_interval", 60)
    
    def _load_json(self, filepath: Path) -> Dict[str, Any]:
        """Carga un archivo JSON"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error cargando {filepath}: {e}")
            return {}
    
    def _save_json(self, filepath: Path, data: Dict[str, Any]):
        """Guarda datos en un archivo JSON"""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    
    def get_json_output_path(self, filename: str) -> Path:
        """Obtiene la ruta completa para guardar un archivo JSON de salida"""
        return self.json_path / filename
    
    def get_log_path(self, filename: str) -> Path:
        """Obtiene la ruta completa para un archivo de log"""
        return self.logs_path / filename


# Instancia global del ConfigManager (Singleton)
_config_manager_instance = None

def get_config_manager() -> ConfigManager:
    """Obtiene la instancia global del ConfigManager"""
    global _config_manager_instance
    if _config_manager_instance is None:
        _config_manager_instance = ConfigManager()
    return _config_manager_instance


# Para importación directa
config = get_config_manager()