# backend/scrapers/lisskins_scraper.py
from typing import List, Dict, Optional
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from backend.core.base_scraper import BaseScraper
class LisskinsScraper(BaseScraper):
    """Scraper para Lis-skins.com"""
    
    def __init__(self, use_proxy: Optional[bool] = None):
        super().__init__('Lisskins', use_proxy)
        
        self.api_url = self.config.get(
            'api_url',
            'https://lis-skins.com/market_export_json/api_csgo_full.json'
        )
    
    def fetch_data(self) -> List[Dict]:
        response = self.make_request(self.api_url)
        if response:
            return self.parse_response(response)
        return []
    
    def parse_response(self, response) -> List[Dict]:
        try:
            data = response.json()
            
            # Diccionario para almacenar el ítem más barato de cada nombre
            cheapest_items = {}
            
            for item in data.get('items', []):
                name = item.get('name')
                price = item.get('price')
                
                if name and price is not None:
                    if name in cheapest_items:
                        if price < cheapest_items[name]['Price']:
                            cheapest_items[name] = {
                                'Item': name,
                                'Price': price,
                                'URL': f"https://lis-skins.com/ru/market/csgo/{self._format_url_name(name)}"
                            }
                    else:
                        cheapest_items[name] = {
                            'Item': name,
                            'Price': price,
                            'URL': f"https://lis-skins.com/ru/market/csgo/{self._format_url_name(name)}"
                        }
            
            items = list(cheapest_items.values())
            self.logger.info(f"Parseados {len(items)} items de Lisskins")
            print("The data obtained has been successfully saved.", flush=True)
            
            return items
        except Exception as e:
            self.logger.error(f"Error parseando Lisskins: {e}")
            return []
    
    def _format_url_name(self, item_name: str) -> str:
        """Formatea el nombre del ítem para la URL"""
        chars_to_remove = "™(),/|"
        
        for char in chars_to_remove:
            item_name = item_name.replace(char, '')
        
        item_name = item_name.replace(' ', '-')
        
        while '--' in item_name:
            item_name = item_name.replace('--', '-')
        
        return item_name.strip('-')
    def main_lisskins():
        scraper = LisskinsScraper()
        scraper.run_forever()
