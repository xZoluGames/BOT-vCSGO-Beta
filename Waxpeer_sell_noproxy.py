import requests
import json
import os
from typing import Dict, List, Optional


def get_base_path() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def cargar_api_key() -> Optional[str]:
    config_file = os.path.join(get_base_path(), 'Configs', 'Api.json')
    try:
        with open(config_file, 'r', encoding='utf-8') as file:
            config = json.load(file)
            return config.get("api_key_waxpeer")
    except FileNotFoundError:
        print("Archivo de configuración 'Api.json' no encontrado.")
        return None


def obtener_todas_buy_orders() -> Optional[Dict]:
    api_url = "https://api.waxpeer.com/v1/buy-orders/snapshot?game=csgo"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()

        if data.get('success') and 'offers' in data:
            return {offer['name']: float(offer['max']) / 1000 for offer in data['offers']}
        else:
            print("No se pudieron obtener las buy orders o la respuesta no fue exitosa.")
            return None
    except requests.RequestException as e:
        print(f"Error en la solicitud a la API: {e}")
        return None
    except Exception as e:
        print(f"Error procesando la respuesta: {e}")
        return None


def cargar_steam_data() -> List[Dict]:
    steam_items_json = os.path.join(get_base_path(), "JSON", "steam_listing_prices.json")
    try:
        with open(steam_items_json, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Archivo {steam_items_json} no encontrado.")
        return []


def comparar_precios(buy_orders: Dict[str, float], steam_items: List[Dict], rentabilidad_minima: float = 0.0) -> List[
    Dict]:
    resultados_profitable = []

    for steam_item in steam_items:
        item_name = steam_item['name']
        precio_steam = float(steam_item['price'])

        if item_name in buy_orders and precio_steam > 0:
            precio_buy_order = buy_orders[item_name]

            if precio_buy_order > precio_steam:
                rentabilidad = precio_buy_order - precio_steam
                rentabilidad_porcentaje = (rentabilidad / precio_steam) * 100

                # Solo incluir si cumple con la rentabilidad mínima
                if rentabilidad_porcentaje >= rentabilidad_minima:
                    resultados_profitable.append({
                        'item': item_name,
                        'precio_steam': precio_steam,
                        'precio_buy_order': precio_buy_order,
                        'rentabilidad': rentabilidad,
                        'rentabilidad_porcentaje': rentabilidad_porcentaje
                    })

    return resultados_profitable


def guardar_resultados(resultados: List[Dict], filename: str = 'profiteable_sells_waxpeer.json') -> None:
    result_path = os.path.join(get_base_path(), "JSON", filename)
    os.makedirs(os.path.dirname(result_path), exist_ok=True)
    with open(result_path, 'w', encoding='utf-8') as file:
        json.dump(resultados, file, indent=4, ensure_ascii=False)
    print(f"Resultados guardados en {result_path}")


if __name__ == "__main__":
    # Configura aquí el porcentaje mínimo de rentabilidad deseado
    RENTABILIDAD_MINIMA = 10.0  # Por ejemplo, 10% de rentabilidad mínima

    steam_items = cargar_steam_data()

    if not steam_items:
        print("No se pudieron cargar los datos de Steam.")
        exit(1)

    buy_orders = obtener_todas_buy_orders()

    if buy_orders:
        resultados_profitable = comparar_precios(buy_orders, steam_items, RENTABILIDAD_MINIMA)

        if resultados_profitable:
            # Ordenar resultados por rentabilidad porcentual
            resultados_profitable.sort(key=lambda x: x['rentabilidad_porcentaje'], reverse=True)
            guardar_resultados(resultados_profitable)
            print(
                f"Se encontraron {len(resultados_profitable)} oportunidades rentables con {RENTABILIDAD_MINIMA}% o más de rentabilidad.")
        else:
            print(f"No se encontraron oportunidades con rentabilidad mayor o igual a {RENTABILIDAD_MINIMA}%.")
    else:
        print("No se pudieron obtener los datos de Waxpeer.")