import json
import os
import requests
import time
import concurrent.futures
# Definiciones de rutas
base_path = os.path.dirname(os.path.abspath(__file__))
STEAM_ITEMS_JSON = os.path.join(base_path, "JSON", "steam_items.json")
WITHDRAWALS_JSON = os.path.join(base_path, "JSON", "withdrawals.json")
def load_api_key():
    config_path = os.path.join("Configs", "Api.json")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get("api_key_empire")
    except Exception as e:
        print(f"Error al cargar la API key: {e}", flush=True)
        return None
API_KEY = load_api_key()  # Reemplaza con tu API Key



# Función para restar comisiones
def subtract_fee(input_value):
    intervals = [0.02, 0.21, 0.32, 0.43]
    fees = [0.02, 0.03, 0.04, 0.05, 0.07, 0.09]
    while input_value > intervals[-1]:
        last_element = intervals[-1]
        if len(intervals) % 2 == 0:
            intervals.append(round(last_element + 0.12, 2))
        else:
            intervals.append(round(last_element + 0.11, 2))
    while len(intervals) > len(fees):
        last_element = fees[-1]
        if len(fees) % 2 == 0:
            fees.append(round(last_element + 0.01, 2))
        else:
            fees.append(round(last_element + 0.02, 2))
    first_greater = next((value for value in intervals if value >= input_value), None)
    index_of_first_greater = intervals.index(first_greater)
    fee_subtraction = round(input_value - fees[index_of_first_greater - 1], 2)
    return fee_subtraction

# Función para calcular la rentabilidad
def calcular_rentabilidad(steam_price, purchase_price):
    net_steam_price = subtract_fee(steam_price)
    if purchase_price == 0:
        return 0, net_steam_price
    rentabilidad = round((net_steam_price - purchase_price) / purchase_price, 4)
    return rentabilidad, net_steam_price

# Función para convertir monedas a dólares
def convert_to_usd(coins):
    conversion_rate = 0.6154
    return coins * conversion_rate


def withdraw_item(deposit_id, coin_value, item_name, steam_price_net, rentabilidad_net):
    conversion_rate = 100
    coin_value = conversion_rate * coin_value
    print(coin_value)

    url = f"https://csgoempire.com/api/v2/trading/deposit/{deposit_id}/withdraw"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "coin_value": coin_value
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))

        # Comprobar si la solicitud fue exitosa
        if response.status_code == 200:
            print("Retiro exitoso!")
            print("Response:", response.json())

            # Guardar detalles del retiro exitoso
            guardar_retiro_exitoso(item_name, coin_value, steam_price_net, rentabilidad_net)
        else:
            print(f"Error en la solicitud de retiro. Código de estado: {response.status_code}")
            print("Detalles:", response.json())

    except Exception as e:
        print(f"Error al realizar el retiro: {e}")


def place_bid(deposit_id, bid_value, item_name):
    url = f"https://csgoempire.com/api/v2/trading/deposit/{deposit_id}/bid"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "bid_value": bid_value
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))

        # Comprobar si la solicitud fue exitosa
        if response.status_code == 200:
            print(f"Oferta exitosa para el objeto '{item_name}'!")
            print("Response:", response.json())
        else:
            print(f"Error en la solicitud de oferta. Código de estado: {response.status_code}")
            print("Detalles:", response.json())

    except Exception as e:
        print(f"Error al realizar la oferta: {e}")


def withdraw_and_bid(deposit_id, coin_value, item_name, steam_price_net, rentabilidad_net):
    # Realizar el retiro
    withdraw_item(deposit_id, coin_value, item_name, steam_price_net, rentabilidad_net)

    # Realizar la oferta
    place_bid(deposit_id, coin_value, item_name)


# Función para guardar los detalles de los retiros exitosos
def guardar_retiro_exitoso(item_name, coin_value, steam_price_net, rentabilidad_net):
    # Cargar los retiros existentes
    if os.path.exists(WITHDRAWALS_JSON):
        with open(WITHDRAWALS_JSON, 'r', encoding='utf-8') as file:
            withdrawals = json.load(file)
    else:
        withdrawals = []


    withdrawal = {
        "item_name": item_name,
        "coin_value": coin_value/100 ,
        "price_usd": convert_to_usd(coin_value)/100,
        "net_steam_price": steam_price_net,
        "net_profitability": rentabilidad_net*100
    }
    withdrawals.append(withdrawal)

    # Guardar los retiros actualizados en el archivo JSON
    with open(WITHDRAWALS_JSON, 'w', encoding='utf-8') as file:
        json.dump(withdrawals, file, ensure_ascii=False, indent=4)

    print("Detalles del retiro guardados exitosamente.")

