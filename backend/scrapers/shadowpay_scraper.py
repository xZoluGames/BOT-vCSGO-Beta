# backend/scrapers/shadowpay_scraper.py
from backend.core.base_scraper import BaseScraper
from typing import List, Dict, Optional
class ShadowpayScraper(BaseScraper):
    """Scraper para Shadowpay.com"""
    
    def __init__(self, use_proxy: Optional[bool] = None):
        super().__init__('Shadowpay', use_proxy)
        
        self.api_url = self.config.get(
            'api_url',
            'https://api.shadowpay.com/api/v2/user/items/prices'
        )
        
        # API Key requerida
        if self.config.get('requires_auth'):
            api_key = self.config_manager.get_api_key('SHADOWPAY')
            if api_key:
                self.headers['Authorization'] = f'Bearer {api_key}'
    
    def fetch_data(self) -> List[Dict]:
        response = self.make_request(self.api_url)
        if response:
            return self.parse_response(response)
        return []
    
    def parse_response(self, response) -> List[Dict]:
        try:
            data = response.json()
            
            items = []
            for item in data.get("data", []):
                items.append({
                    "Item": item["steam_market_hash_name"],
                    "Price": item["price"]
                })
            
            self.logger.info(f"Parseados {len(items)} items de Shadowpay")
            print("Data saved successfully", flush=True)
            
            return items
        except Exception as e:
            self.logger.error(f"Error parseando Shadowpay: {e}")
            return []




    def main():
        scraper = ShadowpayScraper()
        scraper.run_forever()


    if __name__ == "__main__":
        main()
