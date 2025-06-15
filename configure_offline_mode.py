#!/usr/bin/env python3
# configure_offline_mode.py - Configura scrapers para trabajar sin conexión

import json
import sys
from pathlib import Path

def disable_proxy_globally():
    """Desactiva proxies en la configuración global"""
    settings_file = Path("config/settings.json")
    
    if settings_file.exists():
        with open(settings_file, 'r') as f:
            settings = json.load(f)
        
        # Desactivar proxy
        if 'proxy_settings' in settings:
            settings['proxy_settings']['enabled'] = False
        else:
            settings['proxy_settings'] = {'enabled': False}
        
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
        
        print("✓ Proxies desactivados globalmente")
    else:
        print("✗ No se encontró config/settings.json")

def update_scraper_configs():
    """Actualiza configuración individual de scrapers"""
    platforms_file = Path("config/scrapers/platforms.json")
    
    if platforms_file.exists():
        with open(platforms_file, 'r') as f:
            platforms = json.load(f)
        
        # Configuraciones específicas para modo offline
        offline_settings = {
            "use_proxy": False,
            "timeout": 60,
            "max_retries": 5,
            "retry_delay": 5,
            "fallback_mode": True
        }
        
        # Aplicar a scrapers problemáticos
        problem_scrapers = ['manncostore', 'tradeit', 'skinport']
        
        for scraper in problem_scrapers:
            if scraper in platforms:
                platforms[scraper].update(offline_settings)
                print(f"✓ {scraper} configurado para modo offline")
        
        with open(platforms_file, 'w') as f:
            json.dump(platforms, f, indent=2)
    else:
        print("✗ No se encontró config/scrapers/platforms.json")

def create_fallback_scraper():
    """Crea un scraper de respaldo que funcione offline"""
    fallback_content = '''# backend/scrapers/offline_test_scraper.py
from backend.core.base_scraper import BaseScraper
from datetime import datetime
import random

class OfflineTestScraper(BaseScraper):
    """Scraper de prueba que funciona sin conexión"""
    
    def __init__(self, use_proxy=None):
        super().__init__('OfflineTest', use_proxy=False)
    
    def fetch_data(self):
        """Genera datos de prueba sin conexión"""
        self.logger.info("Generando datos de prueba (modo offline)...")
        
        # Simular datos
        items = []
        for i in range(10):
            items.append({
                'Item': f'Test Item {i+1}',
                'Price': round(random.uniform(10, 1000), 2)
            })
        
        return items
    
    def parse_response(self, response):
        """No se usa en modo offline"""
        return response
'''
    
    scraper_file = Path("backend/scrapers/offline_test_scraper.py")
    scraper_file.parent.mkdir(parents=True, exist_ok=True)
    scraper_file.write_text(fallback_content)
    print("✓ Scraper de prueba offline creado")

def create_network_helper():
    """Crea utilidad para manejar problemas de red"""
    helper_content = '''# backend/core/network_helper.py
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
'''
    
    helper_file = Path("backend/core/network_helper.py")
    helper_file.parent.mkdir(parents=True, exist_ok=True)
    helper_file.write_text(helper_content)
    print("✓ NetworkHelper creado")

def update_run_scrapers():
    """Actualiza run_scrapers.py para incluir el scraper de prueba"""
    run_scrapers_file = Path("run_scrapers.py")
    
    if run_scrapers_file.exists():
        content = run_scrapers_file.read_text()
        
        # Agregar import si no existe
        if "from backend.scrapers.offline_test_scraper import OfflineTestScraper" not in content:
            # Buscar donde agregar el import
            import_section = content.find("# Importar scrapers")
            if import_section > 0:
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if "# Importar scrapers" in line:
                        lines.insert(i + 1, "from backend.scrapers.offline_test_scraper import OfflineTestScraper")
                        break
                content = '\n'.join(lines)
        
        # Agregar al diccionario SCRAPERS si no existe
        if "'offlinetest': OfflineTestScraper" not in content:
            scrapers_dict = content.find("SCRAPERS = {")
            if scrapers_dict > 0:
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if "SCRAPERS = {" in line:
                        lines.insert(i + 1, "    'offlinetest': OfflineTestScraper,")
                        break
                content = '\n'.join(lines)
        
        run_scrapers_file.write_text(content)
        print("✓ run_scrapers.py actualizado")

def main():
    print("="*60)
    print("CONFIGURANDO MODO OFFLINE - BOT-vCSGO-Beta")
    print("="*60)
    
    print("\n1. Desactivando proxies...")
    disable_proxy_globally()
    
    print("\n2. Actualizando configuración de scrapers...")
    update_scraper_configs()
    
    print("\n3. Creando scraper de prueba offline...")
    create_fallback_scraper()
    
    print("\n4. Creando utilidades de red...")
    create_network_helper()
    
    print("\n5. Actualizando run_scrapers.py...")
    update_run_scrapers()
    
    print("\n" + "="*60)
    print("CONFIGURACIÓN COMPLETADA")
    print("="*60)
    
    print("\n✅ Ahora puedes probar:")
    print("\n1. Scraper de prueba offline:")
    print("   python run_scrapers.py offlinetest --once")
    
    print("\n2. Scrapers normales sin proxy:")
    print("   python run_scrapers.py waxpeer --no-proxy --once")
    print("   python run_scrapers.py csdeals --no-proxy --once")
    
    print("\n3. Ver estado del sistema:")
    print("   python run_scrapers.py status")
    
    print("\n⚠️  Para scrapers con Selenium (manncostore, tradeit):")
    print("   - Necesitarás ChromeDriver instalado localmente")
    print("   - Ejecuta: python install_chromedriver.py")

if __name__ == "__main__":
    main()