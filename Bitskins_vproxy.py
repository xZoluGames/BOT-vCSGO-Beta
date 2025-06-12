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

# Cargar el archivo de traducciones para 'bitskins'
translator = Translator('bitskins', language_code)

# URL de la API de Bitskins
API_URL = "https://api.bitskins.com/market/insell/730"
# Ruta relativa al directorio donde se ejecuta el script
BITSKINS_JSON = os.path.join(base_path, "JSON", "bitskins_data.json")

def guardar_datos(filename, data):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

def convertir_precio(price_min):
    """Convierte el precio de centavos a dólares y lo retorna como string"""
    return f"{price_min/1000:.2f}"

# Clase para manejar la solicitud de datos con soporte para proxies
class BitskinsClient:
    def __init__(self, proxies):
        self.proxies = proxies
        self.current_proxy_index = 0

    def get_next_proxy(self):
        proxy = self.proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        return proxy

    def obtener_datos_bitskins(self):
        try:
            response = requests.get(API_URL, proxies={"http": self.get_next_proxy(), "https": self.get_next_proxy()})
            response.raise_for_status()
            data = response.json()

            if 'list' in data:
                # Extraer name y convertir price_min a formato de dólares
                items = [
                    {
                        'Item': item['name'], 
                        'Price': convertir_precio(item['price_min'])
                    } 
                    for item in data['list']
                ]
                print(translator.gettext('success_message', total_items=len(items)), flush=True)
                guardar_datos(BITSKINS_JSON, items)
            else:
                print(translator.gettext('unexpected_format'), flush=True)
        except Exception as e:
            print(translator.gettext('fetch_error', error=e), flush=True)

if __name__ == "__main__":
    try:
        # Determinar la ruta base
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        with open(os.path.join(base_path, 'proxy.txt'), 'r') as file:
            proxies = [line.strip() for line in file.readlines()]
        
        client = BitskinsClient(proxies)

        while True:
            client.obtener_datos_bitskins()
            print(translator.gettext('waiting_message'), flush=True)
            time.sleep(5)
    except FileNotFoundError:
        print("Archivo de proxies 'proxy.txt' no encontrado. Asegúrate de que el archivo exista.", flush=True)