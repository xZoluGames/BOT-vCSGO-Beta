# backend/core/base_scraper.py

import os
import requests
import json
import time
import random
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path
import sys
from loguru import logger
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from functools import lru_cache
import threading



# Importar nuestro gestor de configuración
from .config_manager import get_config_manager
from .proxy_manager import ProxyManager
from backend.services.database_service import get_database_service
from backend.services.notification_service import get_notification_service
class BaseScraper(ABC):
    """
    Clase base para todos los scrapers de BOT-vCSGO-Beta
    
    Esta clase unifica la funcionalidad de scrapers con y sin proxy,
    eliminando la necesidad de tener archivos separados _proxy y _noproxy
    """
    
    def __init__(self, 
                 platform_name: str,
                 use_proxy: Optional[bool] = None,
                 custom_config: Optional[Dict[str, Any]] = None):
        """
        Inicializa el scraper base
        
        Args:
            platform_name: Nombre de la plataforma (ej: 'Waxpeer', 'CSDeals')
            use_proxy: Forzar uso de proxy (None = usar config global)
            custom_config: Configuración personalizada (sobrescribe la global)
        """
        self.platform_name = platform_name
        self.config_manager = get_config_manager()
        
        # Cargar configuración de la plataforma
        self.config = self.config_manager.get_scraper_config(platform_name)
        if os.getenv('DEV_MODE') == 'true':
            return self.get_mock_data()
        # Aplicar configuración personalizada si se proporciona
        if custom_config:
            self.config.update(custom_config)
        
        # Determinar si usar proxy
        if use_proxy is not None:
            self.use_proxy = use_proxy
        else:
            self.use_proxy = self.config.get("use_proxy", False)
        
        # Configurar proxy manager si es necesario
        self.proxy_manager = None
        if self.use_proxy:
            proxy_list = self.config_manager.get_proxy_list()
            if proxy_list:
                self.proxy_manager = ProxyManager(proxy_list)
                logger.info(f"{platform_name}: Usando {len(proxy_list)} proxies")
            else:
                logger.warning(f"{platform_name}: Proxies habilitados pero no se encontró proxy.txt")
                self.use_proxy = False
        
        # Configurar logger específico para este scraper
        self.logger = logger.bind(scraper=platform_name)
        
        # Headers por defecto
        self.headers = {
            'User-Agent': self._get_random_user_agent(),
            'Accept': 'application/json',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        
        # Estadísticas de ejecución
        self.stats = {
    'requests_made': 0,
    'requests_failed': 0,
    'items_fetched': 0,
    'last_run': None,
    'last_error': None
}
        # Rate limiting
        try:
            from backend.core.rate_limiter import get_rate_limiter
            self.rate_limiter = get_rate_limiter()
        except:
            self.rate_limiter = None
        
        # Cache service
        try:
            from backend.services.cache_service import get_cache_service
            self.cache_service = get_cache_service()
        except:
            self.cache_service = None

        self.db_service = get_database_service()
        self.notification_service = get_notification_service()
        self.use_database = self.config_manager.settings.get('database', {}).get('enabled', True)
        # Sesión de requests para reutilizar conexiones
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def _get_random_user_agent(self) -> str:
        """Retorna un User-Agent aleatorio para parecer más humano"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        return random.choice(user_agents)
    
    def _get_request_kwargs(self, custom_headers: Optional[Dict] = None) -> Dict[str, Any]:
        """Construye los kwargs para la petición HTTP"""
        kwargs = {
            'timeout': self.config.get('timeout', 10),
            'allow_redirects': True,
            'verify': True
        }
        
        # Headers personalizados
        if custom_headers:
            kwargs['headers'] = {**self.session.headers, **custom_headers}
        
        # Configurar proxy si está habilitado
        if self.use_proxy and self.proxy_manager:
            proxy = self.proxy_manager.get_proxy()
            if proxy:
                kwargs['proxies'] = {'http': proxy, 'https': proxy}
                self.logger.debug(f"Usando proxy: {proxy}")
        
        return kwargs
    
# Correcciones para backend/core/base_scraper.py

# En el método make_request, cambiar la primera parte a:
    def make_request(self, url: str, method: str = 'GET', max_retries: Optional[int] = None, **kwargs) -> Optional[requests.Response]:
        """
        Realiza una petición HTTP con reintentos y manejo de errores
        """
        # Rate limiting
        if self.rate_limiter and hasattr(self, 'platform_name'):
            self.rate_limiter.wait_if_needed(self.platform_name.lower())
        # Definir max_retries ANTES de usarlo
        if max_retries is None:
            max_retries = self.config.get('max_retries', 5)
        
        retry_delay = self.config.get('retry_delay', 2)
        
        # Obtener kwargs base
        request_kwargs = self._get_request_kwargs(kwargs.pop('headers', None))
        request_kwargs.update(kwargs)
        
        for attempt in range(max_retries):
            try:
                self.stats['requests_made'] += 1
                
                # Realizar petición
                if method.upper() == 'GET':
                    response = self.session.get(url, **request_kwargs)
                elif method.upper() == 'POST':
                    response = self.session.post(url, **request_kwargs)
                else:
                    raise ValueError(f"Método no soportado: {method}")
                
                # Verificar respuesta
                response.raise_for_status()
                
                # Si llegamos aquí, la petición fue exitosa
                self.logger.debug(f"Petición exitosa a {url} (intento {attempt + 1})")
                return response
                
            except requests.exceptions.RequestException as e:
                self.stats['requests_failed'] += 1
                self.stats['last_error'] = str(e)
                
                self.logger.warning(
                    f"Error en petición (intento {attempt + 1}/{max_retries}): {e}"
                )
                
                # Si estamos usando proxy y falla, marcar como malo y obtener otro
                if self.use_proxy and self.proxy_manager and 'proxies' in request_kwargs:
                    proxy = request_kwargs['proxies']['http']
                    self.proxy_manager.mark_failed(proxy)
                    
                    # Obtener nuevo proxy para el siguiente intento
                    new_proxy = self.proxy_manager.get_proxy()
                    if new_proxy:
                        request_kwargs['proxies'] = {'http': new_proxy, 'https': new_proxy}
                
                # Si es el último intento, no esperar
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (attempt + 1)  # Backoff exponencial
                    self.logger.info(f"Esperando {wait_time} segundos antes de reintentar...")
                    time.sleep(wait_time)
                    
            except Exception as e:
                self.logger.error(f"Error no manejado: {e}")
                
                # Notificar error crítico si tenemos notification_service
                if hasattr(self, 'notification_service') and self.notification_service:
                    if "timeout" not in str(e).lower():  # No notificar timeouts comunes
                        self.notification_service.notify_scraper_error(
                            scraper_name=self.platform_name,
                            error=str(e)
                        )
        
        self.logger.error(f"Falló después de {max_retries} intentos: {url}")
        return None
    
    def save_data(self, data: List[Dict]) -> bool:
        """
        Guarda los datos en formato JSON y en la base de datos
        
        Args:
            data: Lista de items a guardar
            
        Returns:
            bool: True si se guardó correctamente
        """
        try:
            # Guardar en JSON (mantener compatibilidad)
            filename = f"{self.platform_name.lower()}_data.json"
            filepath = self.config_manager.get_json_output_path(filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            self.logger.info(f"Datos guardados en {filepath}")
            
            # Guardar en base de datos si está habilitada
            if self.use_database:
                try:
                    self.db_service.save_scraper_data(self.platform_name.lower(), data)
                    self.logger.info(f"Datos guardados en base de datos")
                except Exception as e:
                    self.logger.error(f"Error guardando en base de datos: {e}")
                    # No fallar si la DB falla, ya tenemos el JSON
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error guardando datos: {e}")
            return False
    

    @abstractmethod
    def fetch_data(self) -> List[Dict]:
        """
        Método abstracto que cada scraper debe implementar.
        Debe retornar una lista de diccionarios con formato:
        [
            {
                'Item': 'nombre_del_item',
                'Price': 'precio',
                'URL': 'url_opcional'
            },
            ...
        ]
        """
        pass
    
    
    def get_cached_data(self, cache_key: str, fetch_func, ttl: int = 300):
        """Obtiene datos del caché o los fetcha si no existen"""
        if self.cache_service:
            cached = self.cache_service.get(cache_key)
            if cached:
                self.logger.debug(f"Cache hit para {cache_key}")
                return cached
        
        # Fetch fresh data
        data = fetch_func()
        
        if data and self.cache_service:
            self.cache_service.set(cache_key, data, ttl)
        
        return data

    @abstractmethod
    def parse_response(self, response: requests.Response) -> List[Dict]:
        """
        Método abstracto para parsear la respuesta.
        Cada scraper implementa su propia lógica de parsing.
        """
        pass
    
    def validate_item(self, item: Dict) -> bool:
        """
        Valida que un item tenga los campos requeridos
        
        Args:
            item: Diccionario con datos del item
            
        Returns:
            True si el item es válido
        """
        required_fields = ['Item', 'Price']
        
        # Verificar campos requeridos
        for field in required_fields:
            if field not in item:
                self.logger.warning(f"Item inválido, falta campo {field}: {item}")
                return False
        
        # Verificar que el precio sea válido
        try:
            price = float(str(item['Price']).replace(',', '.'))
            if price < 0:
                self.logger.warning(f"Precio negativo en item: {item}")
                return False
        except (ValueError, TypeError):
            self.logger.warning(f"Precio inválido en item: {item}")
            return False
        
        return True
    
    def run_once(self) -> List[Dict]:
        """Ejecuta el scraper una vez y retorna los datos"""
        self.logger.info(f"Iniciando scraper {self.platform_name}")
        self.stats['last_run'] = datetime.now()
        
        try:
            # Obtener datos
            data = self.fetch_data()
            
            if data:
                # Validar items
                valid_data = [item for item in data if self.validate_item(item)]
                invalid_count = len(data) - len(valid_data)
                
                if invalid_count > 0:
                    self.logger.warning(f"Se descartaron {invalid_count} items inválidos")
                
                # Actualizar estadísticas
                self.stats['items_fetched'] = len(valid_data)
                
                # Guardar datos
                self.save_data(valid_data)
                
                self.logger.success(
                    f"Scraper completado: {len(valid_data)} items válidos obtenidos"
                )
                
                return valid_data
            else:
                self.logger.warning("No se obtuvieron datos")
                return []
                
        except Exception as e:
            self.logger.error(f"Error ejecutando scraper: {e}")
            self.stats['last_error'] = str(e)
            return []
    
    def run_forever(self, interval: Optional[int] = None):
        """
        Ejecuta el scraper en bucle infinito
        
        Args:
            interval: Segundos entre ejecuciones (None = usar config)
        """
        if interval is None:
            interval = self.config_manager.get_update_interval(self.platform_name)
        
        self.logger.info(
            f"Iniciando bucle infinito para {self.platform_name} "
            f"(intervalo: {interval}s, proxy: {'Sí' if self.use_proxy else 'No'})"
        )
        
        while True:
            try:
                self.run_once()
                
                self.logger.info(f"Esperando {interval} segundos...")
                time.sleep(interval)
                
            except KeyboardInterrupt:
                self.logger.info("Detenido por el usuario")
                break
                
            except Exception as e:
                self.logger.error(f"Error en bucle: {e}")
                self.logger.info(f"Esperando {interval} segundos antes de reintentar...")
                time.sleep(interval)
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de ejecución del scraper"""
        return self.stats.copy()
    
    def __enter__(self):
        """Context manager para limpieza automática"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cierra la sesión al salir"""
        self.session.close()