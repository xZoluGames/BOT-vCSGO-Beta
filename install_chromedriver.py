#!/usr/bin/env python3
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
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Google\Chrome\BLBeacon')
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
        print("\nDescarga manual:")
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
