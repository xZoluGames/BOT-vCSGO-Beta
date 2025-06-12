# backend/core/proxy_manager.py

import random
import time
from typing import List, Optional, Dict, Set
from datetime import datetime, timedelta
from threading import Lock
import requests
from loguru import logger


class ProxyManager:
    """
    Gestor inteligente de proxies con rotación y detección de proxies muertos
    """
    
    def __init__(self, proxy_list: List[str], health_check_enabled: bool = True):
        """
        Inicializa el gestor de proxies
        
        Args:
            proxy_list: Lista de proxies en formato 'http://ip:puerto' o 'ip:puerto'
            health_check_enabled: Si hacer verificación de salud de proxies
        """
        self.all_proxies = self._normalize_proxies(proxy_list)
        self.available_proxies = self.all_proxies.copy()
        self.failed_proxies: Dict[str, Dict] = {}  # proxy -> {fail_count, last_fail}
        self.lock = Lock()
        self.stats = {
            'total_proxies': len(self.all_proxies),
            'requests_made': 0,
            'failures': 0,
            'last_rotation': datetime.now()
        }
        
        logger.info(f"ProxyManager inicializado con {len(self.all_proxies)} proxies")
        
        # Verificar salud inicial si está habilitado
        if health_check_enabled and self.all_proxies:
            self._initial_health_check()
    
    def _normalize_proxies(self, proxy_list: List[str]) -> List[str]:
        """Normaliza el formato de los proxies"""
        normalized = []
        
        for proxy in proxy_list:
            proxy = proxy.strip()
            if not proxy:
                continue
                
            # Si no tiene protocolo, agregar http://
            if not proxy.startswith(('http://', 'https://', 'socks4://', 'socks5://')):
                proxy = f'http://{proxy}'
                
            normalized.append(proxy)
            
        return normalized
    
    def _initial_health_check(self):
        """Verifica la salud inicial de todos los proxies"""
        logger.info("Realizando verificación inicial de proxies...")
        working_proxies = []
        
        for proxy in self.all_proxies:
            if self._test_proxy(proxy):
                working_proxies.append(proxy)
            else:
                self.failed_proxies[proxy] = {
                    'fail_count': 1,
                    'last_fail': datetime.now()
                }
        
        self.available_proxies = working_proxies
        logger.info(
            f"Verificación completada: {len(working_proxies)}/{len(self.all_proxies)} "
            f"proxies funcionando"
        )
    
    def _test_proxy(self, proxy: str, timeout: int = 5) -> bool:
        """
        Prueba si un proxy está funcionando
        
        Args:
            proxy: Proxy a probar
            timeout: Timeout en segundos
            
        Returns:
            True si el proxy funciona
        """
        test_url = 'http://httpbin.org/ip'
        
        try:
            response = requests.get(
                test_url,
                proxies={'http': proxy, 'https': proxy},
                timeout=timeout
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def get_proxy(self) -> Optional[str]:
        """
        Obtiene un proxy disponible
        
        Returns:
            Proxy en formato string o None si no hay disponibles
        """
        with self.lock:
            self.stats['requests_made'] += 1
            
            # Si no hay proxies disponibles, intentar recuperar algunos
            if not self.available_proxies:
                self._try_recover_failed_proxies()
                
                # Si aún no hay proxies, retornar None
                if not self.available_proxies:
                    logger.warning("No hay proxies disponibles")
                    return None
            
            # Seleccionar proxy aleatorio
            proxy = random.choice(self.available_proxies)
            
            # Rotar el proxy al final de la lista para distribución uniforme
            self.available_proxies.remove(proxy)
            self.available_proxies.append(proxy)
            
            return proxy
    
    def mark_failed(self, proxy: str):
        """
        Marca un proxy como fallido
        
        Args:
            proxy: Proxy que falló
        """
        with self.lock:
            self.stats['failures'] += 1
            
            # Remover de disponibles
            if proxy in self.available_proxies:
                self.available_proxies.remove(proxy)
            
            # Actualizar registro de fallos
            if proxy in self.failed_proxies:
                self.failed_proxies[proxy]['fail_count'] += 1
                self.failed_proxies[proxy]['last_fail'] = datetime.now()
            else:
                self.failed_proxies[proxy] = {
                    'fail_count': 1,
                    'last_fail': datetime.now()
                }
            
            logger.debug(
                f"Proxy marcado como fallido: {proxy} "
                f"(fallos: {self.failed_proxies[proxy]['fail_count']})"
            )
            
            # Si un proxy falla muchas veces, sacarlo permanentemente
            if self.failed_proxies[proxy]['fail_count'] >= 10:
                logger.warning(f"Proxy removido permanentemente: {proxy}")
                if proxy in self.all_proxies:
                    self.all_proxies.remove(proxy)
                del self.failed_proxies[proxy]
    
    def mark_success(self, proxy: str):
        """
        Marca un proxy como exitoso (resetea contador de fallos)
        
        Args:
            proxy: Proxy que funcionó correctamente
        """
        with self.lock:
            if proxy in self.failed_proxies:
                # Reducir contador de fallos
                self.failed_proxies[proxy]['fail_count'] = max(
                    0, 
                    self.failed_proxies[proxy]['fail_count'] - 1
                )
                
                # Si no tiene más fallos, remover del registro
                if self.failed_proxies[proxy]['fail_count'] == 0:
                    del self.failed_proxies[proxy]
    
    def _try_recover_failed_proxies(self):
        """Intenta recuperar proxies que fallaron hace tiempo"""
        recovery_time = timedelta(minutes=5)  # Intentar recuperar después de 5 minutos
        now = datetime.now()
        
        proxies_to_recover = []
        
        for proxy, info in list(self.failed_proxies.items()):
            # Si pasó suficiente tiempo desde el último fallo
            if now - info['last_fail'] > recovery_time:
                # Dar otra oportunidad si no ha fallado demasiado
                if info['fail_count'] < 5:
                    proxies_to_recover.append(proxy)
        
        for proxy in proxies_to_recover:
            logger.info(f"Intentando recuperar proxy: {proxy}")
            if self._test_proxy(proxy):
                self.available_proxies.append(proxy)
                self.failed_proxies[proxy]['fail_count'] = max(
                    0,
                    self.failed_proxies[proxy]['fail_count'] - 2
                )
                logger.success(f"Proxy recuperado: {proxy}")
            else:
                self.failed_proxies[proxy]['last_fail'] = now
    
    def get_stats(self) -> Dict:
        """Retorna estadísticas del gestor de proxies"""
        with self.lock:
            return {
                **self.stats,
                'available_proxies': len(self.available_proxies),
                'failed_proxies': len(self.failed_proxies),
                'health_percentage': (
                    len(self.available_proxies) / self.stats['total_proxies'] * 100
                    if self.stats['total_proxies'] > 0 else 0
                )
            }
    
    def rotate_all(self):
        """Rota todos los proxies disponibles"""
        with self.lock:
            if self.available_proxies:
                random.shuffle(self.available_proxies)
                self.stats['last_rotation'] = datetime.now()
    
    def add_proxy(self, proxy: str):
        """Agrega un nuevo proxy a la lista"""
        proxy = self._normalize_proxies([proxy])[0]
        
        with self.lock:
            if proxy not in self.all_proxies:
                self.all_proxies.append(proxy)
                
                # Probar el proxy antes de agregarlo a disponibles
                if self._test_proxy(proxy):
                    self.available_proxies.append(proxy)
                    logger.info(f"Nuevo proxy agregado: {proxy}")
                else:
                    logger.warning(f"Nuevo proxy no funciona: {proxy}")
                    
                self.stats['total_proxies'] = len(self.all_proxies)
    
    def remove_proxy(self, proxy: str):
        """Remueve un proxy de todas las listas"""
        with self.lock:
            if proxy in self.all_proxies:
                self.all_proxies.remove(proxy)
                
            if proxy in self.available_proxies:
                self.available_proxies.remove(proxy)
                
            if proxy in self.failed_proxies:
                del self.failed_proxies[proxy]
                
            self.stats['total_proxies'] = len(self.all_proxies)
            logger.info(f"Proxy removido: {proxy}")
    
    def get_best_proxies(self, count: int = 5) -> List[str]:
        """
        Obtiene los mejores proxies basado en su historial
        
        Args:
            count: Número de proxies a retornar
            
        Returns:
            Lista de los mejores proxies
        """
        with self.lock:
            # Proxies sin fallos son los mejores
            never_failed = [p for p in self.available_proxies if p not in self.failed_proxies]
            
            # Luego los que tienen menos fallos
            sorted_failed = sorted(
                [(p, info['fail_count']) for p, info in self.failed_proxies.items()],
                key=lambda x: x[1]
            )
            
            best_proxies = never_failed[:count]
            
            # Si necesitamos más, agregar los de menos fallos
            if len(best_proxies) < count:
                for proxy, _ in sorted_failed:
                    if proxy in self.available_proxies:
                        best_proxies.append(proxy)
                        if len(best_proxies) >= count:
                            break
            
            return best_proxies