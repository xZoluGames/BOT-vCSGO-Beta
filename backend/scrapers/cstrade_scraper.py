# backend/scrapers/cstrade_scraper.py

from typing import List, Dict, Optional
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.core.base_scraper import BaseScraper
from backend.core.translator import get_translator


class CstradeScraper(BaseScraper):
    """
    Scraper para CS.trade
    
    Unifica Cstrade_noproxy.py y Cstrade_vproxy.py
    """
    
    def __init__(self, use_proxy: Optional[bool] = None):
        super().__init__('Cstrade', use_proxy)
        
        self.api_url = self.config.get(
            'api_url',
            'https://cdn.cs.trade:2096/api/prices_CSGO'
        )
        
        # Tasa de bono de CsTrade (50% por defecto)
        self.bonus_rate = self.config.get('bonus_rate', 50)
        
        self.translator = get_translator('cstrade', self.config_manager.get_language_config())
    
    def fetch_data(self) -> List[Dict]:
        """Obtiene datos de la API de CsTrade"""
        self.logger.info("Obteniendo datos de CsTrade...")
        
        response = self.make_request(self.api_url)
        if response:
            return self.parse_response(response)
        return []
    
    def parse_response(self, response) -> List[Dict]:
        """Parsea la respuesta de CsTrade"""
        try:
            data = response.json()
            
            items = []
            for item_name, item_data in data.items():
                tradable = item_data.get('tradable', 0)
                reservable = item_data.get('reservable', 0)
                
                # Solo items disponibles (tradable o reservable != 0)
                if tradable == 0 and reservable == 0:
                    continue
                
                original_price = item_data.get('price', 0)
                
                # Calcular precio real antes del bono
                real_price = self._calculate_real_price(original_price, self.bonus_rate)
                
                items.append({
                    'Item': item_name,
                    'Price': f"{real_price:.2f}"
                })
            
            self.logger.info(f"Parseados {len(items)} items de CsTrade")
            
            if hasattr(self, 'translator'):
                print(self.translator.gettext('success_message', total_items=len(items)), flush=True)
            
            return items
            
        except Exception as e:
            self.logger.error(f"Error parseando respuesta de CsTrade: {e}")
            if hasattr(self, 'translator'):
                print(self.translator.gettext('fetch_error', error=str(e)), flush=True)
            return []
    
    def _calculate_real_price(self, page_price: float, bonus_rate: float) -> float:
        """
        Calcula el precio real antes del bono de CsTrade
        
        Args:
            page_price: Precio mostrado en la página
            bonus_rate: Tasa de bono (ej: 50 para 50%)
        
        Returns:
            Precio real sin el bono
        """
        bonus_decimal = bonus_rate / 100
        return page_price / (1 + bonus_decimal)


def main():
    scraper = CstradeScraper()
    scraper.run_forever()


if __name__ == "__main__":
    main()