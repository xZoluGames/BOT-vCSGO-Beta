# backend/scrapers/white_scraper.py

from typing import List, Dict, Optional
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.core.base_scraper import BaseScraper


class WhiteScraper(BaseScraper):
    """Scraper para White.market"""
    
    def __init__(self, use_proxy: Optional[bool] = None):
        super().__init__('White', use_proxy)
        
        self.api_url = self.config.get(
            'api_url',
            'https://api.white.market/export/v1/prices/730.json'
        )
    
    def fetch_data(self) -> List[Dict]:
        response = self.make_request(self.api_url)
        if response:
            return self.parse_response(response)
        return []
    
    def parse_response(self, response) -> List[Dict]:
        try:
            data = response.json()
            
            items = []
            for item in data:
                items.append({
                    "Item": item["market_hash_name"],
                    "Price": item["price"],
                    "URL": item["market_product_link"]
                })
            
            self.logger.info(f"Parseados {len(items)} items de White")
            print(f"Datos guardados en white_data.json, esperando 5 segundos para el reinicio...", flush=True)
            
            return items
        except Exception as e:
            self.logger.error(f"Error parseando White: {e}")
            return []
def main_white():
        scraper = WhiteScraper()
        scraper.run_forever()

def main():
    scraper = WhiteScraper()
    scraper.run_forever()


if __name__ == "__main__":
    main()
