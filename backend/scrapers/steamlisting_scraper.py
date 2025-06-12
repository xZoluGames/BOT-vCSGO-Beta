# backend/scrapers/steamlisting_scraper.py
from typing import List, Dict, Optional
import sys
from pathlib import Path
import concurrent.futures
from urllib.parse import unquote

sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.core.base_scraper import BaseScraper
from backend.core.translator import get_translator
class SteamListingScraper(BaseScraper):
    """
    Scraper para precios de venta de Steam (sell prices)
    """
    
    def __init__(self, use_proxy: Optional[bool] = None):
        super().__init__('SteamListing', use_proxy)
        
        self.base_url = "https://steamcommunity.com/market/search/render/?query=&start={}&count=100&search_descriptions=0&sort_column=popular&sort_dir=desc&appid=730&norender=1"
    
    def fetch_data(self) -> List[Dict]:
        """Obtiene precios de venta de Steam Market"""
        self.logger.info("Obteniendo precios de venta de Steam...")
        
        all_items = []
        start = 0
        no_data_attempts = 0
        
        while no_data_attempts < 5:
            items = self._get_market_items(start)
            
            if items:
                all_items.extend(items)
                self.logger.info(f"Página {start//100 + 1}: {len(items)} items obtenidos")
                no_data_attempts = 0
            else:
                no_data_attempts += 1
            
            start += 100
        
        return all_items
    
    def _get_market_items(self, start: int) -> List[Dict]:
        """Obtiene items con precios de venta"""
        url = self.base_url.format(start)
        response = self.make_request(url, max_retries=20)
        
        if response:
            try:
                data = response.json()
                if "results" in data:
                    return self._extract_items(data["results"])
            except Exception as e:
                self.logger.error(f"Error procesando página: {e}")
        
        return []
    
    def _extract_items(self, json_data: List) -> List[Dict]:
        """Extrae items con precios de venta"""
        items = []
        for item in json_data:
            try:
                name = item.get('name', 'Unknown')
                name = name.replace("/", "-")
                
                sell_price_cents = item.get('sell_price', 0)
                sell_price_dollars = sell_price_cents / 100.0
                
                items.append({
                    "name": name,
                    "price": sell_price_dollars
                })
            except Exception as e:
                self.logger.error(f"Error extrayendo item: {e}")
        
        return items
    
    def parse_response(self, response):
        """No se usa en SteamListing"""
        pass
    def main_steamlisting():
        scraper = SteamListingScraper()
        scraper.run_forever()