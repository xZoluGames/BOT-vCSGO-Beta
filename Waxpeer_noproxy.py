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

# Cargar el archivo de traducciones para 'waxpeer'
translator = Translator('waxpeer', language_code)

API_URL = "https://api.waxpeer.com/v1/prices?game=csgo&minified=0&single=0"
WAXPEER_JSON = os.path.join(base_path, "JSON", "waxpeer_data.json")

class WaxpeerClient:
    def __init__(self):
        pass

    def guardar_datos(self, filename, data):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        print(translator.gettext('data_saved', filename=filename), flush=True)

    def formatear_precio(self, price):
        price_str = str(price)
        if len(price_str) <= 3:
            return "0." + price_str.zfill(3)
        else:
            return price_str[:-3] + '.' + price_str[-3:]

    def obtener_datos_waxpeer(self):
        try:
            response = requests.get(API_URL)
            response.raise_for_status()
            data = response.json()

            if data.get('success') and 'items' in data:
                items = [{'Item': item['name'], 'Price': self.formatear_precio(item['min'])} for item in data['items']]
                print(translator.gettext('data_fetched', count=len(items)), flush=True)
                self.guardar_datos(WAXPEER_JSON, items)
            else:
                print(translator.gettext('unexpected_format'), flush=True)
        except requests.RequestException as e:
            print(f"Request error: {e}", flush=True)
        except Exception as e:
            print(translator.gettext('error_fetching_data', error=str(e)), flush=True)

if __name__ == "__main__":
    client = WaxpeerClient()

    while True:
        client.obtener_datos_waxpeer()
        print(translator.gettext('waiting'), flush=True)
        time.sleep(5)
