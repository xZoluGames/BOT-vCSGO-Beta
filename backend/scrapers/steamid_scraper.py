# backend/scrapers/steamid_scraper.py

import re
from typing import List, Dict, Optional
import sys
from pathlib import Path
import concurrent.futures
from urllib.parse import unquote

sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.core.base_scraper import BaseScraper
from backend.core.translator import get_translator
class SteamIDScraper(BaseScraper):
    """
    Scraper para obtener item_nameids de Steam
    """
    
    def __init__(self, use_proxy: Optional[bool] = None):
        super().__init__('SteamID', use_proxy)
        
        self.base_url = "https://steamcommunity.com/market/listings/730/{}"
    
    def fetch_data(self) -> List[Dict]:
        """Obtiene item_nameids comparando con nombres existentes"""
        self.logger.info("Obteniendo item nameids de Steam...")
        
        # Cargar nombres existentes
        names_file = self.config_manager.get_json_output_path('item_names.json')
        nameids_file = self.config_manager.get_json_output_path('item_nameids.json')
        
        if not names_file.exists():
            self.logger.error("No se encontró item_names.json")
            return []
        
        try:
            import json
            
            # Cargar nombres
            with open(names_file, 'r', encoding='utf-8') as f:
                item_names = json.load(f)
            
            # Cargar nameids existentes
            existing_nameids = []
            if nameids_file.exists():
                with open(nameids_file, 'r', encoding='utf-8') as f:
                    existing_nameids = json.load(f)
            
        except Exception as e:
            self.logger.error(f"Error cargando archivos: {e}")
            return []
        
        # Comparar y encontrar items nuevos
        updated_nameids = self._compare_and_update_items(item_names, existing_nameids)
        
        return updated_nameids
    
    def _compare_and_update_items(self, item_names: List, existing_nameids: List) -> List[Dict]:
        """Compara y actualiza items"""
        names_dict = {item['name']: item for item in item_names}
        nameids_dict = {item['name']: item for item in existing_nameids}
        
        # Items que necesitan actualización
        items_to_update = []
        
        for name, item in names_dict.items():
            if name not in nameids_dict:
                items_to_update.append(item)
                self.logger.info(f"Nuevo item: {name}")
        
        # Mantener items existentes que siguen en la lista
        updated_nameids = [item for item in existing_nameids if item['name'] in names_dict]
        
        # Procesar items nuevos
        if items_to_update:
            self.logger.info(f"Procesando {len(items_to_update)} items nuevos...")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                futures = [
                    executor.submit(self._process_item, item) 
                    for item in items_to_update
                ]
                
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    if result and result['id'] is not None:
                        updated_nameids.append(result)
                        self.logger.info(f"Item procesado: {result['name']}")
        
        return updated_nameids
    
    def _process_item(self, item: Dict, max_attempts: int = 10) -> Optional[Dict]:
        """Procesa un item para obtener su nameid"""
        name = item['name']
        
        for attempt in range(max_attempts):
            nameid = self._get_item_nameid(name)
            if nameid:
                return {"name": name, "id": nameid}
            
            self.logger.warning(f"Intento {attempt + 1}/{max_attempts} fallido para: {name}")
        
        self.logger.error(f"No se pudo obtener nameid para: {name}")
        return {"name": name, "id": None}
    
    def _get_item_nameid(self, name: str) -> Optional[str]:
        """Obtiene el nameid de un item usando regex"""
        url = self.base_url.format(name)
        response = self.make_request(url, max_retries=3)
        
        if response:
            try:
                matches_ids = re.findall(r"Market_LoadOrderSpread\(\s*(\d+)\s*\)", response.text)
                if matches_ids:
                    item_nameid = re.sub(r"\D", "", matches_ids[0])
                    self.logger.debug(f"Nameid obtenido para '{name}': {item_nameid}")
                    return item_nameid
            except Exception as e:
                self.logger.error(f"Error procesando {name}: {e}")
        
        return None
    
    def parse_response(self, response):
        """No se usa en SteamID"""
        pass
    def main_steamid():
        scraper = SteamIDScraper()
        scraper.run_forever()