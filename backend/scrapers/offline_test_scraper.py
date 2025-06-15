# backend/scrapers/offline_test_scraper.py
from backend.core.base_scraper import BaseScraper
from datetime import datetime
import random

class OfflineTestScraper(BaseScraper):
    """Scraper de prueba que funciona sin conexión"""
    
    def __init__(self, use_proxy=None):
        super().__init__('OfflineTest', use_proxy=False)
    
    def fetch_data(self):
        """Genera datos de prueba sin conexión"""
        self.logger.info("Generando datos de prueba (modo offline)...")
        
        # Simular datos
        items = []
        for i in range(10):
            items.append({
                'Item': f'Test Item {i+1}',
                'Price': round(random.uniform(10, 1000), 2)
            })
        
        return items
    
    def parse_response(self, response):
        """No se usa en modo offline"""
        return response
