# backend/scrapers/empire_scraper.py

from typing import List, Dict, Optional
import sys
from pathlib import Path

# Agregar el directorio padre al path para imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.core.base_scraper import BaseScraper
from backend.core.translator import get_translator


class EmpireScraper(BaseScraper):
    """
    Scraper para CSGOEmpire.com
    
    Unifica Empire_noproxy.py y Empire_vproxy.py
    """
    
    def __init__(self, use_proxy: Optional[bool] = None):
        super().__init__('Empire', use_proxy)
        
        # URL de la API
        self.api_url = self.config.get(
            'api_url',
            'https://csgoempire.com/api/v2/trading/items'
        )
        
        # Configurar autenticación
        if self.config.get('requires_auth'):
            api_key = self.config_manager.get_api_key('EMPIRE')
            if api_key:
                self.headers['Authorization'] = f'Bearer {api_key}'
                
        # Traductor
        self.translator = get_translator('empire', self.config_manager.get_language_config())
        
        # Tasa de conversión Empire coins a USD
        self.conversion_rate = 0.6154
    
    def fetch_data(self) -> List[Dict]:
        """Obtiene datos de Empire combinando auction=yes y auction=no"""
        self.logger.info("Obteniendo datos de Empire...")
        
        all_items = {}
        
        # Obtener items con auction=yes y auction=no
        for auction_type in ["yes", "no"]:
            items = self._fetch_auction_items(auction_type)
            
            # Combinar items, manteniendo el precio más bajo
            for name, item_data in items.items():
                if name not in all_items or item_data['Price'] < all_items[name]['Price']:
                    all_items[name] = item_data
        
        # Convertir a lista
        return list(all_items.values())
    
    def _fetch_auction_items(self, auction_type: str) -> Dict[str, Dict]:
        """Obtiene items de un tipo de subasta específico"""
        items = {}
        page = 1
        
        while True:
            params = {
                "per_page": 2500,
                "page": page,
                "order": "market_value",
                "sort": "asc",
                "auction": auction_type
            }
            
            response = self.make_request(self.api_url, params=params)
            if not response:
                break
                
            data = response.json()
            page_items = data.get('data', [])
            
            if not page_items:
                self.logger.info(f"No más items con auction={auction_type} en página {page}")
                break
                
            # Procesar items de esta página
            for item in page_items:
                name = item.get("market_name", "Unknown")
                price_in_coins = item.get("market_value", 0) / 100.0
                price_in_usd = price_in_coins * self.conversion_rate
                item_id = item.get("id")
                
                # Guardar item si es nuevo o tiene precio menor
                if name not in items or price_in_usd < items[name]['Price']:
                    items[name] = {
                        'Item': name,
                        'Price': f"{price_in_usd:.3f}",
                        'Coin': f"{price_in_coins:.3f}",
                        'id': item_id
                    }
            
            self.logger.info(f"Página {page} con auction={auction_type}: {len(page_items)} items")
            page += 1
            
        return items
    
    def parse_response(self, response) -> List[Dict]:
        """Empire maneja el parsing en fetch_data"""
        # Este método no se usa en Empire porque el parsing 
        # se hace directamente en fetch_data debido a la lógica compleja
        pass


# Funciones de compatibilidad
def main():
    """Función principal"""
    scraper = EmpireScraper()
    scraper.run_forever()


if __name__ == "__main__":
    main()