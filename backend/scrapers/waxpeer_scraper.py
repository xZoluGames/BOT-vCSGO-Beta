# backend/scrapers/waxpeer_scraper.py

from typing import List, Dict, Optional
import sys
from pathlib import Path

# Agregar el directorio padre al path para imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.core.base_scraper import BaseScraper
from backend.core.translator import get_translator


class WaxpeerScraper(BaseScraper):
    """
    Scraper para Waxpeer.com
    
    Este scraper reemplaza tanto Waxpeer_noproxy.py como Waxpeer_vproxy.py
    El uso de proxy se determina por configuración, no por archivos separados
    """
    
    def __init__(self, use_proxy: Optional[bool] = None):
        """
        Inicializa el scraper de Waxpeer
        
        Args:
            use_proxy: Forzar uso de proxy (None = usar config global)
        """
        super().__init__('Waxpeer', use_proxy)
        
        # URL de la API de Waxpeer
        self.api_url = self.config.get(
            'api_url',
            'https://api.waxpeer.com/v1/prices?game=csgo&minified=0&single=0'
        )
        
        # Si requiere autenticación, obtener API key
        if self.config.get('requires_auth'):
            api_key = self.config_manager.get_api_key('WAXPEER')
            if api_key:
                self.headers['Authorization'] = f'Bearer {api_key}'
        
        # Configurar traductor
        self.translator = get_translator('waxpeer', self.config_manager.get_language_config())
    
    def fetch_data(self) -> List[Dict]:
        """
        Obtiene los datos de la API de Waxpeer
        
        Returns:
            Lista de items con formato estándar
        """
        self.logger.info(f"Obteniendo datos de Waxpeer...")
        
        # Hacer petición a la API
        response = self.make_request(self.api_url)
        
        if response:
            return self.parse_response(response)
        
        return []
    
    def parse_response(self, response) -> List[Dict]:
        """
        Parsea la respuesta de Waxpeer
        
        Args:
            response: Respuesta de requests
            
        Returns:
            Lista de items parseados
        """
        try:
            data = response.json()
            
            # Verificar que la respuesta sea exitosa
            if not data.get('success'):
                self.logger.error(f"Respuesta no exitosa de Waxpeer: {data}")
                return []
            
            # Verificar que haya items
            if 'items' not in data:
                self.logger.warning("No se encontraron items en la respuesta")
                return []
            
            # Procesar items
            items = []
            for item in data['items']:
                # Obtener nombre y precio
                name = item.get('name')
                price_raw = item.get('min', 0)
                
                if not name:
                    continue
                
                # Formatear precio (Waxpeer lo da en centavos)
                price = self._format_price(price_raw)
                
                # Crear item con formato estándar
                formatted_item = {
                    'Item': name,
                    'Price': price
                }
                
                # URL opcional si está disponible
                if item.get('steam_market_hash_name'):
                    formatted_item['URL'] = f"https://waxpeer.com/es/?game=csgo&search={name}"
                
                items.append(formatted_item)
            
            self.logger.info(f"Parseados {len(items)} items de Waxpeer")
            
            # Mensaje traducido si está en modo interactivo
            if hasattr(self, 'translator'):
                print(self.translator.gettext('data_fetched', count=len(items)), flush=True)
            
            return items
            
        except Exception as e:
            self.logger.error(f"Error parseando respuesta de Waxpeer: {e}")
            return []
    
    def _format_price(self, price: int) -> str:
        """
        Formatea el precio de Waxpeer (viene en centavos como entero)
        
        Args:
            price: Precio en centavos (ej: 1234 = $12.34)
            
        Returns:
            Precio formateado como string
        """
        price_str = str(price)
        
        if len(price_str) <= 3:
            # Precios menores a $1.00
            return "0." + price_str.zfill(3)
        else:
            # Insertar punto decimal
            return price_str[:-3] + '.' + price_str[-3:]


# Funciones de compatibilidad para facilitar la migración
def main_no_proxy():
    """Función principal sin proxy (compatibilidad con script antiguo)"""
    scraper = WaxpeerScraper(use_proxy=False)
    scraper.run_forever()


def main_with_proxy():
    """Función principal con proxy (compatibilidad con script antiguo)"""
    scraper = WaxpeerScraper(use_proxy=True)
    scraper.run_forever()


def main():
    """
    Función principal que decide automáticamente si usar proxy o no
    basándose en la configuración
    """
    # El scraper usará la configuración global por defecto
    scraper = WaxpeerScraper()
    scraper.run_forever()


if __name__ == "__main__":
    # Si se ejecuta directamente, usar configuración automática
    main()