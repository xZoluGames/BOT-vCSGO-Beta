# backend/core/network_helper.py
import socket
import time
from typing import Optional, Callable
from loguru import logger

class NetworkHelper:
    """Ayudante para manejar problemas de red"""
    
    @staticmethod
    def wait_for_connection(timeout: int = 300, check_interval: int = 5) -> bool:
        """Espera hasta que haya conexión a internet"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if NetworkHelper.check_connection():
                return True
            
            logger.info(f"Sin conexión. Reintentando en {check_interval}s...")
            time.sleep(check_interval)
        
        return False
    
    @staticmethod
    def check_connection(host: str = "8.8.8.8", port: int = 53, timeout: int = 3) -> bool:
        """Verifica si hay conexión a internet"""
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except socket.error:
            return False
    
    @staticmethod
    def retry_on_network_error(func: Callable, max_retries: int = 3, delay: int = 5):
        """Decordador para reintentar en caso de error de red"""
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (socket.error, ConnectionError) as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Error de red: {e}. Reintentando en {delay}s...")
                        time.sleep(delay)
                    else:
                        raise
            return None
        return wrapper
