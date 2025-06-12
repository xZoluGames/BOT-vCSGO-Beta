import concurrent.futures
import json
import os
import random
import sys
import time
from urllib.parse import unquote

import requests

# Obtener el path del directorio base donde está el ejecutable o script
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))
# Cargar proxies desde archivo
def load_proxies(filename):
    path = os.path.join(base_path, filename)
    with open(path, 'r') as file:
        return [line.strip() for line in file.readlines()]

# Obtener un proxy aleatorio
def get_random_proxy(proxies):
    return random.choice(proxies)

# Cargar el idioma desde el archivo de configuración
def cargar_idioma():
    config_file = os.path.join(base_path, 'Configs', 'Language.json')
    try:
        with open(config_file, 'r', encoding='utf-8') as file:
            config = json.load(file)
            return config.get("Language", "en")  # Por defecto, 'en' si no se encuentra la clave
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
        # Ruta específica para cargar archivos de traducción desde Languages
        translation_file = os.path.join(base_path, 'Languages', self.lang_code, f'{self.script_name}_{self.lang_code}.json')
        try:
            with open(translation_file, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Archivo de traducción para el script '{self.script_name}' y el idioma '{self.lang_code}' no encontrado.")
            return {}

    def gettext(self, key, **kwargs):
        template = self.translations.get(key, key)
        return template.format(**kwargs)

# Cargar el idioma desde la configuración
language_code = cargar_idioma()

# Cargar el archivo de traducciones para 'SteamMarket_vproxy'
translator = Translator('SteamMarket_vproxy', language_code)

API_URL = "https://steamcommunity.com/market/itemordershistogram?country=PK&language=english&currency=1&item_nameid={item_nameid}&two_factor=0&norender=1"
RUSTSKINS_JSON = os.path.join(base_path, 'JSON', 'steam_items.json')

def guardar_datos(filename, data):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

def obtener_datos():
    proxies = load_proxies('proxy2.txt')
    json_file_path = os.path.join(base_path, 'JSON', 'item_nameids.json')
    with open(json_file_path, 'r', encoding='utf-8') as f:
        items = json.load(f)

    results = []

    def get_highest_buy_order(item_nameid, proxies):
        url = f"https://steamcommunity.com/market/itemordershistogram?country=PK&language=english&currency=1&item_nameid={item_nameid}&two_factor=0&norender=1"
        proxy = get_random_proxy(proxies)
        proxy_dict = {"http": proxy, "https": proxy}

        try:
            response = requests.get(url, proxies=proxy_dict, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Verificar si 'highest_buy_order' está en la respuesta y no es None
            if 'highest_buy_order' in data and data['highest_buy_order'] is not None:
                highest_buy_order = int(data['highest_buy_order']) / 100  # Convertir a float con formato
                return highest_buy_order
            else:
                print(f"No se encontró un 'highest_buy_order' válido para item_nameid: {item_nameid}")
                return 0  # Retorna 0 si no se encuentra el dato o es None
        except (requests.RequestException, ValueError) as e:
            print(f"Error con proxy {proxy}: {e}. Reintentando con otro proxy...")
            return get_highest_buy_order(item_nameid, proxies)  # Reintentar con otro proxy

    # Procesar un solo artículo (decodificar nombre y obtener precio)
    def process_item(item, proxies):
        item_nameid = item['id']
        # Decodificar el nombre del item desde el formato URL a texto normal
        name = unquote(item['name'])
        highest_buy_order = get_highest_buy_order(item_nameid, proxies)
        print(translator.gettext('data_retrieved_success', total_items=1), flush=True)
        return {"name": name, "price": highest_buy_order}

    with concurrent.futures.ThreadPoolExecutor(max_workers=1000) as executor:
        futures = [executor.submit(process_item, item, proxies) for item in items]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                results.append(result)

    guardar_datos(RUSTSKINS_JSON, results)
    print(translator.gettext('waiting_message'), flush=True)

if __name__ == "__main__":
    while True:
        obtener_datos()
        time.sleep(43200)
