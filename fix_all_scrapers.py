#!/usr/bin/env python3
# fix_all_scrapers.py - Arregla todos los problemas de los scrapers

import os
import shutil
from pathlib import Path
import json

def fix_scrapers_with_main_issue():
    """Arregla los scrapers que tienen funciones main mal definidas"""
    print("\n1. Arreglando scrapers con problemas de main...")
    
    scrapers_to_fix = {
        'white_scraper.py': 'main_white',
        'lisskins_scraper.py': 'main_lisskins',
        'skindeck_scraper.py': 'main_skindeck',
        'shadowpay_scraper.py': 'main_shadowpay',
        'skinout_scraper.py': 'main_skinout'
    }
    
    for scraper_file, main_func in scrapers_to_fix.items():
        file_path = Path(f"backend/scrapers/{scraper_file}")
        
        if file_path.exists():
            print(f"  Arreglando {scraper_file}...")
            
            # Leer contenido
            content = file_path.read_text(encoding='utf-8')
            
            # Buscar y reemplazar la función main incorrecta
            old_pattern = f"    def {main_func}():"
            new_pattern = f"def {main_func}():"
            
            if old_pattern in content:
                content = content.replace(old_pattern, new_pattern)
                
            # Agregar código main correcto al final si no existe
            if '__name__ == "__main__"' not in content:
                content += f"""

def main():
    scraper = {scraper_file.replace('_scraper.py', '').title()}Scraper()
    scraper.run_forever()


if __name__ == "__main__":
    main()
"""
            
            # Guardar cambios
            file_path.write_text(content, encoding='utf-8')
            print(f"    ✓ {scraper_file} arreglado")

def fix_manncostore_scraper():
    """Arregla el scraper de ManncoStore específicamente"""
    print("\n2. Arreglando ManncoStore scraper...")
    
    mannco_file = Path("backend/scrapers/manncostore_scraper.py")
    
    if not mannco_file.exists():
        print("  ⚠️ No se encontró manncostore_scraper.py, creándolo...")
        
        mannco_content = '''# backend/scrapers/manncostore_scraper.py
from typing import List, Dict, Optional
import sys
from pathlib import Path
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc

sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.core.base_scraper import BaseScraper


class ManncoStoreScraper(BaseScraper):
    """
    Scraper para Mannco.Store usando Selenium
    """
    
    def __init__(self, use_proxy: Optional[bool] = None):
        super().__init__('ManncoStore', use_proxy)
        
        self.base_url = self.config.get(
            'base_url',
            'https://mannco.store/items/get'
        )
        
        self.driver = None
        self._setup_driver()
    
    def _setup_driver(self):
        """Configura el driver de Chrome"""
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Si está configurado para usar proxy
        if self.use_proxy and self.proxy_manager:
            proxy = self.proxy_manager.get_proxy()
            if proxy:
                options.add_argument(f'--proxy-server={proxy}')
        
        try:
            self.driver = uc.Chrome(options=options, version_main=None)
        except Exception as e:
            self.logger.error(f"Error configurando driver: {e}")
    
    def __del__(self):
        """Cierra el driver al destruir la instancia"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
    
    def fetch_data(self) -> List[Dict]:
        """Obtiene datos de Mannco.Store usando Selenium"""
        if not self.driver:
            self.logger.error("Driver no inicializado")
            return []
        
        all_items = []
        page = 1
        max_empty_pages = 3
        empty_pages = 0
        
        while empty_pages < max_empty_pages:
            self.logger.info(f"Obteniendo página {page} de ManncoStore...")
            
            try:
                # Construir URL con paginación
                url = f"{self.base_url}?page={page}&appid=730"
                self.driver.get(url)
                
                # Esperar a que cargue el contenido
                time.sleep(3)
                
                # Obtener el JSON de la respuesta
                pre_element = self.driver.find_element(By.TAG_NAME, "pre")
                json_text = pre_element.text
                
                data = json.loads(json_text)
                
                if data and 'items' in data and data['items']:
                    items = self._parse_items(data['items'])
                    all_items.extend(items)
                    empty_pages = 0
                else:
                    empty_pages += 1
                
                page += 1
                time.sleep(2)  # Delay entre páginas
                
            except Exception as e:
                self.logger.error(f"Error en página {page}: {e}")
                empty_pages += 1
        
        self.logger.info(f"Total items obtenidos: {len(all_items)}")
        return all_items
    
    def _parse_items(self, items_data: List[Dict]) -> List[Dict]:
        """Parsea los items de Mannco.Store"""
        items = []
        
        for item in items_data:
            name = item.get('market_hash_name')
            price = item.get('price_usd')
            
            if name and price is not None:
                items.append({
                    'Item': name,
                    'Price': float(price) / 100  # Precio viene en centavos
                })
        
        return items
    
    def parse_response(self, response):
        """No se usa en ManncoStore"""
        pass


def main():
    scraper = ManncoStoreScraper()
    scraper.run_forever()


if __name__ == "__main__":
    main()
'''
        
        mannco_file.write_text(mannco_content, encoding='utf-8')
        print("    ✓ manncostore_scraper.py creado")
    else:
        print("    ✓ manncostore_scraper.py existe")

