# backend/scrapers/steamnames_scraper.py
from typing import List, Dict, Optional
import sys
from pathlib import Path
import concurrent.futures
from urllib.parse import unquote

sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.core.base_scraper import BaseScraper
from backend.core.translator import get_translator
class SteamNamesScraper(BaseScraper):
    """
    Scraper para obtener nombres de items de Steam Market
    """
    
    def __init__(self, use_proxy: Optional[bool] = None):
        super().__init__('SteamNames', use_proxy)
        
        self.base_url = "https://steamcommunity.com/market/search/render/?query=&start={}&count=100&search_descriptions=0&sort_column=popular&sort_dir=desc&appid=730&norender=1"
    
    def fetch_data(self) -> List[Dict]:
        """Obtiene nombres de items del Steam Market"""
        self.logger.info("Obteniendo nombres de items de Steam...")
        
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
                self.logger.warning(f"No data attempt {no_data_attempts}/5")
            
            start += 100
        
        self.logger.info(f"Total items obtenidos: {len(all_items)}")
        return all_items
    
    def _get_market_items(self, start: int) -> List[Dict]:
        """Obtiene items de una página específica"""
        url = self.base_url.format(start)
        response = self.make_request(url, max_retries=10)
        
        if response:
            try:
                data = response.json()
                if "results" in data:
                    return self._extract_items(data["results"])
            except Exception as e:
                self.logger.error(f"Error procesando página {start}: {e}")
        
        return []
    
    def _extract_items(self, json_data: List) -> List[Dict]:
        """Extrae nombres de items del JSON"""
        items = []
        for item in json_data:
            try:
                name = item.get('name', 'Unknown')
                name = name.replace("/", "-")  # Limpiar nombre
                items.append({"name": name})
            except Exception as e:
                self.logger.error(f"Error extrayendo item: {e}")
        
        return items
    
    def parse_response(self, response):
        """No se usa en SteamNames"""
        pass

    def main_steamnames():
        scraper = SteamNamesScraper()
        scraper.run_forever()