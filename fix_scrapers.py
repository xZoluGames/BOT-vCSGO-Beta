#!/usr/bin/env python3
# fix_scrapers.py - Arregla problemas comunes en los scrapers

import os
import sys
import json
import shutil
from pathlib import Path

def create_proxy_file():
    """Crea archivo proxy.txt vacío si no existe"""
    print("1. Verificando archivo proxy.txt...")
    proxy_file = Path("proxy.txt")
    
    if not proxy_file.exists():
        print("   Creando archivo proxy.txt vacío...")
        proxy_file.write_text("# Agrega tus proxies aquí, uno por línea\n# Formato: http://usuario:password@ip:puerto\n")
        print("   ✓ proxy.txt creado")
    else:
        print("   ✓ proxy.txt ya existe")

def fix_chromedriver_cache():
    """Limpia el caché problemático de ChromeDriver"""
    print("\n2. Limpiando caché de ChromeDriver...")
    
    # Rutas posibles del caché
    cache_paths = [
        Path.home() / "appdata" / "roaming" / "undetected_chromedriver",
        Path.home() / ".cache" / "undetected_chromedriver",
        Path.home() / "AppData" / "Roaming" / "undetected_chromedriver"
    ]
    
    for cache_path in cache_paths:
        if cache_path.exists():
            print(f"   Eliminando: {cache_path}")
            try:
                shutil.rmtree(cache_path)
                print("   ✓ Caché eliminado")
            except Exception as e:
                print(f"   ✗ Error: {e}")

def create_offline_config():
    """Crea configuración para modo offline"""
    print("\n3. Creando configuración offline...")
    
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    offline_config = {
        "proxy_settings": {
            "enabled": False,
            "timeout": 30,
            "max_retries": 3
        },
        "selenium_settings": {
            "use_offline_driver": True,
            "driver_path": "drivers/chromedriver.exe",
            "headless": True
        },
        "network_settings": {
            "timeout": 30,
            "retry_on_failure": True,
            "max_retries": 3
        }
    }
    
    config_file = config_dir / "offline_settings.json"
    with open(config_file, 'w') as f:
        json.dump(offline_config, f, indent=2)
    
    print("   ✓ Configuración offline creada")

def update_scraper_timeouts():
    """Actualiza timeouts en scrapers problemáticos"""
    print("\n4. Actualizando timeouts de scrapers...")
    
    scrapers_to_fix = ['manncostore_scraper.py', 'tradeit_scraper.py']
    scrapers_dir = Path("backend/scrapers")
    
    for scraper_name in scrapers_to_fix:
        scraper_path = scrapers_dir / scraper_name
        if scraper_path.exists():
            print(f"   Actualizando {scraper_name}...")
            
            content = scraper_path.read_text(encoding='utf-8')
            
            # Aumentar timeouts
            if "timeout=10" in content:
                content = content.replace("timeout=10", "timeout=30")
            if "timeout=5" in content:
                content = content.replace("timeout=5", "timeout=30")
                
            scraper_path.write_text(content, encoding='utf-8')
            print(f"   ✓ {scraper_name} actualizado")

def create_manual_driver_installer():
    """Crea script para instalar ChromeDriver manualmente"""
    print("\n5. Creando instalador manual de ChromeDriver...")
    
    installer_content = '''#!/usr/bin/env python3
# install_chromedriver.py - Instala ChromeDriver manualmente

import os
import sys
import platform
import zipfile
import requests
from pathlib import Path

def get_chrome_version():
    """Intenta obtener la versión de Chrome instalada"""
    if platform.system() == 'Windows':
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\\Google\\Chrome\\BLBeacon')
            version, _ = winreg.QueryValueEx(key, 'version')
            return version.split('.')[0]
        except:
            return None
    return None

def download_chromedriver(version=None):
    """Descarga ChromeDriver"""
    drivers_dir = Path("drivers")
    drivers_dir.mkdir(exist_ok=True)
    
    # URL base para descargar ChromeDriver
    if version:
        url = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{version}"
    else:
        url = "https://chromedriver.storage.googleapis.com/LATEST_RELEASE"
    
    print(f"Obteniendo versión de ChromeDriver...")
    
    try:
        # Obtener versión
        response = requests.get(url, timeout=10)
        driver_version = response.text.strip()
        
        # Descargar ChromeDriver
        download_url = f"https://chromedriver.storage.googleapis.com/{driver_version}/chromedriver_win32.zip"
        print(f"Descargando ChromeDriver {driver_version}...")
        
        zip_path = drivers_dir / "chromedriver.zip"
        response = requests.get(download_url, stream=True, timeout=30)
        
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Extraer
        print("Extrayendo ChromeDriver...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(drivers_dir)
        
        zip_path.unlink()
        print(f"✓ ChromeDriver instalado en: {drivers_dir / 'chromedriver.exe'}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        print("\\nDescarga manual:")
        print("1. Ve a: https://chromedriver.chromium.org/downloads")
        print("2. Descarga la versión correcta para tu Chrome")
        print("3. Extrae chromedriver.exe en la carpeta 'drivers'")

if __name__ == "__main__":
    print("="*60)
    print("INSTALADOR DE CHROMEDRIVER")
    print("="*60)
    
    chrome_version = get_chrome_version()
    if chrome_version:
        print(f"Chrome versión detectada: {chrome_version}")
    else:
        print("No se pudo detectar la versión de Chrome")
    
    download_chromedriver(chrome_version)
'''
    
    with open("install_chromedriver.py", 'w') as f:
        f.write(installer_content)
    
    print("   ✓ install_chromedriver.py creado")

def main():
    print("="*60)
    print("ARREGLANDO SCRAPERS - BOT-vCSGO-Beta")
    print("="*60)
    
    create_proxy_file()
    fix_chromedriver_cache()
    create_offline_config()
    update_scraper_timeouts()
    create_manual_driver_installer()
    
    print("\n" + "="*60)
    print("PRÓXIMOS PASOS:")
    print("="*60)
    
    print("\n1. Primero ejecuta el diagnóstico:")
    print("   python test_connection.py")
    
    print("\n2. Si no hay internet, instala ChromeDriver manualmente:")
    print("   python install_chromedriver.py")
    
    print("\n3. Configura los scrapers para modo offline:")
    print("   - Edita config/settings.json")
    print("   - Establece 'use_proxy': false para todos los scrapers")
    
    print("\n4. Prueba un scraper simple primero:")
    print("   python run_scrapers.py waxpeer --no-proxy --once")
    
    print("\n✓ Script completado!")

if __name__ == "__main__":
    main()