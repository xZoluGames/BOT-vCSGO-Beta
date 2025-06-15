# backend/core/rate_limiter.py
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
