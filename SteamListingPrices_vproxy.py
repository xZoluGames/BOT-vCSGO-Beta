import json
import os
import time
import requests
import sys
import random

# URL base para obtener objetos de CS:GO del mercado de Steam
BASE_URL = "https://steamcommunity.com/market/search/render/?query=&start={}&count=100&search_descriptions=0&sort_column=popular&sort_dir=desc&appid=730&norender=1"

# Cargar proxies desde archivo
def load_proxies(filename):
    with open(filename, 'r') as file:
        return [line.strip() for line in file.readlines()]

# Obtener un proxy aleatorio
def get_random_proxy(proxies):
    return random.choice(proxies)

# Obtener datos de los objetos del mercado usando proxies
def get_market_items(start=0, retries=20, proxies=None):
    url = BASE_URL.format(start)
    attempt = 0

    while attempt < retries:
        print(f"Haciendo solicitud a: {url}", flush=True)

        proxy = get_random_proxy(proxies) if proxies else None
        proxy_dict = {"http": proxy, "https": proxy} if proxy else None

        try:
            response = requests.get(url, timeout=10, proxies=proxy_dict)
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
            print(f"Error en la solicitud: {e}", flush=True)

        attempt += 1
        print(f"Intento {attempt} fallido. Reintentando...\n", flush=True)

    print(f"Fallo tras {retries} intentos.", flush=True)
    return None, True

# Extraer los datos de los items, incluyendo el "sell_price"
def extract_items(json_data):
    items = []
    for item in json_data:
        try:
            name = item.get('name', 'Unknown')
            name = name.replace("/", "-")  # Reemplazar "/" por "-"

            sell_price_cents = item.get('sell_price', 0)  # Obtener el sell_price en centavos
            sell_price_dollars = sell_price_cents / 100.0  # Convertir a dólares

            items.append({
                "name": name,
                "price": sell_price_dollars  # Guardar el precio como float
            })
        except (AttributeError, ValueError) as e:
            print(f"Error al extraer datos de un ítem: {e}", flush=True)

    return items

# Función principal para obtener todos los objetos del mercado
def get_all_market_items(proxies=None):
    all_items = []
    start = 0
    stop_message_found = False
    no_data_attempts = 0

    while not stop_message_found:
        print(f"Obteniendo objetos a partir de la posición {start}...", flush=True)
        json_data, no_data = get_market_items(start, proxies=proxies)
        if json_data:
            items = extract_items(json_data)
            if items:
                all_items.extend(items)
                print(f"Página {start // 100 + 1}: {len(items)} items obtenidos", flush=True)
                no_data_attempts = 0  # Reiniciar el contador si se encuentran datos
            else:
                print(f"No se encontraron objetos en la posición {start}", flush=True)
                no_data_attempts += 1
        else:
            print(f"No se pudo obtener datos JSON para la posición {start}", flush=True)
            no_data_attempts += 1

        if no_data_attempts >= 5:
            print("No se encontraron datos después de varios intentos. Deteniendo el scraping.", flush=True)
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
    proxies = load_proxies('proxy3.txt')  # Cargar los proxies desde el archivo

    while True:
        items = get_all_market_items(proxies)
        save_to_json('steam_listing_prices.json', items)
        print("Reiniciando el scraping...", flush=True)
        time.sleep(120)

