# backend/scrapers/manncostore_scraper.py

from typing import List, Dict, Optional
import sys
from pathlib import Path
import json
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.core.base_scraper import BaseScraper
from backend.core.translator import get_translator


class ManncoStoreScraper(BaseScraper):
    """
    Scraper para ManncoStore usando Selenium
    
    Unifica ManncoStore_noproxy.py y ManncoStore_vproxy.py
    """
    
    def __init__(self, use_proxy: Optional[bool] = None):
        super().__init__('ManncoStore', use_proxy)
        
        self.base_url = self.config.get(
            'base_url',
            'https://mannco.store/items/get?price=DESC&page=1&i=0&game=730&skip={}'
        )
        
        self.manncostore_url = "https://mannco.store/item/"
        self.translator = get_translator('manncostore', self.config_manager.get_language_config())
        
        # Configurar Selenium
        self.driver = None
        self._setup_driver()
    
    def _setup_driver(self):
        """Configura el driver de Chrome"""
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        
        # Configurar proxy si está habilitado
        if self.use_proxy and self.proxy_manager:
            proxy = self.proxy_manager.get_proxy()
            if proxy:
                # Limpiar formato del proxy para Selenium
                proxy_clean = proxy.replace('http://', '').replace('https://', '')
                options.add_argument(f'--proxy-server={proxy_clean}')
        
        # Buscar chromedriver
        chromedriver_path = self.config_manager.base_path / 'Chromedriver' / 'chromedriver.exe'
        if chromedriver_path.exists():
            self.driver = uc.Chrome(options=options, executable_path=str(chromedriver_path))
        else:
            self.driver = uc.Chrome(options=options)
    
    def fetch_data(self) -> List[Dict]:
        """Obtiene datos de ManncoStore usando Selenium"""
        self.logger.info("Obteniendo datos de ManncoStore...")
        
        if not self.driver:
            self.logger.error("Driver de Chrome no inicializado")
            return []
        
        all_items = []
        skip = 0
        
        while True:
            items = self._fetch_page(skip)
            
            if not items:
                self.logger.info(f"No más items en skip {skip}")
                break
                
            all_items.extend(items)
            skip += 50
            
            self.logger.info(f"Skip {skip}: {len(items)} items obtenidos")
        
        self.logger.info(f"Total items obtenidos: {len(all_items)}")
        return all_items
    
    def _fetch_page(self, skip: int) -> List[Dict]:
        """Obtiene items de una página específica"""
        try:
            url = self.base_url.format(skip)
            self.driver.get(url)
            
            # Esperar a que aparezca el JSON
            pre_element = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "pre"))
            )
            
            json_data = pre_element.text
            data = json.loads(json_data)
            
            if isinstance(data, list) and len(data) > 0:
                items = []
                for item in data:
                    items.append({
                        'Item': item['name'],
                        'Price': self._transform_price(item['price']),
                        'URL': self.manncostore_url + (item.get('url', ''))
                    })
                
                if hasattr(self, 'translator'):
                    print(self.translator.gettext('success_message', skip=skip, total_items=len(items)), flush=True)
                
                return items
            else:
                if hasattr(self, 'translator'):
                    print(self.translator.gettext('no_items', skip=skip), flush=True)
                return []
                
        except json.JSONDecodeError:
            if hasattr(self, 'translator'):
                print(self.translator.gettext('json_decode_error', skip=skip), flush=True)
            return []
        except Exception as e:
            if hasattr(self, 'translator'):
                print(self.translator.gettext('fetch_error', skip=skip, error=str(e)), flush=True)
            return []
    
    def _transform_price(self, price: int) -> str:
        """Transforma el precio a formato XX.XX"""
        price_str = str(price)
        if len(price_str) > 2:
            return f"{price_str[:-2]}.{price_str[-2:]}"
        else:
            return f"0.{price_str.zfill(2)}"
    
    def parse_response(self, response):
        """No se usa en ManncoStore, el parsing se hace en fetch_data"""
        pass
    
    def __del__(self):
        """Cierra el driver al destruir el objeto"""
        if self.driver:
            self.driver.quit()

    def main_manncostore():
        scraper = ManncoStoreScraper()
        scraper.run_forever()