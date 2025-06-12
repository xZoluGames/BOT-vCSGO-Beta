
# backend/scrapers/skinout_scraper.py

from typing import List, Dict, Optional
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.core.base_scraper import BaseScraper
from backend.core.translator import get_translator


class SkinoutScraper(BaseScraper):
    """
    Scraper para Skinout.gg
    Scraper multi-threaded para obtener datos de múltiples páginas
    """
    
    def __init__(self, use_proxy: Optional[bool] = None):
        super().__init__('Skinout', use_proxy)
        
        self.base_api_url = self.config.get(
            'base_url',
            'https://skinout.gg/api/market/items'
        )
        
        self.translator = get_translator('skinout', self.config_manager.get_language_config())
        
        # Configuración de concurrencia
        self.max_workers = 10
        self.empty_pages_threshold = 3
        self.retry_delay = 5
    
    def fetch_data(self) -> List[Dict]:
        """Obtiene datos de Skinout usando múltiples threads"""
        self.logger.info("Obteniendo datos de Skinout...")
        
        all_items = []
        current_page = 0
        batch_size = self.max_workers * 2
        
        while True:
            self.logger.info(f"Procesando lote de páginas {current_page} a {current_page + batch_size - 1}")
            
            batch_items, should_stop = self._process_batch(current_page, batch_size)
            all_items.extend(batch_items)
            
            if should_stop:
                self.logger.info("Se detectaron múltiples páginas vacías. Finalizando...")
                break
            
            current_page += batch_size
            time.sleep(1)  # Pausa entre lotes
        
        self.logger.info(f"Total items obtenidos de Skinout: {len(all_items)}")
        return all_items
    
    def _process_batch(self, start_page: int, batch_size: int) -> tuple[List[Dict], bool]:
        """Procesa un lote de páginas en paralelo"""
        results = []
        empty_pages = 0
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Crear futures para cada página
            futures = []
            for page in range(start_page, start_page + batch_size):
                futures.append(executor.submit(self._obtain_page_data, page))
            
            # Procesar resultados
            for future in as_completed(futures):
                page, items = future.result()
                
                if not items:
                    empty_pages += 1
                    if empty_pages >= self.empty_pages_threshold:
                        return results, True  # Stop scraping
                else:
                    empty_pages = 0
                    results.extend(items)
                    self.logger.info(f"Página {page} completada - {len(items)} items")
        
        return results, False
    
    def _obtain_page_data(self, page: int) -> tuple[int, List[Dict]]:
        """Obtiene datos de una página específica con reintentos"""
        while True:  # Bucle infinito para reintentos
            try:
                url = f"{self.base_api_url}?page={page}"
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'application/json',
                    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
                    'Origin': 'https://skinout.gg',
                    'Referer': 'https://skinout.gg/'
                }
                
                response = self.make_request(url, headers=headers)
                if not response:
                    continue
                
                data = response.json()
                
                if data.get('success') and 'items' in data:
                    items = data['items']
                    formatted_items = [
                        {
                            'Item': item['market_hash_name'],
                            'Price': item['price']
                        }
                        for item in items
                    ]
                    return page, formatted_items
                
                # Si success=true pero no hay items
                if data.get('success'):
                    return page, []
                
            except Exception as e:
                self.logger.error(f"Error en página {page}: {e}. Reintentando en {self.retry_delay}s...")
                time.sleep(self.retry_delay)
                continue
    
    def parse_response(self, response):
        """No se usa en Skinout, el parsing se hace en fetch_data"""
        pass

    def main_skinout():
        scraper = SkinoutScraper()
        scraper.run_forever()

    if __name__ == "__main__":
        import os
        filename = os.path.basename(__file__)
        
        if 'skinout' in filename:
            main_skinout()
