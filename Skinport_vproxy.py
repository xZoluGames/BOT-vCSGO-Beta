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

# Cargar el archivo de traducciones para 'skinports'
translator = Translator('skinports', language_code)

API_URL = "https://api.skinport.com/v1/items?app_id=730&currency=USD"
SKINPORT_JSON = os.path.join(base_path, "JSON", "skinport_data.json")

def guardar_datos(filename, data):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

def transformar_precio(price):
    price_str = str(price)
    return f"{price_str}"

# Cargar proxies desde un archivo
def cargar_proxies():
    proxies_file_path = os.path.join(base_path, 'proxy.txt')
    try:
        with open(proxies_file_path, 'r') as file:
            return [line.strip() for line in file.readlines()]
    except FileNotFoundError:
        print("Archivo de proxies 'proxy.txt' no encontrado.")
        return []

def obtener_datos_skinport(proxies, proxy_index):
    try:
        # Usar el proxy actual
        proxy = {"http": proxies[proxy_index], "https": proxies[proxy_index]}
        
        response = requests.get(API_URL, proxies=proxy)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list):
            # Filtrar ítems con quantity mayor que 0
            items = [{'Item': item['market_hash_name'], 'Price': transformar_precio(item['min_price'])} 
                     for item in data if item.get('quantity', 0) > 0]
            
            print(translator.gettext('data_obtained', count=len(items)), flush=True)
            guardar_datos(SKINPORT_JSON, items)
        else:
            print(translator.gettext('unexpected_format'), flush=True)
    except Exception as e:
        print(translator.gettext('error_obtaining_data', error=str(e)), flush=True)

if __name__ == "__main__":
    proxies = cargar_proxies()  # Cargar proxies al inicio
    proxy_index = 0  # Inicializar el índice del proxy

    while True:
        obtener_datos_skinport(proxies, proxy_index)  # Pasar la lista de proxies y el índice actual a la función
        print(translator.gettext('waiting'), flush=True)

        # Actualizar el índice del proxy para usar el siguiente
        proxy_index += 1
        if proxy_index >= len(proxies):  # Volver al inicio si se han usado todos los proxies
            proxy_index = 0
        
        time.sleep(1)
