# backend/scrapers/tradeit_scraper.py
from typing import List, Dict, Optional
import sys
from pathlib import Path
import json
import undetected_chromedriver as uc
sys.path.append(str(Path(__file__).parent.parent.parent))
from backend.core.base_scraper import BaseScraper
class TradeitScraper(BaseScraper):
    """
    Scraper para Tradeit.gg usando Selenium
    """
    
    def __init__(self, use_proxy: Optional[bool] = None):
        super().__init__('Tradeit', use_proxy)
        
        self.base_url = self.config.get(
            'base_url',
            'https://tradeit.gg/api/v2/inventory/data?gameId=730&sortType=Popularity&offset={}&limit=1000&fresh=true'
        )
        
        self.driver = None
        self._setup_driver()
    
        def _setup_driver(self):
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
            self.driver = None
    def fetch_data(self) -> List[Dict]:
        """Obtiene datos de Tradeit usando Selenium"""
        self.logger.info("Obteniendo datos de Tradeit...")
        
        if not self.driver:
            return []
        
        all_items = []
        offset = 0
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            items = self._fetch_inventory_data(offset)
            
            if not items:
                retry_count += 1
                self.logger.warning(f"No items found. Retry {retry_count}/{max_retries}")
                continue
            
            # Reiniciar contador si encontramos items
            retry_count = 0
            all_items.extend(items)
            self.logger.info(f"Obtenidos {len(items)} items. Total: {len(all_items)}")
            
            offset += 1000
        
        return all_items
    
    def _fetch_inventory_data(self, offset: int) -> List[Dict]:
        """Obtiene datos de inventario de una página"""
        try:
            url = self.base_url.format(offset)
            self.driver.get(url)
            
            # Esperar a que cargue la página
            import time
            time.sleep(3)
            
            # Obtener contenido JSON
            page_content = self.driver.execute_script("return document.body.innerText")
            data = json.loads(page_content)
            
            items = data.get('items', [])
            if not items:
                return []
            
            inventory_data = []
            for item in items:
                name = item.get('name', 'Unnamed Item')
                price_for_trade = item.get('priceForTrade', 0)
                
                # Convertir precio a float
                price_for_trade = float(price_for_trade) / 100
                
                inventory_data.append({
                    "Item": name,
                    "Price": price_for_trade
                })
            
            return inventory_data
            
        except Exception as e:
            self.logger.error(f"Error obteniendo datos de Tradeit: {e}")
            return []
    
    def parse_response(self, response):
        """No se usa en Tradeit"""
        pass
    
    def __del__(self):
        if self.driver:
            self.driver.quit()

    def main_tradeit():
        scraper = TradeitScraper()
        scraper.run_forever()