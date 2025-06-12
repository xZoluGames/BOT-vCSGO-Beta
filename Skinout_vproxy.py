import requests
import json
import os
import time
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

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


# Cargar el idioma desde la configuración
language_code = cargar_idioma()

# Cargar el archivo de traducciones para 'skinout'
translator = Translator('skinout', language_code)

# URL base de la API de Skinout
BASE_API_URL = "https://skinout.gg/api/market/items"
# Ruta relativa al directorio donde se ejecuta el script
SKINOUT_JSON = os.path.join(base_path, "JSON", "skinout_data.json")


def guardar_datos(filename, data):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


class SkinoutClient:
    def __init__(self, proxies):
        self.proxies = proxies
        self.current_proxy_index = 0
        self.retry_delay = 5  # Segundos entre reintentos
        self.max_workers = 10  # Número de solicitudes simultáneas
        self.empty_pages_threshold = 3  # Número de páginas vacías consecutivas para considerar el final

    def get_next_proxy(self):
        proxy = self.proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        return proxy

    def obtener_datos_pagina(self, page):
        while True:  # Bucle infinito para reintentos
            try:
                url = f"{BASE_API_URL}?page={page}"
                proxy = self.get_next_proxy()

                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'application/json',
                    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
                    'Origin': 'https://skinout.gg',
                    'Referer': 'https://skinout.gg/'
                }

                response = requests.get(
                    url,
                    proxies={"http": proxy, "https": proxy},
                    headers=headers,
                    timeout=10
                )
                response.raise_for_status()

                json_data = response.json()

                if json_data.get('success') and 'items' in json_data:
                    items = json_data['items']
                    # Solo retornar los items formateados y la página actual
                    formatted_items = [
                        {
                            'Item': item['market_hash_name'],
                            'Price': item['price']
                        }
                        for item in items
                    ]
                    return page, formatted_items

                # Si la respuesta es exitosa pero no hay items
                if json_data.get('success'):
                    return page, []

            except Exception as e:
                print(f"Error en página {page}: {str(e)}. Reintentando en {self.retry_delay} segundos...", flush=True)
                time.sleep(self.retry_delay)
                continue

    def process_batch(self, start_page, batch_size):
        futures = []
        results = []
        empty_pages = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Crear futures para cada página en el lote
            for page in range(start_page, start_page + batch_size):
                futures.append(executor.submit(self.obtener_datos_pagina, page))

            # Procesar los resultados a medida que se completan
            for future in as_completed(futures):
                page, items = future.result()
                if not items:
                    empty_pages += 1
                    if empty_pages >= self.empty_pages_threshold:
                        return results, True  # True indica que debemos detener el scraping
                else:
                    empty_pages = 0  # Reiniciar el contador si encontramos items
                    results.extend(items)
                    print(f"Página {page} completada - {len(items)} items obtenidos", flush=True)

        return results, False  # False indica que podemos continuar

    def obtener_datos_skinout(self):
        try:
            all_items = []
            current_page = 0
            batch_size = self.max_workers * 2  # Procesar el doble de páginas que workers en cada lote

            while True:
                print(f"Procesando lote de páginas {current_page} a {current_page + batch_size - 1}", flush=True)
                batch_items, should_stop = self.process_batch(current_page, batch_size)

                all_items.extend(batch_items)

                if should_stop:
                    print("Se detectaron múltiples páginas vacías consecutivas. Finalizando la búsqueda.", flush=True)
                    break

                current_page += batch_size
                time.sleep(1)  # Pequeña pausa entre lotes

            if all_items:
                print(f"Total de items obtenidos: {len(all_items)}", flush=True)
                guardar_datos(SKINOUT_JSON, all_items)
            else:
                print(translator.gettext('no_items_found'), flush=True)

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

        client = SkinoutClient(proxies)

        while True:
            client.obtener_datos_skinout()
            print(translator.gettext('waiting_message'), flush=True)
            time.sleep(10)
    except FileNotFoundError:
        print("Archivo de proxies 'proxy.txt' no encontrado. Asegúrate de que el archivo exista.", flush=True)