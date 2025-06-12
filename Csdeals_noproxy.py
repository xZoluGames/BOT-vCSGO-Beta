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

# Cargar el archivo de traducciones para 'csdeals'
translator = Translator('csdeals', language_code)

# URL de la API de CsDeals
API_URL = "https://cs.deals/API/IPricing/GetLowestPrices/v1?appid=730"
# Ruta relativa al directorio donde se ejecuta el script
CSDEALS_JSON = os.path.join(base_path, "JSON", "csdeals_data.json")

def guardar_datos(filename, data):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

# Clase para manejar la solicitud de datos sin proxies
class CsDealsClient:
    def obtener_datos_csdeals(self):
        try:
            # Añadir un User-Agent para reducir el riesgo de bloqueo
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(API_URL, headers=headers)
            response.raise_for_status()
            data = response.json()

            if data.get('success') and data.get('response') and 'items' in data['response']:
                items = [{'Item': item['marketname'], 'Price': item['lowest_price']} for item in data['response']['items']]
                print(translator.gettext('success_message', total_items=len(items)), flush=True)
                guardar_datos(CSDEALS_JSON, items)  # Guardar datos de CsDeals
            else:
                print(translator.gettext('unexpected_format'), flush=True)
        except requests.exceptions.RequestException as e:
            print(translator.gettext('fetch_error', error=e), flush=True)
        except Exception as e:
            print(f"Error inesperado: {e}", flush=True)

if __name__ == "__main__":
    client = CsDealsClient()

    while True:
        try:
            client.obtener_datos_csdeals()
            print(translator.gettext('waiting_message'), flush=True)
            
            # Aumentar el tiempo de espera para reducir el riesgo de bloqueo
            time.sleep(10)
        except KeyboardInterrupt:
            print("Proceso detenido por el usuario.")
            break
        except Exception as e:
            print(f"Error en el bucle principal: {e}", flush=True)
            time.sleep(60)