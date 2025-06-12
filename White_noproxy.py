import requests
import json
import os
import time


def obtener_datos_white_market():
    url = "https://api.white.market/export/v1/prices/730.json"
    
    try:
        respuesta = requests.get(url)
        respuesta.raise_for_status()
        
        datos_originales = respuesta.json()
        
        datos_procesados = []
        for item in datos_originales:
            datos_procesados.append({
                "Item": item["market_hash_name"],
                "Price": item["price"],
                "URL": item["market_product_link"]
            })
        
        os.makedirs("JSON", exist_ok=True)

        ruta_archivo = os.path.join("JSON", "white_data.json")
        
        with open(ruta_archivo, 'w', encoding='utf-8') as archivo:
            json.dump(datos_procesados, archivo, ensure_ascii=False, indent=2)
        
        print(f"Datos guardados en {ruta_archivo}, esperando 5 segundos para el reinicio...", flush=True)
        return datos_procesados
    
    except requests.RequestException as e:
        print(f"Error al obtener datos: {e}")
        return None
    except (KeyError, json.JSONDecodeError) as e:
        print(f"Error al procesar datos: {e}")
        return None

def ejecutar_bucle():
    while True:
        obtener_datos_white_market()
        time.sleep(5)

if __name__ == "__main__":
    ejecutar_bucle()