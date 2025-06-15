# backend/scrapers/bitskins_scraper.py

from typing import List, Dict, Optional
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.core.base_scraper import BaseScraper
from backend.core.translator import get_translator


class BitskinsScraper(BaseScraper):
    """
    Scraper para Bitskins.com
    
    Unifica Bitskins_noproxy.py y Bitskins_vproxy.py
    """
    
    def __init__(self, use_proxy: Optional[bool] = None):
        super().__init__('Bitskins', use_proxy)
        
        self.api_url = self.config.get(
            'api_url',
            'https://api.bitskins.com/market/insell/730'
        )
        
        self.translator = get_translator('bitskins', self.config_manager.get_language_config())
    
    def fetch_data(self) -> List[Dict]:
        """Obtiene datos de la API de Bitskins"""
        self.logger.info("Obteniendo datos de Bitskins...")
        
        response = self.make_request(self.api_url)
        if response:
            return self.parse_response(response)
        return []
    
    def parse_response(self, response) -> List[Dict]:
        """Parsea la respuesta de Bitskins"""
        try:
            data = response.json()
            
            # Bitskins tiene estructura: {'list': [...]}
            if 'list' not in data:
                self.logger.error("No se encontró 'list' en respuesta de Bitskins")
                if hasattr(self, 'translator'):
                    print(self.translator.gettext('unexpected_format'), flush=True)
                return []
            
            items = []
            for item in data['list']:
                name = item.get('name')
                price_min = item.get('price_min', 0)  # Precio en milésimas
                
                if name:
                    # Convertir de milésimas a dólares (price_min está en milésimas)
                    price_dollars = self._convert_price(price_min)
                    
                    items.append({
                        'Item': name,
                        'Price': price_dollars
                    })
            
            self.logger.info(f"Parseados {len(items)} items de Bitskins")
            
            if hasattr(self, 'translator'):
                print(self.translator.gettext('success_message', total_items=len(items)), flush=True)
            
            return items
            
        except Exception as e:
            self.logger.error(f"Error parseando respuesta de Bitskins: {e}")
            if hasattr(self, 'translator'):
                print(self.translator.gettext('fetch_error', error=str(e)), flush=True)
            return []
    
    def _convert_price(self, price_min: int) -> str:
        """
        Convierte el precio de Bitskins (en milésimas) a dólares
        
        Args:
            price_min: Precio en milésimas (ej: 1000 = $1.00)
        
        Returns:
            Precio formateado como string
        """
        return f"{price_min / 1000:.2f}"



def main():
    scraper = BitskinsScraper()
    scraper.run_forever()


if __name__ == "__main__":
    main()