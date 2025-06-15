# backend/scrapers/skindeck_scraper.py
from backend.core.base_scraper import BaseScraper
from typing import List, Dict, Optional
from backend.core.translator import get_translator
class SkindeckScraper(BaseScraper):
    """
    Scraper para Skindeck.com
    Requiere token de autenticación
    """
    
    def __init__(self, use_proxy: Optional[bool] = None):
        super().__init__('Skindeck', use_proxy)
        
        self.api_url = self.config.get(
            'api_url',
            'https://api.skindeck.com/client/market'
        )
        
        # Token de autenticación (desde config o hardcoded)
        auth_token = self.config_manager.get_api_key('SKINDECK') or \
                    "eyJhbGciOiJIUzI1NiIsInVzZXJJZCI6IjY3MGY4YzMwNTBjYzQ5NmIzNTRlZjhjZSJ9.eyJjbGllbnQiOnsic3RlYW1JRCI6Ijc2NTYxMTk4ODQ4NjQ0Nzc1IiwidHJhZGVVcmwiOiJodHRwczovL3N0ZWFtY29tbXVuaXR5LmNvbS90cmFkZW9mZmVyL25ldy8_cGFydG5lcj04ODgzNzkwNDcmdG9rZW49Y0dvM1I4M1kifSwiaWF0IjoxNzMxMTEwODg3LCJleHAiOjE3NjI2Njg0ODd9.Iu8TUhg1SC5ax1W870kXqvpCuzzoUH5VWCLCtxETbx4"
        
        if auth_token:
            self.headers.update({
                'Authorization': f'Bearer {auth_token}',
                'Accept': 'application/json',
                'Referer': 'https://api.skindeck.com/'
            })
        
        self.translator = get_translator('skindeck', self.config_manager.get_language_config())
    
    def fetch_data(self) -> List[Dict]:
        """Obtiene datos de Skindeck"""
        params = {
            'page': 1,
            'perPage': 10000,
            'sort': 'price_desc'
        }
        
        response = self.make_request(self.api_url, params=params)
        if response:
            return self.parse_response(response)
        return []
    
    def parse_response(self, response) -> List[Dict]:
        try:
            data = response.json()
            
            if not data.get('success') or 'items' not in data:
                self.logger.error("Respuesta no exitosa de Skindeck")
                if hasattr(self, 'translator'):
                    print(self.translator.gettext('unexpected_format'), flush=True)
                return []
            
            items = []
            for item in data['items']:
                # Solo items que tengan offer
                if not item.get('offer'):
                    continue
                    
                name = item['market_hash_name']
                price = item['offer'].get('price')
                
                if name and price is not None:
                    items.append({
                        'Item': name,
                        'Price': price
                    })
            
            self.logger.info(f"Parseados {len(items)} items de Skindeck")
            
            if hasattr(self, 'translator'):
                print(self.translator.gettext('success_message', total_items=len(items)), flush=True)
            
            return items
            
        except Exception as e:
            self.logger.error(f"Error parseando Skindeck: {e}")
            if hasattr(self, 'translator'):
                print(self.translator.gettext('fetch_error', error=str(e)), flush=True)
            return []




    def main():
        scraper = SkindeckScraper()
        scraper.run_forever()


    if __name__ == "__main__":
        main()
