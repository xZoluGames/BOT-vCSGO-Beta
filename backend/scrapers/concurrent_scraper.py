# backend/scrapers/concurrent_scraper.py
from typing import List, Dict, Optional, Callable
import concurrent.futures
import asyncio
import aiohttp
from backend.core.base_scraper import BaseScraper


class ConcurrentScraper(BaseScraper):
    """Scraper optimizado para realizar múltiples requests concurrentes"""
    
    def __init__(self, platform_name: str, use_proxy: Optional[bool] = None):
        super().__init__(platform_name, use_proxy)
        self.max_workers = 10
        self.semaphore = asyncio.Semaphore(5)  # Limitar concurrencia
    
    async def fetch_url_async(self, session: aiohttp.ClientSession, url: str) -> Optional[Dict]:
        """Fetch asíncrono de una URL"""
        async with self.semaphore:
            try:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        return await response.json()
            except Exception as e:
                self.logger.error(f"Error fetching {url}: {e}")
                return None
    
    async def fetch_multiple_async(self, urls: List[str]) -> List[Dict]:
        """Fetch asíncrono de múltiples URLs"""
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_url_async(session, url) for url in urls]
            results = await asyncio.gather(*tasks)
            return [r for r in results if r is not None]
    
    def fetch_multiple_sync(self, urls: List[str], 
                           parse_func: Callable[[Dict], List[Dict]]) -> List[Dict]:
        """Fetch síncrono concurrente de múltiples URLs"""
        all_items = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {
                executor.submit(self.make_request, url): url 
                for url in urls
            }
            
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    response = future.result()
                    if response:
                        items = parse_func(response)
                        all_items.extend(items)
                except Exception as e:
                    self.logger.error(f"Error processing {url}: {e}")
        
        return all_items
