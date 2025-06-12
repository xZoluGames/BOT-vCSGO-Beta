import os
import requests
import json
import time

# URL de la API
url = "https://market.csgo.com/api/v2/prices/USD.json"


# Función para recolectar datos y guardarlos en un archivo JSON
def recolectar_datos():
    # Solicitar los datos desde la API
    response = requests.get(url)
    data = response.json()

    # Verificar que la respuesta sea exitosa
    if data["success"]:
        # Procesar los datos para obtener solo los campos deseados
        items = data["items"]
        filtered_data = []

        for item in items:
            # Obtener el nombre del artículo y convertir el precio en entero
            nombre = item["market_hash_name"]
            precio = float(item["price"])  # Convertimos el precio a entero
            filtered_data.append({"Item": nombre, "Price": precio})

        # Definir la ruta donde se guardará el archivo
        base_path = os.path.dirname(os.path.abspath(__file__))
        json_dir = os.path.join(base_path, "JSON")
        os.makedirs(json_dir, exist_ok=True)

        # Archivo destino
        output_file = os.path.join(json_dir, "market.csgo_data.json")

        # Guardar los datos procesados en el archivo JSON
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(filtered_data, f, ensure_ascii=False, indent=4)

        print(f"Data saved in {output_file}", flush=True)
    else:
        print("Error al obtener los datos de la API.", flush=True)


# Bucle infinito para recolectar datos cada 60 segundos
while True:
    recolectar_datos()
    # Esperar 60 segundos antes de la siguiente ejecución
    time.sleep(5)
