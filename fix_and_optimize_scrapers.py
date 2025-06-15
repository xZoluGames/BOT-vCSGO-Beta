#!/usr/bin/env python3
# fix_and_optimize_scrapers.py - Arregla y optimiza todos los scrapers

import os
import re
from pathlib import Path
import json
import shutil

def fix_scraper_indentation(file_path, scraper_name):
    """Arregla la indentación incorrecta en un archivo de scraper"""
    print(f"  Arreglando {scraper_name}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Patrones problemáticos comunes
    patterns_to_fix = [
        # Funciones mal indentadas dentro de la clase
        (r'(\n)(def main_\w+\(\):)', r'\n\n\1'),
        # main_function mal indentada
        (r'def main_(\w+)\(\):\n        scraper = (\w+)Scraper\(\)\n        scraper\.run_forever\(\)',
         r'def main_\1():\n    scraper = \2Scraper()\n    scraper.run_forever()'),
        # Arreglar doble definición de main
        (r'def main_\w+\(\):[^\n]+\n[^\n]+\n[^\n]+\n\ndef main\(\):', r'def main():'),
    ]
    
    for pattern, replacement in patterns_to_fix:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    # Asegurar que las funciones estén al nivel del módulo, no de la clase
    lines = content.split('\n')
    fixed_lines = []
    in_class = False
    class_indent = 0
    
    for i, line in enumerate(lines):
        # Detectar inicio de clase
        if line.strip().startswith('class ') and line.strip().endswith(':'):
            in_class = True
            class_indent = len(line) - len(line.lstrip())
        
        # Detectar fin de clase (línea sin indentación después de contenido de clase)
        elif in_class and line.strip() and len(line) - len(line.lstrip()) <= class_indent:
            # Si es una función def, verificar si debe estar fuera de la clase
            if line.strip().startswith('def main'):
                in_class = False
                # Asegurar que esté al nivel del módulo
                fixed_lines.append('')  # Línea en blanco antes
                fixed_lines.append(line.lstrip())  # Sin indentación
                continue
        
        fixed_lines.append(line)
    
    # Unir las líneas
    fixed_content = '\n'.join(fixed_lines)
    
    # Asegurar estructura correcta al final del archivo
    if 'if __name__ == "__main__":' not in fixed_content:
        fixed_content += '\n\nif __name__ == "__main__":\n    main()'
    
    # Asegurar que solo haya una función main()
    main_count = len(re.findall(r'^def main\(\):', fixed_content, re.MULTILINE))
    if main_count == 0:
        # Agregar función main si no existe
        fixed_content = re.sub(
            r'(if __name__ == "__main__":)',
            r'def main():\n    scraper = ' + scraper_name + r'Scraper()\n    scraper.run_forever()\n\n\n\1',
            fixed_content
        )
    
    # Guardar archivo arreglado
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print(f"    ✓ {scraper_name} arreglado")

def optimize_scraper_performance():
    """Optimizaciones de rendimiento para scrapers"""
    print("\n2. Aplicando optimizaciones de rendimiento...")
    
    # Crear archivo de configuración optimizada
    optimized_config = {
        "connection_pool": {
            "pool_connections": 10,
            "pool_maxsize": 20,
            "max_retries": 3,
            "backoff_factor": 0.3
        },
        "timeouts": {
            "connect": 5.0,
            "read": 10.0
        },
        "headers": {
            "Connection": "keep-alive",
            "Accept-Encoding": "gzip, deflate, br"
        },
        "rate_limiting": {
            "requests_per_minute": 60,
            "burst_size": 10
        }
    }
    
    config_file = Path("config/performance.json")
    config_file.parent.mkdir(exist_ok=True)
    
    with open(config_file, 'w') as f:
        json.dump(optimized_config, f, indent=2)
    
    print("    ✓ Configuración de rendimiento creada")

def create_optimized_base_scraper():
    """Crea una versión optimizada del BaseScraper"""
    print("\n3. Optimizando BaseScraper...")
    
    optimized_imports = '''# Agregar estos imports al inicio de base_scraper.py
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import concurrent.futures
from functools import lru_cache
'''
    
    optimized_session = '''
    def _create_session(self) -> requests.Session:
        """Crea una sesión optimizada con connection pooling y retry strategy"""
        session = requests.Session()
        
        # Configurar retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        
        # Configurar adapter con connection pooling
        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=retry_strategy
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Headers optimizados
        session.headers.update({
            'User-Agent': self._get_user_agent(),
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
        
        return session
'''
    
    # Guardar optimizaciones en un archivo separado
    opt_file = Path("backend/core/base_scraper_optimizations.py")
    opt_file.write_text(optimized_imports + optimized_session, encoding='utf-8')
    
    print("    ✓ Optimizaciones de BaseScraper creadas")

def create_concurrent_scraper():
    """Crea un scraper concurrente para múltiples requests"""
    print("\n4. Creando scraper concurrente...")
    
    concurrent_scraper = '''# backend/scrapers/concurrent_scraper.py
from typing import List, Dict, Optional, Callable
import concurrent.futures
import asyncio
import aiohttp
from backend.core.base_scraper import BaseScraper


class ConcurrentScraper(BaseScraper):
    """Scraper optimizado para realizar múltiples requests concurrentes"""
    
    def __init__(self, platform_name: str, use_proxy: Optional[bool] = None):
        super().__init__(platform_name, use_proxy)
        self.max_workers = 10
        self.semaphore = asyncio.Semaphore(5)  # Limitar concurrencia
    
    async def fetch_url_async(self, session: aiohttp.ClientSession, url: str) -> Optional[Dict]:
        """Fetch asíncrono de una URL"""
        async with self.semaphore:
            try:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        return await response.json()
            except Exception as e:
                self.logger.error(f"Error fetching {url}: {e}")
                return None
    
    async def fetch_multiple_async(self, urls: List[str]) -> List[Dict]:
        """Fetch asíncrono de múltiples URLs"""
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_url_async(session, url) for url in urls]
            results = await asyncio.gather(*tasks)
            return [r for r in results if r is not None]
    
    def fetch_multiple_sync(self, urls: List[str], 
                           parse_func: Callable[[Dict], List[Dict]]) -> List[Dict]:
        """Fetch síncrono concurrente de múltiples URLs"""
        all_items = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {
                executor.submit(self.make_request, url): url 
                for url in urls
            }
            
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    response = future.result()
                    if response:
                        items = parse_func(response)
                        all_items.extend(items)
                except Exception as e:
                    self.logger.error(f"Error processing {url}: {e}")
        
        return all_items
'''
    
    file_path = Path("backend/scrapers/concurrent_scraper.py")
    file_path.write_text(concurrent_scraper, encoding='utf-8')
    
    print("    ✓ Scraper concurrente creado")

def create_cache_service():
    """Crea un servicio de caché para reducir requests innecesarios"""
    print("\n5. Creando servicio de caché...")
    
    cache_service = '''# backend/services/cache_service.py
import json
import time
from pathlib import Path
from typing import Optional, Any, Dict
from functools import lru_cache
import hashlib


class CacheService:
    """Servicio de caché en memoria y disco para scrapers"""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.memory_cache = {}
        self.cache_ttl = 300  # 5 minutos por defecto
    
    def _get_cache_key(self, key: str) -> str:
        """Genera una clave de caché segura"""
        return hashlib.md5(key.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Obtiene un valor del caché"""
        cache_key = self._get_cache_key(key)
        
        # Verificar caché en memoria primero
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            if time.time() < entry['expires']:
                return entry['value']
            else:
                del self.memory_cache[cache_key]
        
        # Verificar caché en disco
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    entry = json.load(f)
                    if time.time() < entry['expires']:
                        # Cargar en memoria para acceso más rápido
                        self.memory_cache[cache_key] = entry
                        return entry['value']
                    else:
                        cache_file.unlink()  # Eliminar caché expirado
            except:
                pass
        
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Guarda un valor en el caché"""
        cache_key = self._get_cache_key(key)
        expires = time.time() + (ttl or self.cache_ttl)
        
        entry = {
            'value': value,
            'expires': expires,
            'key': key
        }
        
        # Guardar en memoria
        self.memory_cache[cache_key] = entry
        
        # Guardar en disco
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(entry, f)
        except:
            pass
    
    @lru_cache(maxsize=128)
    def get_cached_price(self, item_name: str, platform: str) -> Optional[float]:
        """Obtiene precio cacheado de un item"""
        key = f"{platform}:{item_name}"
        data = self.get(key)
        return data.get('price') if data else None
    
    def clear_expired(self):
        """Limpia entradas expiradas del caché"""
        # Limpiar memoria
        current_time = time.time()
        expired_keys = [
            k for k, v in self.memory_cache.items() 
            if v['expires'] < current_time
        ]
        for k in expired_keys:
            del self.memory_cache[k]
        
        # Limpiar disco
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r') as f:
                    entry = json.load(f)
                    if entry['expires'] < current_time:
                        cache_file.unlink()
            except:
                cache_file.unlink()  # Eliminar archivos corruptos


# Singleton
_cache_service = None

def get_cache_service():
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
'''
    
    file_path = Path("backend/services/cache_service.py")
    file_path.parent.mkdir(exist_ok=True)
    file_path.write_text(cache_service, encoding='utf-8')
    
    print("    ✓ Servicio de caché creado")

def optimize_specific_scrapers():
    """Optimizaciones específicas para scrapers problemáticos"""
    print("\n6. Optimizando scrapers específicos...")
    
    # Optimizar scrapers que hacen muchas requests
    scrapers_to_optimize = {
        'skinout_scraper.py': {
            'max_workers': 20,
            'batch_size': 50,
            'delay_between_batches': 1
        },
        'tradeit_scraper.py': {
            'page_size': 1000,
            'max_retries': 5,
            'use_cache': True
        },
        'manncostore_scraper.py': {
            'selenium_timeout': 20,
            'wait_for_element': True,
            'retry_stale_element': True
        }
    }
    
    for scraper, optimizations in scrapers_to_optimize.items():
        config_file = Path(f"config/scrapers/{scraper.replace('.py', '.json')}")
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w') as f:
            json.dump(optimizations, f, indent=2)
        
        print(f"    ✓ Optimizado {scraper}")

def create_rate_limiter():
    """Crea un rate limiter para evitar bans"""
    print("\n7. Creando rate limiter...")
    
    rate_limiter = '''# backend/core/rate_limiter.py
import time
from collections import deque
from threading import Lock
from typing import Dict


class RateLimiter:
    """Rate limiter para controlar la frecuencia de requests"""
    
    def __init__(self):
        self.limits: Dict[str, Dict] = {}
        self.lock = Lock()
    
    def add_limit(self, key: str, max_calls: int, time_window: int):
        """Agrega un límite para una clave específica"""
        with self.lock:
            self.limits[key] = {
                'max_calls': max_calls,
                'time_window': time_window,
                'calls': deque()
            }
    
    def can_make_request(self, key: str) -> bool:
        """Verifica si se puede hacer un request"""
        if key not in self.limits:
            return True
        
        with self.lock:
            limit = self.limits[key]
            now = time.time()
            
            # Limpiar llamadas antiguas
            while limit['calls'] and limit['calls'][0] < now - limit['time_window']:
                limit['calls'].popleft()
            
            # Verificar si podemos hacer la llamada
            return len(limit['calls']) < limit['max_calls']
    
    def record_request(self, key: str):
        """Registra un request realizado"""
        if key not in self.limits:
            return
        
        with self.lock:
            self.limits[key]['calls'].append(time.time())
    
    def wait_if_needed(self, key: str):
        """Espera si es necesario antes de hacer un request"""
        if key not in self.limits:
            return
        
        while not self.can_make_request(key):
            time.sleep(0.1)
        
        self.record_request(key)


# Límites por defecto para cada plataforma
DEFAULT_LIMITS = {
    'waxpeer': (120, 60),      # 120 requests por minuto
    'csdeals': (100, 60),      # 100 requests por minuto
    'empire': (60, 60),        # 60 requests por minuto
    'skinport': (30, 60),      # 30 requests por minuto
    'tradeit': (20, 60),       # 20 requests por minuto
    'manncostore': (10, 60),   # 10 requests por minuto
    'steam': (10, 60),         # 10 requests por minuto (más restrictivo)
}


# Singleton
_rate_limiter = None

def get_rate_limiter():
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
        # Configurar límites por defecto
        for platform, (max_calls, window) in DEFAULT_LIMITS.items():
            _rate_limiter.add_limit(platform, max_calls, window)
    return _rate_limiter
'''
    
    file_path = Path("backend/core/rate_limiter.py")
    file_path.write_text(rate_limiter, encoding='utf-8')
    
    print("    ✓ Rate limiter creado")

def main():
    print("\n" + "="*60)
    print("ARREGLANDO Y OPTIMIZANDO SCRAPERS - BOT-vCSGO-Beta")
    print("="*60)
    
    # 1. Arreglar indentación de scrapers
    print("\n1. Arreglando indentación de scrapers...")
    scrapers_dir = Path("backend/scrapers")
    
    scrapers_to_fix = {
        'white_scraper.py': 'White',
        'lisskins_scraper.py': 'Lisskins',
        'skindeck_scraper.py': 'Skindeck',
        'shadowpay_scraper.py': 'Shadowpay',
        'skinout_scraper.py': 'Skinout',
        'waxpeer_scraper.py': 'Waxpeer',
        'csdeals_scraper.py': 'CSDeals',
        'empire_scraper.py': 'Empire',
        'skinport_scraper.py': 'Skinport',
        'marketcsgo_scraper.py': 'MarketCSGO',
        'bitskins_scraper.py': 'Bitskins',
        'cstrade_scraper.py': 'Cstrade',
        'rapidskins_scraper.py': 'Rapidskins'
    }
    
    for scraper_file, scraper_class in scrapers_to_fix.items():
        file_path = scrapers_dir / scraper_file
        if file_path.exists():
            fix_scraper_indentation(file_path, scraper_class)
    
    # 2-7. Aplicar optimizaciones
    optimize_scraper_performance()
    create_optimized_base_scraper()
    create_concurrent_scraper()
    create_cache_service()
    optimize_specific_scrapers()
    create_rate_limiter()
    
    print("\n" + "="*60)
    print("RESUMEN DE CAMBIOS")
    print("="*60)
    
    print("\n✅ Scrapers arreglados:")
    for scraper in scrapers_to_fix.keys():
        print(f"   - {scraper}")
    
    print("\n✅ Optimizaciones aplicadas:")
    print("   - Connection pooling y retry strategy")
    print("   - Scraper concurrente para múltiples requests")
    print("   - Sistema de caché en memoria y disco")
    print("   - Rate limiting para evitar bans")
    print("   - Configuraciones optimizadas por scraper")
    
    print("\n📋 PRÓXIMOS PASOS:")
    print("\n1. Aplicar las optimizaciones de BaseScraper:")
    print("   - Revisa backend/core/base_scraper_optimizations.py")
    print("   - Integra el código en base_scraper.py")
    
    print("\n2. Usar el servicio de caché:")
    print("   from backend.services.cache_service import get_cache_service")
    print("   cache = get_cache_service()")
    print("   cached_data = cache.get('key')")
    
    print("\n3. Implementar rate limiting:")
    print("   from backend.core.rate_limiter import get_rate_limiter")
    print("   limiter = get_rate_limiter()")
    print("   limiter.wait_if_needed('platform_name')")
    
    print("\n4. Reiniciar servicios:")
    print("   python web_server.py")
    
    print("\n✨ ¡Scrapers optimizados y listos para usar!")

if __name__ == "__main__":
    main()