# Clase para manejar la solicitud de ítems
class CSGOEmpireClient:
    def __init__(self):
        pass

    # Función para obtener los objetos según el tipo de subasta
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
                    response = requests.get(items_url, headers=headers, params=params)
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
                        item_id = item.get("id", None)  # Obtener el ID del ítem

                        # Guardar el ítem si es nuevo o tiene un precio menor
                        if name not in all_items or price_in_coins < all_items[name]['Coin']:
                            all_items[name] = {
                                "Coin": price_in_coins,
                                "id": item_id
                            }

                    print(f"Page {page}: {len(items)} items fetched with auction={auction_type}.", flush=True)
                    page += 1
                    time.sleep(1)  # Pequeña pausa para evitar demasiadas solicitudes seguidas
                    break

                except Exception as e:
                    print(f"Error on attempt {attempt + 1}/{retries}: {e}", flush=True)
                    time.sleep(2)  # Esperar un poco antes de reintentar

                    if attempt + 1 == retries:
                        print(f"Failed after {retries} attempts with auction={auction_type}. Stopping.", flush=True)
                        return all_items
def save_items(items):
    os.makedirs("JSON", exist_ok=True)
    # Guardar directamente la lista de compras rentables
    json_filepath = os.path.join("JSON", "empire_autoshop_data.json")
    with open(json_filepath, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=4)
    print(f"Items saved to {json_filepath}! Total items fetched: {len(items)}", flush=True)

def load_profitability_config():
    config_path = os.path.join("Configs", "Autoshops.json")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get("profitability_empire", 2.0)
    except FileNotFoundError:
        print(f"Archivo de configuración {config_path} no encontrado. Usando valor por defecto de 2.0", flush=True)
        return 2.0
    except json.JSONDecodeError:
        print(f"Error al decodificar {config_path}. Usando valor por defecto de 2.0", flush=True)
        return 2.0
    except Exception as e:
        print(f"Error al cargar la configuración de rentabilidad: {e}. Usando valor por defecto de 2.0", flush=True)
        return 2.0
def get_items_loop():
    client = CSGOEmpireClient()
    PROFITABILITY_THRESHOLD = load_profitability_config()
    while True:
        api_key = load_api_key()
        if not api_key:
            print("API key no encontrada. Abortando.", flush=True)
            return

        headers = {
            "Authorization": f"Bearer {api_key}"
        }

        items_yes = client.fetch_items_by_auction_type("yes", headers)
        items_no = client.fetch_items_by_auction_type("no", headers)

        combined_items = items_yes.copy()
        for name, info in items_no.items():
            if name not in combined_items or info['Coin'] < combined_items[name]['Coin']:
                combined_items[name] = info

        # Cargar los precios de Steam desde el archivo JSON
        try:
            with open(STEAM_ITEMS_JSON, 'r', encoding='utf-8') as file:
                steam_items_data = json.load(file)
            steam_items_dict = {item['name']: item['price'] for item in steam_items_data}
        except FileNotFoundError:
            print(f"Error: '{STEAM_ITEMS_JSON}' no encontrado.", flush=True)
            continue

        # Calcular rentabilidad y preparar datos para guardar
        compras_rentables = []
        with concurrent.futures.ThreadPoolExecutor() as executor:  # Crear un executor para manejar las solicitudes
            futures = []
            for name, info in combined_items.items():
                steam_price = steam_items_dict.get(name)
                if steam_price:
                    rentabilidad, net_steam_price = calcular_rentabilidad(steam_price, info["Coin"] * 0.6154)
                    if rentabilidad >= PROFITABILITY_THRESHOLD:  # Ajustar el umbral según tus necesidades
                        info['Price'] = info["Coin"] * 0.6154
                        info['Name'] = name
                        info['Steam_price'] = steam_price
                        info['Net_steam_price'] = net_steam_price
                        info['Rentabilidad'] = rentabilidad * 100
                        compras_rentables.append(info)

                        # Ejecutar las funciones de retiro y oferta en paralelo
                        futures.append(executor.submit(withdraw_and_bid, info['id'], info["Coin"], name, net_steam_price, rentabilidad))

            # Esperar a que todas las tareas se completen
            for future in concurrent.futures.as_completed(futures):
                future.result()  # Esto lanzará cualquier excepción que ocurra

        # Guardar las compras rentables en un archivo JSON
        save_items(compras_rentables)

        print("Esperando 30 segundos antes de la siguiente iteración...", flush=True)
        time.sleep(5)

# Ejecutar la función para obtener los objetos en bucle
get_items_loop()
