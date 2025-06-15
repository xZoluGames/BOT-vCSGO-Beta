# backend/scrapers/skinport_scraper.py

from typing import List, Dict, Optional
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.core.base_scraper import BaseScraper
from backend.core.translator import get_translator


class SkinportScraper(BaseScraper):
    """
    Scraper para Skinport.com
    
    Unifica Skinport_noproxy.py y Skinport_vproxy.py
    """
    
    def __init__(self, use_proxy: Optional[bool] = None):
        super().__init__('Skinport', use_proxy)
        
        self.api_url = self.config.get(
            'api_url',
            'https://api.skinport.com/v1/items?app_id=730&currency=USD'
        )
        
        self.translator = get_translator('skinports', self.config_manager.get_language_config())
    
    def fetch_data(self) -> List[Dict]:
        """Obtiene datos de la API de Skinport"""
        self.logger.info("Obteniendo datos de Skinport...")
        
        response = self.make_request(self.api_url)
        if response:
            return self.parse_response(response)
        return []
    
    def parse_response(self, response) -> List[Dict]:
        """Parsea la respuesta de Skinport"""
        try:
            data = response.json()
            
            # Skinport devuelve una lista directamente
            if not isinstance(data, list):
                self.logger.error("Formato inesperado en respuesta de Skinport")
                return []
            
            items = []
            for item in data:
                # Solo items con cantidad > 0
                if item.get('quantity', 0) <= 0:
                    continue
                    
                name = item.get('market_hash_name')
                price = item.get('min_price')
                
                if name and price is not None:
                    items.append({
                        'Item': name,
                        'Price': str(price)  # Skinport ya da precio en formato correcto
                    })
            
            self.logger.info(f"Parseados {len(items)} items de Skinport")
            
            if hasattr(self, 'translator'):
                print(self.translator.gettext('data_obtained', count=len(items)), flush=True)
            
            return items
            
        except Exception as e:
            self.logger.error(f"Error parseando respuesta de Skinport: {e}")
            if hasattr(self, 'translator'):
                print(self.translator.gettext('error_obtaining_data', error=str(e)), flush=True)
            return []



    def main():
        scraper = SkinportScraper()
        scraper.run_forever()


    if __name__ == "__main__":
        main()