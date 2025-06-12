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
        # Ruta específica para cargar archivos de traducción desde Languages
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


# Cargar el idioma desde la configuración
language_code = cargar_idioma()

# Cargar el archivo de traducciones para 'cstrade'
translator = Translator('cstrade', language_code)

# URL de la API de CsTrade
API_URL = "https://cdn.cs.trade:2096/api/prices_CSGO"
# Ruta relativa al directorio donde se ejecuta el script
CSTRADE_JSON = os.path.join(base_path, "JSON", "cstrade_data.json")


def guardar_datos(filename, data):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def calcular_precio_real(precio_pagina, tasa_bono):
    tasa_decimal = tasa_bono / 100
    return precio_pagina / (1 + tasa_decimal)


# Clase para manejar la solicitud de datos con soporte para proxies
class CsTradeClient:
    def __init__(self, proxies):
        self.proxies = proxies
        self.current_proxy_index = 0

    def get_next_proxy(self):
        proxy = self.proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        return proxy

    def obtener_datos_cstrade(self):
        try:
            response = requests.get(API_URL, proxies={"http": self.get_next_proxy(), "https": self.get_next_proxy()})
            response.raise_for_status()
            data = response.json()

            items = []
            for item_name, item_data in data.items():
                tradable = item_data.get('tradable', 0)
                reservable = item_data.get('reservable', 0)

                # Verificar que tradable o reservable no sean ambos 0
                if tradable != 0 or reservable != 0:
                    original_price = item_data['price']
                    precio_real = calcular_precio_real(original_price, 50)  # Calcular el valor real antes del bono
                    items.append({
                        'Item': item_name,
                        'Price': f"{precio_real:.2f}",  # Convertir el precio a string con 2 decimales
                    })

            if items:
                print(translator.gettext('success_message', total_items=len(items)), flush=True)
                guardar_datos(CSTRADE_JSON, items)
            else:
                print(translator.gettext('no_items'), flush=True)

        except Exception as e:
            print(translator.gettext('fetch_error', error=e), flush=True)


if __name__ == "__main__":
    # Cargar proxies desde un archivo
    try:
        # Determinar la ruta base
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        with open(os.path.join(base_path, 'proxy.txt'), 'r') as file:  # Cargar proxies desde proxy.txt
            proxies = [line.strip() for line in file.readlines()]
        
        client = CsTradeClient(proxies)

        while True:
            client.obtener_datos_cstrade()
            print(translator.gettext('waiting_message'), flush=True)
            time.sleep(5)
    except FileNotFoundError:
        print("Archivo de proxies 'proxy.txt' no encontrado. Asegúrate de que el archivo exista.", flush=True)
