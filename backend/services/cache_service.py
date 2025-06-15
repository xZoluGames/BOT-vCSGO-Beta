# backend/services/cache_service.py
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
