# backend/scrapers/marketcsgo_scraper.py

from typing import List, Dict, Optional
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.core.base_scraper import BaseScraper
from backend.core.translator import get_translator


class MarketCSGOScraper(BaseScraper):
    """
    Scraper para Market.csgo.com
    
    Unifica Market.csgo_noproxy.py 
    """
    
    def __init__(self, use_proxy: Optional[bool] = None):
        super().__init__('MarketCSGO', use_proxy)
        
        self.api_url = self.config.get(
            'api_url',
            'https://market.csgo.com/api/v2/prices/USD.json'
        )
        
        self.translator = get_translator('marketcsgo', self.config_manager.get_language_config())
    
    def fetch_data(self) -> List[Dict]:
        """Obtiene datos de la API de Market.csgo"""
        self.logger.info("Obteniendo datos de Market.csgo...")
        
        response = self.make_request(self.api_url)
        if response:
            return self.parse_response(response)
        return []
    
    def parse_response(self, response) -> List[Dict]:
        """Parsea la respuesta de Market.csgo"""
        try:
            data = response.json()
            
            # Verificar que la respuesta sea exitosa
            if not data.get("success"):
                self.logger.error("Respuesta no exitosa de Market.csgo")
                return []
            
            # Market.csgo tiene estructura: {'success': True, 'items': {...}}
            if 'items' not in data:
                self.logger.error("No se encontraron items en respuesta de Market.csgo")
                return []
            
            items = []
            for item in data['items']:
                name = item.get("market_hash_name")
                price = item.get("price")
                
                if name and price is not None:
                    items.append({
                        'Item': name,
                        'Price': float(price)  # Market.csgo ya da precio en formato correcto
                    })
            
            self.logger.info(f"Parseados {len(items)} items de Market.csgo")
            print(f"Data saved in market.csgo_data.json", flush=True)
            
            return items
            
        except Exception as e:
            self.logger.error(f"Error parseando respuesta de Market.csgo: {e}")
            print("Error al obtener los datos de la API.", flush=True)
            return []



def main():
    scraper = MarketCSGOScraper()
    scraper.run_forever()


if __name__ == "__main__":
    main()