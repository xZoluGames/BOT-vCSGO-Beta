import json
import os
import requests
import time
import concurrent.futures
import random
import traceback

# Definiciones de rutas
base_path = os.path.dirname(os.path.abspath(__file__))
STEAM_ITEMS_JSON = os.path.join(base_path, "JSON", "steam_items.json")
WITHDRAWALS_JSON = os.path.join(base_path, "JSON", "withdrawals.json")
PROXY_FILE = os.path.join(base_path, "proxy.txt")

class ProxyRequestManager:
    def __init__(self, proxies):
        self.proxies = proxies.copy() if proxies else []
        self.used_proxies = set()

    def get_fresh_proxy(self):
        available_proxies = [p for p in self.proxies if p not in self.used_proxies]
        
        if not available_proxies:
            self.used_proxies.clear()
            available_proxies = self.proxies

        if not available_proxies:
            return None

        proxy = random.choice(available_proxies)
        self.used_proxies.add(proxy)
        return proxy

    def make_concurrent_requests(self, urls, headers, max_workers=10, max_retries=5):
        results = []

        def fetch_with_retry(request_config, retry_count=0):
            if isinstance(request_config, str):
                url = request_config
                params = {}
                method = 'get'
            else:
                url = request_config.get('url')
                params = request_config.get('params', {})
                method = request_config.get('method', 'get').lower()

            for attempt in range(max_retries):
                proxy = self.get_fresh_proxy()
                proxies = {"http": proxy, "https": proxy} if proxy else {}

                try:
                    if method == 'get':
                        response = requests.get(
                            url, 
                            headers=headers, 
                            params=params, 
                            proxies=proxies,
                            timeout=10
                        )
                    elif method == 'post':
                        response = requests.post(
                            url, 
                            headers=headers, 
                            json=params, 
                            proxies=proxies,
                            timeout=10
                        )
                    else:
                        raise ValueError(f"Método no soportado: {method}",flush=True)

                    response.raise_for_status()
                    return response.json()

                except requests.exceptions.RequestException as e:
                    print(f"Error en intento {attempt + 1}/{max_retries} para {url}: {e}",flush=True)
                    
                    if "No more items" in str(e) or "404" in str(e):
                        print("No hay más objetos. Deteniendo solicitud.",flush=True)
                        return None

                    if attempt == max_retries - 1:
                        print(f"Falló después de {max_retries} intentos para {url}", flush=True)
                        traceback.print_exc()
                        return None

                    time.sleep(2)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(fetch_with_retry, config) for config in urls]
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    if result is not None:
                        results.append(result)
                except Exception as e:
                    print(f"Error en solicitud concurrente: {e}")

        return results

