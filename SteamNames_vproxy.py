import json
import os
import random
import time
import requests
import sys

# URL base para obtener objetos de CS:GO del mercado de Steam
BASE_URL = "https://steamcommunity.com/market/search/render/?query=&start={}&count=100&search_descriptions=0&sort_column=popular&sort_dir=desc&appid=730&norender=1"

# Cargar proxies desde el archivo
def load_proxies(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()
    proxies = [line.strip() for line in lines]
    return proxies

# Obtener un proxy aleatorio de la lista
def get_random_proxy(proxies):
    return random.choice(proxies)

def get_market_items(start=0, proxies=None, retries=5):
    url = BASE_URL.format(start)
    attempt = 0

    while attempt < retries:
        proxy = get_random_proxy(proxies) if proxies else None
        proxy_dict = {"http": proxy, "https": proxy} if proxy else None
        print(f"Haciendo solicitud a: {url} usando proxy: {proxy}", flush=True)

        try:
            response = requests.get(url, proxies=proxy_dict, timeout=10)
            print(f"Estado de la respuesta: {response.status_code}", flush=True)

            if response.status_code == 200:
                try:
                    # Procesar como JSON
                    data = response.json()
                    if "results" in data:
                        return data["results"], False  # Devolver los resultados en JSON
                    else:
                        print("No se encontraron resultados en la respuesta JSON.", flush=True)
                except json.JSONDecodeError as e:
                    print(f"Error al decodificar JSON: {e}", flush=True)
            elif response.status_code == 429:
                print("Demasiadas solicitudes. Esperando 60 segundos para reintentar...", flush=True)
                time.sleep(60)  # Esperar 60 segundos antes de reintentar
            else:
                print(f"Error en la solicitud: {response.status_code}", flush=True)

        except requests.RequestException as e:
            print(f"Error en la solicitud con proxy {proxy}: {e}", flush=True)
            print("Cambiando a un nuevo proxy e intentando nuevamente...", flush=True)

        attempt += 1
        print(f"Intento {attempt} fallido. Probando con otro proxy...\n", flush=True)

    print(f"Fallo tras {retries} intentos.", flush=True)
    return None, True

def extract_items(json_data):
    items = []
    for item in json_data:
        try:
            name = item.get('name', 'Unknown')
            name = name.replace("/", "-")  # Reemplazar "/" por "-"
            items.append({"name": name})
        except (AttributeError, ValueError) as e:
            print(f"Error al extraer datos de un ítem: {e}", flush=True)

    return items

# Función principal para obtener todos los objetos del mercado
def get_all_market_items(proxies):
    all_items = []
    start = 0
    stop_message_found = False
    no_data_attempts = 0

    while not stop_message_found:
        print(f"Obteniendo objetos a partir de la posición {start}...", flush=True)
        json_data, no_data = get_market_items(start, proxies)
        if json_data:
            items = extract_items(json_data)
            if items:
                all_items.extend(items)
                print(f"Página {start//100 + 1}: {len(items)} items obtenidos", flush=True)
                no_data_attempts = 0  # Reiniciar el contador si se encuentran datos
            else:
                print(f"No se encontraron objetos en la posición {start}", flush=True)
                no_data_attempts += 1
        else:
            print(f"No se pudo obtener datos JSON para la posición {start}", flush=True)
            no_data_attempts += 1

        if no_data_attempts >= 5:
            print("No se encontraron datos después de intentar con 5 proxies diferentes. Deteniendo el scraping.", flush=True)
            stop_message_found = True

        start += 100

    return all_items

# Guardar los objetos en un archivo JSON
def save_to_json(filename, data):
    # Asegúrate de que la subcarpeta "JSON" exista
    os.makedirs("JSON", exist_ok=True)

    # Define la ruta completa del archivo
    filepath = os.path.join("JSON", filename)

    if data:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"Datos guardados en {filepath}", flush=True)
    else:
        print("No hay datos para guardar", flush=True)

if __name__ == '__main__':
    # Determinar la ruta del archivo de proxies
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    proxies = load_proxies(os.path.join(base_path, 'proxy4.txt'))
    
    while True:
        items = get_all_market_items(proxies)
        save_to_json('item_names.json', items)
        print("Reiniciando el scraping...", flush=True)
        time.sleep(43200)
