import requests
import json
import os
import time
import sys
from typing import Dict, List, Optional

# Obtener el path del directorio base donde está el ejecutable o script
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))


# Función para cargar la configuración de idioma desde el archivo "Language.json"
def cargar_idioma():
    config_file = os.path.join(base_path, 'Configs', 'Language.json')
    try:
        with open(config_file, 'r', encoding='utf-8') as file:
            config = json.load(file)
            return config.get("Language", "en")
    except FileNotFoundError:
        print("Archivo de configuración 'Language.json' no encontrado. Usando idioma por defecto 'en'.")
        return "en"


# Clase para gestionar las traducciones
class Translator:
    def __init__(self, script_name, lang_code):
        self.script_name = script_name
        self.lang_code = lang_code
        self.translations = self.load_translations()

    def load_translations(self):
        translation_file = os.path.join(base_path, 'Languages', self.lang_code,
                                        f'{self.script_name}_{self.lang_code}.json')
        try:
            with open(translation_file, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            print(
                f"Archivo de traducción para el script '{self.script_name}' y el idioma '{self.lang_code}' no encontrado.")
            return {}

    def gettext(self, key, **kwargs):
        template = self.translations.get(key, key)
        return template.format(**kwargs)


def cargar_steam_data() -> List[Dict]:
    steam_items_json = os.path.join(base_path, "JSON", "steam_listing_prices.json")
    try:
        with open(steam_items_json, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Archivo {steam_items_json} no encontrado.")
        return []


def comparar_precios(skindeck_items: List[Dict], steam_items: List[Dict], rentabilidad_minima: float = 0.0) -> List[
    Dict]:
    resultados_profitable = []

    # Crear un diccionario de los items de Skindeck para búsqueda más rápida
    skindeck_dict = {item['Item']: float(item['Price']) for item in skindeck_items}

    for steam_item in steam_items:
        item_name = steam_item['name']
        precio_steam = float(steam_item['price'])

        if item_name in skindeck_dict and precio_steam > 0:
            precio_skindeck = skindeck_dict[item_name]

            if precio_skindeck > precio_steam:
                rentabilidad = precio_skindeck - precio_steam
                rentabilidad_porcentaje = (rentabilidad / precio_steam) * 100

                if rentabilidad_porcentaje >= rentabilidad_minima:
                    resultados_profitable.append({
                        'item': item_name,
                        'precio_steam': precio_steam,
                        'precio_skindeck': precio_skindeck,
                        'rentabilidad': rentabilidad,
                        'rentabilidad_porcentaje': rentabilidad_porcentaje
                    })

    return resultados_profitable


def guardar_resultados(resultados: List[Dict], filename: str = 'profiteable_sells_skindeck.json') -> None:
    result_path = os.path.join(base_path, "JSON", filename)
    os.makedirs(os.path.dirname(result_path), exist_ok=True)
    with open(result_path, 'w', encoding='utf-8') as file:
        json.dump(resultados, file, indent=4, ensure_ascii=False)


# Cargar el idioma desde la configuración
language_code = cargar_idioma()

# Cargar el archivo de traducciones para 'skindeck'
translator = Translator('skindeck', language_code)

# Configuración de la API de Skindeck
API_URL = "https://api.skindeck.com/client/market"
SKINDECK_JSON = os.path.join(base_path, "JSON", "profiteable_sells_skindeck_data.json")


# Clase para manejar la solicitud de datos con soporte para proxies
class SkindeckClient:
    def __init__(self, proxies, auth_token):
        self.proxies = proxies
        self.current_proxy_index = 0
        self.auth_token = auth_token
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Referer': 'https://api.skindeck.com/',
            'Authorization': f'Bearer {self.auth_token}'
        }

    def get_next_proxy(self):
        proxy = self.proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        return proxy

    def obtener_datos_skindeck(self, rentabilidad_minima: float = 0.0):
        try:
            params = {
                'page': 1,
                'perPage': 10000,
                'sort': 'price_desc'
            }

            proxy = self.get_next_proxy()
            proxies = {
                "http": proxy,
                "https": proxy
            }

            response = requests.get(
                API_URL,
                params=params,
                headers=self.headers,
                proxies=proxies
            )
            response.raise_for_status()
            data = response.json()

            if data.get('success') and 'items' in data:
                items = [{
                    'Item': item['market_hash_name'],
                    'Price': item['price']
                } for item in data['items']]

                print(translator.gettext('success_message', total_items=len(items)), flush=True)

                # Cargar datos de Steam y comparar precios
                steam_items = cargar_steam_data()
                if steam_items:
                    resultados_profitable = comparar_precios(items, steam_items, rentabilidad_minima)
                    if resultados_profitable:
                        # Ordenar resultados por rentabilidad porcentual
                        resultados_profitable.sort(key=lambda x: x['rentabilidad_porcentaje'], reverse=True)
                        guardar_resultados(resultados_profitable)
                        print(
                            f"Se encontraron {len(resultados_profitable)} oportunidades rentables con {rentabilidad_minima}% o más de rentabilidad.",
                            flush=True)
                    else:
                        print(
                            f"No se encontraron oportunidades con rentabilidad mayor o igual a {rentabilidad_minima}%.",
                            flush=True)
                else:
                    print("No se pudieron cargar los datos de Steam.", flush=True)
            else:
                print(translator.gettext('unexpected_format'), flush=True)
        except Exception as e:
            print(translator.gettext('fetch_error', error=e), flush=True)


if __name__ == "__main__":
    try:
        RENTABILIDAD_MINIMA = 0

        # Cargar proxies desde archivo
        with open(os.path.join(base_path, 'proxy.txt'), 'r') as file:
            proxies = [line.strip() for line in file.readlines()]

        # Tu token de autenticación de Skindeck
        auth_token = "eyJhbGciOiJIUzI1NiIsInVzZXJJZCI6IjY3MGY4YzMwNTBjYzQ5NmIzNTRlZjhjZSJ9.eyJjbGllbnQiOnsic3RlYW1JRCI6Ijc2NTYxMTk4ODQ4NjQ0Nzc1IiwidHJhZGVVcmwiOiJodHRwczovL3N0ZWFtY29tbXVuaXR5LmNvbS90cmFkZW9mZmVyL25ldy8_cGFydG5lcj04ODgzNzkwNDcmdG9rZW49Y0dvM1I4M1kifSwiaWF0IjoxNzMxMTEwODg3LCJleHAiOjE3NjI2Njg0ODd9.Iu8TUhg1SC5ax1W870kXqvpCuzzoUH5VWCLCtxETbx4"

        client = SkindeckClient(proxies, auth_token)

        while True:
            client.obtener_datos_skindeck(RENTABILIDAD_MINIMA)
            print(translator.gettext('waiting_message'), flush=True)
            time.sleep(10)
    except FileNotFoundError:
        print("Archivo de proxies 'proxy.txt' no encontrado. Asegúrate de que el archivo exista.", flush=True)