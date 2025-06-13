# backend/services/profitability_service.py

import json
import os
import time
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
import asyncio
from loguru import logger

# Importar nuestras clases base
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.core.config_manager import get_config_manager
from backend.core.translator import get_translator


@dataclass
class ProfitableItem:
    """Representa un item con oportunidad de arbitraje"""
    name: str
    buy_price: float
    buy_platform: str
    buy_url: str
    steam_price: float
    net_steam_price: float
    rentabilidad: float
    steam_link: str
    
    @property
    def rentabilidad_percentage(self) -> float:
        """Retorna la rentabilidad como porcentaje"""
        return self.rentabilidad * 100
    
    @property
    def profit(self) -> float:
        """Retorna la ganancia potencial"""
        return self.net_steam_price - self.buy_price


class SteamFeeCalculator:
    """Calcula las comisiones de Steam de forma precisa"""
    
    @staticmethod
    def subtract_fee(input_value: float) -> float:
        """
        Calcula el precio neto después de las comisiones de Steam
        Usa el algoritmo exacto del proyecto original
        """
        intervals = [0.02, 0.21, 0.32, 0.43]
        fees = [0.02, 0.03, 0.04, 0.05, 0.07, 0.09]
        
        # Extender intervalos según sea necesario
        while input_value > intervals[-1]:
            last_element = intervals[-1]
            if len(intervals) % 2 == 0:
                intervals.append(round(last_element + 0.12, 2))
            else:
                intervals.append(round(last_element + 0.11, 2))
        
        # Extender fees según sea necesario
        while len(intervals) > len(fees):
            last_element = fees[-1]
            if len(fees) % 2 == 0:
                fees.append(round(last_element + 0.01, 2))
            else:
                fees.append(round(last_element + 0.02, 2))
        
        # Encontrar el intervalo correcto
        first_greater = next((value for value in intervals if value >= input_value), None)
        index_of_first_greater = intervals.index(first_greater)
        
        # Calcular precio después de comisión
        fee_subtraction = round(input_value - fees[index_of_first_greater - 1], 2)
        return fee_subtraction


