# backend/scrapers/rapidskins_scraper.py
import time
from backend.core.base_scraper import BaseScraper
from typing import List, Dict, Optional
from backend.core.translator import get_translator
class RapidskinsScraper(BaseScraper):
    """
    Scraper para Rapidskins.com usando GraphQL
    """
    
    def __init__(self, use_proxy: Optional[bool] = None):
        super().__init__('Rapidskins', use_proxy)
        
        self.api_url = self.config.get(
            'api_url',
            'https://api.rapidskins.com/graphql'
        )
        
        self.translator = get_translator('rapidskins', self.config_manager.get_language_config())
        
        # Headers para GraphQL
        self.headers.update({
            "Content-Type": "application/json"
        })
    
    def fetch_data(self) -> List[Dict]:
        """Obtiene datos de Rapidskins usando GraphQL"""
        self.logger.info("Obteniendo datos de Rapidskins...")
        
        all_items = []
        page = 1
        
        while True:
            items = self._fetch_page(page)
            
            if not items:
                self.logger.info(f"No más items en página {page}")
                break
            
            all_items.extend(items)
            self.logger.info(f"Página {page}: {len(items)} items obtenidos")
            
            page += 1
            time.sleep(1)  # Pausa entre páginas
        
        self.logger.info(f"Total items obtenidos de Rapidskins: {len(all_items)}")
        
        if hasattr(self, 'translator'):
            print(self.translator.gettext('success_message', total_items=len(all_items)), flush=True)
        
        return all_items
    
    def _fetch_page(self, page: int) -> List[Dict]:
        """Obtiene items de una página específica"""
        query = """
        query Inventories($filter: InventoryFilters!) { 
            siteInventory(filter: $filter) {
                csgo {
                    ... on SteamInventory {
                        items {
                            marketHashName
                            price {
                                coinAmount
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            "filter": {
                "page": page,
                "sort": "PRICE_DESC",
                "appIds": [730],
                "search": None,
                "cs2ItemCategories": [],
                "rustItemCategories": [],
                "itemExteriors": [],
                "statTrakOnly": False,
                "tradableOnly": False,
                "souvenirOnly": False,
                "minimumPrice": {"coinAmount": 0},
                "maximumPrice": {"coinAmount": 2000000}
            }
        }
        
        payload = {
            'query': query,
            'variables': variables
        }
        
        response = self.make_request(
            self.api_url,
            method='POST',
            json=payload
        )
        
        if response:
            try:
                data = response.json()
                items = data['data']['siteInventory']['csgo']['items']
                
                # Formatear items
                formatted_items = []
                for item in items:
                    formatted_items.append({
                        'marketHashName': item['marketHashName'],
                        'price': {
                            'coinAmount': item['price']['coinAmount']
                        }
                    })
                
                return formatted_items
                
            except Exception as e:
                self.logger.error(f"Error procesando página {page}: {e}")
                return []
        
        return []
    
    def parse_response(self, response):
        """No se usa en Rapidskins"""
        pass


    def main_rapidskins():
        scraper = RapidskinsScraper()
        scraper.run_forever()


    if __name__ == "__main__":

        import os
        filename = os.path.basename(__file__)
        if 'rapidskins' in filename:
            main_rapidskins()