def create_proxy_file():
    """Crea un archivo proxy.txt vacío si no existe"""
    print("\n3. Verificando archivo proxy.txt...")
    
    proxy_file = Path("proxy.txt")
    
    if not proxy_file.exists():
        print("  Creando archivo proxy.txt vacío...")
        proxy_file.write_text("# Agrega tus proxies aquí, uno por línea\n# Formato: http://usuario:password@ip:puerto\n")
        print("    ✓ proxy.txt creado")
    else:
        print("    ✓ proxy.txt ya existe")

def fix_chromedriver_issue():
    """Arregla el problema de ChromeDriver"""
    print("\n4. Arreglando problema de ChromeDriver...")
    
    # Limpiar archivos de ChromeDriver conflictivos
    chromedriver_path = Path.home() / "appdata" / "roaming" / "undetected_chromedriver"
    
    if chromedriver_path.exists():
        print("  Limpiando archivos de ChromeDriver antiguos...")
        try:
            # Hacer backup primero
            backup_path = chromedriver_path.parent / "undetected_chromedriver_backup"
            if backup_path.exists():
                shutil.rmtree(backup_path)
            shutil.copytree(chromedriver_path, backup_path)
            
            # Limpiar archivos problemáticos
            problem_file = chromedriver_path / "undetected_chromedriver.exe"
            if problem_file.exists():
                problem_file.unlink()
            
            print("    ✓ ChromeDriver limpiado")
        except Exception as e:
            print(f"    ⚠️ No se pudo limpiar ChromeDriver: {e}")
            print("    Intenta eliminar manualmente la carpeta:")
            print(f"    {chromedriver_path}")

def fix_tradeit_scraper():
    """Arregla el scraper TradeIt para manejar mejor los errores"""
    print("\n5. Arreglando TradeIt scraper...")
    
    tradeit_file = Path("backend/scrapers/tradeit_scraper.py")
    
    if tradeit_file.exists():
        content = tradeit_file.read_text(encoding='utf-8')
        
        # Buscar la función _setup_driver
        if "_setup_driver" in content:
            # Agregar manejo de errores mejorado
            new_setup = '''    def _setup_driver(self):
        """Configura el driver de Chrome para Tradeit"""
        try:
            options = uc.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            
            # Limpiar archivos antiguos de ChromeDriver
            import shutil
            chromedriver_path = Path.home() / "appdata" / "roaming" / "undetected_chromedriver"
            if chromedriver_path.exists():
                try:
                    exe_file = chromedriver_path / "undetected_chromedriver.exe"
                    if exe_file.exists():
                        exe_file.unlink()
                except:
                    pass
            
            self.driver = uc.Chrome(options=options, version_main=None)
        except Exception as e:
            self.logger.error(f"Error configurando ChromeDriver: {e}")
            self.driver = None'''
            
            # Reemplazar el método existente
            import re
            pattern = r'def _setup_driver\(self\):.*?(?=\n    def|\Z)'
            content = re.sub(pattern, new_setup, content, flags=re.DOTALL)
            
            tradeit_file.write_text(content, encoding='utf-8')
            print("    ✓ tradeit_scraper.py actualizado")

