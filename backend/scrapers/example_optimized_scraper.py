# backend/scrapers/example_optimized_scraper.py
"""
Ejemplo de scraper optimizado usando todas las mejoras disponibles
"""
from typing import List, Dict, Optional
import asyncio
from backend.scrapers.concurrent_scraper import ConcurrentScraper


class ExampleOptimizedScraper(ConcurrentScraper):
    """Ejemplo de implementación optimizada"""
    
    def __init__(self, use_proxy: Optional[bool] = None):
        super().__init__('ExamplePlatform', use_proxy)
        self.base_url = "https://api.example.com/items"
        
    def fetch_data(self) -> List[Dict]:
        """Implementación optimizada con caché y concurrencia"""
        # Intentar obtener del caché primero
        cache_key = f"{self.platform_name}:all_items"
        
        def fetch_fresh_data():
            # Para APIs paginadas, generar URLs
            urls = [f"{self.base_url}?page={i}" for i in range(1, 11)]
            
            # Fetch concurrente
            return self.fetch_multiple_sync(urls, self.parse_page)
        
        # Usar caché con TTL de 5 minutos
        return self.get_cached_data(cache_key, fetch_fresh_data, ttl=300)
    
    def parse_page(self, response) -> List[Dict]:
        """Parsea una página de resultados"""
        try:
            data = response.json()
            items = []
            
            for item in data.get('items', []):
                items.append({
                    'Item': item['name'],
                    'Price': item['price']
                })
            
            return items
        except Exception as e:
            self.logger.error(f"Error parseando: {e}")
            return []
    
    async def fetch_data_async(self) -> List[Dict]:
        """Versión asíncrona para máximo rendimiento"""
        urls = [f"{self.base_url}?page={i}" for i in range(1, 11)]
        
        # Fetch asíncrono de todas las páginas
        all_results = await self.fetch_multiple_async(urls)
        
        # Procesar resultados
        items = []
        for result in all_results:
            if result and 'items' in result:
                for item in result['items']:
                    items.append({
                        'Item': item['name'],
                        'Price': item['price']
                    })
        
        return items
    
    def parse_response(self, response):
        """Implementación requerida por BaseScraper"""
        return self.parse_page(response)


def main():
    # Ejemplo de uso síncrono
    scraper = ExampleOptimizedScraper()
    data = scraper.run_once()
    print(f"Obtenidos {len(data)} items")
    
    # Ejemplo de uso asíncrono
    async def run_async():
        scraper = ExampleOptimizedScraper()
        data = await scraper.fetch_data_async()
        print(f"Obtenidos {len(data)} items (async)")
    
    # asyncio.run(run_async())


if __name__ == "__main__":
    main()
