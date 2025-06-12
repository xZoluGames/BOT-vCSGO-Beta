import requests
import json
import os
import time
import sys

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

# Cargar el archivo de traducciones para 'rapidskins'
translator = Translator('rapidskins', language_code)

RAPIDSKINS_API_URL = "https://api.rapidskins.com/graphql"
RAPIDSKINS_JSON = os.path.join(base_path, "JSON", "rapidskins_data.json")

# Función para cargar proxies desde un archivo
def cargar_proxies():
    proxies_file_path = os.path.join(base_path, 'proxy.txt')
    try:
        with open(proxies_file_path, 'r') as file:
            return [line.strip() for line in file.readlines()]
    except FileNotFoundError:
        print("Archivo de proxies 'proxy.txt' no encontrado.")
        return []

# Función para guardar los datos en un archivo JSON
def guardar_datos(filename, data):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

# Función para obtener datos de Rapidskins
def obtener_datos_rapidskins(proxies, proxy_index):
    try:
        all_items = []
        page = 1

        while True:
            query = """
            query Inventories($filter: InventoryFilters!) { 
                siteInventory(filter: $filter) {
                    csgo {
                        ... on SteamInventory {
                            items {
                                marketHashName
                                price {
                                    coinAmount
                                }
                            }
                        }
                    }
                }
            }
            """
            headers = {
                "Content-Type": "application/json"
            }
            variables = {
                "filter": {
                    "page": page,
                    "sort": "PRICE_DESC",
                    "appIds": [730],
                    "search": None,
                    "cs2ItemCategories": [],
                    "rustItemCategories": [],
                    "itemExteriors": [],
                    "statTrakOnly": False,
                    "tradableOnly": False,
                    "souvenirOnly": False,
                    "minimumPrice": {"coinAmount": 0},
                    "maximumPrice": {"coinAmount": 2000000}
                }
            }

            # Usar el proxy actual
            proxy = {"http": proxies[proxy_index], "https": proxies[proxy_index]}
            
            response = requests.post(RAPIDSKINS_API_URL, json={'query': query, 'variables': variables}, headers=headers, proxies=proxy)
            response.raise_for_status()
            data = response.json()

            items = data['data']['siteInventory']['csgo']['items']
            if not items:
                break  # Si no hay más ítems, salir del bucle

            all_items.extend(items)
            page += 1
            
            time.sleep(1)  # Esperar 1 segundo antes de la siguiente solicitud

        print(translator.gettext('success_message', total_items=len(all_items)), flush=True)
        guardar_datos(RAPIDSKINS_JSON, all_items)
    except Exception as e:
        print(translator.gettext('fetch_error', error=e), flush=True)

if __name__ == "__main__":
    proxies = cargar_proxies()  # Cargar proxies al inicio
    proxy_index = 0  # Inicializar el índice del proxy

    while True:
        print(translator.gettext('updating_message'), flush=True)
        obtener_datos_rapidskins(proxies, proxy_index)  # Pasar la lista de proxies y el índice actual a la función
        print(translator.gettext('waiting_message'), flush=True)
        
        # Actualizar el índice del proxy para usar el siguiente
        proxy_index += 1
        if proxy_index >= len(proxies):  # Volver al inicio si se han usado todos los proxies
            proxy_index = 0
        
        time.sleep(1)
