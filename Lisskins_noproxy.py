import requests
import json
import time
import os
from datetime import datetime

def format_url_name(item_name):
    """
    Formatea el nombre del ítem para la URL según las reglas especificadas:
    - Mantiene el símbolo ★
    - Elimina ™ y otros caracteres especiales
    - Reemplaza espacios por guiones
    """
    # Lista de caracteres a eliminar (excepto ★)
    chars_to_remove = "™(),/|"
    
    # Eliminar caracteres especiales
    for char in chars_to_remove:
        item_name = item_name.replace(char, '')
    
    # Reemplazar espacios por guiones
    item_name = item_name.replace(' ', '-')
    
    # Eliminar guiones múltiples que puedan haberse creado
    while '--' in item_name:
        item_name = item_name.replace('--', '-')
    
    return item_name.strip('-')

def get_filtered_items():
    url = "https://lis-skins.com/market_export_json/api_csgo_full.json"
    
    try:
        # Realizar la petición GET
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Diccionario para almacenar el ítem más barato de cada nombre
        cheapest_items = {}
        
        # Procesar cada ítem
        for item in data.get('items', []):
            name = item.get('name')
            price = item.get('price')
            
            # Si el nombre ya existe, comparar precios
            if name in cheapest_items:
                if price < cheapest_items[name]['Price']:
                    formatted_url = format_url_name(name)
                    cheapest_items[name] = {
                        'Item': name,
                        'Price': price,
                        'URL': f"https://lis-skins.com/ru/market/csgo/{formatted_url}"
                    }
            else:
                formatted_url = format_url_name(name)
                cheapest_items[name] = {
                    'Item': name,
                    'Price': price,
                    'URL': f"https://lis-skins.com/ru/market/csgo/{formatted_url}"
                }
        
        # Convertir el diccionario a lista
        filtered_items = list(cheapest_items.values())
        
        return filtered_items
        
    except requests.exceptions.RequestException as e:
        print(f"Error al descargar datos: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error al decodificar JSON: {e}")
        return None

def save_json(data):
    # Crear directorio JSON si no existe
    json_dir = "JSON"
    if not os.path.exists(json_dir):
        os.makedirs(json_dir)
    
    # Ruta completa del archivo
    file_path = os.path.join(json_dir, "lisskins_data.json")
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"The data obtained has been successfully saved.", flush=True)
    except IOError as e:
        print(f"Error al guardar el archivo: {e}", flush=True)

def main():
    print("Working...", flush=True)
    while True:
        try:
            # Obtener y filtrar datos
            filtered_data = get_filtered_items()
            
            if filtered_data:
                # Guardar datos filtrados
                save_json(filtered_data)
            
            # Esperar 30 segundos
            time.sleep(30)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error inesperado: {e}")
            time.sleep(30)  # Continuar incluso si hay error

if __name__ == "__main__":
    main()