class ProfitabilityService:
    """
    Servicio principal para calcular oportunidades de arbitraje
    Reemplaza a Rentabilidad.py con arquitectura moderna
    """
    
    # URLs de las plataformas
    PLATFORM_URLS = {
        'csdeals': ('https://cs.deals/es/market/csgo/?name=', '&sort=price'),
        'waxpeer': ('https://waxpeer.com/es/?game=csgo&sort=ASC&order=price&all=0&exact=0&search=', ''),
        'skinport': ('https://skinport.com/es/market?search=', '&sort=price&order=asc'),
        'rapidskins': ('https://rapidskins.com/market', ''),
        'cstrade': ('https://cs.trade/trade?market_name=', ''),
        'tradeit': ('https://tradeit.gg/csgo/trade', ''),
        'empire': ('https://csgoempire.com/item/', ''),
        'marketcsgo': ('https://market.csgo.com/', ''),
        'bitskins': ('https://bitskins.com/market/cs2?search={"order":[{"field":"price","order":"ASC"}],"where":{"skin_name":"', '"}}'),
        'skinout': ('https://skinout.gg/en/market/', ''),
        'skindeck': ('https://skindeck.com/sell?tab=withdraw', ''),
        'lisskins': ('https://lis-skins.com/ru/market/csgo/', ''),
        'shadowpay': ('https://shadowpay.com/csgo-items?search=', '&sort_column=price&sort_dir=asc'),
        'white': ('', ''),  # URLs vienen en el JSON
        'manncostore': ('', '')  # URLs vienen en el JSON
    }
    
    STEAM_URL = "https://steamcommunity.com/market/listings/730/"
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self.fee_calculator = SteamFeeCalculator()
        self.translator = get_translator('rentabilidad', self.config_manager.get_language_config())
        self.logger = logger.bind(service="ProfitabilityService")
        
        # Rutas de archivos JSON
        self.json_path = self.config_manager.get_json_output_path('')
        
        # Cache para evitar recálculos innecesarios
        self._cache = {}
        self._last_update = {}
        
        # Cargar umbrales de rentabilidad
        self.thresholds = self.config_manager.get_notification_thresholds()
        
    def calculate_profitability(self, steam_price: float, buy_price: float) -> Tuple[float, float]:
        """
        Calcula la rentabilidad de un item
        
        Args:
            steam_price: Precio en Steam
            buy_price: Precio de compra en otra plataforma
            
        Returns:
            Tuple de (rentabilidad, precio_neto_steam)
        """
        net_steam_price = self.fee_calculator.subtract_fee(steam_price)
        
        if buy_price == 0:
            return 0, net_steam_price
            
        rentabilidad = round((net_steam_price - buy_price) / buy_price, 4)
        return rentabilidad, net_steam_price
    
    def load_platform_data(self, platform: str) -> List[Dict]:
        """Carga los datos de una plataforma desde JSON"""
        filename = f"{platform}_data.json"
        filepath = self.json_path / filename
        
        if not filepath.exists():
            self.logger.warning(f"No se encontró archivo: {filename}")
            return []
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error cargando {filename}: {e}")
            return []
    
    def load_steam_prices(self) -> Dict[str, float]:
        """Carga los precios de Steam"""
        steam_data = self.load_platform_data('steam_items')
        if not steam_data:
            # Intentar con otros nombres posibles
            steam_data = self.load_platform_data('steam_listing_prices')
            
        return {item['name']: item['price'] for item in steam_data}
    
    def find_profitable_opportunities(self) -> List[ProfitableItem]:
        """
        Encuentra todas las oportunidades de arbitraje rentables
        
        Returns:
            Lista de items rentables ordenados por rentabilidad
        """
        self.logger.info("Buscando oportunidades de arbitraje...")
        
        # Cargar precios de Steam
        steam_prices = self.load_steam_prices()
        if not steam_prices:
            self.logger.error("No se pudieron cargar precios de Steam")
            return []
        
        profitable_items = []
        
        # Plataformas a verificar
        platforms = [
            'rapidskins', 'csdeals', 'manncostore', 'cstrade', 'waxpeer',
            'skinport', 'tradeit', 'empire', 'marketcsgo', 'bitskins',
            'skinout', 'skindeck', 'white', 'lisskins', 'shadowpay'
        ]
        
        for platform in platforms:
            items = self._process_platform(platform, steam_prices)
            profitable_items.extend(items)
        
        # Ordenar por rentabilidad
        profitable_items.sort(key=lambda x: x.rentabilidad, reverse=True)
        
        self.logger.info(f"Se encontraron {len(profitable_items)} oportunidades rentables")
        
        return profitable_items
    
    def _process_platform(self, platform: str, steam_prices: Dict[str, float]) -> List[ProfitableItem]:
        """Procesa una plataforma específica"""
        # Obtener umbral de rentabilidad para esta plataforma
        threshold_key = f'profitability_{platform}'
        threshold = self.thresholds.get(threshold_key, 0.5)
        
        # Cargar datos de la plataforma
        platform_data = self.load_platform_data(platform)
        if not platform_data:
            return []
        
        profitable_items = []
        
        for item in platform_data:
            # Manejo especial para diferentes formatos
            if platform == 'rapidskins':
                name = item.get('marketHashName')
                buy_price = item.get('price', {}).get('coinAmount', 0) / 100.0
            else:
                name = item.get('Item')
                buy_price = self._parse_price(item.get('Price', 0))
            
            if not name or name not in steam_prices:
                continue
                
            steam_price = steam_prices[name]
            rentabilidad, net_steam_price = self.calculate_profitability(steam_price, buy_price)
            
            if rentabilidad >= threshold:
                # Construir URL
                platform_url = self._build_platform_url(platform, name, item)
                
                profitable_item = ProfitableItem(
                    name=name,
                    buy_price=buy_price,
                    buy_platform=platform.capitalize(),
                    buy_url=platform_url,
                    steam_price=steam_price,
                    net_steam_price=net_steam_price,
                    rentabilidad=rentabilidad,
                    steam_link=self.STEAM_URL + name
                )
                
                profitable_items.append(profitable_item)
        
        return profitable_items
    
    def _parse_price(self, price) -> float:
        """Parsea diferentes formatos de precio"""
        if isinstance(price, (int, float)):
            return float(price)
        elif isinstance(price, str):
            # Remover símbolos de moneda y convertir
            price_clean = price.replace('$', '').replace(',', '.').strip()
            try:
                return float(price_clean)
            except ValueError:
                return 0.0
        return 0.0
    
    def _build_platform_url(self, platform: str, item_name: str, item_data: Dict) -> str:
        """Construye la URL para un item en una plataforma"""
        # Algunos items tienen su propia URL
        if 'URL' in item_data:
            return item_data['URL']
        
        # Para Empire, necesitamos el ID
        if platform == 'empire' and 'id' in item_data:
            return f"https://csgoempire.com/item/{item_data['id']}"
        
        # URLs predefinidas
        if platform in self.PLATFORM_URLS:
            prefix, suffix = self.PLATFORM_URLS[platform]
            
            # Limpiar nombre para URLs
            if platform == 'skinout':
                clean_name = self._clean_name_for_url(item_name)
                return prefix + clean_name + suffix
            
            return prefix + item_name + suffix
        
        return ""
    
    def _clean_name_for_url(self, name: str) -> str:
        """Limpia un nombre para usarlo en URLs"""
        # Remover caracteres especiales
        chars_to_remove = "()™"
        for char in chars_to_remove:
            name = name.replace(char, "")
        
        # Reemplazar espacios y caracteres por guiones
        name = name.replace(" ", "-").replace("|", "-").replace(".", "-")
        
        # Eliminar guiones múltiples
        while "--" in name:
            name = name.replace("--", "-")
        
        return name.strip("-")
    
    def save_profitable_items(self, items: List[ProfitableItem]):
        """Guarda los items rentables en formato JSON"""
        # Convertir a formato del proyecto original
        data = []
        for item in items:
            data.append({
                'name': item.name,
                'buy_price': item.buy_price,
                'steam_price': item.steam_price,
                'steam_link': item.steam_link,
                'net_steam_price': item.net_steam_price,
                'rentabilidad': item.rentabilidad,
                'platform': item.buy_platform,
                'link': item.buy_url
            })
        
        output_file = self.json_path / 'rentabilidad.json'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        self.logger.info(f"Guardadas {len(items)} oportunidades en rentabilidad.json")
    
    async def monitor_continuous(self, interval: int = 60):
        """
        Monitorea continuamente las oportunidades de arbitraje
        
        Args:
            interval: Segundos entre actualizaciones
        """
        self.logger.info(f"Iniciando monitoreo continuo (intervalo: {interval}s)")
        
        while True:
            try:
                # Buscar oportunidades
                opportunities = self.find_profitable_opportunities()
                
                # Guardar resultados
                self.save_profitable_items(opportunities)
                
                # Log de resumen
                if opportunities:
                    best = opportunities[0]
                    self.logger.success(
                        f"Mejor oportunidad: {best.name} - "
                        f"Comprar en {best.buy_platform} a ${best.buy_price:.2f} - "
                        f"Rentabilidad: {best.rentabilidad_percentage:.2f}%"
                    )
                
                await asyncio.sleep(interval)
                
            except KeyboardInterrupt:
                self.logger.info("Monitoreo detenido por el usuario")
                break
            except Exception as e:
                self.logger.error(f"Error en monitoreo: {e}")
                await asyncio.sleep(interval)


# Funciones de utilidad para compatibilidad
def run_profitability_monitor():
    """Función para ejecutar el monitor de rentabilidad"""
    service = ProfitabilityService()
    
    # Ejecutar una vez para prueba
    opportunities = service.find_profitable_opportunities()
    service.save_profitable_items(opportunities)
    
    print(f"\nEncontradas {len(opportunities)} oportunidades rentables")
    
    # Mostrar las mejores 5
    for i, opp in enumerate(opportunities[:5], 1):
        print(f"\n{i}. {opp.name}")
        print(f"   Comprar en: {opp.buy_platform} - ${opp.buy_price:.2f}")
        print(f"   Vender en: Steam - ${opp.steam_price:.2f} (neto: ${opp.net_steam_price:.2f})")
        print(f"   Rentabilidad: {opp.rentabilidad_percentage:.2f}%")
        print(f"   Ganancia: ${opp.profit:.2f}")


if __name__ == "__main__":
    # Para pruebas
    run_profitability_monitor()