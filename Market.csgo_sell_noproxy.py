import os
import requests
import json
import time

# URL de la API (sin necesidad de API key)
url = "https://market.csgo.com/api/v2/prices/orders/USD.json"

# Función para recolectar datos de la API
def recolectar_datos():
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.RequestException as e:
        print(f"Error en la solicitud a la API: {e}", flush=True)
        return None

# Comparar precios de las órdenes de compra con precios de otros artículos
def comparar_precio_buy_order(item_name, precio_buy_order, steam_items):
    for steam_item in steam_items:
        if steam_item['name'] == item_name:
            precio_steam = float(steam_item['price'])  # Asegurarse de que sea un número

            if precio_steam > 0:  # Verificar que el precio de Steam no sea cero
                # Comparar precios
                if precio_buy_order > precio_steam:
                    rentabilidad = precio_buy_order - precio_steam
                    rentabilidad_porcentaje = (rentabilidad / precio_steam) * 100
                    return {
                        'item': item_name,
                        'precio_steam': precio_steam,
                        'precio_buy_order': precio_buy_order,
                        'rentabilidad': rentabilidad,
                        'rentabilidad_porcentaje': rentabilidad_porcentaje
                    }
            else:
                print(f"El precio de Steam para {item_name} es 0, no se puede calcular la rentabilidad.", flush=True)
    return None

# Cargar los datos de Steam (simulando una función para cargar datos locales o de otra API)
def cargar_steam_data():
    steam_items_json = os.path.join(get_base_path(), "JSON", "steam_listing_prices.json")
    try:
        with open(steam_items_json, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Archivo {steam_items_json} no encontrado.", flush=True)
        return []

# Obtener el path del directorio base donde está el ejecutable o script
def get_base_path():
    return os.path.dirname(os.path.abspath(__file__))

# Guardar los resultados en un archivo JSON
def guardar_resultados(resultados, filename='profiteable_sells_market.csgo.json'):
    result_path = os.path.join(get_base_path(), "JSON", filename)
    os.makedirs(os.path.dirname(result_path), exist_ok=True)
    with open(result_path, 'w', encoding='utf-8') as file:
        json.dump(resultados, file, indent=4, ensure_ascii=False)
    print(f"Resultados guardados en {result_path}")

def main():
    data = recolectar_datos()
    if not data or not data.get('success'):
        print("Error al obtener los datos de la API.", flush=True)
        return

    # Filtrar los datos necesarios
    items = data.get('items', [])
    steam_items = cargar_steam_data()  # Cargar los datos de Steam

    resultados_profitable = []  # Lista para almacenar los resultados rentables

    # Iterar sobre los items de la API de órdenes de compra
    for item in items:
        item_name = item['market_hash_name']
        precio_buy_order = float(item['price'])  # Mantener el precio en formato float

        # Comparar con los precios de Steam
        resultado = comparar_precio_buy_order(item_name, precio_buy_order, steam_items)

        if resultado and resultado['rentabilidad_porcentaje'] >= 0:
            resultados_profitable.append(resultado)

    # Ordenar los resultados por rentabilidad (de mayor a menor)
    resultados_profitable = sorted(resultados_profitable, key=lambda x: x['rentabilidad_porcentaje'], reverse=True)

    if resultados_profitable:
        guardar_resultados(resultados_profitable)
    else:
        print("No se encontraron oportunidades rentables.", flush=True)

# Ejecutar la función principal
if __name__ == "__main__":
    main()


