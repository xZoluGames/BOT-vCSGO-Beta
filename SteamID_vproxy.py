import concurrent.futures
import json
import os
import random
import re
import sys
import time
import requests

# Verificar base_path
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

# Cargar proxies desde archivo
def load_proxies(filename):
    path = os.path.join(base_path, filename)
    with open(path, 'r') as file:
        return [line.strip() for line in file.readlines()]

# Obtener un proxy aleatorio
def get_random_proxy(proxies):
    return random.choice(proxies)

# Función para obtener el item_nameid usando expresiones regulares
def get_item_nameid(name, proxies):
    proxy = get_random_proxy(proxies)
    url = f"https://steamcommunity.com/market/listings/730/{name}"
    proxy_dict = {"http": proxy, "https": proxy}
    try:
        response = requests.get(url, proxies=proxy_dict, timeout=10)
        response.raise_for_status()
        matches_ids = re.findall(r"Market_LoadOrderSpread\(\s*(\d+)\s*\)", response.text)
        if matches_ids:
            item_nameid = re.sub(r"\D", "", matches_ids[0])
            print(f"item_nameid obtenido para '{name}': {item_nameid}")
            return {"name": name, "id": item_nameid}
        else:
            print(f"No se encontró el item_nameid para '{name}'.")
            return {"name": name, "id": None}
    except (requests.RequestException, ValueError) as e:
        print(f"Error con proxy {proxy}: {e}.")
        return {"name": name, "id": None}

# Función para manejar múltiples solicitudes en paralelo
def process_item(item, proxies):
    name = item['name']
    attempts = 0
    max_attempts = 10
    
    while attempts < max_attempts:
        result = get_item_nameid(name, proxies)
        if result and result["id"]:
            return result
            
        attempts += 1
        print(f"Intento {attempts}/{max_attempts} fallido para '{name}'. Reintentando...")
        time.sleep(1)  # Pequeña pausa entre intentos
    
    print(f"Se alcanzó el límite de {max_attempts} intentos para '{name}'. Saltando este ítem.")
    return {"name": name, "id": None}

# Función para cargar los archivos JSON
def load_json_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Función para guardar los resultados en JSON
def save_json_file(data, filepath):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Función para comparar y actualizar los items
def compare_and_update_items(item_names, existing_nameids, proxies):
    # Convertir las listas a diccionarios para facilitar la búsqueda
    names_dict = {item['name']: item for item in item_names}
    nameids_dict = {item['name']: item for item in existing_nameids}

    # Lista para almacenar los items que necesitan actualización
    items_to_update = []
    
    # Encontrar items nuevos o que necesitan actualización
    for name, item in names_dict.items():
        if name not in nameids_dict:
            items_to_update.append(item)
            print(f"Nuevo item encontrado: {name}")

    # Eliminar items que ya no existen en item_names
    updated_nameids = [item for item in existing_nameids if item['name'] in names_dict]
    
    # Si hay items para actualizar, procesarlos
    if items_to_update:
        print(f"Procesando {len(items_to_update)} items nuevos...", flush=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(process_item, item, proxies) for item in items_to_update]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    # Solo agregamos items con ID válido a la lista final
                    if result['id'] is not None:
                        updated_nameids.append(result)
                        print(f"Item procesado exitosamente: {result['name']}", flush=True)
                    else:
                        print(f"No se pudo obtener ID para: {result['name']}", flush=True)

    return updated_nameids

def main():
    # Cargar proxies
    proxies = load_proxies('proxy3.txt')
    
    # Definir rutas de archivos
    names_file_path = os.path.join(base_path, 'JSON', 'item_names.json')
    nameids_file_path = os.path.join(base_path, 'JSON', 'item_nameids.json')
    
    # Cargar archivos
    item_names = load_json_file(names_file_path)
    existing_nameids = load_json_file(nameids_file_path)
    
    print("Comparando archivos para detectar cambios...", flush=True)
    
    # Comparar y actualizar items
    updated_nameids = compare_and_update_items(item_names, existing_nameids, proxies)
    
    # Guardar resultados actualizados
    save_json_file(updated_nameids, nameids_file_path)
    print("Archivo de nameids actualizado correctamente", flush=True)

if __name__ == "__main__":
    while True:
        main()
        print(f"Esperando próxima actualización... ({time.strftime('%H:%M:%S')})", flush=True)
        time.sleep(43200)