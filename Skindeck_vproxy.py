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

# Cargar el archivo de traducciones para 'skindeck'
translator = Translator('skindeck', language_code)

# Configuración de la API de Skindeck
API_URL = "https://api.skindeck.com/client/market"
SKINDECK_JSON = os.path.join(base_path, "JSON", "skindeck_data.json")

def guardar_datos(filename, data):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

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

    def obtener_datos_skindeck(self, page=1, per_page=10000, sort='price_desc'):
        try:
            params = {
                'page': page,
                'perPage': per_page,
                'sort': sort
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
                    'Price': item['offer']['price'] if item.get('offer') and 'price' in item['offer'] else None
                } for item in data['items'] if item.get('offer')]  # Solo incluir items que tengan offer
                
                # Filtrar items que no tienen precio None
                items = [item for item in items if item['Price'] is not None]
                
                print(translator.gettext('success_message', total_items=len(items)), flush=True)
                guardar_datos(SKINDECK_JSON, items)
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

        # Cargar proxies desde archivo
        with open(os.path.join(base_path, 'proxy.txt'), 'r') as file:
            proxies = [line.strip() for line in file.readlines()]
        
        # Tu token de autenticación de Skindeck
        auth_token = "eyJhbGciOiJIUzI1NiIsInVzZXJJZCI6IjY3MGY4YzMwNTBjYzQ5NmIzNTRlZjhjZSJ9.eyJjbGllbnQiOnsic3RlYW1JRCI6Ijc2NTYxMTk4ODQ4NjQ0Nzc1IiwidHJhZGVVcmwiOiJodHRwczovL3N0ZWFtY29tbXVuaXR5LmNvbS90cmFkZW9mZmVyL25ldy8_cGFydG5lcj04ODgzNzkwNDcmdG9rZW49Y0dvM1I4M1kifSwiaWF0IjoxNzMxMTEwODg3LCJleHAiOjE3NjI2Njg0ODd9.Iu8TUhg1SC5ax1W870kXqvpCuzzoUH5VWCLCtxETbx4"
        
        client = SkindeckClient(proxies, auth_token)

        while True:
            client.obtener_datos_skindeck()
            print(translator.gettext('waiting_message'), flush=True)
            time.sleep(10)
    except FileNotFoundError:
        print("Archivo de proxies 'proxy.txt' no encontrado. Asegúrate de que el archivo exista.", flush=True)