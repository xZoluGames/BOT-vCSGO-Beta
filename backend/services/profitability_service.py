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
    
    def to_dict(self) -> dict:
        """Convierte a diccionario para JSON"""
        return {
            'name': self.name,
            'buy_price': self.buy_price,
            'steam_price': self.steam_price,
            'steam_link': self.steam_link,
            'net_steam_price': self.net_steam_price,
            'rentabilidad': self.rentabilidad,
            'platform': self.buy_platform,
            'link': self.buy_url
        }


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
        
        # Encontrar el primer intervalo mayor o igual
        first_greater = next((value for value in intervals if value >= input_value), None)
        index_of_first_greater = intervals.index(first_greater)
        
        # Calcular precio neto
        fee_subtraction = round(input_value - fees[index_of_first_greater - 1], 2)
        return fee_subtraction


class ProfitabilityService:
    """Servicio principal para calcular rentabilidad entre plataformas"""
    
    # URLs base de las plataformas
    PLATFORM_URLS = {
        'waxpeer': 'https://waxpeer.com/csgo/',
        'csdeals': 'https://cs.deals/pt-BR/market/730/',
        'empire': 'https://csgoempire.com/item/730/',
        'skinport': 'https://skinport.com/es/market/730?search=',
        'manncostore': 'https://mannco.store/item/730/',
        'cstrade': 'https://old.cs.trade/#',
        'bitskins': 'https://bitskins.com/inventory/730/search?market_hash_name=',
        'tradeit': 'https://tradeit.gg/csgo/trade?search=',
        'marketcsgo': 'https://market.csgo.com/?t=all&p=0&f=0&s=0&search=',
        'skinout': 'https://skinout.gg/market/cs2?item=',
        'skindeck': 'https://skindeck.com/listings?query=',
        'white': 'https://white.market/search?game[]=CS2&query=',
        'lisskins': 'https://lis-skins.com/market_730.html?search_item=',
        'shadowpay': 'https://shadowpay.com/en/csgo?search='
    }
    
    STEAM_URL = 'https://steamcommunity.com/market/listings/730/'
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self.fee_calculator = SteamFeeCalculator()
        self.translator = get_translator('rentabilidad', self.config_manager.get_language_config())
        self.logger = logger.bind(service="ProfitabilityService")
        
        # Rutas de archivos JSON
        self.json_path = Path('JSON')
        
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
        """Carga los precios de Steam desde JSON"""
        steam_file = self.json_path / 'steam_data.json'
        
        if not steam_file.exists():
            self.logger.error("No se encontró steam_data.json")
            return {}
            
        try:
            with open(steam_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Convertir lista a diccionario para búsqueda rápida
                return {item['Item']: item['Price'] for item in data}
        except Exception as e:
            self.logger.error(f"Error cargando steam_data.json: {e}")
            return {}
    
    def find_profitable_items(self) -> List[ProfitableItem]:
        """Encuentra todos los items rentables comparando todas las plataformas"""
        profitable_items = []
        
        # Cargar precios de Steam
        steam_prices = self.load_steam_prices()
        if not steam_prices:
            self.logger.error("No hay precios de Steam disponibles")
            return []
        
        # Plataformas a analizar
        platforms = [
            'waxpeer', 'csdeals', 'empire', 'skinport', 'manncostore',
            'cstrade', 'bitskins', 'tradeit', 'marketcsgo', 'skinout',
            'skindeck', 'white', 'lisskins', 'shadowpay'
        ]
        
        # Analizar cada plataforma
        for platform in platforms:
            # Obtener umbral de rentabilidad para esta plataforma
            threshold_key = f'profitability_{platform}'
            min_profitability = self.thresholds.get(threshold_key, 0.05)  # 5% por defecto
            
            # Cargar datos de la plataforma
            platform_data = self.load_platform_data(platform)
            
            for item in platform_data:
                try:
                    name = item.get('Item', '')
                    buy_price = float(item.get('Price', 0))
                    
                    if not name or buy_price == 0:
                        continue
                    
                    # Buscar precio en Steam
                    steam_price = steam_prices.get(name)
                    if not steam_price:
                        continue
                    
                    # Calcular rentabilidad
                    rentabilidad, net_steam_price = self.calculate_profitability(
                        steam_price, buy_price
                    )
                    
                    # Si es rentable según el umbral
                    if rentabilidad >= min_profitability:
                        # Construir URL del item
                        item_url = self.PLATFORM_URLS.get(platform, '') + name
                        steam_url = self.STEAM_URL + name
                        
                        profitable_item = ProfitableItem(
                            name=name,
                            buy_price=buy_price,
                            buy_platform=platform.capitalize(),
                            buy_url=item_url,
                            steam_price=steam_price,
                            net_steam_price=net_steam_price,
                            rentabilidad=rentabilidad,
                            steam_link=steam_url
                        )
                        
                        profitable_items.append(profitable_item)
                        
                except Exception as e:
                    self.logger.error(f"Error procesando item {item} de {platform}: {e}")
                    continue
        
        # Ordenar por rentabilidad descendente
        profitable_items.sort(key=lambda x: x.rentabilidad, reverse=True)
        
        return profitable_items
    
    def save_profitable_items(self, items: List[ProfitableItem]):
        """Guarda los items rentables en JSON"""
        output_file = self.json_path / 'rentabilidad.json'
        
        try:
            # Convertir a lista de diccionarios
            data = [item.to_dict() for item in items]
            
            # Guardar con formato legible
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
                
            self.logger.info(f"Guardadas {len(items)} oportunidades rentables")
            
        except Exception as e:
            self.logger.error(f"Error guardando rentabilidad: {e}")
    
    def run(self):
        """Ejecuta el análisis de rentabilidad"""
        self.logger.info("Iniciando análisis de rentabilidad...")
        
        # Encontrar items rentables
        profitable_items = self.find_profitable_items()
        
        if profitable_items:
            self.logger.info(f"Encontradas {len(profitable_items)} oportunidades rentables")
            
            # Guardar resultados
            self.save_profitable_items(profitable_items)
            
            # Mostrar las mejores oportunidades
            print("\n" + "="*60)
            print("TOP 10 MEJORES OPORTUNIDADES DE ARBITRAJE")
            print("="*60)
            
            for i, item in enumerate(profitable_items[:10], 1):
                print(f"\n{i}. {item.name}")
                print(f"   Comprar en: {item.buy_platform} - ${item.buy_price:.2f}")
                print(f"   Vender en: Steam - ${item.steam_price:.2f} (neto: ${item.net_steam_price:.2f})")
                print(f"   Rentabilidad: {item.rentabilidad_percentage:.2f}%")
                print(f"   Ganancia: ${item.profit:.2f}")
        else:
            self.logger.warning("No se encontraron oportunidades rentables")

def run_profitability_monitor():
    """Función para ejecutar el monitor de rentabilidad continuamente"""
    service = ProfitabilityService()
    
    while True:
        try:
            # Ejecutar análisis
            service.run()
            
            # Esperar 60 segundos antes del próximo análisis
            time.sleep(60)
            
        except KeyboardInterrupt:
            logger.info("Monitor de rentabilidad detenido por el usuario")
            break
        except Exception as e:
            logger.error(f"Error en monitor de rentabilidad: {e}")
            time.sleep(60)  # Esperar antes de reintentar


if __name__ == "__main__":
    # Para pruebas
    run_profitability_monitor()