def update_scraper_configs():
    """Actualiza las configuraciones de scrapers para desactivar proxy por defecto"""
    print("\n6. Actualizando configuraciones de scrapers...")
    
    config_file = Path("config/scraper_configs.json")
    config_file.parent.mkdir(exist_ok=True)
    
    default_configs = {}
    
    # Lista de todos los scrapers
    scrapers = [
        'waxpeer', 'csdeals', 'empire', 'skinport', 'cstrade', 
        'bitskins', 'marketcsgo', 'manncostore', 'tradeit', 
        'skindeck', 'white', 'lisskins', 'shadowpay', 'skinout',
        'rapidskins', 'steammarket', 'steamnames', 'steamid', 'steamlisting'
    ]
    
    for scraper in scrapers:
        # Por defecto, desactivar proxy excepto para algunos scrapers
        use_proxy = scraper in ['manncostore', 'tradeit']  # Solo estos suelen necesitar proxy
        
        default_configs[scraper] = {
            "enabled": True,
            "use_proxy": False,  # Desactivado por defecto
            "interval": 300 if 'steam' in scraper else 60,
            "max_retries": 5,
            "timeout": 15 if scraper in ['tradeit', 'manncostore'] else 10
        }
    
    with open(config_file, 'w') as f:
        json.dump(default_configs, f, indent=2)
    
    print("    ✓ Configuraciones actualizadas (proxy desactivado por defecto)")

def create_database_fix():
    """Crea script para arreglar el problema de la base de datos"""
    print("\n7. Creando fix para base de datos...")
    
    db_fix_content = '''# fix_database_service.py
from pathlib import Path

def fix_database_service():
    """Arregla el error de run_count en database_service.py"""
    db_service_file = Path("backend/services/database_service.py")
    
    if db_service_file.exists():
        content = db_service_file.read_text(encoding='utf-8')
        
        # Buscar la línea problemática
        old_line = "scraper_status.run_count += 1"
        new_lines = """if scraper_status.run_count is None:
                scraper_status.run_count = 1
            else:
                scraper_status.run_count += 1"""
        
        if old_line in content and "if scraper_status.run_count is None:" not in content:
            content = content.replace(old_line, new_lines)
            db_service_file.write_text(content, encoding='utf-8')
            print("✓ database_service.py arreglado")
        else:
            print("✓ database_service.py ya está arreglado")
    else:
        print("⚠️ No se encontró database_service.py")

if __name__ == "__main__":
    fix_database_service()
'''
    
    Path("fix_database_service.py").write_text(db_fix_content, encoding='utf-8')
    print("    ✓ fix_database_service.py creado")

def main():
    print("\n" + "="*60)
    print("ARREGLANDO TODOS LOS SCRAPERS - BOT-vCSGO-Beta")
    print("="*60)
    
    # Ejecutar todos los arreglos
    fix_scrapers_with_main_issue()
    fix_manncostore_scraper()
    create_proxy_file()
    fix_chromedriver_issue()
    fix_tradeit_scraper()
    update_scraper_configs()
    create_database_fix()
    
    print("\n" + "="*60)
    print("RESUMEN DE ARREGLOS")
    print("="*60)
    
    print("\n✅ Scrapers arreglados:")
    print("   - white_scraper.py")
    print("   - lisskins_scraper.py")
    print("   - skindeck_scraper.py")
    print("   - shadowpay_scraper.py")
    print("   - skinout_scraper.py")
    print("   - manncostore_scraper.py")
    print("   - tradeit_scraper.py")
    
    print("\n✅ Archivos creados:")
    print("   - proxy.txt (vacío)")
    print("   - config/scraper_configs.json (proxy desactivado)")
    print("   - fix_database_service.py")
    
    print("\n📋 PRÓXIMOS PASOS:")
    print("\n1. Ejecuta el fix de base de datos:")
    print("   python fix_database_service.py")
    
    print("\n2. Si quieres usar proxies:")
    print("   - Edita proxy.txt y agrega tus proxies")
    print("   - Activa proxy para scrapers específicos en la interfaz web")
    
    print("\n3. Para scrapers con Selenium (tradeit, manncostore):")
    print("   - Asegúrate de tener Chrome instalado")
    print("   - Si siguen fallando, ejecuta:")
    print("     pip install --upgrade undetected-chromedriver")
    
    print("\n4. Reinicia la interfaz web:")
    print("   python web_server.py")
    
    print("\n¡Listo! Los scrapers deberían funcionar correctamente ahora.")

if __name__ == "__main__":
    main()