# backend/scrapers/steammarket_scraper.py

from typing import List, Dict, Optional
import sys
from pathlib import Path
import concurrent.futures
from urllib.parse import unquote

sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.core.base_scraper import BaseScraper
from backend.core.translator import get_translator


class SteamMarketScraper(BaseScraper):
    """
    Scraper para Steam Market
    Obtiene los highest buy orders de Steam
    """
    
    def __init__(self, use_proxy: Optional[bool] = None):
        super().__init__('SteamMarket', use_proxy)
        
        self.api_url = "https://steamcommunity.com/market/itemordershistogram?country=PK&language=english&currency=1&item_nameid={item_nameid}&two_factor=0&norender=1"
        
        self.translator = get_translator('SteamMarket_vproxy', self.config_manager.get_language_config())
    
    def fetch_data(self) -> List[Dict]:
        """Obtiene datos del Steam Market usando item_nameids"""
        self.logger.info("Obteniendo datos de Steam Market...")
        
        # Cargar item_nameids
        nameids_file = self.config_manager.get_json_output_path('item_nameids.json')
        if not nameids_file.exists():
            self.logger.error("No se encontró archivo item_nameids.json")
            return []
        
        try:
            import json
            with open(nameids_file, 'r', encoding='utf-8') as f:
                items = json.load(f)
        except Exception as e:
            self.logger.error(f"Error cargando item_nameids.json: {e}")
            return []
        
        results = []
        
        # Procesar en paralelo
        with concurrent.futures.ThreadPoolExecutor(max_workers=1000) as executor:
            futures = [
                executor.submit(self._process_item, item) 
                for item in items
            ]
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)
        
        self.logger.info(f"Obtenidos {len(results)} precios de Steam Market")
        return results
    
    def _process_item(self, item: Dict) -> Optional[Dict]:
        """Procesa un item individual"""
        item_nameid = item.get('id')
        name = unquote(item.get('name', ''))
        
        if not item_nameid:
            return None
        
        url = self.api_url.format(item_nameid=item_nameid)
        response = self.make_request(url, max_retries=3)
        
        if response:
            try:
                data = response.json()
                
                # Verificar si hay highest_buy_order
                if 'highest_buy_order' in data and data['highest_buy_order'] is not None:
                    highest_buy_order = int(data['highest_buy_order']) / 100.0
                    
                    print(self.translator.gettext('data_retrieved_success', total_items=1), flush=True)
                    
                    return {
                        "name": name,
                        "price": highest_buy_order
                    }
                else:
                    self.logger.debug(f"No buy order para: {name}")
                    return {
                        "name": name,
                        "price": 0
                    }
                    
            except Exception as e:
                self.logger.error(f"Error procesando {name}: {e}")
                return None
        
        return None
    
    def parse_response(self, response):
        """No se usa en Steam Market"""
        pass
    def main_steammarket():
        scraper = SteamMarketScraper()
        scraper.run_forever()