import undetected_chromedriver as uc
import json
import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys

MANNCOSTORE_URL = "https://mannco.store/item/"
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
            print(
                f"Archivo de traducción para el script '{self.script_name}' y el idioma '{self.lang_code}' no encontrado.")
            return {}

    def gettext(self, key, **kwargs):
        template = self.translations.get(key, key)
        return template.format(**kwargs)


# Cargar el idioma desde la configuración
language_code = cargar_idioma()

# Cargar el archivo de traducciones para 'manncostore'
translator = Translator('manncostore', language_code)

URL = "https://mannco.store/items/get?price=DESC&page=1&i=0&game=730&skip={}"
MANNCOSTORE_JSON = os.path.join(base_path, "JSON", "manncostore_data.json")


class ManncoClient:
    def __init__(self):
        pass

    # Configuración de undetected_chromedriver
    def iniciar_navegador(self):
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # Especifica la ruta del chromedriver
        driver_path = os.path.join(base_path, 'Chromedriver', 'chromedriver.exe')
        driver = uc.Chrome(options=options, executable_path=driver_path)
        return driver

    # Función para guardar los datos en un archivo JSON
    def guardar_datos(self, filename, data):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

    # Función para transformar el precio en formato "XX.XX"
    def transformar_precio(self, price):
        price_str = str(price)
        if len(price_str) > 2:
            return f"{price_str[:-2]}.{price_str[-2:]}"
        else:
            return f"0.{price_str.zfill(2)}"

    # Función para obtener datos de MannCoStore
    def obtener_datos_manncostore(self, driver, skip):
        try:
            driver.get(URL.format(skip))

            # Esperar hasta que la etiqueta <pre> esté presente (donde está el JSON)
            pre_element = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "pre")))

            # Obtener el contenido de la etiqueta <pre> (donde está el JSON)
            json_data = pre_element.text

            # Asegurarse de que los datos sean JSON válidos
            data = json.loads(json_data)

            if isinstance(data, list) and len(data) > 0:
                items = [
                    {
                        'Item': item['name'],
                        'Price': self.transformar_precio(item['price']),
                        'URL': MANNCOSTORE_URL + (item['url'] if item.get('url') else "")
                    }
                    for item in data
                ]
                print(translator.gettext('success_message', skip=skip, total_items=len(items)), flush=True)
                return items
            else:
                print(translator.gettext('no_items', skip=skip), flush=True)
                return None
        except json.JSONDecodeError:
            print(translator.gettext('json_decode_error', skip=skip), flush=True)
            return None
        except Exception as e:
            print(translator.gettext('fetch_error', skip=skip, error=e), flush=True)
            return None


if __name__ == "__main__":
    client = ManncoClient()
    driver = client.iniciar_navegador()

    while True:
        skip = 0
        todos_los_items = []  # Lista para acumular todos los ítems obtenidos

        while True:
            items = client.obtener_datos_manncostore(driver, skip)

            if items:
                todos_los_items.extend(items)
                skip += 50
            else:
                print(translator.gettext('total_items', total_items=len(todos_los_items)), flush=True)
                client.guardar_datos(MANNCOSTORE_JSON, todos_los_items)
                break

            print(translator.gettext('continue_skip', skip=skip), flush=True)

        print(translator.gettext('waiting_message'), flush=True)
        time.sleep(5)
