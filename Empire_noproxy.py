import json
import os
import requests
import time

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Cargar la API key desde el archivo "Api.json" en la subcarpeta "Configs"
def load_api_key():
    config_path = os.path.join("Configs", "Api.json")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get("api_key_empire")
    except Exception as e:
        print(f"Error al cargar la API key: {e}", flush=True)
        return None

# Convertir monedas a dólares usando la tasa promedio calculada
def convert_to_usd(coins):
    # Tasa promedio calculada previamente: 0.6154 dólares por moneda
    conversion_rate = 0.6154
    return coins * conversion_rate

# Clase para manejar la solicitud de ítems sin proxies
class CSGOEmpireClient:
    # Función para obtener los objetos según el tipo de subasta y guardarlos en un diccionario
    def fetch_items_by_auction_type(self, auction_type, headers, retries=5):
        domain = "csgoempire.com"
        items_url = f"https://{domain}/api/v2/trading/items"
        all_items = {}
        page = 1

        while True:
            print(f"Fetching items with auction={auction_type} from page {page}...", flush=True)
            params = {
                "per_page": 2500,
                "page": page,
                "order": "market_value",
                "sort": "asc",
                "auction": auction_type
            }

            for attempt in range(retries):
                try:
                    # Añadir User-Agent y otros headers para reducir riesgo de bloqueo
                    request_headers = headers.copy()
                    request_headers.update({
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Accept': 'application/json',
                        'Accept-Language': 'en-US,en;q=0.9'
                    })

                    response = requests.get(items_url, headers=request_headers, params=params)
                    response.raise_for_status()  # Verificar si la solicitud fue exitosa
                    data = response.json()

                    # Procesar y comparar los ítems
                    items = data.get('data', [])
                    if not items:
                        print(f"No more items found with auction={auction_type}. Stopping at page {page}.", flush=True)
                        return all_items

                    for item in items:
                        name = item.get("market_name", "Unknown")
                        price_in_coins = item.get("market_value", 0) / 100.0  # Convertir centavos a monedas
                        price_in_usd = convert_to_usd(price_in_coins)  # Convertir a dólares
                        item_id = item.get("id", None)  # Obtener el ID del ítem

                        # Guardar el ítem si es nuevo o tiene un precio menor
                        if name not in all_items or price_in_usd < all_items[name]['Price']:
                            all_items[name] = {
                                "Price": price_in_usd,
                                "Coin": price_in_coins,  # Guardar el precio en monedas
                                "id": item_id
                            }

                    print(f"Page {page}: {len(items)} items fetched with auction={auction_type}.", flush=True)
                    page += 1
                    time.sleep(3)  # Aumentar tiempo de espera para reducir riesgo de bloqueo
                    break

                except Exception as e:
                    print(f"Error on attempt {attempt + 1}/{retries}: {e}", flush=True)
                    time.sleep(5)  # Aumentar tiempo de espera entre reintentos

                    if attempt + 1 == retries:
                        print(f"Failed after {retries} attempts with auction={auction_type}. Stopping.", flush=True)
                        return all_items

# Guardar los ítems en un archivo JSON en la subcarpeta "JSON" con la estructura solicitada
def save_items(items):
    # Crear la subcarpeta "JSON" si no existe
    os.makedirs("JSON", exist_ok=True)

    # Formatear los ítems en la estructura solicitada
    formatted_items = [{"Item": name, "Price": f"{info['Price']:.3f}", "Coin": f"{info['Coin']:.3f}", "id": info['id']} for name, info in items.items()]

    # Guardar los ítems en un archivo JSON
    json_filepath = os.path.join("JSON", "empire_data.json")
    with open(json_filepath, 'w', encoding='utf-8') as f:
        json.dump(formatted_items, f, ensure_ascii=False, indent=4)

    print(f"Items saved to {json_filepath}! Total items fetched: {len(formatted_items)}", flush=True)

# Función principal para ejecutar el proceso en bucle
def get_items_loop():
    client = CSGOEmpireClient()

    while True:
        try:
            api_key = load_api_key()
            if not api_key:
                print("API key no encontrada. Abortando.", flush=True)
                return

            headers = {
                "Authorization": f"Bearer {api_key}"
            }

            # Obtener ítems con "auction": "yes"
            items_yes = client.fetch_items_by_auction_type("yes", headers)

            # Obtener ítems con "auction": "no"
            items_no = client.fetch_items_by_auction_type("no", headers)

            # Combinar y comparar los precios de ambos resultados
            combined_items = items_yes.copy()
            for name, info in items_no.items():
                if name not in combined_items or info['Price'] < combined_items[name]['Price']:
                    combined_items[name] = info

            # Guardar los ítems con los precios más bajos en un archivo JSON
            save_items(combined_items)

            print("Waiting 5 seconds before next iteration...", flush=True)
            time.sleep(5)

        except Exception as e:
            print(f"Error en el bucle principal: {e}", flush=True)
            time.sleep(60)

# Ejecutar la función para obtener los objetos en bucle
if __name__ == "__main__":
    get_items_loop()