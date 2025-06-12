# backend/scrapers/csdeals_scraper.py

from typing import List, Dict, Optional
import sys
from pathlib import Path

# Agregar el directorio padre al path para imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.core.base_scraper import BaseScraper
from backend.core.translator import get_translator


class CSDealsScraper(BaseScraper):
    """
    Scraper para CS.deals
    
    Este scraper unifica Csdeals_noproxy.py y Csdeals_vproxy.py
    """
    
    def __init__(self, use_proxy: Optional[bool] = None):
        """
        Inicializa el scraper de CSDeals
        
        Args:
            use_proxy: Forzar uso de proxy (None = usar config global)
        """
        super().__init__('CSDeals', use_proxy)
        
        # URL de la API
        self.api_url = self.config.get(
            'api_url',
            'https://cs.deals/API/IPricing/GetLowestPrices/v1?appid=730'
        )
        
        # Configurar traductor
        self.translator = get_translator('csdeals', self.config_manager.get_language_config())
        
        # Headers adicionales si son necesarios
        self.headers.update({
            'Accept': 'application/json',
            'Referer': 'https://cs.deals/'
        })
    
    def fetch_data(self) -> List[Dict]:
        """
        Obtiene los datos de la API de CSDeals
        
        Returns:
            Lista de items con formato estándar
        """
        self.logger.info("Obteniendo datos de CSDeals...")
        
        # Hacer petición a la API
        response = self.make_request(self.api_url)
        
        if response:
            return self.parse_response(response)
        
        return []
    
    def parse_response(self, response) -> List[Dict]:
        """
        Parsea la respuesta de CSDeals
        
        Args:
            response: Respuesta de requests
            
        Returns:
            Lista de items parseados
        """
        try:
            data = response.json()
            
            # Verificar estructura de respuesta de CSDeals
            if not data.get('success'):
                self.logger.error(f"Respuesta no exitosa de CSDeals: {data}")
                if hasattr(self, 'translator'):
                    print(self.translator.gettext('unexpected_format'), flush=True)
                return []
            
            # CSDeals tiene la estructura: data -> response -> items
            if 'response' not in data or 'items' not in data['response']:
                self.logger.warning("Estructura inesperada en respuesta de CSDeals")
                if hasattr(self, 'translator'):
                    print(self.translator.gettext('unexpected_format'), flush=True)
                return []
            
            # Procesar items
            items = []
            for item in data['response']['items']:
                # Obtener campos necesarios
                name = item.get('marketname')
                price = item.get('lowest_price')
                
                if not name or price is None:
                    continue
                
                # Crear item con formato estándar
                formatted_item = {
                    'Item': name,
                    'Price': float(price)  # CSDeals ya devuelve el precio en formato decimal
                }
                
                items.append(formatted_item)
            
            self.logger.info(f"Parseados {len(items)} items de CSDeals")
            
            # Mensaje traducido
            if hasattr(self, 'translator'):
                print(self.translator.gettext('success_message', total_items=len(items)), flush=True)
            
            return items
            
        except Exception as e:
            self.logger.error(f"Error parseando respuesta de CSDeals: {e}")
            if hasattr(self, 'translator'):
                print(self.translator.gettext('fetch_error', error=str(e)), flush=True)
            return []


# Funciones de compatibilidad
def main():
    """Función principal - usa configuración automática"""
    scraper = CSDealsScraper()
    scraper.run_forever()


if __name__ == "__main__":
    main()