def load_proxies():
    try:
        with open(PROXY_FILE, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Error loading proxies: {e}", flush=True)
        return []

def load_api_key():
    config_path = os.path.join("Configs", "Api.json")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get("api_key_empire")
    except Exception as e:
        print(f"Error al cargar la API key: {e}", flush=True)
        return None

API_KEY = load_api_key()
PROXIES = load_proxies()

# [Funciones anteriores como subtract_fee, calcular_rentabilidad, etc. permanecen iguales]
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

def calcular_rentabilidad(steam_price, purchase_price):
    net_steam_price = subtract_fee(steam_price)
    if purchase_price == 0:
        return 0, net_steam_price
    rentabilidad = round((net_steam_price - purchase_price) / purchase_price, 4)
    return rentabilidad, net_steam_price

def convert_to_usd(coins):
    conversion_rate = 0.6154
    return coins * conversion_rate

# [Funciones de retiro y oferta permanecen iguales]
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

        if response.status_code == 200:
            print("Retiro exitoso!",flush=True)
            print("Response:", response.json(),flush=True)
            guardar_retiro_exitoso(item_name, coin_value, steam_price_net, rentabilidad_net)
        else:
            print(f"Error en la solicitud de retiro. Código de estado: {response.status_code}",flush=True)
            print("Detalles:", response.json(),flush=True)

    except Exception as e:
        print(f"Error al realizar el retiro: {e}",flush=True)

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

        if response.status_code == 200:
            print(f"Oferta exitosa para el objeto '{item_name}'!",flush=True)
            print("Response:", response.json(),flush=True)
        else:
            print(f"Error en la solicitud de oferta. Código de estado: {response.status_code}",flush=True)
            print("Detalles:", response.json(),flush=True)

    except Exception as e:
        print(f"Error al realizar la oferta: {e}",flush=True)

def withdraw_and_bid(deposit_id, coin_value, item_name, steam_price_net, rentabilidad_net):
    withdraw_item(deposit_id, coin_value, item_name, steam_price_net, rentabilidad_net)
    place_bid(deposit_id, coin_value, item_name)

def guardar_retiro_exitoso(item_name, coin_value, steam_price_net, rentabilidad_net):
    if os.path.exists(WITHDRAWALS_JSON):
        with open(WITHDRAWALS_JSON, 'r', encoding='utf-8') as file:
            withdrawals = json.load(file)
    else:
        withdrawals = []

    withdrawal = {
        "item_name": item_name,
        "coin_value": coin_value/100,
        "price_usd": convert_to_usd(coin_value)/100,
        "net_steam_price": steam_price_net,
        "net_profitability": rentabilidad_net*100
    }
    withdrawals.append(withdrawal)

    with open(WITHDRAWALS_JSON, 'w', encoding='utf-8') as file:
        json.dump(withdrawals, file, ensure_ascii=False, indent=4)

    print("Detalles del retiro guardados exitosamente.",flush=True)

def save_items(items):
    os.makedirs("JSON", exist_ok=True)
    json_filepath = os.path.join("JSON", "empire_autoshop_data.json")
    with open(json_filepath, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=4)
    print(f"Items saved to {json_filepath}! Total items fetched: {len(items)}", flush=True)

class CSGOEmpireClient:
    def __init__(self):
        self.proxies = PROXIES
        self.proxy_manager = ProxyRequestManager(self.proxies)

    def fetch_multiple_auction_types(self, headers):
        requests_config = [
            {
                'url': 'https://csgoempire.com/api/v2/trading/items',
                'params': {
                    "per_page": 2500,
                    "page": 1,
                    "order": "market_value",
                    "sort": "asc",
                    "auction": auction_type
                }
            } for auction_type in ["yes", "no"]
        ]

        responses = self.proxy_manager.make_concurrent_requests(
            requests_config, 
            headers, 
            max_workers=10, 
            max_retries=5
        )

        combined_items = {}
        for response in responses:
            items = response.get('data', [])
            for item in items:
                name = item.get("market_name", "Unknown")
                price_in_coins = item.get("market_value", 0) / 100.0
                item_id = item.get("id", None)

                if name not in combined_items or price_in_coins < combined_items[name]['Coin']:
                    combined_items[name] = {
                        "Coin": price_in_coins,
                        "id": item_id
                    }

        return combined_items
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

        combined_items = client.fetch_multiple_auction_types(headers)

        try:
            with open(STEAM_ITEMS_JSON, 'r', encoding='utf-8') as file:
                steam_items_data = json.load(file)
            steam_items_dict = {item['name']: item['price'] for item in steam_items_data}
        except FileNotFoundError:
            print(f"Error: '{STEAM_ITEMS_JSON}' no encontrado.", flush=True)
            continue

        compras_rentables = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            for name, info in combined_items.items():
                steam_price = steam_items_dict.get(name)
                if steam_price:
                    rentabilidad, net_steam_price = calcular_rentabilidad(steam_price, info["Coin"] * 0.6154)
                    if rentabilidad >= PROFITABILITY_THRESHOLD:
                        info['Price'] = info["Coin"] * 0.6154
                        info['Name'] = name
                        info['Steam_price'] = steam_price
                        info['Net_steam_price'] = net_steam_price
                        info['Rentabilidad'] = rentabilidad * 100
                        compras_rentables.append(info)

                        futures.append(executor.submit(withdraw_and_bid, info['id'], info["Coin"], name, net_steam_price, rentabilidad))

            for future in concurrent.futures.as_completed(futures):
                future.result()

        save_items(compras_rentables)

        print("Esperando 1 segundos antes de la siguiente iteración...", flush=True)
        time.sleep(1)

# Ejecutar la función para obtener los objetos en bucle
get_items_loop()